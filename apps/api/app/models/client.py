from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.advisor import Advisor
    from app.models.budget import Budget
    from app.models.document import Document
    from app.models.financial_goal import FinancialGoal
    from app.models.insurance_policy import InsurancePolicy
    from app.models.task import Task


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)

    advisor_id: Mapped[int] = mapped_column(
        ForeignKey("advisors.id"),
        nullable=False,
        index=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    advisor: Mapped["Advisor"] = relationship(
        "Advisor",
        back_populates="clients",
    )

    accounts: Mapped[list["Account"]] = relationship(
        "Account",
        back_populates="client",
        cascade="all, delete-orphan",
    )

    financial_goals: Mapped[list["FinancialGoal"]] = relationship(
        "FinancialGoal",
        back_populates="client",
        cascade="all, delete-orphan",
    )

    budgets: Mapped[list["Budget"]] = relationship(
        "Budget",
        back_populates="client",
        cascade="all, delete-orphan",
    )

    insurance_policies: Mapped[list["InsurancePolicy"]] = relationship(
        "InsurancePolicy",
        back_populates="client",
        cascade="all, delete-orphan",
    )

    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="client",
        cascade="all, delete-orphan",
    )

    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="client",
    )
