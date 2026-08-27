from decimal import Decimal

from app.services.financial_plan_generator import (
    generate_action_items,
    generate_narrative_summary,
)
from app.services.financial_recommendations import AccountRecommendation


def _kwargs(**overrides):
    base = {
        "monthly_expenses": Decimal("3000"),
        "liquid_savings": Decimal("9000"),  # exactly 3 months -- fully funded
        "emergency_fund_months": None,
        "debts": [],
        "insurance_recommended_type": "term",
        "insurance_coverage_gap": Decimal("0"),
        "registered_account_recommendations": [],
        "goals": [],
        "retirement_goal": None,
        "priority_ratings": None,
    }
    base.update(overrides)
    return base


class TestGenerateActionItems:
    def test_no_items_when_nothing_needed(self) -> None:
        assert generate_action_items(**_kwargs()) == []

    def test_emergency_fund_item_when_underfunded(self) -> None:
        items = generate_action_items(
            **_kwargs(liquid_savings=Decimal("1000"))
        )
        assert len(items) == 1
        assert items[0].category == "emergency_fund"
        assert items[0].target_amount == Decimal("8000")

    def test_no_emergency_fund_item_when_fully_funded(self) -> None:
        items = generate_action_items(**_kwargs(liquid_savings=Decimal("50000")))
        assert not [i for i in items if i.category == "emergency_fund"]

    def test_emergency_fund_uses_custom_months(self) -> None:
        items = generate_action_items(
            **_kwargs(liquid_savings=Decimal("9000"), emergency_fund_months=6)
        )
        # 6 months * 3000 = 18000 target, 9000 saved -> underfunded now
        assert len(items) == 1
        assert items[0].target_amount == Decimal("9000")

    def test_high_interest_debt_item(self) -> None:
        items = generate_action_items(
            **_kwargs(
                debts=[
                    {
                        "description": "Visa",
                        "balance": Decimal("5000"),
                        "interest_rate": Decimal("19.99"),
                    }
                ]
            )
        )
        assert len(items) == 1
        assert items[0].category == "debt_payoff"
        assert "Visa" in items[0].title
        assert items[0].target_amount == Decimal("5000")

    def test_low_interest_debt_included_as_remaining(self) -> None:
        items = generate_action_items(
            **_kwargs(
                debts=[
                    {
                        "description": "Student Loan",
                        "balance": Decimal("10000"),
                        "interest_rate": Decimal("4.5"),
                    }
                ]
            )
        )
        assert len(items) == 1
        assert items[0].category == "debt_payoff"

    def test_no_interest_rate_debt_treated_as_low_priority(self) -> None:
        items = generate_action_items(
            **_kwargs(
                debts=[
                    {
                        "description": "Family Loan",
                        "balance": Decimal("2000"),
                        "interest_rate": None,
                    }
                ]
            )
        )
        assert len(items) == 1
        assert "Family Loan" in items[0].title

    def test_insurance_gap_item(self) -> None:
        items = generate_action_items(
            **_kwargs(
                insurance_coverage_gap=Decimal("100000"),
                insurance_recommended_type="permanent",
            )
        )
        assert len(items) == 1
        assert items[0].category == "insurance"
        assert "permanent" in items[0].description

    def test_no_insurance_item_when_gap_zero(self) -> None:
        items = generate_action_items(**_kwargs(insurance_coverage_gap=Decimal("0")))
        assert not [i for i in items if i.category == "insurance"]

    def test_registered_account_items(self) -> None:
        recs = [
            AccountRecommendation("fhsa", 1, "reason a"),
            AccountRecommendation("tfsa", 2, "reason b"),
        ]
        items = generate_action_items(
            **_kwargs(registered_account_recommendations=recs)
        )
        assert len(items) == 2
        assert {i.category for i in items} == {"registered_account"}
        assert [i.title for i in items] == [
            "Open/contribute to FHSA",
            "Open/contribute to TFSA",
        ]

    def test_goal_item_with_projection(self) -> None:
        items = generate_action_items(
            **_kwargs(
                goals=[
                    {
                        "name": "New Car",
                        "target_amount": Decimal("20000"),
                        "current_amount": Decimal("5000"),
                        "monthly_contribution": Decimal("500"),
                    }
                ]
            )
        )
        assert len(items) == 1
        assert items[0].category == "goal"
        assert "30 month" in items[0].description

    def test_retirement_item_when_goal_set_and_no_rrsp(self) -> None:
        items = generate_action_items(
            **_kwargs(
                retirement_goal={
                    "name": "Retirement",
                    "target_amount": Decimal("1000000"),
                    "current_amount": Decimal("100000"),
                    "monthly_contribution": Decimal("1000"),
                }
            )
        )
        assert len(items) == 1
        assert items[0].category == "retirement"

    def test_no_retirement_item_when_rrsp_already_recommended(self) -> None:
        items = generate_action_items(
            **_kwargs(
                registered_account_recommendations=[
                    AccountRecommendation("rrsp", 1, "reason")
                ],
                retirement_goal={
                    "name": "Retirement",
                    "target_amount": Decimal("1000000"),
                    "current_amount": Decimal("100000"),
                    "monthly_contribution": Decimal("1000"),
                },
            )
        )
        assert not [i for i in items if i.category == "retirement"]

    def test_no_retirement_item_when_no_retirement_goal(self) -> None:
        items = generate_action_items(**_kwargs(retirement_goal=None))
        assert not [i for i in items if i.category == "retirement"]

    def test_default_ordering_follows_waterfall(self) -> None:
        items = generate_action_items(
            **_kwargs(
                liquid_savings=Decimal("0"),
                debts=[
                    {
                        "description": "Visa",
                        "balance": Decimal("5000"),
                        "interest_rate": Decimal("20"),
                    },
                    {
                        "description": "Student Loan",
                        "balance": Decimal("10000"),
                        "interest_rate": Decimal("4"),
                    },
                ],
                insurance_coverage_gap=Decimal("50000"),
                registered_account_recommendations=[
                    AccountRecommendation("tfsa", 1, "reason")
                ],
                goals=[
                    {
                        "name": "Vacation",
                        "target_amount": Decimal("5000"),
                        "current_amount": Decimal("1000"),
                        "monthly_contribution": Decimal("200"),
                    }
                ],
                retirement_goal={
                    "name": "Retirement",
                    "target_amount": Decimal("1000000"),
                    "current_amount": Decimal("100000"),
                    "monthly_contribution": Decimal("500"),
                },
            )
        )
        categories = [i.category for i in items]
        assert categories == [
            "emergency_fund",
            "debt_payoff",  # high-interest (Visa)
            "insurance",
            "registered_account",
            "debt_payoff",  # remaining (Student Loan)
            "goal",
            "retirement",
        ]

    def test_priorities_are_sequential_starting_at_one(self) -> None:
        items = generate_action_items(
            **_kwargs(
                liquid_savings=Decimal("0"),
                insurance_coverage_gap=Decimal("50000"),
            )
        )
        assert [i.priority for i in items] == list(range(1, len(items) + 1))

    def test_fna_priority_reorders_debt_ahead_of_retirement(self) -> None:
        kwargs = _kwargs(
            debts=[
                {
                    "description": "Student Loan",
                    "balance": Decimal("10000"),
                    "interest_rate": Decimal("4"),
                }
            ],
            retirement_goal={
                "name": "Retirement",
                "target_amount": Decimal("1000000"),
                "current_amount": Decimal("100000"),
                "monthly_contribution": Decimal("500"),
            },
        )

        default_order = generate_action_items(**kwargs)
        default_categories = [i.category for i in default_order]
        # default: remaining debt (step 5) sorts before retirement (step 7)
        assert default_categories.index("debt_payoff") < default_categories.index(
            "retirement"
        )

        rated = generate_action_items(
            **{
                **kwargs,
                "priority_ratings": {"debt": 1, "retirement": 10},
            }
        )
        rated_categories = [i.category for i in rated]
        # client rates retirement far above debt -> retirement now first
        assert rated_categories.index("retirement") < rated_categories.index(
            "debt_payoff"
        )

    def test_unrated_categories_keep_default_order_when_fna_exists(self) -> None:
        items = generate_action_items(
            **_kwargs(
                registered_account_recommendations=[
                    AccountRecommendation("tfsa", 1, "reason")
                ],
                goals=[
                    {
                        "name": "Vacation",
                        "target_amount": Decimal("5000"),
                        "current_amount": Decimal("1000"),
                        "monthly_contribution": Decimal("200"),
                    }
                ],
                priority_ratings={"debt": 5},
            )
        )
        categories = [i.category for i in items]
        assert categories.index("registered_account") < categories.index("goal")


