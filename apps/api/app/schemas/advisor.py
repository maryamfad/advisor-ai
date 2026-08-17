from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class AdvisorBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class AdvisorCreate(AdvisorBase):
    """Payload for POST /advisors."""


class AdvisorRead(AdvisorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
