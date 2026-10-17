"""Pins recursion_limit_for()'s exact multiplier against LangGraph's
real step-counting -- see the comment on recursion_limit_for() in
ai_graph.py for why this isn't just trusted by inspection."""

import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.errors import GraphRecursionError

from app.services.ai_graph import build_agent_graph, recursion_limit_for
from tests._fake_chat_model import ScriptedChatModel


def _never_ending_tool_use(count: int) -> list[AIMessage]:
    return [
        AIMessage(
            content="",
            tool_calls=[{"name": "noop", "args": {}, "id": f"t{i}"}],
        )
        for i in range(count)
    ]


def _noop_tool() -> StructuredTool:
    return StructuredTool.from_function(
        func=lambda: "{}", name="noop", description="d", args_schema=None
    )


def test_recursion_limit_matches_max_tool_iterations() -> None:
    for max_tool_iterations in (1, 3, 4):
        llm = ScriptedChatModel(responses=_never_ending_tool_use(50))
        graph = build_agent_graph(llm, [_noop_tool()], "sys prompt")
        thread_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        invoke_config = {
            **thread_config,
            "recursion_limit": recursion_limit_for(max_tool_iterations),
        }

        try:
            graph.invoke({"messages": [HumanMessage("go")]}, config=invoke_config)
            raise AssertionError("expected GraphRecursionError to be raised")
        except GraphRecursionError:
            pass

        messages = graph.get_state(thread_config).values["messages"]
        tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
        assert len(tool_messages) == max_tool_iterations