class TestGenerateNarrativeSummary:
    def test_no_items(self) -> None:
        summary = generate_narrative_summary(
            monthly_cash_flow=Decimal("500"),
            savings_rate=Decimal("10"),
            net_worth=Decimal("20000"),
            action_items=[],
        )
        assert "No action items" in summary
        assert "$500.00" in summary

    def test_singular_item_count(self) -> None:
        items = generate_action_items(
            **_kwargs(insurance_coverage_gap=Decimal("50000"))
        )
        summary = generate_narrative_summary(
            monthly_cash_flow=Decimal("500"),
            savings_rate=Decimal("10"),
            net_worth=Decimal("20000"),
            action_items=items,
        )
        assert items[0].title in summary
        assert "0 additional action items" in summary

    def test_plural_item_count(self) -> None:
        items = generate_action_items(
            **_kwargs(
                liquid_savings=Decimal("0"),
                insurance_coverage_gap=Decimal("50000"),
                registered_account_recommendations=[
                    AccountRecommendation("tfsa", 1, "reason")
                ],
            )
        )
        summary = generate_narrative_summary(
            monthly_cash_flow=Decimal("500"),
            savings_rate=Decimal("10"),
            net_worth=Decimal("20000"),
            action_items=items,
        )
        assert len(items) == 3
        assert f"{len(items) - 1} additional action items" in summary
