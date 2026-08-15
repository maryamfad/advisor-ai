from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_client_spouse, get_db, get_owned_client
from app.models.client import Client
from app.models.spouse import Spouse
from app.schemas.spouse import SpouseCreate, SpouseRead, SpouseUpdate

router = APIRouter(prefix="/clients/{client_id}/spouse", tags=["spouse"])


@router.post("", response_model=SpouseRead, status_code=status.HTTP_201_CREATED)
def create_spouse(
    payload: SpouseCreate,
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> Spouse:
    existing = db.scalar(select(Spouse).where(Spouse.client_id == client.id))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This client already has a spouse on file.",
        )

    spouse = Spouse(
        client_id=client.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        date_of_birth=payload.date_of_birth,
        email=payload.email,
        phone=payload.phone,
        employer=payload.employer,
        retirement_age=payload.retirement_age,
        life_expectancy_age=payload.life_expectancy_age,
    )

    db.add(spouse)
    db.commit()
    db.refresh(spouse)

    return spouse


@router.get("", response_model=SpouseRead)
def get_spouse(spouse: Spouse = Depends(get_client_spouse)) -> Spouse:
    return spouse


@router.patch("", response_model=SpouseRead)
def update_spouse(
    payload: SpouseUpdate,
    db: Session = Depends(get_db),
    spouse: Spouse = Depends(get_client_spouse),
) -> Spouse:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(spouse, field, value)

    db.commit()
    db.refresh(spouse)

    return spouse


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_spouse(
    db: Session = Depends(get_db),
    spouse: Spouse = Depends(get_client_spouse),
) -> None:
    db.delete(spouse)
    db.commit()
