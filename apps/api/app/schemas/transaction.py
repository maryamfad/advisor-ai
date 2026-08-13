from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.transaction import TransactionCategory


class TransactionBase(BaseModel):
    transaction_date: date
    description: str
    merchant: str | None = None
    amount: Decimal
    category: TransactionCategory = TransactionCategory.OTHER


class TransactionCreate(TransactionBase):
    """Payload for POST .../accounts/{account_id}/transactions.
    account_id comes from the URL, never from the request body."""


class TransactionUpdate(BaseModel):
    """Payload for PATCH .../transactions/{transaction_id}. All fields
    optional so the advisor can update just what changed."""

    transaction_date: date | None = None
    description: str | None = None
    merchant: str | None = None
    amount: Decimal | None = None
    category: TransactionCategory | None = None


class TransactionRead(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    created_at: datetime
