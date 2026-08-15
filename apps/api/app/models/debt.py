import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.client import Client


class DebtType(enum.StrEnum):
    MORTGAGE_PRIMARY = "mortgage_primary"
    MORTGAGE_SECONDARY_HELOC = "mortgage_secondary_heloc"
    AUTO_LOAN = "auto_loan"
    STUDENT_LOAN = "student_loan"
    CREDIT_CARD = "credit_card"
    PERSONAL_LOAN = "personal_loan"
    OTHER = "other"


class Debt(Base):
    """A single debt from the FNA intake's Debts table -- richer than
    an Account's bare balance (rate, term, lender), used by the
    insurance-need and financial-plan waterfall calculations. Net-worth
    calculation keeps using Account balances, not this table, to avoid
    double-counting."""

    __tablename__ = "debts"

    id: Mapped[int] = mapped_column(primary_key=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    debt_type: Mapped[DebtType] = mapped_column(
        SAEnum(DebtType, name="debt_type"),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    lender: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    original_term_months: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    origination_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    interest_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    current_payment: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    minimum_payment: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="debts",
    )
