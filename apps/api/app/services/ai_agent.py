"""The agentic orchestration loop: turns a user's natural-language
question into a sequence of tool calls, then a final prose reply. The
model never computes a financial number itself, only calls tools and
explains what they returned -- the same principle stated in
financial_calculations.py's docstring, now actually wired up to an
LLM via a LangGraph state machine (see ai_graph.py for the graph
itself).

Deliberately NOT pure -- it makes a live API call and touches the DB
-- kept in app/services/ anyway as a clearly-labeled exception, same
category as market_data_client.py and client_financial_snapshot.py.
"""

import json
import uuid
from dataclasses import dataclass

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langgraph.errors import GraphRecursionError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_conversation import AiConversation, AiMessage, MessageRole
from app.models.client import Client
from app.services.ai_graph import build_agent_graph, recursion_limit_for
from app.services.ai_tools import build_langchain_tools
from app.services.chat_model import build_chat_model

SYSTEM_PROMPT = """\
You are an assistant helping a financial advisor prepare for and \
understand a specific client's situation. You have read-only tools \
that compute the client's financial summary, insurance need, \
registered-account recommendations, risk tolerance, a financial-plan \
preview, and fund performance comparisons.

Rules you must follow:
1. Never state a number that isn't present in a tool's returned JSON. \
If you haven't called the relevant tool yet, call it before answering.
2. Never originate investment or insurance advice beyond what the \
deterministic tools already concluded -- explain and contextualize \
their output, don't invent a new recommendation of your own.
3. When asked "why" about a figure or recommendation, cite the \
specific tool call(s) that back it.
4. If a tool's output doesn't answer the question, say so plainly \
rather than guessing.
"""

FALLBACK_REPLY = (
    "I wasn't able to finish answering that within the allowed number "
    "of tool calls. Try asking a more specific question."
)


@dataclass(frozen=True)
class ToolCallRecord:
    tool_name: str
    tool_input: dict
    tool_output: dict


@dataclass(frozen=True)
class AssistantTurnResult:
    reply: str
    tool_calls: list[ToolCallRecord]


def _load_history(db: Session, conversation: AiConversation) -> list[BaseMessage]:
    """Prior USER/ASSISTANT turns, in order -- intermediate TOOL rows
    from past turns aren't replayed, since the assistant's final text
    for each turn already captures what mattered for continuity. The
    live tool-call exchange for the *current* turn is built separately
    in run_agent_turn(), not reloaded from the DB mid-turn."""
    stmt = (
        select(AiMessage)
        .where(
            AiMessage.conversation_id == conversation.id,
            AiMessage.role.in_([MessageRole.USER, MessageRole.ASSISTANT]),
        )
        .order_by(AiMessage.created_at)
    )
    rows = db.scalars(stmt).all()
    return [
        HumanMessage(content=row.content)
        if row.role == MessageRole.USER
        else AIMessage(content=row.content)
        for row in rows
    ]


def _persist_tool_messages(
    db: Session, conversation: AiConversation, new_messages: list[BaseMessage]
) -> list[ToolCallRecord]:
    """Walks the messages a graph run added beyond the input history,
    persisting one AiMessage(role=TOOL) per ToolMessage and returning
    a matching ToolCallRecord for each -- tool_input is recovered from
    the triggering AIMessage.tool_calls entry (matched by id), since a
    ToolMessage itself only carries the tool's name and output."""
    tool_calls: list[ToolCallRecord] = []
    pending_args_by_id: dict[str, dict] = {}

    for message in new_messages:
        if isinstance(message, AIMessage) and message.tool_calls:
            for call in message.tool_calls:
                pending_args_by_id[call["id"]] = call["args"]
        elif isinstance(message, ToolMessage):
            tool_input = pending_args_by_id.pop(message.tool_call_id, {})
            tool_output = json.loads(message.content)

            db.add(
                AiMessage(
                    conversation_id=conversation.id,
                    role=MessageRole.TOOL,
                    content=message.content,
                    tool_name=message.name,
                    tool_input=tool_input,
                )
            )
            tool_calls.append(
                ToolCallRecord(
                    tool_name=message.name,
                    tool_input=tool_input,
                    tool_output=tool_output,
                )
            )

    return tool_calls


def run_agent_turn(
    db: Session,
    conversation: AiConversation,
    client: Client,
    user_message: str,
) -> AssistantTurnResult:
    llm = build_chat_model()  # raises RuntimeError if not configured

    db.add(
        AiMessage(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=user_message,
        )
    )
    db.commit()

    history = _load_history(db, conversation)
    tools = build_langchain_tools(db, client)
    graph = build_agent_graph(llm, tools, SYSTEM_PROMPT)

    thread_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    invoke_config = {
        **thread_config,
        "recursion_limit": recursion_limit_for(settings.ai_agent_max_tool_iterations),
    }

    try:
        graph.invoke({"messages": history}, config=invoke_config)
        hit_recursion_limit = False
    except GraphRecursionError:
        hit_recursion_limit = True

    # Read back from the checkpointer either way: on success this is
    # the same final state .invoke() returned; on GraphRecursionError
    # it's whatever got checkpointed up to the last completed step --
    # the only way to recover which tool calls already ran before the
    # cap was hit.
    final_messages: list[BaseMessage] = graph.get_state(thread_config).values[
        "messages"
    ]
    new_messages = final_messages[len(history) :]  # drop the replayed history
    tool_calls = _persist_tool_messages(db, conversation, new_messages)
    db.commit()

    if hit_recursion_limit:
        db.add(
            AiMessage(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=FALLBACK_REPLY,
            )
        )
        db.commit()
        return AssistantTurnResult(reply=FALLBACK_REPLY, tool_calls=tool_calls)

    final_text = final_messages[-1].content
    db.add(
        AiMessage(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=final_text,
        )
    )
    db.commit()
    return AssistantTurnResult(reply=final_text, tool_calls=tool_calls)
