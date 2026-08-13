from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.financial_goal import GoalStatus, GoalType


class GoalBase(BaseModel):
    name: str
    goal_type: GoalType
    target_amount: Decimal
    current_amount: Decimal = Decimal("0")
    monthly_contribution: Decimal | None = None
    target_date: date | None = None
    status: GoalStatus = GoalStatus.ACTIVE


class GoalCreate(GoalBase):
    """Payload for POST /clients/{client_id}/goals. client_id comes
    from the URL, never from the request body."""


class GoalRead(GoalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    created_at: datetime
