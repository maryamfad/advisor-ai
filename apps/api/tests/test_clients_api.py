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
