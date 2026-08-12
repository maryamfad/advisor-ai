from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class ClientBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None


class ClientCreate(ClientBase):
    advisor_id: int


class ClientResponse(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    advisor_id: int
    created_at: datetime
