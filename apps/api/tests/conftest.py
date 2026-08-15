from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models.account import Account
from app.models.advisor import Advisor
from app.models.budget import Budget
from app.models.client import Client as ClientModel
from app.models.dependent import Dependent
from app.models.financial_goal import FinancialGoal
from app.models.spouse import Spouse
from app.models.task import Task
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
        # Tasks reference advisor_id directly (never null) and
        # optionally client_id, so clear them first, before either
        # clients or the advisor are touched.
        db.query(Task).filter(Task.advisor_id == advisor.id).delete(
            synchronize_session=False
        )

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
            db.query(Budget).filter(Budget.client_id.in_(client_ids)).delete(
                synchronize_session=False
            )
            db.query(Spouse).filter(Spouse.client_id.in_(client_ids)).delete(
                synchronize_session=False
            )
            db.query(Dependent).filter(
                Dependent.client_id.in_(client_ids)
            ).delete(synchronize_session=False)
            db.query(ClientModel).filter(
                ClientModel.id.in_(client_ids)
            ).delete(synchronize_session=False)

        db.delete(advisor)
        db.commit()
        db.close()
