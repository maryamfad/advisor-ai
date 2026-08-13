from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.transaction import TransactionCategory


class BudgetBase(BaseModel):
    category: TransactionCategory
    monthly_limit: Decimal


class BudgetCreate(BudgetBase):
    """Payload for POST /clients/{client_id}/budgets. client_id comes
    from the URL, never from the request body."""


class BudgetUpdate(BaseModel):
    """Payload for PATCH /clients/{client_id}/budgets/{budget_id}. All
    fields optional so the advisor can update just what changed."""

    category: TransactionCategory | None = None
    monthly_limit: Decimal | None = None


class BudgetRead(BudgetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    created_at: datetime
