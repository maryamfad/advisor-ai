from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.financial_needs_analysis import RiskTolerance

if TYPE_CHECKING:
    from app.models.client import Client


class RiskQuestionnaire(Base):
    """One instance of the scored risk-tolerance questionnaire sent to
    a client. A client may retake it over time (many per Client); the
    advice engine always uses the latest completed one. The token is
    the client's only credential for the public, unauthenticated
    submit endpoint -- see app/api/routes/risk_questionnaire.py."""

    __tablename__ = "risk_questionnaires"

    id: Mapped[int] = mapped_column(primary_key=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    questions_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    answers: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    risk_tolerance: Mapped[RiskTolerance | None] = mapped_column(
        SAEnum(RiskTolerance, name="risk_tolerance"),
        nullable=True,
    )

    ai_summary: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="risk_questionnaires",
    )
