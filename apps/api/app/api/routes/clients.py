from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_advisor_id, get_db
from app.models.advisor import Advisor
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate

router = APIRouter(prefix="/clients", tags=["clients"])


def _get_owned_client_or_404(
    db: Session, client_id: int, advisor_id: int
) -> Client:
    """Fetch a client by id, scoped to the acting advisor.

    Returns 404 (not 403) when the client exists but belongs to a
    different advisor, so the API never confirms another advisor's
    client IDs to a caller who doesn't own them.
    """
    client = db.get(Client, client_id)

    if client is None or client.advisor_id != advisor_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found.",
        )

    return client


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
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    advisor_id: int = Depends(get_current_advisor_id),
) -> Client:
    return _get_owned_client_or_404(db, client_id, advisor_id)


@router.patch("/{client_id}", response_model=ClientRead)
def update_client(
    client_id: int,
    payload: ClientUpdate,
    db: Session = Depends(get_db),
    advisor_id: int = Depends(get_current_advisor_id),
) -> Client:
    client = _get_owned_client_or_404(db, client_id, advisor_id)

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)

    return client
