from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.services.ai_agent as ai_agent_module
from app.db import SessionLocal
from app.models.advisor import Advisor
from app.models.ai_conversation import AiConversation, AiMessage, MessageRole
from app.models.client import Client as ClientModel
from app.services.ai_agent import run_agent_turn


def _headers(advisor_id: int) -> dict[str, str]:
    return {"X-Advisor-Id": str(advisor_id)}


def _create_client(api_client: TestClient, advisor_id: int, email: str) -> dict:
    return api_client.post(
        "/clients",
        json={"first_name": "Sarah", "last_name": "Chen", "email": email},
        headers=_headers(advisor_id),
    ).json()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _make_conversation(
    db_session: Session, client_id: int, advisor_id: int
) -> AiConversation:
    conversation = AiConversation(client_id=client_id, advisor_id=advisor_id)
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)
    return conversation


class _FakeTextBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _FakeToolUseBlock:
    def __init__(self, name: str, tool_input: dict, block_id: str = "tool_1") -> None:
        self.type = "tool_use"
        self.name = name
        self.input = tool_input
        self.id = block_id


class _FakeResponse:
    def __init__(self, content: list) -> None:
        self.content = content


class _FakeMessages:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    def create(self, **kwargs) -> _FakeResponse:
        self.calls.append(kwargs)
        if not self._responses:
            raise AssertionError("Fake Anthropic client ran out of canned responses")
        return self._responses.pop(0)


class _FakeAnthropicClient:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self.messages = _FakeMessages(responses)


def _patch_anthropic(
    monkeypatch, responses: list[_FakeResponse]
) -> _FakeAnthropicClient:
    fake_client = _FakeAnthropicClient(responses)
    monkeypatch.setattr(
        ai_agent_module.settings, "anthropic_api_key", "fake-test-key"
    )
    monkeypatch.setattr(
        ai_agent_module.anthropic, "Anthropic", lambda **kwargs: fake_client
    )
    return fake_client


def test_missing_api_key_raises(
    api_client: TestClient, advisor: Advisor, db_session: Session, monkeypatch
) -> None:
    client = _create_client(api_client, advisor.id, "agent1@example.com")
    conversation = _make_conversation(db_session, client["id"], advisor.id)
    client_orm = db_session.get(ClientModel, client["id"])
    monkeypatch.setattr(ai_agent_module.settings, "anthropic_api_key", None)

    with pytest.raises(RuntimeError, match="No anthropic_api_key"):
        run_agent_turn(
            db_session, conversation, client_orm, "How much does this client need?"
        )


def test_single_turn_with_no_tool_calls(
    api_client: TestClient, advisor: Advisor, db_session: Session, monkeypatch
) -> None:
    client = _create_client(api_client, advisor.id, "agent2@example.com")
    conversation = _make_conversation(db_session, client["id"], advisor.id)
    client_orm = db_session.get(ClientModel, client["id"])

    _patch_anthropic(
        monkeypatch,
        [_FakeResponse([_FakeTextBlock("Hello, how can I help?")])],
    )

    result = run_agent_turn(db_session, conversation, client_orm, "Hi there")

    assert result.reply == "Hello, how can I help?"
    assert result.tool_calls == []

    messages = (
        db_session.query(AiMessage)
        .filter(AiMessage.conversation_id == conversation.id)
        .order_by(AiMessage.created_at)
        .all()
    )
    assert [m.role for m in messages] == [MessageRole.USER, MessageRole.ASSISTANT]
    assert messages[0].content == "Hi there"
    assert messages[1].content == "Hello, how can I help?"


def test_tool_call_then_final_answer(
    api_client: TestClient, advisor: Advisor, db_session: Session, monkeypatch
) -> None:
    client = _create_client(api_client, advisor.id, "agent3@example.com")
    conversation = _make_conversation(db_session, client["id"], advisor.id)
    client_orm = db_session.get(ClientModel, client["id"])

    fake_client = _patch_anthropic(
        monkeypatch,
        [
            _FakeResponse(
                [_FakeToolUseBlock("get_financial_summary", {}, block_id="t1")]
            ),
            _FakeResponse([_FakeTextBlock("The client's net worth is as shown.")]),
        ],
    )

    result = run_agent_turn(
        db_session, conversation, client_orm, "What's this client's net worth?"
    )

    assert result.reply == "The client's net worth is as shown."
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "get_financial_summary"
    assert "net_worth" in result.tool_calls[0].tool_output

    tool_messages = (
        db_session.query(AiMessage)
        .filter(
            AiMessage.conversation_id == conversation.id,
            AiMessage.role == MessageRole.TOOL,
        )
        .all()
    )
    assert len(tool_messages) == 1
    assert tool_messages[0].tool_name == "get_financial_summary"

    # Second .create() call's `messages` should include the tool_result.
    assert len(fake_client.messages.calls) == 2
    second_call_messages = fake_client.messages.calls[1]["messages"]
    assert second_call_messages[-1]["role"] == "user"
    assert second_call_messages[-1]["content"][0]["type"] == "tool_result"


def test_max_iterations_returns_fallback_not_infinite_loop(
    api_client: TestClient, advisor: Advisor, db_session: Session, monkeypatch
) -> None:
    client = _create_client(api_client, advisor.id, "agent4@example.com")
    conversation = _make_conversation(db_session, client["id"], advisor.id)
    client_orm = db_session.get(ClientModel, client["id"])

    monkeypatch.setattr(ai_agent_module.settings, "ai_agent_max_tool_iterations", 3)
    always_tool_use = [
        _FakeResponse(
            [_FakeToolUseBlock("get_financial_summary", {}, block_id=f"t{i}")]
        )
        for i in range(10)  # more than max_tool_iterations
    ]
    _patch_anthropic(monkeypatch, always_tool_use)

    result = run_agent_turn(db_session, conversation, client_orm, "Keep going forever")

    assert "wasn't able to finish" in result.reply
    assert len(result.tool_calls) == 3  # capped at ai_agent_max_tool_iterations


def test_history_includes_prior_turns(
    api_client: TestClient, advisor: Advisor, db_session: Session, monkeypatch
) -> None:
    client = _create_client(api_client, advisor.id, "agent5@example.com")
    conversation = _make_conversation(db_session, client["id"], advisor.id)
    client_orm = db_session.get(ClientModel, client["id"])

    db_session.add(
        AiMessage(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="What's the client's risk tolerance?",
        )
    )
    db_session.add(
        AiMessage(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="No risk tolerance data is on file yet.",
        )
    )
    db_session.commit()

    fake_client = _patch_anthropic(
        monkeypatch,
        [_FakeResponse([_FakeTextBlock("Following up on that.")])],
    )

    run_agent_turn(db_session, conversation, client_orm, "And now?")

    first_call_messages = fake_client.messages.calls[0]["messages"]
    assert first_call_messages[0]["content"] == "What's the client's risk tolerance?"
    assert first_call_messages[1]["content"] == "No risk tolerance data is on file yet."
    assert first_call_messages[2]["content"] == "And now?"
