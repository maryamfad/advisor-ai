import uuid
from io import BytesIO
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_advisor_id,
    get_db,
    get_owned_client,
    get_owned_document,
)
from app.core.config import settings
from app.models.client import Client
from app.models.document import Document, DocumentCategory
from app.schemas.document import DocumentRead
from app.services.policy_document_ingestion import (
    EmbeddingUnavailableError,
    delete_policy_document_chunks,
    ingest_policy_document,
)

router = APIRouter(prefix="/documents", tags=["documents"])

# Read-only convenience route for browsing one client's documents.
# Separate router (different prefix) registered alongside the one
# above -- all mutation (upload/delete) lives on the advisor-scoped
# router, same split as tasks.py's router/client_tasks_router.
client_documents_router = APIRouter(
    prefix="/clients/{client_id}/documents", tags=["documents"]
)


def _validate_client_ownership(
    db: Session, client_id: int | None, advisor_id: int
) -> None:
    """If a client_id is supplied, make sure it refers to a client
    actually owned by the acting advisor -- otherwise an advisor could
    attach a document to a client that isn't theirs."""
    if client_id is None:
        return

    client = db.get(Client, client_id)

    if client is None or client.advisor_id != advisor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No client with id {client_id} owned by this advisor.",
        )


def _extract_text(filename: str, raw_bytes: bytes) -> str:
    """pypdf for .pdf uploads, a plain decode otherwise -- good enough
    for the policy documents this endpoint is meant for; not a general
    document-text-extraction service."""
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(raw_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    return raw_bytes.decode("utf-8", errors="ignore")


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    category: DocumentCategory = Form(DocumentCategory.OTHER),
    client_id: int | None = Form(None),
    db: Session = Depends(get_db),
    advisor_id: int = Depends(get_current_advisor_id),
) -> Document:
    _validate_client_ownership(db, client_id, advisor_id)

    raw_bytes = file.file.read()

    storage_dir = Path(settings.document_storage_dir) / (
        str(client_id) if client_id is not None else "firm"
    )
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / f"{uuid.uuid4().hex}_{file.filename}"
    storage_path.write_bytes(raw_bytes)

    document = Document(
        advisor_id=advisor_id,
        client_id=client_id,
        uploaded_by_advisor_id=advisor_id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        storage_path=str(storage_path),
        category=category,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    if client_id is None:
        # Firm-wide documents (no client) are the ones made searchable
        # by the AI assistant -- per-client documents are plain
        # storage, never ingested, regardless of category.
        try:
            ingest_policy_document(document, _extract_text(file.filename, raw_bytes))
        except EmbeddingUnavailableError as exc:
            # The file itself is already saved and the Document row
            # already committed -- only the search enrichment step is
            # unavailable, same "optional feature, clear error"
            # pattern as the AI assistant's own 503.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
            ) from exc

    return document


@router.get("", response_model=list[DocumentRead])
def list_documents(
    db: Session = Depends(get_db),
    advisor_id: int = Depends(get_current_advisor_id),
    client_id: int | None = None,
) -> list[Document]:
    stmt = select(Document).where(Document.advisor_id == advisor_id)

    if client_id is not None:
        stmt = stmt.where(Document.client_id == client_id)

    return list(db.scalars(stmt).all())


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    db: Session = Depends(get_db),
    document: Document = Depends(get_owned_document),
) -> None:
    # Best-effort: the row is the source of truth either way, and a
    # missing/already-gone file shouldn't block deleting the record.
    Path(document.storage_path).unlink(missing_ok=True)
    delete_policy_document_chunks(document.id)

    db.delete(document)
    db.commit()


@client_documents_router.get("", response_model=list[DocumentRead])
def list_client_documents(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> list[Document]:
    stmt = select(Document).where(Document.client_id == client.id)

    return list(db.scalars(stmt).all())
