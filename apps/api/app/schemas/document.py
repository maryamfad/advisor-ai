from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentCategory


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    advisor_id: int
    client_id: int | None
    uploaded_by_advisor_id: int | None
    filename: str
    content_type: str
    storage_path: str
    category: DocumentCategory
    uploaded_at: datetime
