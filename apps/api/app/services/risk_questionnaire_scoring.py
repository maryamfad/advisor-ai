"""Deterministic scoring for the risk-tolerance questionnaire.

Same principle as the rest of app/services/: pure, DB-free, so the
score can be trusted and unit-tested in isolation -- an AI may explain
the result later, never compute it.
"""

from dataclasses import dataclass

from app.services.risk_questionnaire_constants import QUESTIONS, SCORE_THRESHOLDS


@dataclass(frozen=True)
class RiskScoreResult:
    total_score: int
    risk_tolerance: str


def score_risk_tolerance(answers: dict[str, str]) -> RiskScoreResult:
    """Sums points for each question's selected option and maps the
    total onto a risk-tolerance band.

    Raises ValueError if `answers` doesn't cover exactly the question
    set, or if an answer isn't a valid option for its question -- the
    API route is expected to translate that into a 400, not a generic
    500, since it's an input problem, not a data problem.
    """
    questions_by_key = {question.key: question for question in QUESTIONS}

    missing = questions_by_key.keys() - answers.keys()
    unexpected = answers.keys() - questions_by_key.keys()
    if missing or unexpected:
        raise ValueError(
            "Answers must cover exactly the question set. "
            f"Missing: {sorted(missing)}. Unexpected: {sorted(unexpected)}."
        )

    total_score = 0
    for question_key, option_key in answers.items():
        question = questions_by_key[question_key]
        options_by_key = {option.key: option for option in question.options}
        if option_key not in options_by_key:
            raise ValueError(
                f"'{option_key}' is not a valid option for question "
                f"'{question_key}'."
            )
        total_score += options_by_key[option_key].points

    return RiskScoreResult(
        total_score=total_score,
        risk_tolerance=_score_to_risk_tolerance(total_score),
    )


def _score_to_risk_tolerance(total_score: int) -> str:
    band: str | None = None
    for lower_bound, level in SCORE_THRESHOLDS:
        if total_score >= lower_bound:
            band = level

    if band is None:
        raise ValueError(
            f"Score {total_score} is below the minimum possible score."
        )

    return band
