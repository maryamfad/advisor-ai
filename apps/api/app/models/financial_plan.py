import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.client import Client


class ActionItemCategory(enum.StrEnum):
    EMERGENCY_FUND = "emergency_fund"
    DEBT_PAYOFF = "debt_payoff"
    INSURANCE = "insurance"
    REGISTERED_ACCOUNT = "registered_account"
    RETIREMENT = "retirement"
    GOAL = "goal"
    OTHER = "other"


class ActionItemStatus(enum.StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class FinancialPlan(Base):
    """A generated snapshot -- not a live view -- of a client's plan.
    A new row each time the advisor regenerates it, preserving history
    for comparison/compliance, same versioning idea as
    FinancialNeedsAnalysis."""

    __tablename__ = "financial_plans"

    id: Mapped[int] = mapped_column(primary_key=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    summary_snapshot: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    narrative_summary: Mapped[str | None] = mapped_column(
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
        back_populates="financial_plans",
    )

    action_items: Mapped[list["FinancialPlanActionItem"]] = relationship(
        "FinancialPlanActionItem",
        back_populates="financial_plan",
        cascade="all, delete-orphan",
        order_by="FinancialPlanActionItem.priority",
    )


class FinancialPlanActionItem(Base):
    """One item of a FinancialPlan's checklist -- an ordered, working
    list rather than a static report, so status can be tracked over
    time as the advisor and client work through it."""

    __tablename__ = "financial_plan_action_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    financial_plan_id: Mapped[int] = mapped_column(
        ForeignKey("financial_plans.id"),
        nullable=False,
        index=True,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    category: Mapped[ActionItemCategory] = mapped_column(
        SAEnum(ActionItemCategory, name="action_item_category"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )

    target_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    status: Mapped[ActionItemStatus] = mapped_column(
        SAEnum(ActionItemStatus, name="action_item_status"),
        nullable=False,
        default=ActionItemStatus.NOT_STARTED,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    financial_plan: Mapped["FinancialPlan"] = relationship(
        "FinancialPlan",
        back_populates="action_items",
    )
