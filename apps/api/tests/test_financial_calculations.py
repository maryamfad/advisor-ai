from decimal import Decimal

from app.services.financial_calculations import (
    calculate_budget_variance,
    calculate_cash_flow,
    calculate_goal_projection,
    calculate_monthly_expenses,
    calculate_monthly_income,
    calculate_net_worth,
    calculate_savings_rate,
)


class TestCalculateMonthlyIncome:
    def test_sums_only_positive_amounts(self) -> None:
        amounts = [Decimal("7200.00"), Decimal("-1200.00"), Decimal("-50.00")]
        assert calculate_monthly_income(amounts) == Decimal("7200.00")

    def test_empty_list_returns_zero(self) -> None:
        assert calculate_monthly_income([]) == Decimal("0.00")

    def test_all_negative_returns_zero(self) -> None:
        amounts = [Decimal("-10.00"), Decimal("-20.00")]
        assert calculate_monthly_income(amounts) == Decimal("0.00")


class TestCalculateMonthlyExpenses:
    def test_sums_negative_amounts_as_positive(self) -> None:
        amounts = [Decimal("7200.00"), Decimal("-1200.00"), Decimal("-50.00")]
        assert calculate_monthly_expenses(amounts) == Decimal("1250.00")

    def test_empty_list_returns_zero(self) -> None:
        assert calculate_monthly_expenses([]) == Decimal("0.00")


class TestCalculateCashFlow:
    def test_surplus_is_positive(self) -> None:
        result = calculate_cash_flow(Decimal("7200"), Decimal("5100"))
        assert result == Decimal("2100.00")

    def test_deficit_is_negative(self) -> None:
        result = calculate_cash_flow(Decimal("3000"), Decimal("4500"))
        assert result == Decimal("-1500.00")


class TestCalculateSavingsRate:
    def test_matches_reference_example(self) -> None:
        # This is the exact example from the project plan's doc --
        # pinning it down here catches any accidental drift in the
        # formula.
        result = calculate_savings_rate(Decimal("7200"), Decimal("5100"))
        assert result == Decimal("29.17")

    def test_zero_income_returns_zero_not_a_division_error(self) -> None:
        assert calculate_savings_rate(Decimal("0"), Decimal("500")) == Decimal("0")

    def test_negative_income_returns_zero(self) -> None:
        result = calculate_savings_rate(Decimal("-100"), Decimal("50"))
        assert result == Decimal("0")

    def test_spending_more_than_income_is_negative_rate(self) -> None:
        result = calculate_savings_rate(Decimal("3000"), Decimal("4000"))
        assert result < 0


class TestCalculateNetWorth:
    def test_assets_minus_liabilities(self) -> None:
        assets = [Decimal("18500.00"), Decimal("42000.00")]
        liabilities = [Decimal("12000.00")]
        assert calculate_net_worth(assets, liabilities) == Decimal("48500.00")

    def test_no_liabilities(self) -> None:
        assert calculate_net_worth([Decimal("1000")], []) == Decimal("1000.00")

    def test_liabilities_exceed_assets_is_negative(self) -> None:
        result = calculate_net_worth([Decimal("500")], [Decimal("2000")])
        assert result == Decimal("-1500.00")


class TestCalculateGoalProjection:
    def test_typical_case_rounds_up_to_whole_months(self) -> None:
        # (10000 - 1000) / 500 = 18 exactly
        result = calculate_goal_projection(
            Decimal("1000"), Decimal("10000"), Decimal("500")
        )
        assert result == 18

    def test_partial_month_rounds_up(self) -> None:
        # (10000 - 1000) / 700 = 12.857... -> should round up to 13
        result = calculate_goal_projection(
            Decimal("1000"), Decimal("10000"), Decimal("700")
        )
        assert result == 13

    def test_goal_already_met_returns_zero(self) -> None:
        result = calculate_goal_projection(
            Decimal("12000"), Decimal("10000"), Decimal("500")
        )
        assert result == 0

    def test_zero_contribution_returns_none_not_infinity(self) -> None:
        result = calculate_goal_projection(
            Decimal("1000"), Decimal("10000"), Decimal("0")
        )
        assert result is None

    def test_negative_contribution_returns_none(self) -> None:
        result = calculate_goal_projection(
            Decimal("1000"), Decimal("10000"), Decimal("-50")
        )
        assert result is None


class TestCalculateBudgetVariance:
    def test_under_budget_is_positive(self) -> None:
        result = calculate_budget_variance(Decimal("400"), Decimal("320"))
        assert result == Decimal("80.00")

    def test_over_budget_is_negative(self) -> None:
        result = calculate_budget_variance(Decimal("400"), Decimal("450"))
        assert result == Decimal("-50.00")

    def test_exactly_on_budget_is_zero(self) -> None:
        result = calculate_budget_variance(Decimal("400"), Decimal("400"))
        assert result == Decimal("0.00")
