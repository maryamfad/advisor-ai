import enum
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.account import Account


class TransactionCategory(enum.StrEnum):
    INCOME = "income"
    HOUSING = "housing"
    UTILITIES = "utilities"
    GROCERIES = "groceries"
    DINING = "dining"
    TRANSPORTATION = "transportation"
    HEALTHCARE = "healthcare"
    INSURANCE = "insurance"
    ENTERTAINMENT = "entertainment"
    SAVINGS_TRANSFER = "savings_transfer"
    DEBT_PAYMENT = "debt_payment"
    OTHER = "other"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )

    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    merchant: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    # Positive = money in, negative = money out.
    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    category: Mapped[TransactionCategory] = mapped_column(
        SAEnum(TransactionCategory, name="transaction_category"),
        nullable=False,
        default=TransactionCategory.OTHER,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="transactions",
    )
