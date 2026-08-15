from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.income_source import IncomeFrequency
from app.models.spouse import HouseholdMemberRole


class IncomeSourceBase(BaseModel):
    owner: HouseholdMemberRole = HouseholdMemberRole.CLIENT
    source: str
    gross_amount: Decimal
    frequency: IncomeFrequency
    net_takehome: Decimal | None = None
    is_future: bool = False
    start_age: int | None = None


class IncomeSourceCreate(IncomeSourceBase):
    """Payload for POST /clients/{client_id}/income-sources. client_id
    comes from the URL, never from the request body."""


class IncomeSourceUpdate(BaseModel):
    """Payload for PATCH /clients/{client_id}/income-sources/{id}. All
    fields optional so the advisor can update just what changed."""

    owner: HouseholdMemberRole | None = None
    source: str | None = None
    gross_amount: Decimal | None = None
    frequency: IncomeFrequency | None = None
    net_takehome: Decimal | None = None
    is_future: bool | None = None
    start_age: int | None = None


class IncomeSourceRead(IncomeSourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    created_at: datetime
