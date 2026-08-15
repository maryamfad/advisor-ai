import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.spouse import HouseholdMemberRole

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.dependent import Dependent
    from app.models.transaction import Transaction


class AccountType(enum.StrEnum):
    CHECKING = "checking"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    RETIREMENT = "retirement"
    CREDIT = "credit"
    LOAN = "loan"
    TFSA = "tfsa"
    RRSP = "rrsp"
    FHSA = "fhsa"
    RESP = "resp"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    account_type: Mapped[AccountType] = mapped_column(
        SAEnum(AccountType, name="account_type"),
        nullable=False,
    )

    institution: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=0,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="CAD",
    )

    owner: Mapped[HouseholdMemberRole] = mapped_column(
        SAEnum(HouseholdMemberRole, name="household_member_role"),
        nullable=False,
        default=HouseholdMemberRole.CLIENT,
    )

    invest_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    monthly_contribution: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    resp_beneficiary_dependent_id: Mapped[int | None] = mapped_column(
        ForeignKey("dependents.id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="accounts",
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="account",
        cascade="all, delete-orphan",
    )

    resp_beneficiary: Mapped["Dependent | None"] = relationship(
        "Dependent",
    )
