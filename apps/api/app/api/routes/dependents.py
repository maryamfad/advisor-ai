from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_owned_client, get_owned_dependent
from app.models.client import Client
from app.models.dependent import Dependent
from app.schemas.dependent import DependentCreate, DependentRead, DependentUpdate

router = APIRouter(prefix="/clients/{client_id}/dependents", tags=["dependents"])


@router.post("", response_model=DependentRead, status_code=status.HTTP_201_CREATED)
def create_dependent(
    payload: DependentCreate,
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> Dependent:
    dependent = Dependent(
        client_id=client.id,
        name=payload.name,
        date_of_birth=payload.date_of_birth,
        years_of_education_remaining=payload.years_of_education_remaining,
    )

    db.add(dependent)
    db.commit()
    db.refresh(dependent)

    return dependent


@router.get("", response_model=list[DependentRead])
def list_dependents(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> list[Dependent]:
    stmt = select(Dependent).where(Dependent.client_id == client.id)

    return list(db.scalars(stmt).all())


@router.get("/{dependent_id}", response_model=DependentRead)
def get_dependent(
    dependent: Dependent = Depends(get_owned_dependent),
) -> Dependent:
    return dependent


@router.patch("/{dependent_id}", response_model=DependentRead)
def update_dependent(
    payload: DependentUpdate,
    db: Session = Depends(get_db),
    dependent: Dependent = Depends(get_owned_dependent),
) -> Dependent:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(dependent, field, value)

    db.commit()
    db.refresh(dependent)

    return dependent


@router.delete("/{dependent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dependent(
    db: Session = Depends(get_db),
    dependent: Dependent = Depends(get_owned_dependent),
) -> None:
    db.delete(dependent)
    db.commit()
