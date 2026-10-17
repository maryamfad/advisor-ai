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

from app.api.dependencies import get_current_advisor_id, get_db, get_owned_client
from app.core.config import settings
from app.models.client import Client
from app.models.document import Document, DocumentCategory
from app.schemas.document import DocumentRead
from app.services.policy_document_ingestion import (
    EmbeddingUnavailableError,
    ingest_policy_document,
)

router = APIRouter(prefix="/clients/{client_id}/documents", tags=["documents"])


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
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
    advisor_id: int = Depends(get_current_advisor_id),
) -> Document:
    raw_bytes = file.file.read()

    client_dir = Path(settings.document_storage_dir) / str(client.id)
    client_dir.mkdir(parents=True, exist_ok=True)
    storage_path = client_dir / f"{uuid.uuid4().hex}_{file.filename}"
    storage_path.write_bytes(raw_bytes)

    document = Document(
        client_id=client.id,
        uploaded_by_advisor_id=advisor_id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        storage_path=str(storage_path),
        category=category,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    if category == DocumentCategory.INSURANCE_POLICY:
        try:
            ingest_policy_document(document, _extract_text(file.filename, raw_bytes))
        except EmbeddingUnavailableError as exc:
            # The file itself is already saved and the Document row
            # already committed -- only the policy-search enrichment
            # step is unavailable, same "optional feature, clear
            # error" pattern as the AI assistant's own 503.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
            ) from exc

    return document


@router.get("", response_model=list[DocumentRead])
def list_documents(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> list[Document]:
    stmt = select(Document).where(Document.client_id == client.id)

    return list(db.scalars(stmt).all())
