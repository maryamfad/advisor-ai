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


def test_create_spouse_requires_owned_client(
    api_client: TestClient, advisor: Advisor
) -> None:
    response = api_client.post(
        "/clients/999999999/spouse",
        json={"first_name": "Alex", "last_name": "Chen"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 404


def test_create_and_get_spouse(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "spouse1@example.com")

    create_response = api_client.post(
        f"/clients/{client['id']}/spouse",
        json={
            "first_name": "Alex",
            "last_name": "Chen",
            "date_of_birth": "1985-03-14",
            "employer": "Acme Corp",
            "retirement_age": 65,
        },
        headers=_headers(advisor.id),
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["client_id"] == client["id"]
    assert created["first_name"] == "Alex"

    get_response = api_client.get(
        f"/clients/{client['id']}/spouse",
        headers=_headers(advisor.id),
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]


def test_get_spouse_404_when_none_exists(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "spouse2@example.com")

    response = api_client.get(
        f"/clients/{client['id']}/spouse",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 404


def test_cannot_create_second_spouse(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "spouse3@example.com")

    api_client.post(
        f"/clients/{client['id']}/spouse",
        json={"first_name": "Alex", "last_name": "Chen"},
        headers=_headers(advisor.id),
    )

    second_response = api_client.post(
        f"/clients/{client['id']}/spouse",
        json={"first_name": "Jordan", "last_name": "Chen"},
        headers=_headers(advisor.id),
    )

    assert second_response.status_code == 400


def test_update_spouse(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "spouse4@example.com")
    api_client.post(
        f"/clients/{client['id']}/spouse",
        json={"first_name": "Alex", "last_name": "Chen"},
        headers=_headers(advisor.id),
    )

    response = api_client.patch(
        f"/clients/{client['id']}/spouse",
        json={"employer": "New Employer"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["employer"] == "New Employer"
    assert response.json()["first_name"] == "Alex"  # untouched


def test_delete_spouse(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "spouse5@example.com")
    api_client.post(
        f"/clients/{client['id']}/spouse",
        json={"first_name": "Alex", "last_name": "Chen"},
        headers=_headers(advisor.id),
    )

    delete_response = api_client.delete(
        f"/clients/{client['id']}/spouse",
        headers=_headers(advisor.id),
    )
    assert delete_response.status_code == 204

    get_response = api_client.get(
        f"/clients/{client['id']}/spouse",
        headers=_headers(advisor.id),
    )
    assert get_response.status_code == 404


def test_advisor_cannot_access_another_advisors_spouse(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "spouse6@example.com")
    api_client.post(
        f"/clients/{client['id']}/spouse",
        json={"first_name": "Alex", "last_name": "Chen"},
        headers=_headers(advisor.id),
    )
    other_advisor_id = advisor.id + 999999

    response = api_client.get(
        f"/clients/{client['id']}/spouse",
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 404
