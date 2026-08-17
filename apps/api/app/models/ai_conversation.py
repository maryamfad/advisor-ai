import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.advisor import Advisor
    from app.models.client import Client


class MessageRole(enum.StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class AiConversation(Base):
    """Always client-scoped -- the assistant's value is entirely
    about one client's data, and scoping it this way means the agent
    has no path to ask for a different client's data than the one its
    conversation belongs to (see app/services/ai_tools.py)."""

    __tablename__ = "ai_conversations"

    id: Mapped[int] = mapped_column(primary_key=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    advisor_id: Mapped[int] = mapped_column(
        ForeignKey("advisors.id"),
        nullable=False,
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="ai_conversations",
    )

    advisor: Mapped["Advisor"] = relationship("Advisor")

    messages: Mapped[list["AiMessage"]] = relationship(
        "AiMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AiMessage.created_at",
    )


class AiMessage(Base):
    """One turn of a conversation transcript. For TOOL rows, `content`
    is the tool's raw JSON result (as a string) and tool_name/
    tool_input record what was called -- persisting this, not just the
    final reply, is what makes the tool-call trace inspectable
    directly from the conversation history."""

    __tablename__ = "ai_messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("ai_conversations.id"),
        nullable=False,
        index=True,
    )

    role: Mapped[MessageRole] = mapped_column(
        SAEnum(MessageRole, name="message_role"),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    tool_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    tool_input: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    conversation: Mapped["AiConversation"] = relationship(
        "AiConversation",
        back_populates="messages",
    )
