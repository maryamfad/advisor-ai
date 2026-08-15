import pytest

from app.services.risk_questionnaire_constants import QUESTIONS
from app.services.risk_questionnaire_scoring import score_risk_tolerance


def _option_key(question_key: str, points: int) -> str:
    question = next(q for q in QUESTIONS if q.key == question_key)
    option = next(o for o in question.options if o.points == points)
    return option.key


def _all_minimum_answers() -> dict[str, str]:
    return {
        q.key: _option_key(q.key, min(o.points for o in q.options)) for q in QUESTIONS
    }


def _with_overrides(**points_by_question: int) -> dict[str, str]:
    answers = _all_minimum_answers()
    for question_key, points in points_by_question.items():
        answers[question_key] = _option_key(question_key, points)
    return answers


class TestScoreRiskTolerance:
    def test_all_minimum_answers_score_ten_and_are_low(self) -> None:
        result = score_risk_tolerance(_all_minimum_answers())
        assert result.total_score == 10
        assert result.risk_tolerance == "low"

    def test_all_maximum_answers_score_fifty_and_are_high(self) -> None:
        answers = {
            q.key: _option_key(q.key, max(o.points for o in q.options))
            for q in QUESTIONS
        }
        result = score_risk_tolerance(answers)
        assert result.total_score == 50
        assert result.risk_tolerance == "high"

    def test_low_upper_boundary(self) -> None:
        answers = _with_overrides(time_horizon=5, primary_objective=5)
        result = score_risk_tolerance(answers)
        assert result.total_score == 18
        assert result.risk_tolerance == "low"

    def test_low_medium_lower_boundary(self) -> None:
        answers = _with_overrides(time_horizon=5, primary_objective=5, loss_reaction=2)
        result = score_risk_tolerance(answers)
        assert result.total_score == 19
        assert result.risk_tolerance == "low_medium"

    def test_low_medium_upper_boundary(self) -> None:
        answers = _with_overrides(
            time_horizon=5, primary_objective=5, loss_reaction=5, income_stability=5
        )
        result = score_risk_tolerance(answers)
        assert result.total_score == 26
        assert result.risk_tolerance == "low_medium"

    def test_medium_lower_boundary(self) -> None:
        answers = _with_overrides(
            time_horizon=5,
            primary_objective=5,
            loss_reaction=5,
            income_stability=5,
            investment_experience=2,
        )
        result = score_risk_tolerance(answers)
        assert result.total_score == 27
        assert result.risk_tolerance == "medium"

    def test_medium_upper_boundary(self) -> None:
        answers = _with_overrides(
            time_horizon=5,
            primary_objective=5,
            loss_reaction=5,
            income_stability=5,
            investment_experience=5,
            liquidity_needs=5,
        )
        result = score_risk_tolerance(answers)
        assert result.total_score == 34
        assert result.risk_tolerance == "medium"

    def test_medium_high_lower_boundary(self) -> None:
        answers = _with_overrides(
            time_horizon=5,
            primary_objective=5,
            loss_reaction=5,
            income_stability=5,
            investment_experience=5,
            liquidity_needs=5,
            volatility_comfort=2,
        )
        result = score_risk_tolerance(answers)
        assert result.total_score == 35
        assert result.risk_tolerance == "medium_high"

    def test_medium_high_upper_boundary(self) -> None:
        answers = _with_overrides(
            time_horizon=5,
            primary_objective=5,
            loss_reaction=5,
            income_stability=5,
            investment_experience=5,
            liquidity_needs=5,
            volatility_comfort=5,
            debt_load=5,
        )
        result = score_risk_tolerance(answers)
        assert result.total_score == 42
        assert result.risk_tolerance == "medium_high"

    def test_high_lower_boundary(self) -> None:
        answers = _with_overrides(
            time_horizon=5,
            primary_objective=5,
            loss_reaction=5,
            income_stability=4,
            investment_experience=5,
            liquidity_needs=5,
            volatility_comfort=5,
            debt_load=5,
            emergency_fund=3,
        )
        result = score_risk_tolerance(answers)
        assert result.total_score == 43
        assert result.risk_tolerance == "high"

    def test_missing_question_raises(self) -> None:
        answers = _all_minimum_answers()
        del answers["time_horizon"]
        with pytest.raises(ValueError, match="Missing"):
            score_risk_tolerance(answers)

    def test_unexpected_question_raises(self) -> None:
        answers = _all_minimum_answers()
        answers["not_a_real_question"] = "some_option"
        with pytest.raises(ValueError, match="Unexpected"):
            score_risk_tolerance(answers)

    def test_invalid_option_key_raises(self) -> None:
        answers = _all_minimum_answers()
        answers["time_horizon"] = "not_a_real_option"
        with pytest.raises(ValueError, match="not a valid option"):
            score_risk_tolerance(answers)
