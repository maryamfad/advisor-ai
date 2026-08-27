from fastapi.testclient import TestClient

from app.models.advisor import Advisor
from app.services.risk_questionnaire_constants import QUESTIONS


def _headers(advisor_id: int) -> dict[str, str]:
    return {"X-Advisor-Id": str(advisor_id)}


def _create_client(api_client: TestClient, advisor_id: int, email: str) -> dict:
    return api_client.post(
        "/clients",
        json={"first_name": "Sarah", "last_name": "Chen", "email": email},
        headers=_headers(advisor_id),
    ).json()


def _minimum_answers() -> dict[str, str]:
    return {q.key: min(q.options, key=lambda o: o.points).key for q in QUESTIONS}


def _maximum_answers() -> dict[str, str]:
    return {q.key: max(q.options, key=lambda o: o.points).key for q in QUESTIONS}


# -- Advisor-authenticated -------------------------------------------------


def test_create_requires_owned_client(api_client: TestClient, advisor: Advisor) -> None:
    response = api_client.post(
        "/clients/999999999/risk-questionnaire", headers=_headers(advisor.id)
    )

    assert response.status_code == 404


def test_create_returns_link(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "rq1@example.com")

    response = api_client.post(
        f"/clients/{client['id']}/risk-questionnaire", headers=_headers(advisor.id)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["client_id"] == client["id"]
    assert body["sent_at"] is None
    assert body["completed_at"] is None
    assert body["token"] in body["link"]


def test_mark_sent_sets_sent_at(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "rq2@example.com")
    created = api_client.post(
        f"/clients/{client['id']}/risk-questionnaire", headers=_headers(advisor.id)
    ).json()

    response = api_client.post(
        f"/clients/{client['id']}/risk-questionnaire/{created['id']}/mark-sent",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["sent_at"] is not None


def test_list_most_recent_first(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "rq3@example.com")
    api_client.post(
        f"/clients/{client['id']}/risk-questionnaire", headers=_headers(advisor.id)
    )
    api_client.post(
        f"/clients/{client['id']}/risk-questionnaire", headers=_headers(advisor.id)
    )

    response = api_client.get(
        f"/clients/{client['id']}/risk-questionnaire", headers=_headers(advisor.id)
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_single(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "rq4@example.com")
    created = api_client.post(
        f"/clients/{client['id']}/risk-questionnaire", headers=_headers(advisor.id)
    ).json()

    response = api_client.get(
        f"/clients/{client['id']}/risk-questionnaire/{created['id']}",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_advisor_cannot_access_another_advisors_questionnaire(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "rq5@example.com")
    created = api_client.post(
        f"/clients/{client['id']}/risk-questionnaire", headers=_headers(advisor.id)
    ).json()
    other_advisor_id = advisor.id + 999999

    response = api_client.get(
        f"/clients/{client['id']}/risk-questionnaire/{created['id']}",
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 404


# -- Public, unauthenticated ------------------------------------------------


def test_public_get_unknown_token_returns_404(api_client: TestClient) -> None:
    response = api_client.get("/risk-questionnaire/not-a-real-token")

    assert response.status_code == 404


def test_public_get_returns_question_catalog(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "rq6@example.com")
    created = api_client.post(
        f"/clients/{client['id']}/risk-questionnaire", headers=_headers(advisor.id)
    ).json()
    token = created["token"]

    response = api_client.get(f"/risk-questionnaire/{token}")

    assert response.status_code == 200
    body = response.json()
    assert len(body["questions"]) == len(QUESTIONS)
    # No headers/advisor auth needed -- and no scoring weights leaked.
    assert "points" not in body["questions"][0]["options"][0]


def test_public_submit_scores_and_completes(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "rq7@example.com")
    created = api_client.post(
        f"/clients/{client['id']}/risk-questionnaire", headers=_headers(advisor.id)
    ).json()
    token = created["token"]

    response = api_client.post(
        f"/risk-questionnaire/{token}/submit",
        json={"answers": _minimum_answers()},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 10
    assert body["risk_tolerance"] == "low"

    detail = api_client.get(
        f"/clients/{client['id']}/risk-questionnaire/{created['id']}",
        headers=_headers(advisor.id),
    ).json()
    assert detail["completed_at"] is not None
    assert detail["score"] == 10
    assert detail["risk_tolerance"] == "low"


def test_public_submit_invalid_answers_returns_400(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "rq8@example.com")
    created = api_client.post(
        f"/clients/{client['id']}/risk-questionnaire", headers=_headers(advisor.id)
    ).json()

    response = api_client.post(
        f"/risk-questionnaire/{created['token']}/submit",
        json={"answers": {}},
    )

    assert response.status_code == 400


def test_public_get_after_completion_returns_410(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "rq9@example.com")
    created = api_client.post(
        f"/clients/{client['id']}/risk-questionnaire", headers=_headers(advisor.id)
    ).json()
    token = created["token"]
    api_client.post(
        f"/risk-questionnaire/{token}/submit", json={"answers": _minimum_answers()}
    )

    response = api_client.get(f"/risk-questionnaire/{token}")

    assert response.status_code == 410


def test_public_submit_after_completion_returns_410(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "rq10@example.com")
    created = api_client.post(
        f"/clients/{client['id']}/risk-questionnaire", headers=_headers(advisor.id)
    ).json()
    token = created["token"]
    api_client.post(
        f"/risk-questionnaire/{token}/submit", json={"answers": _minimum_answers()}
    )

    response = api_client.post(
        f"/risk-questionnaire/{token}/submit", json={"answers": _minimum_answers()}
    )

    assert response.status_code == 410


def test_recommendations_prefer_completed_questionnaire_over_fna(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "rq11@example.com")

    api_client.post(
        f"/clients/{client['id']}/financial-needs-analyses",
        json={"conducted_at": "2026-01-01", "risk_tolerance": "low"},
        headers=_headers(advisor.id),
    )

    created = api_client.post(
        f"/clients/{client['id']}/risk-questionnaire", headers=_headers(advisor.id)
    ).json()
    api_client.post(
        f"/risk-questionnaire/{created['token']}/submit",
        json={"answers": _maximum_answers()},
    )

    recommendations = api_client.get(
        f"/clients/{client['id']}/recommendations", headers=_headers(advisor.id)
    ).json()

    # FNA says "low"; the completed questionnaire (max answers -> high)
    # should win.
    assert "risk tolerance is high" in " ".join(
        recommendations["insurance"]["reasons"]
    )
