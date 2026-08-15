from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_owned_client, get_owned_debt
from app.models.client import Client
from app.models.debt import Debt
from app.schemas.debt import DebtCreate, DebtRead, DebtUpdate

router = APIRouter(prefix="/clients/{client_id}/debts", tags=["debts"])


@router.post("", response_model=DebtRead, status_code=status.HTTP_201_CREATED)
def create_debt(
    payload: DebtCreate,
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> Debt:
    debt = Debt(
        client_id=client.id,
        debt_type=payload.debt_type,
        description=payload.description,
        lender=payload.lender,
        original_term_months=payload.original_term_months,
        origination_year=payload.origination_year,
        balance=payload.balance,
        interest_rate=payload.interest_rate,
        current_payment=payload.current_payment,
        minimum_payment=payload.minimum_payment,
    )

    db.add(debt)
    db.commit()
    db.refresh(debt)

    return debt


@router.get("", response_model=list[DebtRead])
def list_debts(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> list[Debt]:
    stmt = select(Debt).where(Debt.client_id == client.id)

    return list(db.scalars(stmt).all())


@router.get("/{debt_id}", response_model=DebtRead)
def get_debt(debt: Debt = Depends(get_owned_debt)) -> Debt:
    return debt


@router.patch("/{debt_id}", response_model=DebtRead)
def update_debt(
    payload: DebtUpdate,
    db: Session = Depends(get_db),
    debt: Debt = Depends(get_owned_debt),
) -> Debt:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(debt, field, value)

    db.commit()
    db.refresh(debt)

    return debt


@router.delete("/{debt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_debt(
    db: Session = Depends(get_db),
    debt: Debt = Depends(get_owned_debt),
) -> None:
    db.delete(debt)
    db.commit()
