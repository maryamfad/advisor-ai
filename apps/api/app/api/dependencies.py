from collections.abc import Generator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.account import Account
from app.models.client import Client
from app.models.financial_goal import FinancialGoal
from app.models.transaction import Transaction


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_advisor_id(
    x_advisor_id: int | None = Header(default=None),
) -> int:
    """Resolve the acting advisor's id.

    TEMPORARY: real authentication (JWT-based, Phase 16 of the roadmap)
    hasn't been built yet. Until then we trust an X-Advisor-Id header so
    the rest of the API can be scoped by advisor ownership from day one,
    matching the rule that authorization is decided by the API layer,
    never inferred by a client or by the AI. Every route below filters by
    this id -- replace only this function when real auth lands; the
    routes and their ownership checks don't need to change.
    """
    if x_advisor_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Advisor-Id header (temporary stand-in for auth).",
        )

    return x_advisor_id


def get_owned_client(
    client_id: int,
    db: Session = Depends(get_db),
    advisor_id: int = Depends(get_current_advisor_id),
) -> Client:
    """Fetch a client by id, scoped to the acting advisor.

    Used as a dependency by any route nested under /clients/{client_id}/...
    (accounts, goals, documents, etc.) so ownership is checked in exactly
    one place. Returns 404 (not 403) when the client exists but belongs
    to a different advisor, so the API never confirms another advisor's
    client IDs to a caller who doesn't own them.
    """
    client = db.get(Client, client_id)

    if client is None or client.advisor_id != advisor_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found.",
        )

    return client


def get_owned_account(
    account_id: int,
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> Account:
    """Fetch an account by id, scoped to the already-verified owned
    client. Used by routes nested under
    /clients/{client_id}/accounts/{account_id}/... (transactions, etc.).
    Returns 404 (not 403) when the account exists but belongs to a
    different client, for the same enumeration-avoidance reason as
    get_owned_client.
    """
    account = db.get(Account, account_id)

    if account is None or account.client_id != client.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found.",
        )

    return account


def get_owned_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(get_owned_account),
) -> Transaction:
    """Fetch a transaction by id, scoped to the already-verified owned
    account. Used by routes nested under
    /clients/{client_id}/accounts/{account_id}/transactions/{transaction_id}.
    """
    transaction = db.get(Transaction, transaction_id)

    if transaction is None or transaction.account_id != account.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found.",
        )

    return transaction


def get_owned_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> FinancialGoal:
    """Fetch a financial goal by id, scoped to the already-verified
    owned client. Used by routes nested under
    /clients/{client_id}/goals/{goal_id}.
    """
    goal = db.get(FinancialGoal, goal_id)

    if goal is None or goal.client_id != client.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found.",
        )

    return goal
