from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_owned_client
from app.models.account import Account
from app.models.client import Client
from app.schemas.account import AccountCreate, AccountRead

router = APIRouter(prefix="/clients/{client_id}/accounts", tags=["accounts"])


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> Account:
    account = Account(
        client_id=client.id,
        name=payload.name,
        account_type=payload.account_type,
        institution=payload.institution,
        balance=payload.balance,
        currency=payload.currency,
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account


@router.get("", response_model=list[AccountRead])
def list_accounts(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> list[Account]:
    stmt = select(Account).where(Account.client_id == client.id)

    return list(db.scalars(stmt).all())
