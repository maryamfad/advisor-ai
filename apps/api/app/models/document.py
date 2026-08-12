import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.advisor import Advisor
    from app.models.client import Client


class DocumentCategory(enum.StrEnum):
    STATEMENT = "statement"
    TAX_DOCUMENT = "tax_document"
    INSURANCE_POLICY = "insurance_policy"
    IDENTIFICATION = "identification"
    OTHER = "other"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    uploaded_by_advisor_id: Mapped[int | None] = mapped_column(
        ForeignKey("advisors.id"),
        nullable=True,
        index=True,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    category: Mapped[DocumentCategory] = mapped_column(
        SAEnum(DocumentCategory, name="document_category"),
        nullable=False,
        default=DocumentCategory.OTHER,
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="documents",
    )

    uploaded_by: Mapped["Advisor | None"] = relationship(
        "Advisor",
    )
