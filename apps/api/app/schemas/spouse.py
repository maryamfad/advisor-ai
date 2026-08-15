from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class SpouseBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    email: str | None = None
    phone: str | None = None
    employer: str | None = None
    retirement_age: int | None = None
    life_expectancy_age: int | None = None


class SpouseCreate(SpouseBase):
    """Payload for POST /clients/{client_id}/spouse. client_id comes
    from the URL, never from the request body."""


class SpouseUpdate(BaseModel):
    """Payload for PATCH /clients/{client_id}/spouse. All fields
    optional so the advisor can update just what changed."""

    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    email: str | None = None
    phone: str | None = None
    employer: str | None = None
    retirement_age: int | None = None
    life_expectancy_age: int | None = None


class SpouseRead(SpouseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    created_at: datetime
