from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models.advisor import Advisor
from app.models.client import Client as ClientModel


@pytest.fixture
def api_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def advisor() -> Generator[Advisor, None, None]:
    """Creates a throwaway advisor for a single test, then deletes it
    (and any clients it ended up owning) afterwards so tests don't
    leave rows behind in the dev database."""
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
        db.query(ClientModel).filter(
            ClientModel.advisor_id == advisor.id
        ).delete()
        db.delete(advisor)
        db.commit()
        db.close()
