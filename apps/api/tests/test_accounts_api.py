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


def test_create_account_requires_owned_client(
    api_client: TestClient, advisor: Advisor
) -> None:
    response = api_client.post(
        "/clients/999999999/accounts",
        json={"name": "Checking", "account_type": "checking"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 404


def test_create_and_list_accounts(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "accounts1@example.com")

    create_response = api_client.post(
        f"/clients/{client['id']}/accounts",
        json={
            "name": "Everyday Checking",
            "account_type": "checking",
            "institution": "First Bank",
            "balance": "1450.32",
        },
        headers=_headers(advisor.id),
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["client_id"] == client["id"]
    assert created["balance"] == "1450.32"
    assert created["currency"] == "USD"

    list_response = api_client.get(
        f"/clients/{client['id']}/accounts",
        headers=_headers(advisor.id),
    )

    assert list_response.status_code == 200
    accounts = list_response.json()
    assert len(accounts) == 1
    assert accounts[0]["name"] == "Everyday Checking"


def test_invalid_account_type_is_rejected(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "accounts2@example.com")

    response = api_client.post(
        f"/clients/{client['id']}/accounts",
        json={"name": "Mystery Account", "account_type": "crypto_wallet"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 422


def test_advisor_cannot_list_another_advisors_client_accounts(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "accounts3@example.com")
    other_advisor_id = advisor.id + 999999

    response = api_client.get(
        f"/clients/{client['id']}/accounts",
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 404


def _create_account(api_client: TestClient, advisor_id: int, client_id: int) -> dict:
    return api_client.post(
        f"/clients/{client_id}/accounts",
        json={"name": "Everyday Checking", "account_type": "checking"},
        headers=_headers(advisor_id),
    ).json()


def test_get_single_account(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "accounts4@example.com")
    account = _create_account(api_client, advisor.id, client["id"])

    response = api_client.get(
        f"/clients/{client['id']}/accounts/{account['id']}",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["id"] == account["id"]


def test_update_account(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "accounts5@example.com")
    account = _create_account(api_client, advisor.id, client["id"])

    response = api_client.patch(
        f"/clients/{client['id']}/accounts/{account['id']}",
        json={"balance": "2500.00"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["balance"] == "2500.00"
    assert response.json()["name"] == "Everyday Checking"  # untouched


def test_delete_account_cascades_to_transactions(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "accounts6@example.com")
    account = _create_account(api_client, advisor.id, client["id"])

    api_client.post(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions",
        json={
            "transaction_date": "2026-08-01",
            "description": "Groceries",
            "amount": "-50.00",
        },
        headers=_headers(advisor.id),
    )

    delete_response = api_client.delete(
        f"/clients/{client['id']}/accounts/{account['id']}",
        headers=_headers(advisor.id),
    )
    assert delete_response.status_code == 204

    get_response = api_client.get(
        f"/clients/{client['id']}/accounts/{account['id']}",
        headers=_headers(advisor.id),
    )
    assert get_response.status_code == 404

    transactions_response = api_client.get(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions",
        headers=_headers(advisor.id),
    )
    # The account is gone, so its transaction sub-route 404s too --
    # confirms nothing is left dangling.
    assert transactions_response.status_code == 404


def test_advisor_cannot_update_another_advisors_account(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "accounts7@example.com")
    account = _create_account(api_client, advisor.id, client["id"])
    other_advisor_id = advisor.id + 999999

    response = api_client.patch(
        f"/clients/{client['id']}/accounts/{account['id']}",
        json={"balance": "999.00"},
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 404
