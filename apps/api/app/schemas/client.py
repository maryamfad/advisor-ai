from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class ClientBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None


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


class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    advisor_id: int
    created_at: datetime
