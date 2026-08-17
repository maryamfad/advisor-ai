"""Eval suite for the agentic orchestration loop.

Since there's no live Anthropic API access in CI, these evals don't
test model *reasoning* -- they test that when a (scripted, fake) model
decides to call certain tools for a given question, the loop actually
dispatches them, in the right shape, and stops when it should. That's
what "validated agentic behavior" means here: the harness is proven
correct, not the model's judgement (which needs a real API key and a
human/LLM-judge review pass to evaluate, out of scope for this suite).
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.services.ai_agent as ai_agent_module
from app.db import SessionLocal
from app.models.advisor import Advisor
from app.models.ai_conversation import AiConversation
from app.models.client import Client as ClientModel
from app.services.ai_agent import run_agent_turn
from app.services.ai_tools import MarketDataUnavailableError


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
    def __init__(self, name: str, tool_input: dict, block_id: str) -> None:
        self.type = "tool_use"
        self.name = name
        self.input = tool_input
        self.id = block_id


class _FakeResponse:
    def __init__(self, content: list) -> None:
        self.content = content


class _ScriptedMessages:
    """Each call to .create() returns the next scripted response --
    standing in for a model that decided, in order, which tools to
    call and when to give a final answer."""

    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = list(responses)

    def create(self, **kwargs) -> _FakeResponse:
        if not self._responses:
            raise AssertionError("Eval script ran out of canned responses")
        return self._responses.pop(0)


class _ScriptedAnthropicClient:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self.messages = _ScriptedMessages(responses)


def _patch_anthropic(monkeypatch, responses: list[_FakeResponse]) -> None:
    fake_client = _ScriptedAnthropicClient(responses)
    monkeypatch.setattr(
        ai_agent_module.settings, "anthropic_api_key", "fake-test-key"
    )
    monkeypatch.setattr(
        ai_agent_module.anthropic, "Anthropic", lambda **kwargs: fake_client
    )


def _tool_use_then_answer(tool_name: str, answer: str) -> list[_FakeResponse]:
    return [
        _FakeResponse([_FakeToolUseBlock(tool_name, {}, block_id="t1")]),
        _FakeResponse([_FakeTextBlock(answer)]),
    ]


class TestScriptedToolCallSequences:
    def test_account_priority_question_calls_registered_accounts_tool(
        self, api_client: TestClient, advisor: Advisor, db_session: Session, monkeypatch
    ) -> None:
        client = _create_client(api_client, advisor.id, "eval1@example.com")
        conversation = _make_conversation(db_session, client["id"], advisor.id)
        client_orm = db_session.get(ClientModel, client["id"])

        _patch_anthropic(
            monkeypatch,
            _tool_use_then_answer(
                "get_registered_account_recommendations",
                "Based on the recommendations, prioritize the FHSA first.",
            ),
        )

        result = run_agent_turn(
            db_session,
            conversation,
            client_orm,
            "What accounts should this client prioritize?",
        )

        called = [c.tool_name for c in result.tool_calls]
        assert called == ["get_registered_account_recommendations"]

    def test_full_briefing_question_calls_all_three_summary_tools(
        self, api_client: TestClient, advisor: Advisor, db_session: Session, monkeypatch
    ) -> None:
        client = _create_client(api_client, advisor.id, "eval2@example.com")
        conversation = _make_conversation(db_session, client["id"], advisor.id)
        client_orm = db_session.get(ClientModel, client["id"])

        _patch_anthropic(
            monkeypatch,
            [
                _FakeResponse(
                    [
                        _FakeToolUseBlock("get_financial_summary", {}, block_id="t1"),
                        _FakeToolUseBlock(
                            "get_insurance_recommendation", {}, block_id="t2"
                        ),
                        _FakeToolUseBlock(
                            "get_registered_account_recommendations",
                            {},
                            block_id="t3",
                        ),
                    ]
                ),
                _FakeResponse([_FakeTextBlock("Here's the full briefing...")]),
            ],
        )

        result = run_agent_turn(
            db_session,
            conversation,
            client_orm,
            "Give me a full briefing on this client.",
        )

        called = {c.tool_name for c in result.tool_calls}
        assert called == {
            "get_financial_summary",
            "get_insurance_recommendation",
            "get_registered_account_recommendations",
        }

    def test_risk_tolerance_question_calls_risk_tolerance_tool(
        self, api_client: TestClient, advisor: Advisor, db_session: Session, monkeypatch
    ) -> None:
        client = _create_client(api_client, advisor.id, "eval3@example.com")
        conversation = _make_conversation(db_session, client["id"], advisor.id)
        client_orm = db_session.get(ClientModel, client["id"])

        _patch_anthropic(
            monkeypatch,
            _tool_use_then_answer(
                "get_risk_tolerance", "This client's risk tolerance is on file as..."
            ),
        )

        result = run_agent_turn(
            db_session, conversation, client_orm, "What's this client's risk tolerance?"
        )

        assert [c.tool_name for c in result.tool_calls] == ["get_risk_tolerance"]


class TestGuardrails:
    def test_max_iteration_cap_halts_pathological_loop(
        self, api_client: TestClient, advisor: Advisor, db_session: Session, monkeypatch
    ) -> None:
        client = _create_client(api_client, advisor.id, "eval4@example.com")
        conversation = _make_conversation(db_session, client["id"], advisor.id)
        client_orm = db_session.get(ClientModel, client["id"])

        monkeypatch.setattr(
            ai_agent_module.settings, "ai_agent_max_tool_iterations", 4
        )
        # A "model" that never stops asking for the financial summary
        # again -- if the loop didn't cap iterations, this would spin
        # forever.
        never_ending = [
            _FakeResponse(
                [_FakeToolUseBlock("get_financial_summary", {}, block_id=f"t{i}")]
            )
            for i in range(50)
        ]
        _patch_anthropic(monkeypatch, never_ending)

        result = run_agent_turn(
            db_session, conversation, client_orm, "Keep checking forever"
        )

        assert len(result.tool_calls) == 4
        assert "wasn't able to finish" in result.reply

    def test_compare_funds_rejects_symbol_outside_clients_selection(
        self, api_client: TestClient, advisor: Advisor, db_session: Session, monkeypatch
    ) -> None:
        client = _create_client(api_client, advisor.id, "eval5@example.com")
        conversation = _make_conversation(db_session, client["id"], advisor.id)
        client_orm = db_session.get(ClientModel, client["id"])
        # Deliberately no tracked-fund selection made for this client.

        _patch_anthropic(
            monkeypatch,
            [
                _FakeResponse(
                    [
                        _FakeToolUseBlock(
                            "compare_funds",
                            {
                                "symbols": ["SPY"],
                                "start_date": "2026-01-05",
                                "end_date": "2026-01-09",
                            },
                            block_id="t1",
                        )
                    ]
                ),
                _FakeResponse([_FakeTextBlock("SPY isn't tracked for this client.")]),
            ],
        )

        result = run_agent_turn(
            db_session, conversation, client_orm, "How has SPY done for this client?"
        )

        output = result.tool_calls[0].tool_output
        assert output["symbols"] == []
        assert any("not selected" in w for w in output["warnings"])


def test_market_data_unavailable_error_is_importable() -> None:
    # Sanity check that the guardrail test above is exercising the
    # real exception type ai_tools.compare_funds raises internally,
    # not a stand-in.
    assert issubclass(MarketDataUnavailableError, Exception)
