from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_advisor_id, get_db, get_owned_client
from app.models.advisor import Advisor
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    advisor_id: int = Depends(get_current_advisor_id),
) -> Client:
    if db.get(Advisor, advisor_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"No advisor with id {advisor_id} exists. "
                "Create the advisor first, or check your X-Advisor-Id header."
            ),
        )

    client = Client(
        advisor_id=advisor_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
    )

    db.add(client)
    db.commit()
    db.refresh(client)

    return client


@router.get("", response_model=list[ClientRead])
def list_clients(
    db: Session = Depends(get_db),
    advisor_id: int = Depends(get_current_advisor_id),
) -> list[Client]:
    stmt = select(Client).where(Client.advisor_id == advisor_id)

    return list(db.scalars(stmt).all())


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client: Client = Depends(get_owned_client)) -> Client:
    return client


@router.patch("/{client_id}", response_model=ClientRead)
def update_client(
    payload: ClientUpdate,
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> Client:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)

    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> None:
    # ORM-level delete (not a bulk query) so the cascade="all,
    # delete-orphan" on Client's relationships actually fires, taking
    # accounts, goals, budgets, insurance_policies, and documents with
    # it -- see app/models/client.py.
    db.delete(client)
    db.commit()
