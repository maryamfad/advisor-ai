from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langchain_postgres import PGVector

import app.api.routes.documents as documents_module
from app.db import SessionLocal
from app.models.advisor import Advisor
from app.models.client import Client as ClientModel
from app.models.document import Document
from app.services.policy_document_ingestion import search_policy_documents


def _headers(advisor_id: int) -> dict[str, str]:
    return {"X-Advisor-Id": str(advisor_id)}


@pytest.fixture
def second_advisor() -> Generator[Advisor, None, None]:
    """A genuine second advisor row -- unlike the 'other advisor' id
    used elsewhere in this suite for 404 checks (a fabricated id that
    never writes any data), this one actually owns a client/documents
    within a test, so it needs to be a row the FK constraints on
    clients.advisor_id/documents.advisor_id can resolve."""
    db = SessionLocal()
    other = Advisor(
        first_name="Other",
        last_name="Advisor",
        email=f"other-advisor-{id(object())}@example.com",
    )
    db.add(other)
    db.commit()
    db.refresh(other)

    try:
        yield other
    finally:
        client_ids = [
            row[0]
            for row in db.query(ClientModel.id)
            .filter(ClientModel.advisor_id == other.id)
            .all()
        ]
        db.query(Document).filter(Document.advisor_id == other.id).delete(
            synchronize_session=False
        )
        if client_ids:
            db.query(ClientModel).filter(ClientModel.id.in_(client_ids)).delete(
                synchronize_session=False
            )
        db.delete(other)
        db.commit()
        db.close()


def _create_client(api_client: TestClient, advisor_id: int, email: str) -> dict:
    return api_client.post(
        "/clients",
        json={"first_name": "Sarah", "last_name": "Chen", "email": email},
        headers=_headers(advisor_id),
    ).json()


def _upload(
    api_client: TestClient,
    advisor_id: int,
    *,
    filename: str,
    content: bytes,
    category: str,
    client_id: int | None = None,
):
    data = {"category": category}
    if client_id is not None:
        data["client_id"] = str(client_id)

    return api_client.post(
        "/documents",
        files={"file": (filename, content, "text/plain")},
        data=data,
        headers=_headers(advisor_id),
    )


@pytest.fixture(autouse=True)
def _isolated_document_storage(tmp_path: Path, monkeypatch) -> None:
    """Uploaded files land under pytest's own tmp_path rather than the
    real ./data/documents -- keeps tests from littering the working
    tree (and from colliding with each other)."""
    monkeypatch.setattr(
        documents_module.settings, "document_storage_dir", str(tmp_path)
    )


def test_upload_document_persists_file_and_row(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "doc1@example.com")

    response = _upload(
        api_client,
        advisor.id,
        filename="statement.txt",
        content=b"hello statement",
        category="statement",
        client_id=client["id"],
    )

    assert response.status_code == 201
    body = response.json()
    assert body["client_id"] == client["id"]
    assert body["advisor_id"] == advisor.id
    assert body["filename"] == "statement.txt"
    assert body["category"] == "statement"
    assert Path(body["storage_path"]).read_bytes() == b"hello statement"


