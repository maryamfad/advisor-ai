from decimal import Decimal

from app.services.financial_recommendations import (
    calculate_insurance_gap,
    calculate_life_insurance_need,
    prioritize_registered_accounts,
    recommend_life_insurance_type,
)


def _dime_kwargs(**overrides):
    base = {
        "wants_debt_payoff": False,
        "total_debt_excluding_mortgage": Decimal("0"),
        "wants_mortgage_payoff": False,
        "mortgage_balance": Decimal("0"),
        "wants_income_replacement": False,
        "annual_income": Decimal("0"),
        "income_replacement_amount": None,
        "income_replacement_percent": None,
        "income_replacement_years": None,
        "wants_education_funding": False,
        "education_funding_amount": None,
        "wants_final_expenses": False,
        "final_expenses_amount": None,
        "wants_emergency_fund": False,
        "monthly_expenses": Decimal("0"),
        "emergency_fund_months": None,
    }
    base.update(overrides)
    return base


class TestCalculateLifeInsuranceNeed:
    def test_all_flags_off_returns_zero(self) -> None:
        assert calculate_life_insurance_need(**_dime_kwargs()) == Decimal("0.00")

    def test_debt_payoff_component(self) -> None:
        kwargs = _dime_kwargs(
            wants_debt_payoff=True,
            total_debt_excluding_mortgage=Decimal("15000"),
        )
        assert calculate_life_insurance_need(**kwargs) == Decimal("15000.00")

    def test_debt_component_excluded_when_flag_off(self) -> None:
        kwargs = _dime_kwargs(
            wants_debt_payoff=False,
            total_debt_excluding_mortgage=Decimal("15000"),
        )
        assert calculate_life_insurance_need(**kwargs) == Decimal("0.00")

    def test_mortgage_payoff_component(self) -> None:
        kwargs = _dime_kwargs(
            wants_mortgage_payoff=True, mortgage_balance=Decimal("400000")
        )
        assert calculate_life_insurance_need(**kwargs) == Decimal("400000.00")

    def test_income_replacement_direct_amount(self) -> None:
        kwargs = _dime_kwargs(
            wants_income_replacement=True,
            income_replacement_amount=Decimal("250000"),
            annual_income=Decimal("80000"),
            income_replacement_percent=Decimal("70"),
            income_replacement_years=10,
        )
        # direct amount wins even though percent/years are also given
        assert calculate_life_insurance_need(**kwargs) == Decimal("250000.00")

    def test_income_replacement_percent_form(self) -> None:
        kwargs = _dime_kwargs(
            wants_income_replacement=True,
            annual_income=Decimal("80000"),
            income_replacement_percent=Decimal("70"),
            income_replacement_years=10,
        )
        # 80000 * 0.70 * 10
        assert calculate_life_insurance_need(**kwargs) == Decimal("560000.00")

    def test_income_replacement_plain_multiple(self) -> None:
        kwargs = _dime_kwargs(
            wants_income_replacement=True,
            annual_income=Decimal("80000"),
            income_replacement_years=5,
        )
        assert calculate_life_insurance_need(**kwargs) == Decimal("400000.00")

    def test_income_replacement_defaults_years_when_unset(self) -> None:
        kwargs = _dime_kwargs(
            wants_income_replacement=True, annual_income=Decimal("50000")
        )
        # default 10 years
        assert calculate_life_insurance_need(**kwargs) == Decimal("500000.00")

    def test_education_funding_component(self) -> None:
        kwargs = _dime_kwargs(
            wants_education_funding=True,
            education_funding_amount=Decimal("60000"),
        )
        assert calculate_life_insurance_need(**kwargs) == Decimal("60000.00")

    def test_final_expenses_component(self) -> None:
        kwargs = _dime_kwargs(
            wants_final_expenses=True, final_expenses_amount=Decimal("15000")
        )
        assert calculate_life_insurance_need(**kwargs) == Decimal("15000.00")

    def test_emergency_fund_component_default_months(self) -> None:
        kwargs = _dime_kwargs(
            wants_emergency_fund=True, monthly_expenses=Decimal("4000")
        )
        # default 3 months
        assert calculate_life_insurance_need(**kwargs) == Decimal("12000.00")

    def test_emergency_fund_component_explicit_months(self) -> None:
        kwargs = _dime_kwargs(
            wants_emergency_fund=True,
            monthly_expenses=Decimal("4000"),
            emergency_fund_months=6,
        )
        assert calculate_life_insurance_need(**kwargs) == Decimal("24000.00")

    def test_sums_multiple_components(self) -> None:
        kwargs = _dime_kwargs(
            wants_debt_payoff=True,
            total_debt_excluding_mortgage=Decimal("10000"),
            wants_mortgage_payoff=True,
            mortgage_balance=Decimal("300000"),
            wants_final_expenses=True,
            final_expenses_amount=Decimal("15000"),
        )
        assert calculate_life_insurance_need(**kwargs) == Decimal("325000.00")


