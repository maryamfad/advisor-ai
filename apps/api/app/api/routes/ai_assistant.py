from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_advisor_id,
    get_db,
    get_owned_ai_conversation,
    get_owned_client,
)
from app.models.ai_conversation import AiConversation
from app.models.client import Client
from app.schemas.ai_conversation import (
    AiConversationRead,
    SendMessageRequest,
    SendMessageResponse,
    ToolCallOut,
)
from app.services.ai_agent import run_agent_turn

router = APIRouter(prefix="/clients/{client_id}/assistant", tags=["ai-assistant"])


@router.post(
    "/conversations",
    response_model=AiConversationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
    advisor_id: int = Depends(get_current_advisor_id),
) -> AiConversation:
    conversation = AiConversation(client_id=client.id, advisor_id=advisor_id)

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


@router.get("/conversations", response_model=list[AiConversationRead])
def list_conversations(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> list[AiConversation]:
    stmt = (
        select(AiConversation)
        .where(AiConversation.client_id == client.id)
        .order_by(AiConversation.started_at.desc())
    )

    return list(db.scalars(stmt).all())


@router.get("/conversations/{conversation_id}", response_model=AiConversationRead)
def get_conversation(
    conversation: AiConversation = Depends(get_owned_ai_conversation),
) -> AiConversation:
    return conversation


@router.post(
    "/conversations/{conversation_id}/messages", response_model=SendMessageResponse
)
def send_message(
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
    conversation: AiConversation = Depends(get_owned_ai_conversation),
) -> SendMessageResponse:
    try:
        result = run_agent_turn(db, conversation, client, payload.message)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    return SendMessageResponse(
        reply=result.reply,
        tool_calls=[
            ToolCallOut(
                tool_name=call.tool_name,
                tool_input=call.tool_input,
                tool_output=call.tool_output,
            )
            for call in result.tool_calls
        ],
    )
