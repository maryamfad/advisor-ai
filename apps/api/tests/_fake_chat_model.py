"""Shared fake chat model for tests that exercise the LangGraph agent
loop (app/services/ai_agent.py, ai_graph.py) without a live Anthropic
API call. Mirrors just enough of langchain_core's BaseChatModel for
graph.invoke() to treat it like a real one: a queue of pre-built
AIMessage responses, returned one per call, in order -- the same
"scripted model" idea the old hand-duck-typed Anthropic SDK fakes used,
translated into LangChain's message types.
"""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field


class ScriptedChatModel(BaseChatModel):
    responses: list[BaseMessage] = Field(default_factory=list)
    calls: list[list[BaseMessage]] = Field(default_factory=list)

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        self.calls.append(list(messages))
        if not self.responses:
            raise AssertionError("Scripted chat model ran out of canned responses")
        response = self.responses.pop(0)
        return ChatResult(generations=[ChatGeneration(message=response)])

    def bind_tools(self, tools, **kwargs) -> "ScriptedChatModel":
        return self

    @property
    def _llm_type(self) -> str:
        return "scripted-chat-model"


def patch_chat_model(
    monkeypatch, module, responses: list[AIMessage]
) -> ScriptedChatModel:
    """Patches `module`'s ChatAnthropic import (and its settings'
    anthropic_api_key, to pass run_agent_turn's presence check) so the
    agent loop drives `fake_model` instead of a real API call. Mirrors
    the old `_patch_anthropic(monkeypatch, responses)` helper's
    call-site shape."""
    fake_model = ScriptedChatModel(responses=list(responses))
    monkeypatch.setattr(module.settings, "anthropic_api_key", "fake-test-key")
    monkeypatch.setattr(module, "ChatAnthropic", lambda **kwargs: fake_model)
    return fake_model