class TestCalculateInsuranceGap:
    def test_gap_when_target_exceeds_existing(self) -> None:
        result = calculate_insurance_gap(Decimal("500000"), Decimal("100000"))
        assert result == Decimal("400000.00")

    def test_gap_is_zero_when_existing_meets_target(self) -> None:
        result = calculate_insurance_gap(Decimal("100000"), Decimal("100000"))
        assert result == Decimal("0.00")

    def test_gap_is_never_negative(self) -> None:
        result = calculate_insurance_gap(Decimal("50000"), Decimal("200000"))
        assert result == Decimal("0.00")


class TestRecommendLifeInsuranceType:
    def test_low_cash_flow_returns_term(self) -> None:
        result = recommend_life_insurance_type(
            age=50,
            dependents_count=0,
            net_worth=Decimal("500000"),
            monthly_income=Decimal("5000"),
            monthly_cash_flow=Decimal("100"),  # 2% ratio, below 10% threshold
        )
        assert result.recommendation == "term"
        assert result.reasons

    def test_zero_income_returns_term(self) -> None:
        result = recommend_life_insurance_type(
            age=50,
            dependents_count=0,
            net_worth=Decimal("500000"),
            monthly_income=Decimal("0"),
            monthly_cash_flow=Decimal("0"),
        )
        assert result.recommendation == "term"

    def test_older_high_net_worth_returns_permanent(self) -> None:
        result = recommend_life_insurance_type(
            age=50,
            dependents_count=0,
            net_worth=Decimal("200000"),
            monthly_income=Decimal("10000"),
            monthly_cash_flow=Decimal("2000"),  # 20% ratio, passes gate
        )
        assert result.recommendation == "permanent"

    def test_young_with_dependents_returns_term(self) -> None:
        result = recommend_life_insurance_type(
            age=32,
            dependents_count=2,
            net_worth=Decimal("50000"),
            monthly_income=Decimal("8000"),
            monthly_cash_flow=Decimal("1500"),
        )
        assert result.recommendation == "term"

    def test_unknown_age_with_dependents_returns_term(self) -> None:
        result = recommend_life_insurance_type(
            age=None,
            dependents_count=1,
            net_worth=Decimal("50000"),
            monthly_income=Decimal("8000"),
            monthly_cash_flow=Decimal("1500"),
        )
        assert result.recommendation == "term"

    def test_no_signal_returns_term_with_permanent_review(self) -> None:
        result = recommend_life_insurance_type(
            age=35,
            dependents_count=0,
            net_worth=Decimal("50000"),
            monthly_income=Decimal("8000"),
            monthly_cash_flow=Decimal("1500"),
        )
        assert result.recommendation == "term_with_permanent_review"

    def test_risk_tolerance_appended_as_note_not_deciding(self) -> None:
        without_note = recommend_life_insurance_type(
            age=32,
            dependents_count=2,
            net_worth=Decimal("50000"),
            monthly_income=Decimal("8000"),
            monthly_cash_flow=Decimal("1500"),
        )
        with_note = recommend_life_insurance_type(
            age=32,
            dependents_count=2,
            net_worth=Decimal("50000"),
            monthly_income=Decimal("8000"),
            monthly_cash_flow=Decimal("1500"),
            risk_tolerance="high",
        )
        assert with_note.recommendation == without_note.recommendation == "term"
        assert len(with_note.reasons) == len(without_note.reasons) + 1
        assert "risk tolerance is high" in with_note.reasons[-1]


