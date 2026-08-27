import enum
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.client import Client


class InvestorRating(enum.StrEnum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class RiskTolerance(enum.StrEnum):
    LOW = "low"
    LOW_MEDIUM = "low_medium"
    MEDIUM = "medium"
    MEDIUM_HIGH = "medium_high"
    HIGH = "high"


class FinancialNeedsAnalysis(Base):
    """One row per FNA intake/review session (the source form is
    explicitly meant to be redone periodically). The recommendation
    engine always uses the most recent row for a client. Groups the three
    things the form groups together: household planning habits, the
    investor profile, goal priority ratings, and the client's own
    declared life-insurance needs (the DIME checklist)."""

    __tablename__ = "financial_needs_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    conducted_at: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # -- Household planning --------------------------------------------

    has_monthly_budget: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_regular_savings_plan: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )
    monthly_savings_capacity: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    biggest_financial_concern: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # -- Investor profile -------------------------------------------------

    investment_knowledge: Mapped[InvestorRating | None] = mapped_column(
        SAEnum(InvestorRating, name="investor_rating"), nullable=True
    )
    risk_tolerance: Mapped[RiskTolerance | None] = mapped_column(
        SAEnum(RiskTolerance, name="risk_tolerance"), nullable=True
    )
    investment_experience: Mapped[InvestorRating | None] = mapped_column(
        SAEnum(InvestorRating, name="investor_rating"), nullable=True
    )

    # -- Goal priority ratings (1-10) --------------------------------------

    priority_cash_flow: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority_protection: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority_retirement: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority_emergency_fund: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    priority_debt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority_estate_preservation: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    # -- Declared life-insurance needs (the DIME checklist) ----------------

    wants_debt_payoff: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    wants_income_replacement: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    income_replacement_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    income_replacement_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    income_replacement_years: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    wants_mortgage_payoff: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    wants_education_funding: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    education_funding_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    wants_final_expenses: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    final_expenses_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    wants_emergency_fund: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    emergency_fund_months: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="financial_needs_analyses",
    )
