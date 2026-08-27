"""Turns already-computed recommendation-engine outputs into a
prioritized, trackable action-item checklist -- the standard
financial-planning order-of-operations, not just a report.

Pure and DB-free, like the rest of app/services/: takes plain
Decimals/ints/strings/dicts and the pure dataclasses from
financial_recommendations.py, never an ORM model or a DB session. The
caller (the financial-plans route) is responsible for extracting these
plain values out of a ClientFinancialSnapshot/FinancialNeedsAnalysis
first.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.services.financial_calculations import calculate_goal_projection
from app.services.financial_recommendations import (
    DEFAULT_EMERGENCY_FUND_MONTHS,
    AccountRecommendation,
)

HIGH_INTEREST_DEBT_THRESHOLD_PERCENT = Decimal("10.00")

# Default waterfall position for each step. "debt_payoff" appears
# twice (high-interest first, remaining later) -- tracked separately
# here since both steps share the same item category string.
STEP_EMERGENCY_FUND = 1
STEP_HIGH_INTEREST_DEBT = 2
STEP_INSURANCE = 3
STEP_REGISTERED_ACCOUNTS = 4
STEP_REMAINING_DEBT = 5
STEP_GOALS = 6
STEP_RETIREMENT = 7

# Maps an item's category to the FinancialNeedsAnalysis priority
# rating that applies to it, when the caller supplies one.
# REGISTERED_ACCOUNT and GOAL have no direct FNA rating and always
# keep their default waterfall position.
_CATEGORY_TO_FNA_PRIORITY_KEY = {
    "emergency_fund": "emergency_fund",
    "debt_payoff": "debt",
    "insurance": "protection",
    "retirement": "retirement",
}


@dataclass(frozen=True)
class ActionItem:
    priority: int
    category: str
    title: str
    description: str
    target_amount: Decimal | None


def generate_action_items(
    *,
    monthly_expenses: Decimal,
    liquid_savings: Decimal,
    emergency_fund_months: int | None,
    debts: list[dict],
    insurance_recommended_type: str,
    insurance_coverage_gap: Decimal,
    registered_account_recommendations: list[AccountRecommendation],
    goals: list[dict],
    retirement_goal: dict | None,
    priority_ratings: dict[str, int] | None,
) -> list[ActionItem]:
    """Builds the checklist via the standard order-of-operations,
    including a step only when there's an actual gap to close.

    `debts`: [{"description": str | None, "balance": Decimal,
      "interest_rate": Decimal | None}, ...]
    `goals`: active goals EXCLUDING retirement-type, already filtered
      by the caller: [{"name": str, "target_amount": Decimal,
      "current_amount": Decimal, "monthly_contribution": Decimal | None}]
    `retirement_goal`: same shape as one `goals` entry, or None if no
      retirement goal is on file.
    `priority_ratings`: {"emergency_fund": int, "debt": int,
      "protection": int, "retirement": int} from the latest FNA (only
      the keys present are used), or None if no FNA exists -- in which
      case items keep pure default-waterfall order.
    """
    staged: list[tuple[int, ActionItem]] = []

    # 1. Emergency fund
    months = emergency_fund_months or DEFAULT_EMERGENCY_FUND_MONTHS
    emergency_fund_target = monthly_expenses * months
    if liquid_savings < emergency_fund_target:
        shortfall = emergency_fund_target - liquid_savings
        staged.append((
            STEP_EMERGENCY_FUND,
            ActionItem(
                priority=0,
                category="emergency_fund",
                title="Build emergency fund",
                description=(
                    f"Liquid savings of ${liquid_savings:,.2f} fall short of "
                    f"the ${emergency_fund_target:,.2f} target ({months} "
                    f"months of expenses) by ${shortfall:,.2f}."
                ),
                target_amount=shortfall,
            ),
        ))

    # 2 & 5. Debt payoff, high-interest first
    high_interest_debts = sorted(
        (
            d
            for d in debts
            if d["interest_rate"] is not None
            and d["interest_rate"] >= HIGH_INTEREST_DEBT_THRESHOLD_PERCENT
        ),
        key=lambda d: d["interest_rate"],
        reverse=True,
    )
    remaining_debts = [d for d in debts if d not in high_interest_debts]

    for debt in high_interest_debts:
        staged.append((
            STEP_HIGH_INTEREST_DEBT,
            _debt_action_item(debt, urgent=True),
        ))

    # 3. Insurance gap
    if insurance_coverage_gap > 0:
        staged.append((
            STEP_INSURANCE,
            ActionItem(
                priority=0,
                category="insurance",
                title=(
                    f"Close ${insurance_coverage_gap:,.2f} life insurance gap "
                    f"({insurance_recommended_type})"
                ),
                description=(
                    f"Recommended coverage type is {insurance_recommended_type}; "
                    f"current coverage falls ${insurance_coverage_gap:,.2f} "
                    "short of the estimated need."
                ),
                target_amount=insurance_coverage_gap,
            ),
        ))

    # 4. Registered accounts
    for recommendation in registered_account_recommendations:
        staged.append((
            STEP_REGISTERED_ACCOUNTS,
            ActionItem(
                priority=0,
                category="registered_account",
                title=f"Open/contribute to {recommendation.account_type.upper()}",
                description=recommendation.reason,
                target_amount=None,
            ),
        ))

    for debt in remaining_debts:
        staged.append((
            STEP_REMAINING_DEBT,
            _debt_action_item(debt, urgent=False),
        ))

    # 6. Active goals (retirement excluded -- handled in step 7)
    for goal in goals:
        staged.append((STEP_GOALS, _goal_action_item(goal, category="goal")))

    # 7. Retirement, only if a target exists and step 4 didn't already
    # recommend an RRSP (the RRSP contribution IS the retirement-
    # savings action; a separate generic item would be redundant).
    has_rrsp_recommendation = any(
        r.account_type == "rrsp" for r in registered_account_recommendations
    )
    if retirement_goal is not None and not has_rrsp_recommendation:
        staged.append((
            STEP_RETIREMENT,
            _goal_action_item(retirement_goal, category="retirement"),
        ))

    ordered = _apply_priority_ratings(staged, priority_ratings)

    return [
        ActionItem(
            priority=index,
            category=item.category,
            title=item.title,
            description=item.description,
            target_amount=item.target_amount,
        )
        for index, item in enumerate(ordered, start=1)
    ]


def _debt_action_item(debt: dict, *, urgent: bool) -> ActionItem:
    description = debt.get("description") or "this debt"
    rate = debt["interest_rate"]
    balance = debt["balance"]

    if urgent:
        title = f"Pay off {description} ({rate}% interest)"
        detail = (
            f"Balance of ${balance:,.2f} at {rate}% interest -- at or above "
            f"the {HIGH_INTEREST_DEBT_THRESHOLD_PERCENT}% rule-of-thumb "
            "threshold for prioritizing payoff."
        )
    else:
        title = f"Continue paying down {description}"
        rate_note = f" at {rate}% interest" if rate is not None else ""
        detail = f"Balance of ${balance:,.2f}{rate_note}."

    return ActionItem(
        priority=0,
        category="debt_payoff",
        title=title,
        description=detail,
        target_amount=balance,
    )


def _goal_action_item(goal: dict, *, category: str) -> ActionItem:
    current = goal["current_amount"]
    target = goal["target_amount"]
    contribution = goal.get("monthly_contribution") or Decimal("0")
    projection = calculate_goal_projection(current, target, contribution)

    if projection is None:
        timing = "no current contribution plan in place to project a completion date"
    elif projection == 0:
        timing = "already met"
    else:
        timing = f"about {projection} month(s) away at the current contribution rate"

    return ActionItem(
        priority=0,
        category=category,
        title=f"Progress toward {goal['name']}",
        description=(
            f"${current:,.2f} saved toward ${target:,.2f} -- {timing}."
        ),
        target_amount=target - current,
    )


def _apply_priority_ratings(
    staged: list[tuple[int, ActionItem]],
    priority_ratings: dict[str, int] | None,
) -> list[ActionItem]:
    def sort_key(entry: tuple[int, ActionItem]) -> tuple[int, int]:
        default_step_order, item = entry
        if priority_ratings is None:
            return (0, default_step_order)

        fna_key = _CATEGORY_TO_FNA_PRIORITY_KEY.get(item.category)
        rating = priority_ratings.get(fna_key, 0) if fna_key else 0
        return (-rating, default_step_order)

    return [item for _, item in sorted(staged, key=sort_key)]


def generate_narrative_summary(
    monthly_cash_flow: Decimal,
    savings_rate: Decimal,
    net_worth: Decimal,
    action_items: list[ActionItem],
) -> str:
    """Short, deterministic templated paragraph -- not AI-generated.
    An AI-written narrative is a natural future extension (same
    "explain, never compute" pattern as RiskQuestionnaire.ai_summary)
    but isn't built here."""
    header = (
        f"This plan covers a household with a monthly cash flow of "
        f"${monthly_cash_flow:,.2f} ({savings_rate}% savings rate) and net "
        f"worth of ${net_worth:,.2f}."
    )

    if not action_items:
        return f"{header} No action items were identified from the data on file."

    top_item = action_items[0]
    remaining = len(action_items) - 1
    other_categories = sorted(
        {item.category.replace("_", " ") for item in action_items[1:]}
    )
    categories_text = (
        ", ".join(other_categories) if other_categories else "no other categories"
    )
    plural = "s" if remaining != 1 else ""

    return (
        f"{header} The top priority is {top_item.title}, followed by "
        f"{remaining} additional action item{plural} across {categories_text}."
    )
