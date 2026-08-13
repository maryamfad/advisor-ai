from fastapi.testclient import TestClient

from app.models.advisor import Advisor


def _headers(advisor_id: int) -> dict[str, str]:
    return {"X-Advisor-Id": str(advisor_id)}


def test_create_client_requires_advisor_header(api_client: TestClient) -> None:
    response = api_client.post(
        "/clients",
        json={"first_name": "Sarah", "last_name": "Chen", "email": "sarah@example.com"},
    )

    assert response.status_code == 401


def test_create_client_rejects_unknown_advisor_id(api_client: TestClient) -> None:
    response = api_client.post(
        "/clients",
        json={"first_name": "Sarah", "last_name": "Chen", "email": "sarah@example.com"},
        headers=_headers(advisor_id=999999999),
    )

    assert response.status_code == 400


def test_create_and_get_client(api_client: TestClient, advisor: Advisor) -> None:
    create_response = api_client.post(
        "/clients",
        json={
            "first_name": "Sarah",
            "last_name": "Chen",
            "email": "sarah.chen@example.com",
            "phone": "555-0100",
        },
        headers=_headers(advisor.id),
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["first_name"] == "Sarah"
    assert created["advisor_id"] == advisor.id

    get_response = api_client.get(
        f"/clients/{created['id']}",
        headers=_headers(advisor.id),
    )

    assert get_response.status_code == 200
    assert get_response.json()["email"] == "sarah.chen@example.com"


def test_list_clients_scoped_to_advisor(
    api_client: TestClient, advisor: Advisor
) -> None:
    api_client.post(
        "/clients",
        json={"first_name": "A", "last_name": "One", "email": "a1@example.com"},
        headers=_headers(advisor.id),
    )
    api_client.post(
        "/clients",
        json={"first_name": "B", "last_name": "Two", "email": "b2@example.com"},
        headers=_headers(advisor.id),
    )

    response = api_client.get("/clients", headers=_headers(advisor.id))

    assert response.status_code == 200
    names = {c["first_name"] for c in response.json()}
    assert names == {"A", "B"}


def test_update_client(api_client: TestClient, advisor: Advisor) -> None:
    created = api_client.post(
        "/clients",
        json={
            "first_name": "Sarah",
            "last_name": "Chen",
            "email": "sarah2@example.com",
        },
        headers=_headers(advisor.id),
    ).json()

    response = api_client.patch(
        f"/clients/{created['id']}",
        json={"phone": "555-9999"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["phone"] == "555-9999"
    assert response.json()["first_name"] == "Sarah"  # untouched fields stay


def test_advisor_cannot_access_another_advisors_client(
    api_client: TestClient, advisor: Advisor
) -> None:
    created = api_client.post(
        "/clients",
        json={
            "first_name": "Sarah",
            "last_name": "Chen",
            "email": "sarah3@example.com",
        },
        headers=_headers(advisor.id),
    ).json()

    other_advisor_id = advisor.id + 999999

    response = api_client.get(
        f"/clients/{created['id']}",
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 404


def test_get_nonexistent_client_returns_404(
    api_client: TestClient, advisor: Advisor
) -> None:
    response = api_client.get("/clients/999999999", headers=_headers(advisor.id))

    assert response.status_code == 404


def test_delete_client(api_client: TestClient, advisor: Advisor) -> None:
    created = api_client.post(
        "/clients",
        json={"first_name": "Sarah", "last_name": "Chen", "email": "del1@example.com"},
        headers=_headers(advisor.id),
    ).json()

    delete_response = api_client.delete(
        f"/clients/{created['id']}", headers=_headers(advisor.id)
    )
    assert delete_response.status_code == 204

    get_response = api_client.get(
        f"/clients/{created['id']}", headers=_headers(advisor.id)
    )
    assert get_response.status_code == 404


def test_delete_client_cascades_to_accounts_and_goals(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = api_client.post(
        "/clients",
        json={"first_name": "Sarah", "last_name": "Chen", "email": "del2@example.com"},
        headers=_headers(advisor.id),
    ).json()

    account = api_client.post(
        f"/clients/{client['id']}/accounts",
        json={"name": "Checking", "account_type": "checking"},
        headers=_headers(advisor.id),
    ).json()

    api_client.post(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions",
        json={
            "transaction_date": "2026-08-01",
            "description": "Groceries",
            "amount": "-50.00",
        },
        headers=_headers(advisor.id),
    )

    api_client.post(
        f"/clients/{client['id']}/goals",
        json={
            "name": "Emergency Fund",
            "goal_type": "emergency_fund",
            "target_amount": "5000",
        },
        headers=_headers(advisor.id),
    )

    api_client.post(
        f"/clients/{client['id']}/budgets",
        json={"category": "dining", "monthly_limit": "400.00"},
        headers=_headers(advisor.id),
    )

    delete_response = api_client.delete(
        f"/clients/{client['id']}", headers=_headers(advisor.id)
    )
    assert delete_response.status_code == 204

    # Deleting the client should not leave orphaned accounts/goals/
    # transactions behind -- the cascade in Client's relationships
    # should have removed them too.
    accounts_response = api_client.get(
        f"/clients/{client['id']}/accounts", headers=_headers(advisor.id)
    )
    assert accounts_response.status_code == 404

    budgets_response = api_client.get(
        f"/clients/{client['id']}/budgets", headers=_headers(advisor.id)
    )
    assert budgets_response.status_code == 404


def test_advisor_cannot_delete_another_advisors_client(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = api_client.post(
        "/clients",
        json={"first_name": "Sarah", "last_name": "Chen", "email": "del3@example.com"},
        headers=_headers(advisor.id),
    ).json()

    other_advisor_id = advisor.id + 999999

    response = api_client.delete(
        f"/clients/{client['id']}", headers=_headers(other_advisor_id)
    )
    assert response.status_code == 404
