from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_owned_account
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionRead

router = APIRouter(
    prefix="/clients/{client_id}/accounts/{account_id}/transactions",
    tags=["transactions"],
)


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    account: Account = Depends(get_owned_account),
) -> Transaction:
    transaction = Transaction(
        account_id=account.id,
        transaction_date=payload.transaction_date,
        description=payload.description,
        merchant=payload.merchant,
        amount=payload.amount,
        category=payload.category,
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


@router.get("", response_model=list[TransactionRead])
def list_transactions(
    db: Session = Depends(get_db),
    account: Account = Depends(get_owned_account),
) -> list[Transaction]:
    stmt = (
        select(Transaction)
        .where(Transaction.account_id == account.id)
        .order_by(Transaction.transaction_date.desc())
    )

    return list(db.scalars(stmt).all())
