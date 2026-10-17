"""The LangGraph state machine behind the agentic orchestration loop --
a two-node graph (agent <-> tools) built fresh per request, closing
over that request's bound tools and system prompt. Replaces the
hand-rolled `for` loop that used to live in ai_agent.py.
"""

from typing import Annotated, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def recursion_limit_for(max_tool_iterations: int) -> int:
    """LangGraph's recursion_limit counts graph *steps*, not full
    agent<->tool round trips -- one round trip here costs 2 steps
    (the `agent` node, then the `tools` node). Doubling reproduces the
    exact max_tool_iterations semantics the hand-rolled loop used to
    have: with recursion_limit = 2 * N, exactly N tool-call round
    trips complete before GraphRecursionError is raised. Verified
    empirically against langgraph's own step-counting, not just by
    inspection -- see test_ai_graph.py.
    """
    return 2 * max_tool_iterations


def build_agent_graph(
    llm: BaseChatModel,
    tools: list[BaseTool],
    system_prompt: str,
) -> CompiledStateGraph:
    """Builds and compiles a fresh graph for one request. Cheap --
    no I/O happens in `.compile()` -- so there's no reason to share a
    graph instance across requests, which would risk leaking one
    client's tools into another's conversation."""
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: AgentState) -> dict:
        response = llm_with_tools.invoke(
            [SystemMessage(system_prompt), *state["messages"]]
        )
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent", tools_condition, {"tools": "tools", END: END}
    )
    graph.add_edge("tools", "agent")

    # A checkpointer is required to recover the partial message history
    # (and therefore which tool calls already happened) when
    # GraphRecursionError cuts a run short -- see run_agent_turn's
    # except branch in ai_agent.py. It's in-memory and scoped to this
    # one compiled graph, discarded with it at the end of the request.
    return graph.compile(checkpointer=InMemorySaver())
