from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.models.advisor import Advisor


def test_create_advisor(api_client: TestClient) -> None:
    email = f"pat.nguyen.advisor-api-test-{id(object())}@example.com"

    response = api_client.post(
        "/advisors",
        json={"first_name": "Pat", "last_name": "Nguyen", "email": email},
    )

    try:
        assert response.status_code == 201
        body = response.json()
        assert body["first_name"] == "Pat"
        assert body["email"] == email
        assert "id" in body
    finally:
        # No DELETE /advisors endpoint exists (not part of the picker's
        # minimal API) -- clean up directly so re-running the suite
        # against the same dev database doesn't hit the unique email
        # constraint from a leftover row.
        db = SessionLocal()
        db.query(Advisor).filter(Advisor.email == email).delete(
            synchronize_session=False
        )
        db.commit()
        db.close()


def test_list_advisors_includes_created_advisor(
    api_client: TestClient, advisor: Advisor
) -> None:
    response = api_client.get("/advisors")

    assert response.status_code == 200
    ids = [row["id"] for row in response.json()]
    assert advisor.id in ids


def test_get_advisor(api_client: TestClient, advisor: Advisor) -> None:
    response = api_client.get(f"/advisors/{advisor.id}")

    assert response.status_code == 200
    assert response.json()["id"] == advisor.id


def test_get_unknown_advisor_returns_404(api_client: TestClient) -> None:
    response = api_client.get("/advisors/999999999")

    assert response.status_code == 404
