"""The agentic orchestration loop: turns a user's natural-language
question into a sequence of tool calls against ai_tools.py, then a
final prose reply. The model never computes a financial number
itself, only calls tools and explains what they returned -- the same
principle stated in financial_calculations.py's docstring, now
actually wired up to an LLM.

Deliberately NOT pure -- it makes a live API call and touches the DB
-- kept in app/services/ anyway as a clearly-labeled exception, same
category as market_data_client.py and client_financial_snapshot.py.
"""

import json
from dataclasses import dataclass

import anthropic
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_conversation import AiConversation, AiMessage, MessageRole
from app.models.client import Client
from app.services.ai_tools import AI_TOOLS, TOOLS_BY_NAME

MAX_RESPONSE_TOKENS = 1024

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


@dataclass(frozen=True)
class ToolCallRecord:
    tool_name: str
    tool_input: dict
    tool_output: dict


@dataclass(frozen=True)
class AssistantTurnResult:
    reply: str
    tool_calls: list[ToolCallRecord]


def _anthropic_tool_schemas() -> list[dict]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
        }
        for tool in AI_TOOLS
    ]


def _load_history(db: Session, conversation: AiConversation) -> list[dict]:
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
    return [{"role": row.role.value, "content": row.content} for row in rows]


def run_agent_turn(
    db: Session,
    conversation: AiConversation,
    client: Client,
    user_message: str,
) -> AssistantTurnResult:
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "No anthropic_api_key configured -- set one in .env to use the "
            "AI assistant."
        )

    api_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    db.add(
        AiMessage(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=user_message,
        )
    )
    db.commit()

    messages = _load_history(db, conversation)
    tool_calls: list[ToolCallRecord] = []
    tool_schemas = _anthropic_tool_schemas()

    for _ in range(settings.ai_agent_max_tool_iterations):
        response = api_client.messages.create(
            model=settings.ai_agent_model,
            max_tokens=MAX_RESPONSE_TOKENS,
            system=SYSTEM_PROMPT,
            tools=tool_schemas,
            messages=messages,
        )

        tool_use_blocks = [
            block for block in response.content if block.type == "tool_use"
        ]

        if not tool_use_blocks:
            final_text = "".join(
                block.text for block in response.content if block.type == "text"
            )
            db.add(
                AiMessage(
                    conversation_id=conversation.id,
                    role=MessageRole.ASSISTANT,
                    content=final_text,
                )
            )
            db.commit()
            return AssistantTurnResult(reply=final_text, tool_calls=tool_calls)

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in tool_use_blocks:
            tool = TOOLS_BY_NAME.get(block.name)
            if tool is None:
                output = {"error": f"Unknown tool: {block.name}"}
            else:
                output = tool.handler(db, client, **block.input)

            tool_calls.append(
                ToolCallRecord(
                    tool_name=block.name, tool_input=block.input, tool_output=output
                )
            )

            db.add(
                AiMessage(
                    conversation_id=conversation.id,
                    role=MessageRole.TOOL,
                    content=json.dumps(output),
                    tool_name=block.name,
                    tool_input=block.input,
                )
            )

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(output),
                }
            )

        db.commit()
        messages.append({"role": "user", "content": tool_results})

    # Exceeded ai_agent_max_tool_iterations without a final answer --
    # this is the guardrail against a pathological tool-call loop.
    fallback = (
        "I wasn't able to finish answering that within the allowed number "
        "of tool calls. Try asking a more specific question."
    )
    db.add(
        AiMessage(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=fallback,
        )
    )
    db.commit()

    return AssistantTurnResult(reply=fallback, tool_calls=tool_calls)
