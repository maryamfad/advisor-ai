from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.account import AccountType
from app.models.spouse import HouseholdMemberRole


class AccountBase(BaseModel):
    name: str
    account_type: AccountType
    institution: str | None = None
    balance: Decimal = Decimal("0")
    currency: str = "CAD"
    owner: HouseholdMemberRole = HouseholdMemberRole.CLIENT
    invest_rate: Decimal | None = None
    monthly_contribution: Decimal | None = None
    resp_beneficiary_dependent_id: int | None = None


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
    owner: HouseholdMemberRole | None = None
    invest_rate: Decimal | None = None
    monthly_contribution: Decimal | None = None
    resp_beneficiary_dependent_id: int | None = None


class AccountRead(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    created_at: datetime
