from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.financial_needs_analysis import RiskTolerance


class QuestionOptionOut(BaseModel):
    """Public-facing option -- deliberately omits `points` so the
    client being scored can't see how answers are weighted."""

    key: str
    text: str


class QuestionOut(BaseModel):
    key: str
    text: str
    options: list[QuestionOptionOut]


class QuestionnaireCatalog(BaseModel):
    """Served by the public GET /risk-questionnaire/{token} endpoint."""

    questions_version: str
    questions: list[QuestionOut]


class SubmitAnswersRequest(BaseModel):
    answers: dict[str, str]


class SubmitResultResponse(BaseModel):
    """Client-facing confirmation returned by the public submit
    endpoint. risk_tolerance is a plain string (score_risk_tolerance's
    own output type), not the ORM enum."""

    score: int
    risk_tolerance: str


class RiskQuestionnaireRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    token: str
    questions_version: str
    sent_at: datetime | None
    completed_at: datetime | None
    answers: dict[str, str] | None
    score: int | None
    risk_tolerance: RiskTolerance | None
    created_at: datetime


class RiskQuestionnaireCreateResult(RiskQuestionnaireRead):
    """RiskQuestionnaireRead plus the shareable link -- only returned
    at creation time, since the link isn't persisted (it's derived
    from the token, which is)."""

    link: str
