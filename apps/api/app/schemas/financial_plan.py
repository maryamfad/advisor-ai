from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.financial_plan import ActionItemCategory, ActionItemStatus


class FinancialPlanActionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    financial_plan_id: int
    priority: int
    category: ActionItemCategory
    title: str
    description: str
    target_amount: Decimal | None
    status: ActionItemStatus
    created_at: datetime


class FinancialPlanActionItemUpdate(BaseModel):
    """Payload for PATCH .../financial-plans/{plan_id}/action-items/{item_id}.
    Status is the only thing this checklist item can be updated to --
    everything else is fixed at generation time."""

    status: ActionItemStatus


class FinancialPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    generated_at: datetime
    summary_snapshot: dict
    narrative_summary: str | None
    created_at: datetime
    action_items: list[FinancialPlanActionItemRead] = []
