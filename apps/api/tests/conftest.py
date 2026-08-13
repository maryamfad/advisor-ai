from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models.account import Account
from app.models.advisor import Advisor
from app.models.client import Client as ClientModel
from app.models.financial_goal import FinancialGoal
from app.models.transaction import Transaction


@pytest.fixture
def api_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def advisor() -> Generator[Advisor, None, None]:
    """Creates a throwaway advisor for a single test, then deletes it
    (and anything it ended up owning) afterwards so tests don't leave
    rows behind in the dev database."""
    db = SessionLocal()

    advisor = Advisor(
        first_name="Test",
        last_name="Advisor",
        email=f"test-advisor-{id(object())}@example.com",
    )
    db.add(advisor)
    db.commit()
    db.refresh(advisor)

    try:
        yield advisor
    finally:
        client_ids = [
            row[0]
            for row in db.query(ClientModel.id)
            .filter(ClientModel.advisor_id == advisor.id)
            .all()
        ]

        # Bulk Query.delete() bypasses SQLAlchemy's ORM-level cascades,
        # so child rows (accounts, and anything else added later) must
        # be cleared explicitly before their parent clients, or the
        # foreign key constraint rejects the delete.
        if client_ids:
            account_ids = [
                row[0]
                for row in db.query(Account.id)
                .filter(Account.client_id.in_(client_ids))
                .all()
            ]

            if account_ids:
                db.query(Transaction).filter(
                    Transaction.account_id.in_(account_ids)
                ).delete(synchronize_session=False)

            db.query(Account).filter(Account.client_id.in_(client_ids)).delete(
                synchronize_session=False
            )
            db.query(FinancialGoal).filter(
                FinancialGoal.client_id.in_(client_ids)
            ).delete(synchronize_session=False)
            db.query(ClientModel).filter(
                ClientModel.id.in_(client_ids)
            ).delete(synchronize_session=False)

        db.delete(advisor)
        db.commit()
        db.close()
