from fastapi.testclient import TestClient

from app.models.advisor import Advisor


def _headers(advisor_id: int) -> dict[str, str]:
    return {"X-Advisor-Id": str(advisor_id)}


def _create_client(
    api_client: TestClient, advisor_id: int, email: str, **overrides
) -> dict:
    payload = {"first_name": "Sarah", "last_name": "Chen", "email": email}
    payload.update(overrides)
    response = api_client.post(
        "/clients", json=payload, headers=_headers(advisor_id)
    )
    return response.json()


def test_recommendations_require_owned_client(
    api_client: TestClient, advisor: Advisor
) -> None:
    response = api_client.get(
        "/clients/999999999/recommendations", headers=_headers(advisor.id)
    )

    assert response.status_code == 404


def test_recommendations_with_no_data_degrades_gracefully(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "recommendations1@example.com")

    response = api_client.get(
        f"/clients/{client['id']}/recommendations", headers=_headers(advisor.id)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["financial_summary"]["monthly_income"] == "0.00"
    assert body["insurance"]["estimated_coverage_need"] == "0.00"
    assert "No financial needs analysis on file" in " ".join(
        body["insurance"]["reasons"]
    )
    assert body["registered_accounts"][0]["owner"] == "client"


def test_recommendations_compute_financial_summary_from_income_sources_and_transactions(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "recommendations2@example.com")

    api_client.post(
        f"/clients/{client['id']}/income-sources",
        json={
            "source": "Salary",
            "gross_amount": "6000.00",
            "frequency": "monthly",
        },
        headers=_headers(advisor.id),
    )

    account = api_client.post(
        f"/clients/{client['id']}/accounts",
        json={"name": "Checking", "account_type": "checking", "balance": "5000.00"},
        headers=_headers(advisor.id),
    ).json()
    api_client.post(
        f"/clients/{client['id']}/accounts/{account['id']}/transactions",
        json={
            "transaction_date": "2026-08-01",
            "description": "Rent",
            "amount": "-1500.00",
        },
        headers=_headers(advisor.id),
    )

    response = api_client.get(
        f"/clients/{client['id']}/recommendations", headers=_headers(advisor.id)
    )

    body = response.json()
    assert body["financial_summary"]["monthly_income"] == "6000.00"
    assert body["financial_summary"]["monthly_expenses"] == "1500.00"
    assert body["financial_summary"]["monthly_cash_flow"] == "4500.00"
    assert body["financial_summary"]["net_worth"] == "5000.00"


def test_recommendations_insurance_need_uses_fna_dime_checklist(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "recommendations3@example.com")

    api_client.post(
        f"/clients/{client['id']}/financial-needs-analyses",
        json={
            "conducted_at": "2026-01-01",
            "wants_final_expenses": True,
            "final_expenses_amount": "15000.00",
        },
        headers=_headers(advisor.id),
    )

    response = api_client.get(
        f"/clients/{client['id']}/recommendations", headers=_headers(advisor.id)
    )

    body = response.json()
    assert body["insurance"]["estimated_coverage_need"] == "15000.00"
    assert body["insurance"]["coverage_gap"] == "15000.00"


def test_recommendations_existing_coverage_reduces_gap(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "recommendations4@example.com")

    api_client.post(
        f"/clients/{client['id']}/financial-needs-analyses",
        json={
            "conducted_at": "2026-01-01",
            "wants_final_expenses": True,
            "final_expenses_amount": "15000.00",
        },
        headers=_headers(advisor.id),
    )
    api_client.post(
        f"/clients/{client['id']}/insurance-policies",
        json={
            "policy_type": "term_life",
            "provider": "Sun Life",
            "coverage_amount": "10000.00",
            "status": "active",
        },
        headers=_headers(advisor.id),
    )

    response = api_client.get(
        f"/clients/{client['id']}/recommendations", headers=_headers(advisor.id)
    )

    body = response.json()
    assert body["insurance"]["existing_coverage"] == "10000.00"
    assert body["insurance"]["coverage_gap"] == "5000.00"


def test_recommendations_lapsed_policy_not_counted_as_existing_coverage(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "recommendations5@example.com")

    api_client.post(
        f"/clients/{client['id']}/insurance-policies",
        json={
            "policy_type": "term_life",
            "provider": "Sun Life",
            "coverage_amount": "10000.00",
            "status": "lapsed",
        },
        headers=_headers(advisor.id),
    )

    response = api_client.get(
        f"/clients/{client['id']}/recommendations", headers=_headers(advisor.id)
    )

    assert response.json()["insurance"]["existing_coverage"] == "0.00"


def test_recommendations_toggling_first_time_home_buyer_changes_fhsa_recommendation(
    api_client: TestClient, advisor: Advisor
) -> None:
    not_buyer = _create_client(
        api_client,
        advisor.id,
        "recommendations6@example.com",
        first_time_home_buyer=False,
    )
    buyer = _create_client(
        api_client,
        advisor.id,
        "recommendations7@example.com",
        first_time_home_buyer=True,
    )

    for client in (not_buyer, buyer):
        api_client.post(
            f"/clients/{client['id']}/goals",
            json={
                "name": "Buy a home",
                "goal_type": "home_purchase",
                "target_amount": "50000",
            },
            headers=_headers(advisor.id),
        )

    not_buyer_response = api_client.get(
        f"/clients/{not_buyer['id']}/recommendations", headers=_headers(advisor.id)
    ).json()
    buyer_response = api_client.get(
        f"/clients/{buyer['id']}/recommendations", headers=_headers(advisor.id)
    ).json()

    not_buyer_types = {
        r["account_type"]
        for r in not_buyer_response["registered_accounts"][0]["recommendations"]
    }
    buyer_types = {
        r["account_type"]
        for r in buyer_response["registered_accounts"][0]["recommendations"]
    }
    assert "fhsa" not in not_buyer_types
    assert "fhsa" in buyer_types


def test_recommendations_second_underfunded_dependent_adds_second_resp_recommendation(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "recommendations8@example.com")

    api_client.post(
        f"/clients/{client['id']}/dependents",
        json={"name": "Jamie", "date_of_birth": "2015-01-01"},
        headers=_headers(advisor.id),
    )
    api_client.post(
        f"/clients/{client['id']}/dependents",
        json={"name": "Riley", "date_of_birth": "2018-01-01"},
        headers=_headers(advisor.id),
    )

    response = api_client.get(
        f"/clients/{client['id']}/recommendations", headers=_headers(advisor.id)
    )

    resp_recommendations = [
        r
        for r in response.json()["registered_accounts"][0]["recommendations"]
        if r["account_type"] == "resp"
    ]
    assert len(resp_recommendations) == 2
    reasons = " ".join(r["reason"] for r in resp_recommendations)
    assert "Jamie" in reasons
    assert "Riley" in reasons


def test_recommendations_include_spouse_recommendations_when_spouse_exists(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "recommendations9@example.com")

    response_before = api_client.get(
        f"/clients/{client['id']}/recommendations", headers=_headers(advisor.id)
    ).json()
    assert len(response_before["registered_accounts"]) == 1

    api_client.post(
        f"/clients/{client['id']}/spouse",
        json={"first_name": "Alex", "last_name": "Chen"},
        headers=_headers(advisor.id),
    )

    response_after = api_client.get(
        f"/clients/{client['id']}/recommendations", headers=_headers(advisor.id)
    ).json()
    owners = {r["owner"] for r in response_after["registered_accounts"]}
    assert owners == {"client", "spouse"}
