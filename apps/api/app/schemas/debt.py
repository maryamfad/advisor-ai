from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.debt import DebtType


class DebtBase(BaseModel):
    debt_type: DebtType
    description: str | None = None
    lender: str | None = None
    original_term_months: int | None = None
    origination_year: int | None = None
    balance: Decimal
    interest_rate: Decimal | None = None
    current_payment: Decimal | None = None
    minimum_payment: Decimal | None = None


class DebtCreate(DebtBase):
    """Payload for POST /clients/{client_id}/debts. client_id comes
    from the URL, never from the request body."""


class DebtUpdate(BaseModel):
    """Payload for PATCH /clients/{client_id}/debts/{debt_id}. All
    fields optional so the advisor can update just what changed."""

    debt_type: DebtType | None = None
    description: str | None = None
    lender: str | None = None
    original_term_months: int | None = None
    origination_year: int | None = None
    balance: Decimal | None = None
    interest_rate: Decimal | None = None
    current_payment: Decimal | None = None
    minimum_payment: Decimal | None = None


class DebtRead(DebtBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    created_at: datetime
