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


def _create_income_source(
    api_client: TestClient, advisor_id: int, client_id: int
) -> dict:
    return api_client.post(
        f"/clients/{client_id}/income-sources",
        json={
            "owner": "client",
            "source": "Salary",
            "gross_amount": "8000.00",
            "frequency": "monthly",
            "net_takehome": "6200.00",
        },
        headers=_headers(advisor_id),
    ).json()


def test_create_income_source_requires_owned_client(
    api_client: TestClient, advisor: Advisor
) -> None:
    response = api_client.post(
        "/clients/999999999/income-sources",
        json={
            "source": "Salary",
            "gross_amount": "8000.00",
            "frequency": "monthly",
        },
        headers=_headers(advisor.id),
    )

    assert response.status_code == 404


def test_create_and_list_income_sources(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "income1@example.com")

    created = _create_income_source(api_client, advisor.id, client["id"])
    assert created["client_id"] == client["id"]
    assert created["owner"] == "client"
    assert created["is_future"] is False

    list_response = api_client.get(
        f"/clients/{client['id']}/income-sources",
        headers=_headers(advisor.id),
    )

    assert list_response.status_code == 200
    sources = list_response.json()
    assert len(sources) == 1
    assert sources[0]["source"] == "Salary"


def test_create_future_income_source_for_spouse(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "income2@example.com")

    response = api_client.post(
        f"/clients/{client['id']}/income-sources",
        json={
            "owner": "spouse",
            "source": "CPP",
            "gross_amount": "1200.00",
            "frequency": "monthly",
            "is_future": True,
            "start_age": 65,
        },
        headers=_headers(advisor.id),
    )

    assert response.status_code == 201
    created = response.json()
    assert created["owner"] == "spouse"
    assert created["is_future"] is True
    assert created["start_age"] == 65


def test_invalid_frequency_is_rejected(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "income3@example.com")

    response = api_client.post(
        f"/clients/{client['id']}/income-sources",
        json={
            "source": "Salary",
            "gross_amount": "8000.00",
            "frequency": "hourly",
        },
        headers=_headers(advisor.id),
    )

    assert response.status_code == 422


def test_update_income_source(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "income4@example.com")
    income_source = _create_income_source(api_client, advisor.id, client["id"])

    response = api_client.patch(
        f"/clients/{client['id']}/income-sources/{income_source['id']}",
        json={"gross_amount": "8500.00"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["gross_amount"] == "8500.00"
    assert response.json()["source"] == "Salary"  # untouched


def test_delete_income_source(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "income5@example.com")
    income_source = _create_income_source(api_client, advisor.id, client["id"])

    delete_response = api_client.delete(
        f"/clients/{client['id']}/income-sources/{income_source['id']}",
        headers=_headers(advisor.id),
    )
    assert delete_response.status_code == 204

    get_response = api_client.get(
        f"/clients/{client['id']}/income-sources/{income_source['id']}",
        headers=_headers(advisor.id),
    )
    assert get_response.status_code == 404


def test_advisor_cannot_list_another_advisors_client_income_sources(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "income6@example.com")
    other_advisor_id = advisor.id + 999999

    response = api_client.get(
        f"/clients/{client['id']}/income-sources",
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 404