def test_upload_firm_wide_document_with_no_client_id(
    api_client: TestClient, advisor: Advisor, fake_policy_vectorstore: PGVector
) -> None:
    response = _upload(
        api_client,
        advisor.id,
        filename="compliance.txt",
        content=b"firm-wide compliance notice",
        category="regulatory",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["client_id"] is None
    assert body["advisor_id"] == advisor.id
    assert body["category"] == "regulatory"


def test_upload_rejects_client_id_not_owned_by_advisor(
    api_client: TestClient, advisor: Advisor, second_advisor: Advisor
) -> None:
    other_client = _create_client(
        api_client, second_advisor.id, "doc-other@example.com"
    )

    response = _upload(
        api_client,
        advisor.id,
        filename="statement.txt",
        content=b"hello statement",
        category="statement",
        client_id=other_client["id"],
    )

    assert response.status_code == 400


def test_investment_category_round_trips(
    api_client: TestClient, advisor: Advisor, fake_policy_vectorstore: PGVector
) -> None:
    response = _upload(
        api_client,
        advisor.id,
        filename="fund_fact_sheet.txt",
        content=b"fund fact sheet",
        category="investment",
    )

    assert response.status_code == 201
    assert response.json()["category"] == "investment"

    list_response = api_client.get("/documents", headers=_headers(advisor.id))
    assert any(d["category"] == "investment" for d in list_response.json())


def test_list_documents_is_scoped_to_advisor(
    api_client: TestClient,
    advisor: Advisor,
    second_advisor: Advisor,
    fake_policy_vectorstore: PGVector,
) -> None:
    _upload(
        api_client,
        advisor.id,
        filename="mine.txt",
        content=b"mine",
        category="regulatory",
    )
    _upload(
        api_client,
        second_advisor.id,
        filename="theirs.txt",
        content=b"theirs",
        category="regulatory",
    )

    response = api_client.get("/documents", headers=_headers(advisor.id))

    assert [d["filename"] for d in response.json()] == ["mine.txt"]


def test_list_documents_filters_by_client_id_query_param(
    api_client: TestClient, advisor: Advisor, fake_policy_vectorstore: PGVector
) -> None:
    client = _create_client(api_client, advisor.id, "doc-filter@example.com")
    _upload(
        api_client,
        advisor.id,
        filename="for_client.txt",
        content=b"for client",
        category="statement",
        client_id=client["id"],
    )
    _upload(
        api_client,
        advisor.id,
        filename="firm_wide.txt",
        content=b"firm wide",
        category="regulatory",
    )

    response = api_client.get(
        "/documents", params={"client_id": client["id"]}, headers=_headers(advisor.id)
    )

    assert [d["filename"] for d in response.json()] == ["for_client.txt"]


def test_list_client_documents_returns_uploaded_documents(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "doc2@example.com")
    _upload(
        api_client,
        advisor.id,
        filename="id.txt",
        content=b"id contents",
        category="identification",
        client_id=client["id"],
    )

    response = api_client.get(
        f"/clients/{client['id']}/documents", headers=_headers(advisor.id)
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["category"] == "identification"


def test_upload_without_configured_embeddings_returns_503(
    api_client: TestClient, advisor: Advisor, monkeypatch
) -> None:
    import app.services.policy_document_ingestion as ingestion_module

    monkeypatch.setattr(ingestion_module.settings, "openai_api_key", None)

    response = _upload(
        api_client,
        advisor.id,
        filename="policy.txt",
        content=b"policy contents",
        category="regulatory",
    )

    assert response.status_code == 503


def test_per_client_upload_is_never_ingested(
    api_client: TestClient, advisor: Advisor, monkeypatch
) -> None:
    import app.services.policy_document_ingestion as ingestion_module

    # No OpenAI key configured -- if this upload attempted ingestion
    # it would 503, same as the firm-wide case above. A per-client
    # upload must succeed regardless, proving ingestion was never
    # attempted at all.
    monkeypatch.setattr(ingestion_module.settings, "openai_api_key", None)

    client = _create_client(api_client, advisor.id, "doc-never-ingested@example.com")

    response = _upload(
        api_client,
        advisor.id,
        filename="policy.txt",
        content=b"policy contents",
        category="insurance_policy",
        client_id=client["id"],
    )

    assert response.status_code == 201


def test_per_client_document_never_appears_in_search(
    api_client: TestClient,
    advisor: Advisor,
    fake_policy_vectorstore: PGVector,
) -> None:
    client = _create_client(api_client, advisor.id, "doc-not-searchable@example.com")

    upload = _upload(
        api_client,
        advisor.id,
        filename="policy.txt",
        content=b"This policy has a surrender value of ten thousand dollars.",
        category="insurance_policy",
        client_id=client["id"],
    ).json()

    results = search_policy_documents(advisor.id, "surrender value", k=10)

    assert not any(r["document_id"] == upload["id"] for r in results)


def test_firm_wide_document_is_searchable(
    api_client: TestClient,
    advisor: Advisor,
    fake_policy_vectorstore: PGVector,
) -> None:
    response = _upload(
        api_client,
        advisor.id,
        filename="policy.txt",
        content=b"This policy has a surrender value of ten thousand dollars.",
        category="regulatory",
    )
    assert response.status_code == 201
    document_id = response.json()["id"]

    results = search_policy_documents(advisor.id, "surrender value", k=4)

    assert any(r["document_id"] == document_id for r in results)


def test_firm_wide_search_is_scoped_to_advisor(
    api_client: TestClient,
    advisor: Advisor,
    second_advisor: Advisor,
    fake_policy_vectorstore: PGVector,
) -> None:
    _upload(
        api_client,
        advisor.id,
        filename="mine.txt",
        content=b"My firm mentions a disability waiver rider.",
        category="regulatory",
    )
    _upload(
        api_client,
        second_advisor.id,
        filename="theirs.txt",
        content=b"Their firm mentions a disability waiver rider.",
        category="regulatory",
    )

    results_for_mine = search_policy_documents(advisor.id, "disability waiver", k=10)

    assert len(results_for_mine) == 1
    assert results_for_mine[0]["source_document"] == "mine.txt"


def test_delete_document_removes_row_and_file(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "doc6@example.com")
    upload = _upload(
        api_client,
        advisor.id,
        filename="statement.txt",
        content=b"hello statement",
        category="statement",
        client_id=client["id"],
    ).json()
    storage_path = Path(upload["storage_path"])
    assert storage_path.exists()

    response = api_client.delete(
        f"/documents/{upload['id']}",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 204
    assert not storage_path.exists()

    list_response = api_client.get(
        f"/clients/{client['id']}/documents", headers=_headers(advisor.id)
    )
    assert list_response.json() == []


def test_delete_firm_wide_document_removes_row_and_file(
    api_client: TestClient, advisor: Advisor, fake_policy_vectorstore: PGVector
) -> None:
    upload = _upload(
        api_client,
        advisor.id,
        filename="compliance.txt",
        content=b"firm-wide compliance notice",
        category="regulatory",
    ).json()
    storage_path = Path(upload["storage_path"])
    assert storage_path.exists()

    response = api_client.delete(
        f"/documents/{upload['id']}",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 204
    assert not storage_path.exists()


def test_delete_document_requires_owned_advisor(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "doc7@example.com")
    upload = _upload(
        api_client,
        advisor.id,
        filename="statement.txt",
        content=b"hello statement",
        category="statement",
        client_id=client["id"],
    ).json()
    other_advisor_id = advisor.id + 999999

    response = api_client.delete(
        f"/documents/{upload['id']}",
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 404


def test_delete_firm_wide_document_removes_it_from_search(
    api_client: TestClient,
    advisor: Advisor,
    fake_policy_vectorstore: PGVector,
) -> None:
    upload = _upload(
        api_client,
        advisor.id,
        filename="policy.txt",
        content=b"This policy has a surrender value of ten thousand dollars.",
        category="regulatory",
    ).json()
    assert search_policy_documents(advisor.id, "surrender value", k=4)

    response = api_client.delete(
        f"/documents/{upload['id']}",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 204
    results = search_policy_documents(advisor.id, "surrender value", k=4)
    assert not any(r["document_id"] == upload["id"] for r in results)