class TestPrioritizeRegisteredAccounts:
    def test_first_time_home_buyer_with_home_goal_prioritizes_fhsa(self) -> None:
        results = prioritize_registered_accounts(
            age=30,
            annual_income=Decimal("70000"),
            first_time_home_buyer=True,
            monthly_cash_flow=Decimal("500"),
            goal_types={"home_purchase"},
            existing_account_types=set(),
            dependents=[],
        )
        assert results[0].account_type == "fhsa"
        assert results[0].priority == 1

    def test_fhsa_not_recommended_if_already_has_one(self) -> None:
        results = prioritize_registered_accounts(
            age=30,
            annual_income=Decimal("70000"),
            first_time_home_buyer=True,
            monthly_cash_flow=Decimal("500"),
            goal_types={"home_purchase"},
            existing_account_types={"fhsa"},
            dependents=[],
        )
        assert "fhsa" not in {r.account_type for r in results}

    def test_fhsa_not_recommended_if_not_first_time_buyer(self) -> None:
        results = prioritize_registered_accounts(
            age=30,
            annual_income=Decimal("70000"),
            first_time_home_buyer=False,
            monthly_cash_flow=Decimal("500"),
            goal_types={"home_purchase"},
            existing_account_types=set(),
            dependents=[],
        )
        assert "fhsa" not in {r.account_type for r in results}

    def test_fhsa_not_recommended_outside_age_window(self) -> None:
        results = prioritize_registered_accounts(
            age=75,
            annual_income=Decimal("70000"),
            first_time_home_buyer=True,
            monthly_cash_flow=Decimal("500"),
            goal_types={"home_purchase"},
            existing_account_types=set(),
            dependents=[],
        )
        assert "fhsa" not in {r.account_type for r in results}

    def test_low_income_ranks_tfsa_above_rrsp(self) -> None:
        results = prioritize_registered_accounts(
            age=30,
            annual_income=Decimal("40000"),
            first_time_home_buyer=False,
            monthly_cash_flow=Decimal("0"),
            goal_types=set(),
            existing_account_types=set(),
            dependents=[],
        )
        account_order = [r.account_type for r in results]
        assert account_order.index("tfsa") < account_order.index("rrsp")

    def test_high_income_ranks_rrsp_above_tfsa(self) -> None:
        results = prioritize_registered_accounts(
            age=30,
            annual_income=Decimal("90000"),
            first_time_home_buyer=False,
            monthly_cash_flow=Decimal("0"),
            goal_types=set(),
            existing_account_types=set(),
            dependents=[],
        )
        account_order = [r.account_type for r in results]
        assert account_order.index("rrsp") < account_order.index("tfsa")

    def test_existing_rrsp_and_tfsa_excluded(self) -> None:
        results = prioritize_registered_accounts(
            age=30,
            annual_income=Decimal("90000"),
            first_time_home_buyer=False,
            monthly_cash_flow=Decimal("0"),
            goal_types=set(),
            existing_account_types={"rrsp", "tfsa"},
            dependents=[],
        )
        assert {r.account_type for r in results} == set()

    def test_dependents_with_underfunded_resp_recommended(self) -> None:
        results = prioritize_registered_accounts(
            age=40,
            annual_income=Decimal("90000"),
            first_time_home_buyer=False,
            monthly_cash_flow=Decimal("0"),
            goal_types=set(),
            existing_account_types={"rrsp", "tfsa"},
            dependents=[{"name": "Jamie", "resp_monthly_contribution": Decimal("50")}],
        )
        resp_entries = [r for r in results if r.account_type == "resp"]
        assert len(resp_entries) == 1
        assert "Jamie" in resp_entries[0].reason

    def test_dependents_with_fully_funded_resp_not_recommended(self) -> None:
        results = prioritize_registered_accounts(
            age=40,
            annual_income=Decimal("90000"),
            first_time_home_buyer=False,
            monthly_cash_flow=Decimal("0"),
            goal_types=set(),
            existing_account_types={"rrsp", "tfsa"},
            dependents=[
                {"name": "Jamie", "resp_monthly_contribution": Decimal("300")}
            ],
        )
        assert not [r for r in results if r.account_type == "resp"]

    def test_multiple_dependents_each_get_named_entry(self) -> None:
        results = prioritize_registered_accounts(
            age=40,
            annual_income=Decimal("90000"),
            first_time_home_buyer=False,
            monthly_cash_flow=Decimal("0"),
            goal_types=set(),
            existing_account_types={"rrsp", "tfsa"},
            dependents=[
                {"name": "Jamie", "resp_monthly_contribution": Decimal("0")},
                {"name": "Riley", "resp_monthly_contribution": Decimal("0")},
            ],
        )
        resp_reasons = [r.reason for r in results if r.account_type == "resp"]
        assert len(resp_reasons) == 2
        assert any("Jamie" in reason for reason in resp_reasons)
        assert any("Riley" in reason for reason in resp_reasons)

    def test_non_registered_fallback_when_positive_cash_flow(self) -> None:
        results = prioritize_registered_accounts(
            age=40,
            annual_income=Decimal("90000"),
            first_time_home_buyer=False,
            monthly_cash_flow=Decimal("500"),
            goal_types=set(),
            existing_account_types={"rrsp", "tfsa"},
            dependents=[],
        )
        assert results[-1].account_type == "non_registered"

    def test_no_non_registered_fallback_when_no_cash_flow(self) -> None:
        results = prioritize_registered_accounts(
            age=40,
            annual_income=Decimal("90000"),
            first_time_home_buyer=False,
            monthly_cash_flow=Decimal("0"),
            goal_types=set(),
            existing_account_types={"rrsp", "tfsa"},
            dependents=[],
        )
        assert "non_registered" not in {r.account_type for r in results}

    def test_priorities_are_sequential_starting_at_one(self) -> None:
        results = prioritize_registered_accounts(
            age=30,
            annual_income=Decimal("40000"),
            first_time_home_buyer=True,
            monthly_cash_flow=Decimal("500"),
            goal_types={"home_purchase"},
            existing_account_types=set(),
            dependents=[],
        )
        assert [r.priority for r in results] == list(range(1, len(results) + 1))
