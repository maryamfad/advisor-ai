"""Retrieval-quality eval for the RAG pipeline (ingest_policy_document
+ search_policy_documents). Like test_ai_agent_evals.py, this proves
the harness -- chunking, metadata storage, client-scoped similarity
search -- actually retrieves the right document for an obviously
relevant question. It is not a judgement of embedding-model quality:
the shared fake_policy_vectorstore fixture uses a deterministic
bag-of-hashed-words embedding (see tests/_fake_embeddings.py), not a
real semantic model.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from langchain_postgres import PGVector
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.advisor import Advisor
from app.models.document import Document, DocumentCategory
from app.services.policy_document_ingestion import (
    ingest_policy_document,
    search_policy_documents,
)
from tests.fixtures.policy_eval_set import POLICY_EVAL_SET

MIN_HIT_RATE = 0.8


def _headers(advisor_id: int) -> dict[str, str]:
    return {"X-Advisor-Id": str(advisor_id)}


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_retrieval_hit_rate_across_eval_set(
    api_client: TestClient,
    advisor: Advisor,
    db_session,
    fake_policy_vectorstore: PGVector,
) -> None:
    # One client per case, all ingested into the same collection --
    # mirrors a real multi-client deployment and exercises
    # client-scoped filtering, not just raw similarity search.
    documents_by_filename: dict[str, tuple[int, Document]] = {}

    for case in POLICY_EVAL_SET:
        client = api_client.post(
            "/clients",
            json={
                "first_name": "Eval",
                "last_name": case.filename,
                "email": f"retrieval-eval-{case.filename}@example.com",
            },
            headers=_headers(advisor.id),
        ).json()

        document = Document(
            client_id=client["id"],
            filename=case.filename,
            content_type="text/plain",
            storage_path=f"/tmp/{case.filename}",
            category=DocumentCategory.INSURANCE_POLICY,
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)

        ingest_policy_document(document, case.document_text)
        documents_by_filename[case.filename] = (client["id"], document)

    total_questions = 0
    hits = 0

    for case in POLICY_EVAL_SET:
        client_id, _ = documents_by_filename[case.filename]
        for question in case.questions:
            total_questions += 1
            results = search_policy_documents(client_id, question, k=4)
            if any(r["source_document"] == case.filename for r in results):
                hits += 1

    hit_rate = hits / total_questions
    print(f"\nretrieval hit rate: {hits}/{total_questions} ({hit_rate:.0%})")

    assert hit_rate >= MIN_HIT_RATE
