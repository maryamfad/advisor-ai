from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_owned_client
from app.models.client import Client
from app.models.financial_goal import FinancialGoal
from app.schemas.goal import GoalCreate, GoalRead

router = APIRouter(prefix="/clients/{client_id}/goals", tags=["goals"])


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: GoalCreate,
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> FinancialGoal:
    goal = FinancialGoal(
        client_id=client.id,
        name=payload.name,
        goal_type=payload.goal_type,
        target_amount=payload.target_amount,
        current_amount=payload.current_amount,
        monthly_contribution=payload.monthly_contribution,
        target_date=payload.target_date,
        status=payload.status,
    )

    db.add(goal)
    db.commit()
    db.refresh(goal)

    return goal


@router.get("", response_model=list[GoalRead])
def list_goals(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> list[FinancialGoal]:
    stmt = select(FinancialGoal).where(FinancialGoal.client_id == client.id)

    return list(db.scalars(stmt).all())
