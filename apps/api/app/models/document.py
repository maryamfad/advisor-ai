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
    REGULATORY = "regulatory"
    INVESTMENT = "investment"
    OTHER = "other"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    # The real owner, always set -- a document may or may not belong
    # to a client (client_id below is nullable, same shape as Task),
    # so ownership is always checked against this column directly,
    # never by chaining through the client. Distinct from
    # uploaded_by_advisor_id, which just records who clicked upload.
    advisor_id: Mapped[int] = mapped_column(
        ForeignKey("advisors.id"),
        nullable=False,
        index=True,
    )

    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id"),
        nullable=True,
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

    advisor: Mapped["Advisor"] = relationship(
        "Advisor",
        foreign_keys=[advisor_id],
    )

    client: Mapped["Client | None"] = relationship(
        "Client",
        back_populates="documents",
    )

    uploaded_by: Mapped["Advisor | None"] = relationship(
        "Advisor",
        foreign_keys=[uploaded_by_advisor_id],
    )
