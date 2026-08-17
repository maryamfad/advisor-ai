from fastapi.testclient import TestClient

import app.services.ai_agent as ai_agent_module
from app.models.advisor import Advisor


def _headers(advisor_id: int) -> dict[str, str]:
    return {"X-Advisor-Id": str(advisor_id)}


def _create_client(api_client: TestClient, advisor_id: int, email: str) -> dict:
    return api_client.post(
        "/clients",
        json={"first_name": "Sarah", "last_name": "Chen", "email": email},
        headers=_headers(advisor_id),
    ).json()


class _FakeTextBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _FakeResponse:
    def __init__(self, content: list) -> None:
        self.content = content


class _FakeMessages:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = list(responses)

    def create(self, **kwargs) -> _FakeResponse:
        return self._responses.pop(0)


class _FakeAnthropicClient:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self.messages = _FakeMessages(responses)


def _patch_anthropic(monkeypatch, reply_text: str) -> None:
    fake_client = _FakeAnthropicClient([_FakeResponse([_FakeTextBlock(reply_text)])])
    monkeypatch.setattr(
        ai_agent_module.settings, "anthropic_api_key", "fake-test-key"
    )
    monkeypatch.setattr(
        ai_agent_module.anthropic, "Anthropic", lambda **kwargs: fake_client
    )


def test_create_conversation_requires_owned_client(
    api_client: TestClient, advisor: Advisor
) -> None:
    response = api_client.post(
        "/clients/999999999/assistant/conversations", headers=_headers(advisor.id)
    )

    assert response.status_code == 404


def test_create_and_list_conversations(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "assist1@example.com")

    created = api_client.post(
        f"/clients/{client['id']}/assistant/conversations",
        headers=_headers(advisor.id),
    )
    assert created.status_code == 201
    assert created.json()["client_id"] == client["id"]

    list_response = api_client.get(
        f"/clients/{client['id']}/assistant/conversations",
        headers=_headers(advisor.id),
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_get_single_conversation(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "assist2@example.com")
    created = api_client.post(
        f"/clients/{client['id']}/assistant/conversations",
        headers=_headers(advisor.id),
    ).json()

    response = api_client.get(
        f"/clients/{client['id']}/assistant/conversations/{created['id']}",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["messages"] == []


def test_advisor_cannot_access_another_advisors_conversation(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "assist3@example.com")
    created = api_client.post(
        f"/clients/{client['id']}/assistant/conversations",
        headers=_headers(advisor.id),
    ).json()
    other_advisor_id = advisor.id + 999999

    response = api_client.get(
        f"/clients/{client['id']}/assistant/conversations/{created['id']}",
        headers=_headers(other_advisor_id),
    )

    assert response.status_code == 404


def test_send_message_returns_503_when_no_api_key_configured(
    api_client: TestClient, advisor: Advisor, monkeypatch
) -> None:
    client = _create_client(api_client, advisor.id, "assist5@example.com")
    conversation = api_client.post(
        f"/clients/{client['id']}/assistant/conversations",
        headers=_headers(advisor.id),
    ).json()

    monkeypatch.setattr(ai_agent_module.settings, "anthropic_api_key", None)

    response = api_client.post(
        f"/clients/{client['id']}/assistant/conversations/{conversation['id']}/messages",
        json={"message": "Hi there"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 503


def test_send_message_returns_reply_and_updates_transcript(
    api_client: TestClient, advisor: Advisor, monkeypatch
) -> None:
    client = _create_client(api_client, advisor.id, "assist4@example.com")
    conversation = api_client.post(
        f"/clients/{client['id']}/assistant/conversations",
        headers=_headers(advisor.id),
    ).json()

    _patch_anthropic(monkeypatch, "Sure, happy to help.")

    response = api_client.post(
        f"/clients/{client['id']}/assistant/conversations/{conversation['id']}/messages",
        json={"message": "Hi there"},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Sure, happy to help."
    assert body["tool_calls"] == []

    detail = api_client.get(
        f"/clients/{client['id']}/assistant/conversations/{conversation['id']}",
        headers=_headers(advisor.id),
    ).json()
    roles = [m["role"] for m in detail["messages"]]
    assert roles == ["user", "assistant"]
