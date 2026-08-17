from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.ai_conversation import MessageRole


class AiMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: MessageRole
    content: str
    tool_name: str | None
    tool_input: dict | None
    created_at: datetime


class AiConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    advisor_id: int
    started_at: datetime
    created_at: datetime
    messages: list[AiMessageRead] = []


class SendMessageRequest(BaseModel):
    message: str


class ToolCallOut(BaseModel):
    tool_name: str
    tool_input: dict
    tool_output: dict


class SendMessageResponse(BaseModel):
    """Includes the ordered tool-call trace alongside the reply, so a
    future UI can render it rather than hiding it -- the assistant's
    numbers should always be traceable back to a specific tool call."""

    reply: str
    tool_calls: list[ToolCallOut]
