from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.client import MaritalStatus


class ClientBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    date_of_birth: date | None = None
    marital_status: MaritalStatus | None = None
    first_time_home_buyer: bool = False
    retirement_age: int | None = None
    life_expectancy_age: int | None = None
    desired_retirement_monthly_income: Decimal | None = None
    desired_retirement_income_percent: Decimal | None = None


class ClientCreate(ClientBase):
    """Payload for POST /clients. advisor_id is taken from the
    authenticated advisor, never from the request body."""


class ClientUpdate(BaseModel):
    """Payload for PATCH /clients/{id}. All fields optional so the
    advisor can update just what changed."""

    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    date_of_birth: date | None = None
    marital_status: MaritalStatus | None = None
    first_time_home_buyer: bool | None = None
    retirement_age: int | None = None
    life_expectancy_age: int | None = None
    desired_retirement_monthly_income: Decimal | None = None
    desired_retirement_income_percent: Decimal | None = None


class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    advisor_id: int
    created_at: datetime
