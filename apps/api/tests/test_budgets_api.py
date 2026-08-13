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


def _create_budget(api_client: TestClient, advisor_id: int, client_id: int) -> dict:
    return api_client.post(
        f"/clients/{client_id}/budgets",
        json={"category": "dining", "monthly_limit": "400.00"},
        headers=_headers(advisor_id),
    ).json()


def test_create_budget_requires_owned_client(
    api_client: TestClient, advisor: Advisor
) -> None:
    response = api_client.post(
        "/clients/999999999/budgets",
        json={"category": "dining", "monthly_limit": "400.00"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 404


def test_create_and_list_budgets(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "budget1@example.com")

    created = _create_budget(api_client, advisor.id, client["id"])
    assert created["client_id"] == client["id"]
    assert created["category"] == "dining"

    list_response = api_client.get(
        f"/clients/{client['id']}/budgets", headers=_headers(advisor.id)
    )

    assert list_response.status_code == 200
    budgets = list_response.json()
    assert len(budgets) == 1


def test_invalid_budget_category_is_rejected(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "budget2@example.com")

    response = api_client.post(
        f"/clients/{client['id']}/budgets",
        json={"category": "vacations", "monthly_limit": "1000.00"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 422


def test_get_single_budget(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "budget3@example.com")
    budget = _create_budget(api_client, advisor.id, client["id"])

    response = api_client.get(
        f"/clients/{client['id']}/budgets/{budget['id']}",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["id"] == budget["id"]


def test_update_budget(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "budget4@example.com")
    budget = _create_budget(api_client, advisor.id, client["id"])

    response = api_client.patch(
        f"/clients/{client['id']}/budgets/{budget['id']}",
        json={"monthly_limit": "350.00"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["monthly_limit"] == "350.00"
    assert response.json()["category"] == "dining"  # untouched


def test_delete_budget(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "budget5@example.com")
    budget = _create_budget(api_client, advisor.id, client["id"])

    delete_response = api_client.delete(
        f"/clients/{client['id']}/budgets/{budget['id']}",
        headers=_headers(advisor.id),
    )
    assert delete_response.status_code == 204

    get_response = api_client.get(
        f"/clients/{client['id']}/budgets/{budget['id']}",
        headers=_headers(advisor.id),
    )
    assert get_response.status_code == 404


def test_advisor_cannot_access_another_advisors_budget(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "budget6@example.com")
    budget = _create_budget(api_client, advisor.id, client["id"])
    other_advisor_id = advisor.id + 999999

    get_response = api_client.get(
        f"/clients/{client['id']}/budgets/{budget['id']}",
        headers=_headers(other_advisor_id),
    )
    assert get_response.status_code == 404

    delete_response = api_client.delete(
        f"/clients/{client['id']}/budgets/{budget['id']}",
        headers=_headers(other_advisor_id),
    )
    assert delete_response.status_code == 404
