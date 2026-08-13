from fastapi.testclient import TestClient

from app.models.advisor import Advisor


def _headers(advisor_id: int) -> dict[str, str]:
    return {"X-Advisor-Id": str(advisor_id)}


def _create_client(api_client: TestClient, advisor_id: int, email: str) -> dict:
    return api_client.post(
        "/clients",
        json={"first_name": "Sarah", "last_name": "Chen", "email": email},
        headers=_headers(advisor_id),
    ).json()


def test_create_goal_requires_owned_client(
    api_client: TestClient, advisor: Advisor
) -> None:
    response = api_client.post(
        "/clients/999999999/goals",
        json={
            "name": "Emergency Fund",
            "goal_type": "emergency_fund",
            "target_amount": "10000",
        },
        headers=_headers(advisor.id),
    )

    assert response.status_code == 404


def test_create_and_list_goals(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "goal1@example.com")

    create_response = api_client.post(
        f"/clients/{client['id']}/goals",
        json={
            "name": "Emergency Fund",
            "goal_type": "emergency_fund",
            "target_amount": "10000.00",
            "monthly_contribution": "500.00",
            "target_date": "2027-06-01",
        },
        headers=_headers(advisor.id),
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["client_id"] == client["id"]
    assert created["status"] == "active"
    assert created["current_amount"] == "0.00"

    list_response = api_client.get(
        f"/clients/{client['id']}/goals",
        headers=_headers(advisor.id),
    )

    assert list_response.status_code == 200
    goals = list_response.json()
    assert len(goals) == 1
    assert goals[0]["name"] == "Emergency Fund"


def test_invalid_goal_type_is_rejected(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "goal2@example.com")

    response = api_client.post(
        f"/clients/{client['id']}/goals",
        json={
            "name": "Buy a Yacht",
            "goal_type": "yacht",
            "target_amount": "500000",
        },
        headers=_headers(advisor.id),
    )

    assert response.status_code == 422


def test_advisor_cannot_list_another_advisors_client_goals(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "goal3@example.com")
    other_advisor_id = advisor.id + 999999

    response = api_client.get(
        f"/clients/{client['id']}/goals",
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 404
