from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langchain_postgres import PGVector

import app.api.routes.documents as documents_module
from app.models.advisor import Advisor
from app.services.policy_document_ingestion import search_policy_documents


def _headers(advisor_id: int) -> dict[str, str]:
    return {"X-Advisor-Id": str(advisor_id)}


def _create_client(api_client: TestClient, advisor_id: int, email: str) -> dict:
    return api_client.post(
        "/clients",
        json={"first_name": "Sarah", "last_name": "Chen", "email": email},
        headers=_headers(advisor_id),
    ).json()


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

    response = api_client.post(
        f"/clients/{client['id']}/documents",
        files={"file": ("statement.txt", b"hello statement", "text/plain")},
        data={"category": "statement"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["client_id"] == client["id"]
    assert body["filename"] == "statement.txt"
    assert body["category"] == "statement"
    assert Path(body["storage_path"]).read_bytes() == b"hello statement"


def test_list_documents_returns_uploaded_documents(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "doc2@example.com")
    api_client.post(
        f"/clients/{client['id']}/documents",
        files={"file": ("id.txt", b"id contents", "text/plain")},
        data={"category": "identification"},
        headers=_headers(advisor.id),
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
    client = _create_client(api_client, advisor.id, "doc3@example.com")
    import app.services.policy_document_ingestion as ingestion_module

    monkeypatch.setattr(ingestion_module.settings, "openai_api_key", None)

    response = api_client.post(
        f"/clients/{client['id']}/documents",
        files={"file": ("policy.txt", b"policy contents", "text/plain")},
        data={"category": "insurance_policy"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 503


def test_upload_insurance_policy_document_is_searchable(
    api_client: TestClient,
    advisor: Advisor,
    fake_policy_vectorstore: PGVector,
) -> None:
    client = _create_client(api_client, advisor.id, "doc4@example.com")

    response = api_client.post(
        f"/clients/{client['id']}/documents",
        files={
            "file": (
                "policy.txt",
                b"This policy has a surrender value of ten thousand dollars.",
                "text/plain",
            )
        },
        data={"category": "insurance_policy"},
        headers=_headers(advisor.id),
    )
    assert response.status_code == 201
    document_id = response.json()["id"]

    results = search_policy_documents(client["id"], "surrender value", k=4)

    assert any(r["document_id"] == document_id for r in results)


def test_insurance_policy_search_is_scoped_to_client(
    api_client: TestClient,
    advisor: Advisor,
    fake_policy_vectorstore: PGVector,
) -> None:
    client_a = _create_client(api_client, advisor.id, "doc5a@example.com")
    client_b = _create_client(api_client, advisor.id, "doc5b@example.com")

    api_client.post(
        f"/clients/{client_a['id']}/documents",
        files={
            "file": (
                "policy_a.txt",
                b"Client A policy mentions a disability waiver rider.",
                "text/plain",
            )
        },
        data={"category": "insurance_policy"},
        headers=_headers(advisor.id),
    )
    api_client.post(
        f"/clients/{client_b['id']}/documents",
        files={
            "file": (
                "policy_b.txt",
                b"Client B policy mentions a disability waiver rider.",
                "text/plain",
            )
        },
        data={"category": "insurance_policy"},
        headers=_headers(advisor.id),
    )

    results_for_a = search_policy_documents(client_a["id"], "disability waiver", k=10)

    assert len(results_for_a) == 1
    assert results_for_a[0]["source_document"] == "policy_a.txt"
