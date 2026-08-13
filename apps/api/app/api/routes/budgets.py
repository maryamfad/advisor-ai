from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_owned_budget, get_owned_client
from app.models.budget import Budget
from app.models.client import Client
from app.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate

router = APIRouter(prefix="/clients/{client_id}/budgets", tags=["budgets"])


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(
    payload: BudgetCreate,
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> Budget:
    budget = Budget(
        client_id=client.id,
        category=payload.category,
        monthly_limit=payload.monthly_limit,
    )

    db.add(budget)
    db.commit()
    db.refresh(budget)

    return budget


@router.get("", response_model=list[BudgetRead])
def list_budgets(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> list[Budget]:
    stmt = select(Budget).where(Budget.client_id == client.id)

    return list(db.scalars(stmt).all())


@router.get("/{budget_id}", response_model=BudgetRead)
def get_budget(budget: Budget = Depends(get_owned_budget)) -> Budget:
    return budget


@router.patch("/{budget_id}", response_model=BudgetRead)
def update_budget(
    payload: BudgetUpdate,
    db: Session = Depends(get_db),
    budget: Budget = Depends(get_owned_budget),
) -> Budget:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(budget, field, value)

    db.commit()
    db.refresh(budget)

    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    db: Session = Depends(get_db),
    budget: Budget = Depends(get_owned_budget),
) -> None:
    db.delete(budget)
    db.commit()
