import enum
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.advisor import Advisor
    from app.models.budget import Budget
    from app.models.debt import Debt
    from app.models.dependent import Dependent
    from app.models.document import Document
    from app.models.financial_goal import FinancialGoal
    from app.models.financial_needs_analysis import FinancialNeedsAnalysis
    from app.models.income_source import IncomeSource
    from app.models.insurance_policy import InsurancePolicy
    from app.models.spouse import Spouse
    from app.models.task import Task


class MaritalStatus(enum.StrEnum):
    SINGLE = "single"
    MARRIED = "married"
    COMMON_LAW = "common_law"
    DIVORCED = "divorced"
    WIDOWED = "widowed"


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

    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    marital_status: Mapped[MaritalStatus | None] = mapped_column(
        SAEnum(MaritalStatus, name="marital_status"),
        nullable=True,
    )

    first_time_home_buyer: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    retirement_age: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    life_expectancy_age: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    desired_retirement_monthly_income: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    desired_retirement_income_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
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

    spouse: Mapped["Spouse | None"] = relationship(
        "Spouse",
        back_populates="client",
        uselist=False,
        cascade="all, delete-orphan",
    )

    dependents: Mapped[list["Dependent"]] = relationship(
        "Dependent",
        back_populates="client",
        cascade="all, delete-orphan",
    )

    income_sources: Mapped[list["IncomeSource"]] = relationship(
        "IncomeSource",
        back_populates="client",
        cascade="all, delete-orphan",
    )

    debts: Mapped[list["Debt"]] = relationship(
        "Debt",
        back_populates="client",
        cascade="all, delete-orphan",
    )

    financial_needs_analyses: Mapped[list["FinancialNeedsAnalysis"]] = relationship(
        "FinancialNeedsAnalysis",
        back_populates="client",
        cascade="all, delete-orphan",
    )
