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


class GoalUpdate(BaseModel):
    """Payload for PATCH /clients/{client_id}/goals/{goal_id}. All
    fields optional so the advisor can update just what changed."""

    name: str | None = None
    goal_type: GoalType | None = None
    target_amount: Decimal | None = None
    current_amount: Decimal | None = None
    monthly_contribution: Decimal | None = None
    target_date: date | None = None
    status: GoalStatus | None = None


class GoalRead(GoalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    created_at: datetime
