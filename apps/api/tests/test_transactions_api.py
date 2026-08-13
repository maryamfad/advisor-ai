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


def _create_account(api_client: TestClient, advisor_id: int, client_id: int) -> dict:
    return api_client.post(
        f"/clients/{client_id}/accounts",
        json={"name": "Everyday Checking", "account_type": "checking"},
        headers=_headers(advisor_id),
    ).json()


def test_create_transaction_requires_owned_account(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "tx1@example.com")

    response = api_client.post(
        f"/clients/{client['id']}/accounts/999999999/transactions",
        json={
            "transaction_date": "2026-08-01",
            "description": "Groceries",
            "amount": "-84.20",
        },
        headers=_headers(advisor.id),
    )

    assert response.status_code == 404


def test_create_and_list_transactions(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "tx2@example.com")
    account = _create_account(api_client, advisor.id, client["id"])

    create_response = api_client.post(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions",
        json={
            "transaction_date": "2026-08-01",
            "description": "Trader Joe's",
            "merchant": "Trader Joe's",
            "amount": "-84.20",
            "category": "groceries",
        },
        headers=_headers(advisor.id),
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["account_id"] == account["id"]
    assert created["amount"] == "-84.20"
    assert created["category"] == "groceries"

    list_response = api_client.get(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions",
        headers=_headers(advisor.id),
    )

    assert list_response.status_code == 200
    transactions = list_response.json()
    assert len(transactions) == 1
    assert transactions[0]["description"] == "Trader Joe's"


def test_transaction_defaults_to_other_category(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "tx3@example.com")
    account = _create_account(api_client, advisor.id, client["id"])

    response = api_client.post(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions",
        json={
            "transaction_date": "2026-08-01",
            "description": "Misc",
            "amount": "-10.00",
        },
        headers=_headers(advisor.id),
    )

    assert response.status_code == 201
    assert response.json()["category"] == "other"


def test_advisor_cannot_access_another_advisors_account_transactions(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "tx4@example.com")
    account = _create_account(api_client, advisor.id, client["id"])
    other_advisor_id = advisor.id + 999999

    response = api_client.get(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions",
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 404


def test_account_from_different_client_returns_404(
    api_client: TestClient, advisor: Advisor
) -> None:
    client_a = _create_client(api_client, advisor.id, "tx5a@example.com")
    client_b = _create_client(api_client, advisor.id, "tx5b@example.com")
    account_a = _create_account(api_client, advisor.id, client_a["id"])

    # account_a belongs to client_a, not client_b -- requesting it
    # through client_b's URL should 404, not leak data across clients.
    response = api_client.get(
        f"/clients/{client_b['id']}/accounts/{account_a['id']}/transactions",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 404


def test_get_single_transaction(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "tx6@example.com")
    account = _create_account(api_client, advisor.id, client["id"])

    created = api_client.post(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions",
        json={
            "transaction_date": "2026-08-01",
            "description": "Coffee",
            "amount": "-4.50",
        },
        headers=_headers(advisor.id),
    ).json()

    response = api_client.get(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions/{created['id']}",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Coffee"


def test_update_transaction(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "tx7@example.com")
    account = _create_account(api_client, advisor.id, client["id"])

    created = api_client.post(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions",
        json={
            "transaction_date": "2026-08-01",
            "description": "Coffee",
            "amount": "-4.50",
            "category": "other",
        },
        headers=_headers(advisor.id),
    ).json()

    response = api_client.patch(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions/{created['id']}",
        json={"category": "dining"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["category"] == "dining"
    assert response.json()["description"] == "Coffee"  # untouched


def test_delete_transaction(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "tx8@example.com")
    account = _create_account(api_client, advisor.id, client["id"])

    created = api_client.post(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions",
        json={
            "transaction_date": "2026-08-01",
            "description": "Coffee",
            "amount": "-4.50",
        },
        headers=_headers(advisor.id),
    ).json()

    delete_response = api_client.delete(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions/{created['id']}",
        headers=_headers(advisor.id),
    )
    assert delete_response.status_code == 204

    list_response = api_client.get(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions",
        headers=_headers(advisor.id),
    )
    assert list_response.json() == []


def test_advisor_cannot_update_another_advisors_transaction(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "tx9@example.com")
    account = _create_account(api_client, advisor.id, client["id"])

    created = api_client.post(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions",
        json={
            "transaction_date": "2026-08-01",
            "description": "Coffee",
            "amount": "-4.50",
        },
        headers=_headers(advisor.id),
    ).json()

    other_advisor_id = advisor.id + 999999

    response = api_client.patch(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions/{created['id']}",
        json={"amount": "-999.00"},
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 404
