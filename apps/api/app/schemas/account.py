from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.account import AccountType


class AccountBase(BaseModel):
    name: str
    account_type: AccountType
    institution: str | None = None
    balance: Decimal = Decimal("0")
    currency: str = "USD"


class AccountCreate(AccountBase):
    """Payload for POST /clients/{client_id}/accounts. client_id comes
    from the URL, never from the request body."""


class AccountUpdate(BaseModel):
    """Payload for PATCH .../accounts/{account_id}. All fields optional
    so the advisor can update just what changed."""

    name: str | None = None
    account_type: AccountType | None = None
    institution: str | None = None
    balance: Decimal | None = None
    currency: str | None = None


class AccountRead(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    created_at: datetime
