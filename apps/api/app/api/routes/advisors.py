from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models.advisor import Advisor
from app.schemas.advisor import AdvisorCreate, AdvisorRead

router = APIRouter(prefix="/advisors", tags=["advisors"])


@router.post("", response_model=AdvisorRead, status_code=status.HTTP_201_CREATED)
def create_advisor(
    payload: AdvisorCreate,
    db: Session = Depends(get_db),
) -> Advisor:
    advisor = Advisor(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
    )

    db.add(advisor)
    db.commit()
    db.refresh(advisor)

    return advisor


@router.get("", response_model=list[AdvisorRead])
def list_advisors(db: Session = Depends(get_db)) -> list[Advisor]:
    return list(db.scalars(select(Advisor)).all())


@router.get("/{advisor_id}", response_model=AdvisorRead)
def get_advisor(advisor_id: int, db: Session = Depends(get_db)) -> Advisor:
    advisor = db.get(Advisor, advisor_id)
    if advisor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No advisor with id {advisor_id} exists.",
        )

    return advisor
