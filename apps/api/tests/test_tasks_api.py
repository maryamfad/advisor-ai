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


def test_create_task_without_client(api_client: TestClient, advisor: Advisor) -> None:
    response = api_client.post(
        "/tasks",
        json={"title": "Follow up on onboarding paperwork"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 201
    created = response.json()
    assert created["advisor_id"] == advisor.id
    assert created["client_id"] is None
    assert created["status"] == "open"
    assert created["completed_at"] is None


def test_create_task_with_owned_client(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "task1@example.com")

    response = api_client.post(
        "/tasks",
        json={"title": "Review portfolio", "client_id": client["id"]},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 201
    assert response.json()["client_id"] == client["id"]


def test_create_task_with_unowned_client_is_rejected(
    api_client: TestClient, advisor: Advisor
) -> None:
    other_advisor_id = advisor.id + 999999

    response = api_client.post(
        "/tasks",
        json={"title": "Sneaky task", "client_id": 999999999},
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 400


def test_list_tasks_scoped_to_advisor(api_client: TestClient, advisor: Advisor) -> None:
    api_client.post(
        "/tasks", json={"title": "Task A"}, headers=_headers(advisor.id)
    )
    api_client.post(
        "/tasks", json={"title": "Task B"}, headers=_headers(advisor.id)
    )

    response = api_client.get("/tasks", headers=_headers(advisor.id))

    assert response.status_code == 200
    titles = {t["title"] for t in response.json()}
    assert titles == {"Task A", "Task B"}


def test_list_tasks_filter_by_status(api_client: TestClient, advisor: Advisor) -> None:
    open_task = api_client.post(
        "/tasks", json={"title": "Open task"}, headers=_headers(advisor.id)
    ).json()
    to_complete = api_client.post(
        "/tasks", json={"title": "Will complete"}, headers=_headers(advisor.id)
    ).json()

    api_client.patch(
        f"/tasks/{to_complete['id']}",
        json={"status": "completed"},
        headers=_headers(advisor.id),
    )

    response = api_client.get(
        "/tasks?status_filter=open", headers=_headers(advisor.id)
    )

    assert response.status_code == 200
    ids = {t["id"] for t in response.json()}
    assert ids == {open_task["id"]}


def test_get_single_task(api_client: TestClient, advisor: Advisor) -> None:
    created = api_client.post(
        "/tasks", json={"title": "Follow up"}, headers=_headers(advisor.id)
    ).json()

    response = api_client.get(
        f"/tasks/{created['id']}", headers=_headers(advisor.id)
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Follow up"


def test_update_task_sets_completed_at(
    api_client: TestClient, advisor: Advisor
) -> None:
    created = api_client.post(
        "/tasks", json={"title": "Follow up"}, headers=_headers(advisor.id)
    ).json()
    assert created["completed_at"] is None

    response = api_client.patch(
        f"/tasks/{created['id']}",
        json={"status": "completed"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["status"] == "completed"
    assert updated["completed_at"] is not None


def test_moving_task_off_completed_clears_completed_at(
    api_client: TestClient, advisor: Advisor
) -> None:
    created = api_client.post(
        "/tasks", json={"title": "Follow up"}, headers=_headers(advisor.id)
    ).json()

    api_client.patch(
        f"/tasks/{created['id']}",
        json={"status": "completed"},
        headers=_headers(advisor.id),
    )

    response = api_client.patch(
        f"/tasks/{created['id']}",
        json={"status": "in_progress"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
    assert response.json()["completed_at"] is None


def test_update_task_client_id_validates_ownership(
    api_client: TestClient, advisor: Advisor
) -> None:
    created = api_client.post(
        "/tasks", json={"title": "Follow up"}, headers=_headers(advisor.id)
    ).json()

    response = api_client.patch(
        f"/tasks/{created['id']}",
        json={"client_id": 999999999},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 400


def test_delete_task(api_client: TestClient, advisor: Advisor) -> None:
    created = api_client.post(
        "/tasks", json={"title": "Follow up"}, headers=_headers(advisor.id)
    ).json()

    delete_response = api_client.delete(
        f"/tasks/{created['id']}", headers=_headers(advisor.id)
    )
    assert delete_response.status_code == 204

    get_response = api_client.get(
        f"/tasks/{created['id']}", headers=_headers(advisor.id)
    )
    assert get_response.status_code == 404


def test_advisor_cannot_access_another_advisors_task(
    api_client: TestClient, advisor: Advisor
) -> None:
    created = api_client.post(
        "/tasks", json={"title": "Follow up"}, headers=_headers(advisor.id)
    ).json()
    other_advisor_id = advisor.id + 999999

    get_response = api_client.get(
        f"/tasks/{created['id']}", headers=_headers(other_advisor_id)
    )
    assert get_response.status_code == 404

    delete_response = api_client.delete(
        f"/tasks/{created['id']}", headers=_headers(other_advisor_id)
    )
    assert delete_response.status_code == 404


def test_list_client_tasks(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "task2@example.com")

    api_client.post(
        "/tasks",
        json={"title": "Client-linked task", "client_id": client["id"]},
        headers=_headers(advisor.id),
    )
    api_client.post(
        "/tasks", json={"title": "Unrelated task"}, headers=_headers(advisor.id)
    )

    response = api_client.get(
        f"/clients/{client['id']}/tasks", headers=_headers(advisor.id)
    )

    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Client-linked task"


def test_list_client_tasks_requires_owned_client(
    api_client: TestClient, advisor: Advisor
) -> None:
    response = api_client.get(
        "/clients/999999999/tasks", headers=_headers(advisor.id)
    )

    assert response.status_code == 404
