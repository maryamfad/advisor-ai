from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    get_owned_client,
    get_owned_income_source,
)
from app.models.client import Client
from app.models.income_source import IncomeSource
from app.schemas.income_source import (
    IncomeSourceCreate,
    IncomeSourceRead,
    IncomeSourceUpdate,
)

router = APIRouter(
    prefix="/clients/{client_id}/income-sources", tags=["income-sources"]
)


@router.post(
    "", response_model=IncomeSourceRead, status_code=status.HTTP_201_CREATED
)
def create_income_source(
    payload: IncomeSourceCreate,
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> IncomeSource:
    income_source = IncomeSource(
        client_id=client.id,
        owner=payload.owner,
        source=payload.source,
        gross_amount=payload.gross_amount,
        frequency=payload.frequency,
        net_takehome=payload.net_takehome,
        is_future=payload.is_future,
        start_age=payload.start_age,
    )

    db.add(income_source)
    db.commit()
    db.refresh(income_source)

    return income_source


@router.get("", response_model=list[IncomeSourceRead])
def list_income_sources(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> list[IncomeSource]:
    stmt = select(IncomeSource).where(IncomeSource.client_id == client.id)

    return list(db.scalars(stmt).all())


@router.get("/{income_source_id}", response_model=IncomeSourceRead)
def get_income_source(
    income_source: IncomeSource = Depends(get_owned_income_source),
) -> IncomeSource:
    return income_source


@router.patch("/{income_source_id}", response_model=IncomeSourceRead)
def update_income_source(
    payload: IncomeSourceUpdate,
    db: Session = Depends(get_db),
    income_source: IncomeSource = Depends(get_owned_income_source),
) -> IncomeSource:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(income_source, field, value)

    db.commit()
    db.refresh(income_source)

    return income_source


@router.delete("/{income_source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income_source(
    db: Session = Depends(get_db),
    income_source: IncomeSource = Depends(get_owned_income_source),
) -> None:
    db.delete(income_source)
    db.commit()
