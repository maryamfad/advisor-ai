import enum
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.client import Client


class PolicyType(enum.StrEnum):
    TERM_LIFE = "term_life"
    WHOLE_LIFE = "whole_life"
    DISABILITY = "disability"
    CRITICAL_ILLNESS = "critical_illness"
    HEALTH = "health"
    AUTO = "auto"
    HOME = "home"
    OTHER = "other"


class PremiumFrequency(enum.StrEnum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class PolicyStatus(enum.StrEnum):
    ACTIVE = "active"
    LAPSED = "lapsed"
    CANCELLED = "cancelled"


class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"

    id: Mapped[int] = mapped_column(primary_key=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    policy_type: Mapped[PolicyType] = mapped_column(
        SAEnum(PolicyType, name="policy_type"),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    policy_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    coverage_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    premium: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    premium_frequency: Mapped[PremiumFrequency | None] = mapped_column(
        SAEnum(PremiumFrequency, name="premium_frequency"),
        nullable=True,
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    status: Mapped[PolicyStatus] = mapped_column(
        SAEnum(PolicyStatus, name="policy_status"),
        nullable=False,
        default=PolicyStatus.ACTIVE,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="insurance_policies",
    )
