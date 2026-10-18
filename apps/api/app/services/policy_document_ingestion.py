"""Embeds and stores firm-wide document text in pgvector, and
searches it back out for the AI assistant's search_policy_documents
tool (app/services/ai_tools.py).

Only documents uploaded with no client (firm-wide -- regulatory,
investment, or other practice-level material) are ever ingested here;
per-client documents are plain storage and never reach this module.
See the `client_id is None` check in
app/api/routes/documents.py::upload_document.

The one deliberate exception to this codebase's "every service
function is pure" rule -- embedding a document is unavoidably a live
API call, and searching touches the DB. Kept small and clearly
labeled as the exception, same category as market_data_client.py and
ai_agent.py.

advisor_id/client_id/document_id/chunk_index/filename are stored in
PGVector's own metadata JSONB column rather than a hand-rolled, FK'd
table -- langchain_postgres.PGVector manages its own tables outside
SQLAlchemy's Base.metadata, so there's no Alembic-visible schema for
chunks themselves (only the `vector` extension is enabled by a
migration; see migrations/versions/d7aaf9bc765f_*). Isolation is
enforced by filtering on `advisor_id` at query time (every ingested
document is firm-wide, so client_id is always null in practice and
isn't useful for filtering), verified by test_documents_api.py.
"""

import json
from functools import lru_cache

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.core.config import settings
from app.db import engine
from app.models.document import Document

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


class EmbeddingUnavailableError(Exception):
    """Raised when no openai_api_key is configured -- document
    ingestion and policy search are both disabled until one is set,
    same pattern as MarketDataUnavailableError."""


@lru_cache(maxsize=1)
def _embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=settings.embedding_model_name, api_key=settings.openai_api_key
    )


@lru_cache(maxsize=1)
def get_vectorstore() -> PGVector:
    """A single, process-wide PGVector handle -- cheap to construct
    (it just holds a connection string and an embeddings client until
    a query actually runs) and safe to share, since every call site
    passes its own client_id as a filter rather than relying on
    per-request isolation here.

    create_extension=False because the `vector` extension is already
    enabled by an Alembic migration -- PGVector would otherwise try
    (and in most deployments fail, for lack of privilege) to run
    CREATE EXTENSION itself on first use.
    """
    return PGVector(
        embeddings=_embeddings(),
        connection=settings.database_url,
        collection_name=settings.pgvector_collection_name,
        create_extension=False,
        use_jsonb=True,
    )


def chunk_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    return splitter.split_text(text)


def ingest_policy_document(document: Document, text: str) -> int:
    """Chunks `text` and embeds it into pgvector, tagged with enough
    metadata to filter by advisor at search time and to cite the
    source document in a tool result. Returns the number of chunks
    stored."""
    if not settings.openai_api_key:
        raise EmbeddingUnavailableError(
            "No openai_api_key configured -- set one in .env to ingest "
            "policy documents."
        )

    chunks = chunk_text(text)
    if not chunks:
        return 0

    get_vectorstore().add_texts(
        texts=chunks,
        metadatas=[
            {
                "advisor_id": document.advisor_id,
                "client_id": document.client_id,
                "document_id": document.id,
                "chunk_index": index,
                "filename": document.filename,
            }
            for index in range(len(chunks))
        ],
    )
    return len(chunks)


def delete_policy_document_chunks(document_id: int) -> None:
    """Removes any pgvector chunks for `document_id`, called when a
    Document row is deleted so a removed policy stops being
    searchable. Goes straight at PGVector's own table via a JSONB
    containment query rather than through PGVector itself -- its
    delete() only accepts chunk ids (never recorded; add_texts'
    return value is discarded in ingest_policy_document), and
    constructing it at all requires embeddings credentials this
    doesn't need. A no-op if nothing has ever been ingested yet (the
    table doesn't exist).
    """
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "DELETE FROM langchain_pg_embedding "
                    "WHERE cmetadata @> CAST(:filter AS jsonb)"
                ),
                {"filter": json.dumps({"document_id": document_id})},
            )
    except ProgrammingError:
        pass


def search_policy_documents(advisor_id: int, query: str, k: int = 4) -> list[dict]:
    """Returns the top-k passages for `query`, restricted to
    `advisor_id`'s own firm-wide documents -- the metadata filter is
    what prevents one advisor's documents from ever surfacing in
    another advisor's conversation. Every ingested document applies
    to all of that advisor's clients (nothing client-specific is ever
    ingested), so this is not further scoped by client."""
    if not settings.openai_api_key:
        raise EmbeddingUnavailableError(
            "No openai_api_key configured -- set one in .env to search "
            "policy documents."
        )

    results = get_vectorstore().similarity_search_with_score(
        query, k=k, filter={"advisor_id": advisor_id}
    )

    return [
        {
            "passage": document.page_content,
            "source_document": document.metadata.get("filename"),
            "document_id": document.metadata.get("document_id"),
            "score": score,
        }
        for document, score in results
    ]
