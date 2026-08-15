from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class DependentBase(BaseModel):
    name: str
    date_of_birth: date | None = None
    years_of_education_remaining: int | None = None


class DependentCreate(DependentBase):
    """Payload for POST /clients/{client_id}/dependents. client_id
    comes from the URL, never from the request body."""


class DependentUpdate(BaseModel):
    """Payload for PATCH /clients/{client_id}/dependents/{dependent_id}.
    All fields optional so the advisor can update just what changed."""

    name: str | None = None
    date_of_birth: date | None = None
    years_of_education_remaining: int | None = None


class DependentRead(DependentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    created_at: datetime
