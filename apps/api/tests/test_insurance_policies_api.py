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


def _create_policy(api_client: TestClient, advisor_id: int, client_id: int) -> dict:
    return api_client.post(
        f"/clients/{client_id}/insurance-policies",
        json={
            "policy_type": "term_life",
            "provider": "Sun Life",
            "coverage_amount": "500000.00",
            "premium": "45.00",
            "premium_frequency": "monthly",
            "policy_year": 2023,
        },
        headers=_headers(advisor_id),
    ).json()


def test_create_policy_requires_owned_client(
    api_client: TestClient, advisor: Advisor
) -> None:
    response = api_client.post(
        "/clients/999999999/insurance-policies",
        json={"policy_type": "term_life", "provider": "Sun Life"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 404


def test_create_and_list_policies(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "policy1@example.com")

    created = _create_policy(api_client, advisor.id, client["id"])
    assert created["client_id"] == client["id"]
    assert created["insured_owner"] == "client"
    assert created["status"] == "active"

    list_response = api_client.get(
        f"/clients/{client['id']}/insurance-policies",
        headers=_headers(advisor.id),
    )

    assert list_response.status_code == 200
    policies = list_response.json()
    assert len(policies) == 1
    assert policies[0]["provider"] == "Sun Life"


def test_create_policy_for_spouse_with_beneficiary(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "policy2@example.com")

    response = api_client.post(
        f"/clients/{client['id']}/insurance-policies",
        json={
            "policy_type": "whole_life",
            "insured_owner": "spouse",
            "beneficiary": "Sarah Chen",
            "provider": "Manulife",
            "coverage_amount": "250000.00",
            "surrender_value": "12000.00",
        },
        headers=_headers(advisor.id),
    )

    assert response.status_code == 201
    created = response.json()
    assert created["insured_owner"] == "spouse"
    assert created["beneficiary"] == "Sarah Chen"
    assert created["surrender_value"] == "12000.00"


def test_get_single_policy(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "policy3@example.com")
    policy = _create_policy(api_client, advisor.id, client["id"])

    response = api_client.get(
        f"/clients/{client['id']}/insurance-policies/{policy['id']}",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["id"] == policy["id"]


def test_update_policy(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "policy4@example.com")
    policy = _create_policy(api_client, advisor.id, client["id"])

    response = api_client.patch(
        f"/clients/{client['id']}/insurance-policies/{policy['id']}",
        json={"status": "lapsed"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "lapsed"
    assert response.json()["provider"] == "Sun Life"  # untouched


def test_delete_policy(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "policy5@example.com")
    policy = _create_policy(api_client, advisor.id, client["id"])

    delete_response = api_client.delete(
        f"/clients/{client['id']}/insurance-policies/{policy['id']}",
        headers=_headers(advisor.id),
    )
    assert delete_response.status_code == 204

    get_response = api_client.get(
        f"/clients/{client['id']}/insurance-policies/{policy['id']}",
        headers=_headers(advisor.id),
    )
    assert get_response.status_code == 404


def test_advisor_cannot_list_another_advisors_client_policies(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "policy6@example.com")
    other_advisor_id = advisor.id + 999999

    response = api_client.get(
        f"/clients/{client['id']}/insurance-policies",
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 404
