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


def _create_fna(
    api_client: TestClient, advisor_id: int, client_id: int, conducted_at: str
) -> dict:
    return api_client.post(
        f"/clients/{client_id}/financial-needs-analyses",
        json={
            "conducted_at": conducted_at,
            "risk_tolerance": "medium",
            "priority_debt": 9,
            "priority_retirement": 4,
            "wants_income_replacement": True,
            "income_replacement_percent": "70.00",
            "income_replacement_years": 10,
            "wants_mortgage_payoff": True,
            "wants_emergency_fund": True,
            "emergency_fund_months": 6,
        },
        headers=_headers(advisor_id),
    ).json()


def test_create_fna_requires_owned_client(
    api_client: TestClient, advisor: Advisor
) -> None:
    response = api_client.post(
        "/clients/999999999/financial-needs-analyses",
        json={"conducted_at": "2026-01-15"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 404


def test_create_and_list_fna(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "fna1@example.com")

    created = _create_fna(api_client, advisor.id, client["id"], "2026-01-15")
    assert created["client_id"] == client["id"]
    assert created["risk_tolerance"] == "medium"
    assert created["wants_debt_payoff"] is False  # untouched default
    assert created["wants_mortgage_payoff"] is True

    list_response = api_client.get(
        f"/clients/{client['id']}/financial-needs-analyses",
        headers=_headers(advisor.id),
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_list_orders_most_recent_first(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "fna2@example.com")
    _create_fna(api_client, advisor.id, client["id"], "2025-01-01")
    _create_fna(api_client, advisor.id, client["id"], "2026-06-01")

    list_response = api_client.get(
        f"/clients/{client['id']}/financial-needs-analyses",
        headers=_headers(advisor.id),
    )

    dates = [row["conducted_at"] for row in list_response.json()]
    assert dates == ["2026-06-01", "2025-01-01"]


def test_invalid_risk_tolerance_is_rejected(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "fna3@example.com")

    response = api_client.post(
        f"/clients/{client['id']}/financial-needs-analyses",
        json={"conducted_at": "2026-01-15", "risk_tolerance": "extreme"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 422


def test_get_single_fna(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "fna4@example.com")
    fna = _create_fna(api_client, advisor.id, client["id"], "2026-01-15")

    response = api_client.get(
        f"/clients/{client['id']}/financial-needs-analyses/{fna['id']}",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["id"] == fna["id"]


def test_update_fna(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "fna5@example.com")
    fna = _create_fna(api_client, advisor.id, client["id"], "2026-01-15")

    response = api_client.patch(
        f"/clients/{client['id']}/financial-needs-analyses/{fna['id']}",
        json={"risk_tolerance": "high"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["risk_tolerance"] == "high"
    assert response.json()["priority_debt"] == 9  # untouched


def test_delete_fna(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "fna6@example.com")
    fna = _create_fna(api_client, advisor.id, client["id"], "2026-01-15")

    delete_response = api_client.delete(
        f"/clients/{client['id']}/financial-needs-analyses/{fna['id']}",
        headers=_headers(advisor.id),
    )
    assert delete_response.status_code == 204

    get_response = api_client.get(
        f"/clients/{client['id']}/financial-needs-analyses/{fna['id']}",
        headers=_headers(advisor.id),
    )
    assert get_response.status_code == 404


def test_advisor_cannot_list_another_advisors_client_fnas(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "fna7@example.com")
    other_advisor_id = advisor.id + 999999

    response = api_client.get(
        f"/clients/{client['id']}/financial-needs-analyses",
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 404
