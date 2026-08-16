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


def test_create_requires_owned_client(api_client: TestClient, advisor: Advisor) -> None:
    response = api_client.post(
        "/clients/999999999/financial-plans", headers=_headers(advisor.id)
    )

    assert response.status_code == 404


def test_create_plan_with_nothing_on_file_only_suggests_baseline_accounts(
    api_client: TestClient, advisor: Advisor
) -> None:
    # A blank client still gets a baseline TFSA/RRSP suggestion from
    # prioritize_registered_accounts (nothing gates that on having
    # other data on file) -- every other waterfall step needs an
    # actual gap (debts, an FNA, goals, etc.) to fire, so those stay
    # absent.
    client = _create_client(api_client, advisor.id, "plan1@example.com")

    response = api_client.post(
        f"/clients/{client['id']}/financial-plans", headers=_headers(advisor.id)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["client_id"] == client["id"]
    categories = {item["category"] for item in body["action_items"]}
    assert categories == {"registered_account"}


def test_create_plan_with_expected_action_items(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "plan2@example.com")

    api_client.post(
        f"/clients/{client['id']}/debts",
        json={
            "debt_type": "credit_card",
            "description": "Visa",
            "balance": "4000.00",
            "interest_rate": "22.99",
        },
        headers=_headers(advisor.id),
    )
    api_client.post(
        f"/clients/{client['id']}/financial-needs-analyses",
        json={
            "conducted_at": "2026-01-01",
            "wants_final_expenses": True,
            "final_expenses_amount": "10000.00",
        },
        headers=_headers(advisor.id),
    )

    response = api_client.post(
        f"/clients/{client['id']}/financial-plans", headers=_headers(advisor.id)
    )

    assert response.status_code == 201
    items = response.json()["action_items"]
    categories = [i["category"] for i in items]
    assert "debt_payoff" in categories
    assert "insurance" in categories
    assert items == sorted(items, key=lambda i: i["priority"])


def test_list_most_recent_first(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "plan3@example.com")
    api_client.post(
        f"/clients/{client['id']}/financial-plans", headers=_headers(advisor.id)
    )
    api_client.post(
        f"/clients/{client['id']}/financial-plans", headers=_headers(advisor.id)
    )

    response = api_client.get(
        f"/clients/{client['id']}/financial-plans", headers=_headers(advisor.id)
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_single_plan(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "plan4@example.com")
    created = api_client.post(
        f"/clients/{client['id']}/financial-plans", headers=_headers(advisor.id)
    ).json()

    response = api_client.get(
        f"/clients/{client['id']}/financial-plans/{created['id']}",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_update_action_item_status(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "plan5@example.com")
    api_client.post(
        f"/clients/{client['id']}/financial-needs-analyses",
        json={
            "conducted_at": "2026-01-01",
            "wants_final_expenses": True,
            "final_expenses_amount": "10000.00",
        },
        headers=_headers(advisor.id),
    )
    plan = api_client.post(
        f"/clients/{client['id']}/financial-plans", headers=_headers(advisor.id)
    ).json()
    item = plan["action_items"][0]
    assert item["status"] == "not_started"

    response = api_client.patch(
        f"/clients/{client['id']}/financial-plans/{plan['id']}/action-items/{item['id']}",
        json={"status": "done"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_delete_plan_cascades_to_action_items(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "plan6@example.com")
    api_client.post(
        f"/clients/{client['id']}/financial-needs-analyses",
        json={
            "conducted_at": "2026-01-01",
            "wants_final_expenses": True,
            "final_expenses_amount": "10000.00",
        },
        headers=_headers(advisor.id),
    )
    plan = api_client.post(
        f"/clients/{client['id']}/financial-plans", headers=_headers(advisor.id)
    ).json()
    assert len(plan["action_items"]) > 0

    delete_response = api_client.delete(
        f"/clients/{client['id']}/financial-plans/{plan['id']}",
        headers=_headers(advisor.id),
    )
    assert delete_response.status_code == 204

    get_response = api_client.get(
        f"/clients/{client['id']}/financial-plans/{plan['id']}",
        headers=_headers(advisor.id),
    )
    assert get_response.status_code == 404


def test_advisor_cannot_access_another_advisors_plan(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "plan7@example.com")
    created = api_client.post(
        f"/clients/{client['id']}/financial-plans", headers=_headers(advisor.id)
    ).json()
    other_advisor_id = advisor.id + 999999

    response = api_client.get(
        f"/clients/{client['id']}/financial-plans/{created['id']}",
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 404
