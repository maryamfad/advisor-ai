"""Retrieval-quality eval for the RAG pipeline (ingest_policy_document
+ search_policy_documents). Like test_ai_agent_evals.py, this proves
the harness -- chunking, metadata storage, advisor-scoped similarity
search -- actually retrieves the right document for an obviously
relevant question. It is not a judgement of embedding-model quality:
the shared fake_policy_vectorstore fixture uses a deterministic
bag-of-hashed-words embedding (see tests/_fake_embeddings.py), not a
real semantic model.

All eval-set documents are ingested as firm-wide (no client) under a
single advisor, coexisting in one collection -- this proves pipeline
correctness for one advisor's firm-wide library. Advisor-level
isolation is covered separately by
test_documents_api.py::test_firm_wide_search_is_scoped_to_advisor.
"""

from collections.abc import Generator

import pytest
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


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_retrieval_hit_rate_across_eval_set(
    advisor: Advisor,
    db_session: Session,
    fake_policy_vectorstore: PGVector,
) -> None:
    for case in POLICY_EVAL_SET:
        document = Document(
            advisor_id=advisor.id,
            client_id=None,
            filename=case.filename,
            content_type="text/plain",
            storage_path=f"/tmp/{case.filename}",
            category=DocumentCategory.REGULATORY,
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)

        ingest_policy_document(document, case.document_text)

    total_questions = 0
    hits = 0

    for case in POLICY_EVAL_SET:
        for question in case.questions:
            total_questions += 1
            results = search_policy_documents(advisor.id, question, k=4)
            if any(r["source_document"] == case.filename for r in results):
                hits += 1

    hit_rate = hits / total_questions
    print(f"\nretrieval hit rate: {hits}/{total_questions} ({hit_rate:.0%})")

    assert hit_rate >= MIN_HIT_RATE
