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


def _create_dependent(
    api_client: TestClient, advisor_id: int, client_id: int, name: str = "Jamie"
) -> dict:
    return api_client.post(
        f"/clients/{client_id}/dependents",
        json={
            "name": name,
            "date_of_birth": "2015-06-01",
            "years_of_education_remaining": 14,
        },
        headers=_headers(advisor_id),
    ).json()


def test_create_dependent_requires_owned_client(
    api_client: TestClient, advisor: Advisor
) -> None:
    response = api_client.post(
        "/clients/999999999/dependents",
        json={"name": "Jamie"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 404


def test_create_and_list_dependents(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "dep1@example.com")

    created = _create_dependent(api_client, advisor.id, client["id"])
    assert created["client_id"] == client["id"]
    assert created["name"] == "Jamie"
    assert created["years_of_education_remaining"] == 14

    list_response = api_client.get(
        f"/clients/{client['id']}/dependents",
        headers=_headers(advisor.id),
    )

    assert list_response.status_code == 200
    dependents = list_response.json()
    assert len(dependents) == 1
    assert dependents[0]["name"] == "Jamie"


def test_get_single_dependent(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "dep2@example.com")
    dependent = _create_dependent(api_client, advisor.id, client["id"])

    response = api_client.get(
        f"/clients/{client['id']}/dependents/{dependent['id']}",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["id"] == dependent["id"]


def test_update_dependent(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "dep3@example.com")
    dependent = _create_dependent(api_client, advisor.id, client["id"])

    response = api_client.patch(
        f"/clients/{client['id']}/dependents/{dependent['id']}",
        json={"years_of_education_remaining": 12},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["years_of_education_remaining"] == 12
    assert response.json()["name"] == "Jamie"  # untouched


def test_delete_dependent(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "dep4@example.com")
    dependent = _create_dependent(api_client, advisor.id, client["id"])

    delete_response = api_client.delete(
        f"/clients/{client['id']}/dependents/{dependent['id']}",
        headers=_headers(advisor.id),
    )
    assert delete_response.status_code == 204

    get_response = api_client.get(
        f"/clients/{client['id']}/dependents/{dependent['id']}",
        headers=_headers(advisor.id),
    )
    assert get_response.status_code == 404


def test_advisor_cannot_list_another_advisors_client_dependents(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "dep5@example.com")
    other_advisor_id = advisor.id + 999999

    response = api_client.get(
        f"/clients/{client['id']}/dependents",
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 404


def test_multiple_dependents_per_client(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "dep6@example.com")
    _create_dependent(api_client, advisor.id, client["id"], name="Jamie")
    _create_dependent(api_client, advisor.id, client["id"], name="Riley")

    list_response = api_client.get(
        f"/clients/{client['id']}/dependents",
        headers=_headers(advisor.id),
    )

    names = {d["name"] for d in list_response.json()}
    assert names == {"Jamie", "Riley"}
