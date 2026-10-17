"""Embeds and stores insurance-policy document text in pgvector, and
searches it back out for the AI assistant's search_policy_documents
tool (app/services/ai_tools.py).

The one deliberate exception to this codebase's "every service
function is pure" rule -- embedding a document is unavoidably a live
API call, and searching touches the DB. Kept small and clearly
labeled as the exception, same category as market_data_client.py and
ai_agent.py.

client_id/document_id/chunk_index/filename are stored in PGVector's
own metadata JSONB column rather than a hand-rolled, FK'd table --
langchain_postgres.PGVector manages its own tables outside
SQLAlchemy's Base.metadata, so there's no Alembic-visible schema for
chunks themselves (only the `vector` extension is enabled by a
migration; see migrations/versions/d7aaf9bc765f_*). Client isolation
is enforced by filtering on `client_id` at query time, verified by
test_documents_api.py.
"""

from functools import lru_cache

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
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
    metadata to filter by client at search time and to cite the
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
                "client_id": document.client_id,
                "document_id": document.id,
                "chunk_index": index,
                "filename": document.filename,
            }
            for index in range(len(chunks))
        ],
    )
    return len(chunks)


def search_policy_documents(client_id: int, query: str, k: int = 4) -> list[dict]:
    """Returns the top-k passages for `query`, restricted to
    `client_id`'s own documents -- the metadata filter is what
    prevents one client's policy details from ever surfacing in
    another's conversation."""
    if not settings.openai_api_key:
        raise EmbeddingUnavailableError(
            "No openai_api_key configured -- set one in .env to search "
            "policy documents."
        )

    results = get_vectorstore().similarity_search_with_score(
        query, k=k, filter={"client_id": client_id}
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
