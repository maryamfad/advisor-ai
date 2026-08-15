import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    get_owned_client,
    get_owned_risk_questionnaire,
)
from app.core.config import settings
from app.models.client import Client
from app.models.financial_needs_analysis import RiskTolerance
from app.models.risk_questionnaire import RiskQuestionnaire
from app.schemas.risk_questionnaire import (
    QuestionnaireCatalog,
    QuestionOptionOut,
    QuestionOut,
    RiskQuestionnaireCreateResult,
    RiskQuestionnaireRead,
    SubmitAnswersRequest,
    SubmitResultResponse,
)
from app.services.risk_questionnaire_constants import QUESTIONS, QUESTIONS_VERSION
from app.services.risk_questionnaire_scoring import score_risk_tolerance

router = APIRouter(
    prefix="/clients/{client_id}/risk-questionnaire", tags=["risk-questionnaire"]
)

# Unauthenticated by design -- the token itself is the credential, not
# X-Advisor-Id/get_owned_client. This is the first such surface in the
# app; keep any future public endpoint just as narrowly scoped as this
# one (read the catalog, submit once, nothing else).
public_router = APIRouter(prefix="/risk-questionnaire", tags=["risk-questionnaire"])


def _build_link(token: str) -> str:
    return f"{settings.public_base_url}/risk-questionnaire/{token}"


def _catalog() -> QuestionnaireCatalog:
    return QuestionnaireCatalog(
        questions_version=QUESTIONS_VERSION,
        questions=[
            QuestionOut(
                key=question.key,
                text=question.text,
                options=[
                    QuestionOptionOut(key=option.key, text=option.text)
                    for option in question.options
                ],
            )
            for question in QUESTIONS
        ],
    )


def _get_by_token_or_404(token: str, db: Session) -> RiskQuestionnaire:
    questionnaire = db.scalar(
        select(RiskQuestionnaire).where(RiskQuestionnaire.token == token)
    )
    if questionnaire is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk questionnaire not found.",
        )
    return questionnaire


# -- Advisor-authenticated ------------------------------------------------


@router.post(
    "",
    response_model=RiskQuestionnaireCreateResult,
    status_code=status.HTTP_201_CREATED,
)
def create_risk_questionnaire(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> RiskQuestionnaireCreateResult:
    questionnaire = RiskQuestionnaire(
        client_id=client.id,
        token=secrets.token_urlsafe(32),
        questions_version=QUESTIONS_VERSION,
    )

    db.add(questionnaire)
    db.commit()
    db.refresh(questionnaire)

    base = RiskQuestionnaireRead.model_validate(questionnaire)
    return RiskQuestionnaireCreateResult(
        **base.model_dump(), link=_build_link(questionnaire.token)
    )


@router.post("/{questionnaire_id}/mark-sent", response_model=RiskQuestionnaireRead)
def mark_risk_questionnaire_sent(
    db: Session = Depends(get_db),
    questionnaire: RiskQuestionnaire = Depends(get_owned_risk_questionnaire),
) -> RiskQuestionnaire:
    # Re-callable to support resends -- each call just updates sent_at.
    questionnaire.sent_at = datetime.utcnow()

    db.commit()
    db.refresh(questionnaire)

    return questionnaire


@router.get("", response_model=list[RiskQuestionnaireRead])
def list_risk_questionnaires(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> list[RiskQuestionnaire]:
    stmt = (
        select(RiskQuestionnaire)
        .where(RiskQuestionnaire.client_id == client.id)
        .order_by(RiskQuestionnaire.created_at.desc())
    )

    return list(db.scalars(stmt).all())


@router.get("/{questionnaire_id}", response_model=RiskQuestionnaireRead)
def get_risk_questionnaire(
    questionnaire: RiskQuestionnaire = Depends(get_owned_risk_questionnaire),
) -> RiskQuestionnaire:
    return questionnaire


# -- Public, unauthenticated -----------------------------------------------


@public_router.get("/{token}", response_model=QuestionnaireCatalog)
def get_public_questionnaire(
    token: str, db: Session = Depends(get_db)
) -> QuestionnaireCatalog:
    questionnaire = _get_by_token_or_404(token, db)

    if questionnaire.completed_at is not None:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This questionnaire has already been completed.",
        )

    return _catalog()


@public_router.post("/{token}/submit", response_model=SubmitResultResponse)
def submit_public_questionnaire(
    token: str,
    payload: SubmitAnswersRequest,
    db: Session = Depends(get_db),
) -> SubmitResultResponse:
    questionnaire = _get_by_token_or_404(token, db)

    if questionnaire.completed_at is not None:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This questionnaire has already been completed.",
        )

    try:
        result = score_risk_tolerance(payload.answers)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    questionnaire.answers = payload.answers
    questionnaire.score = result.total_score
    questionnaire.risk_tolerance = RiskTolerance(result.risk_tolerance)
    questionnaire.completed_at = datetime.utcnow()

    db.commit()

    return SubmitResultResponse(
        score=result.total_score, risk_tolerance=result.risk_tolerance
    )
