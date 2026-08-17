from fastapi.testclient import TestClient

from app.models.advisor import Advisor


def test_create_advisor(api_client: TestClient) -> None:
    response = api_client.post(
        "/advisors",
        json={
            "first_name": "Pat",
            "last_name": "Nguyen",
            "email": "pat.nguyen.advisor-api-test@example.com",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["first_name"] == "Pat"
    assert body["email"] == "pat.nguyen.advisor-api-test@example.com"
    assert "id" in body


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
