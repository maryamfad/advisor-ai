import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.spouse import HouseholdMemberRole

if TYPE_CHECKING:
    from app.models.client import Client


class IncomeFrequency(enum.StrEnum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    SEMI_MONTHLY = "semi_monthly"
    MONTHLY = "monthly"
    ANNUALLY = "annually"


class IncomeSource(Base):
    """A declared income source for the client or spouse, from the FNA
    intake's Current Income / Anticipated Future Income tables. Distinct
    from Transaction (bank activity): this is self-reported gross
    income, which is what RRSP-room and insurance-need math need."""

    __tablename__ = "income_sources"

    id: Mapped[int] = mapped_column(primary_key=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    owner: Mapped[HouseholdMemberRole] = mapped_column(
        SAEnum(HouseholdMemberRole, name="household_member_role"),
        nullable=False,
        default=HouseholdMemberRole.CLIENT,
    )

    source: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    gross_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    frequency: Mapped[IncomeFrequency] = mapped_column(
        SAEnum(IncomeFrequency, name="income_frequency"),
        nullable=False,
    )

    net_takehome: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    is_future: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    start_age: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="income_sources",
    )
