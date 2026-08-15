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


def _create_debt(api_client: TestClient, advisor_id: int, client_id: int) -> dict:
    return api_client.post(
        f"/clients/{client_id}/debts",
        json={
            "debt_type": "credit_card",
            "lender": "Big Bank",
            "balance": "4500.00",
            "interest_rate": "19.99",
            "minimum_payment": "150.00",
        },
        headers=_headers(advisor_id),
    ).json()


def test_create_debt_requires_owned_client(
    api_client: TestClient, advisor: Advisor
) -> None:
    response = api_client.post(
        "/clients/999999999/debts",
        json={"debt_type": "credit_card", "balance": "4500.00"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 404


def test_create_and_list_debts(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "debt1@example.com")

    created = _create_debt(api_client, advisor.id, client["id"])
    assert created["client_id"] == client["id"]
    assert created["debt_type"] == "credit_card"
    assert created["interest_rate"] == "19.99"

    list_response = api_client.get(
        f"/clients/{client['id']}/debts",
        headers=_headers(advisor.id),
    )

    assert list_response.status_code == 200
    debts = list_response.json()
    assert len(debts) == 1
    assert debts[0]["lender"] == "Big Bank"


def test_invalid_debt_type_is_rejected(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "debt2@example.com")

    response = api_client.post(
        f"/clients/{client['id']}/debts",
        json={"debt_type": "yacht_loan", "balance": "500000"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 422


def test_get_single_debt(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "debt3@example.com")
    debt = _create_debt(api_client, advisor.id, client["id"])

    response = api_client.get(
        f"/clients/{client['id']}/debts/{debt['id']}",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["id"] == debt["id"]


def test_update_debt(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "debt4@example.com")
    debt = _create_debt(api_client, advisor.id, client["id"])

    response = api_client.patch(
        f"/clients/{client['id']}/debts/{debt['id']}",
        json={"balance": "4000.00"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["balance"] == "4000.00"
    assert response.json()["lender"] == "Big Bank"  # untouched


def test_delete_debt(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "debt5@example.com")
    debt = _create_debt(api_client, advisor.id, client["id"])

    delete_response = api_client.delete(
        f"/clients/{client['id']}/debts/{debt['id']}",
        headers=_headers(advisor.id),
    )
    assert delete_response.status_code == 204

    get_response = api_client.get(
        f"/clients/{client['id']}/debts/{debt['id']}",
        headers=_headers(advisor.id),
    )
    assert get_response.status_code == 404


def test_advisor_cannot_list_another_advisors_client_debts(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "debt6@example.com")
    other_advisor_id = advisor.id + 999999

    response = api_client.get(
        f"/clients/{client['id']}/debts",
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 404
