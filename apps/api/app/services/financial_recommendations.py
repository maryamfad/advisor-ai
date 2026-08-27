"""Deterministic, rule-based advisory calculations.

Same principle as financial_calculations.py: every function here is
pure and framework-agnostic so the AI can call it as a tool and
explain the result, never compute the number itself. Rule thresholds
below are explicit named constants, not hidden magic numbers, so an
advisor can see and tune exactly why a recommendation fired.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.services.canadian_account_constants import (
    FHSA_ANNUAL_LIMIT,
    FHSA_LIFETIME_LIMIT,
    FHSA_MAX_AGE,
    FHSA_MIN_AGE,
    RESP_CESG_ANNUAL_CONTRIBUTION_FOR_MAX_GRANT,
    RESP_CESG_MATCH_RATE,
    RRSP_MIN_INCOME_FOR_PRIORITY,
    TFSA_ANNUAL_LIMIT,
)

TWO_PLACES = Decimal("0.01")


def _round(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


# --- Insurance -------------------------------------------------------------

DEFAULT_INCOME_REPLACEMENT_YEARS = 10
DEFAULT_EMERGENCY_FUND_MONTHS = 3


def calculate_life_insurance_need(
    *,
    wants_debt_payoff: bool,
    total_debt_excluding_mortgage: Decimal,
    wants_mortgage_payoff: bool,
    mortgage_balance: Decimal,
    wants_income_replacement: bool,
    annual_income: Decimal,
    income_replacement_amount: Decimal | None,
    income_replacement_percent: Decimal | None,
    income_replacement_years: int | None,
    wants_education_funding: bool,
    education_funding_amount: Decimal | None,
    wants_final_expenses: bool,
    final_expenses_amount: Decimal | None,
    wants_emergency_fund: bool,
    monthly_expenses: Decimal,
    emergency_fund_months: int | None,
) -> Decimal:
    """DIME-method insurance need: sums only the components the client
    explicitly asked for (the FNA intake's checklist), never a guessed
    income-multiple. Each component is independently explainable.

    Income replacement resolution order when the flag is set:
    1. income_replacement_amount, if given directly.
    2. annual_income * (income_replacement_percent / 100) * years, if
       a percent was given instead.
    3. annual_income * years, as a plain multiple, if neither was
       given.
    """
    total = Decimal("0")

    if wants_debt_payoff:
        total += total_debt_excluding_mortgage

    if wants_mortgage_payoff:
        total += mortgage_balance

    if wants_income_replacement:
        years = income_replacement_years or DEFAULT_INCOME_REPLACEMENT_YEARS
        if income_replacement_amount is not None:
            total += income_replacement_amount
        elif income_replacement_percent is not None:
            total += annual_income * (income_replacement_percent / 100) * years
        else:
            total += annual_income * years

    if wants_education_funding and education_funding_amount is not None:
        total += education_funding_amount

    if wants_final_expenses and final_expenses_amount is not None:
        total += final_expenses_amount

    if wants_emergency_fund:
        months = emergency_fund_months or DEFAULT_EMERGENCY_FUND_MONTHS
        total += monthly_expenses * months

    return _round(total)


def calculate_insurance_gap(
    target_coverage: Decimal, existing_coverage: Decimal
) -> Decimal:
    """max(0, target - existing); never negative."""
    return _round(max(Decimal("0"), target_coverage - existing_coverage))


# Rule-ladder thresholds for recommend_life_insurance_type -- named so
# an advisor can see and tune exactly why a recommendation fired.
MIN_CASH_FLOW_TO_INCOME_RATIO_FOR_PERMANENT = Decimal("0.10")
PERMANENT_MIN_AGE = 45
HIGH_NET_WORTH_ESTATE_THRESHOLD = Decimal("150000")


@dataclass(frozen=True)
class InsuranceTypeRecommendation:
    recommendation: str  # "term" | "permanent" | "term_with_permanent_review"
    reasons: list[str]


def recommend_life_insurance_type(
    age: int | None,
    dependents_count: int,
    net_worth: Decimal,
    monthly_income: Decimal,
    monthly_cash_flow: Decimal,
    risk_tolerance: str | None = None,
) -> InsuranceTypeRecommendation:
    """Explicit ordered rule ladder -- first match wins:
    1. Affordability gate: no/negative income, or cash flow too thin
       relative to income, to support permanent's higher premium.
    2. Estate-planning signal: older and high net worth.
    3. Temporary-need signal: has dependents and isn't in the
       estate-planning bracket.
    4. No strong signal -- flagged for manual review.

    risk_tolerance, when known, is appended as a secondary note in the
    reasons -- it never changes which branch fires.
    """
    cash_flow_ratio = (
        monthly_cash_flow / monthly_income
        if monthly_income > 0
        else Decimal("0")
    )

    if (
        monthly_income <= 0
        or cash_flow_ratio < MIN_CASH_FLOW_TO_INCOME_RATIO_FOR_PERMANENT
    ):
        reasons = [
            "Monthly cash flow is too tight relative to income to "
            "comfortably support permanent insurance's higher premium -- "
            "term life covers the need at a lower cost.",
        ]
        return _with_risk_note(
            InsuranceTypeRecommendation("term", reasons), risk_tolerance
        )

    if (
        age is not None
        and age >= PERMANENT_MIN_AGE
        and net_worth >= HIGH_NET_WORTH_ESTATE_THRESHOLD
    ):
        reasons = [
            f"Age {age} and net worth of ${net_worth:,.2f} suggest an "
            "estate-planning need (permanent coverage, cash value, wealth "
            "transfer) rather than a purely temporary one.",
        ]
        return _with_risk_note(
            InsuranceTypeRecommendation("permanent", reasons), risk_tolerance
        )

    if dependents_count >= 1 and (age is None or age < PERMANENT_MIN_AGE):
        reasons = [
            f"{dependents_count} dependent(s) and a younger age point to a "
            "temporary income-replacement need -- term life matches that "
            "need without paying for permanent coverage.",
        ]
        return _with_risk_note(
            InsuranceTypeRecommendation("term", reasons), risk_tolerance
        )

    reasons = [
        "No strong signal toward permanent or term from age, net worth, "
        "or dependents -- worth a manual review to confirm the right fit.",
    ]
    return _with_risk_note(
        InsuranceTypeRecommendation("term_with_permanent_review", reasons),
        risk_tolerance,
    )


def _with_risk_note(
    recommendation: InsuranceTypeRecommendation, risk_tolerance: str | None
) -> InsuranceTypeRecommendation:
    if risk_tolerance is None:
        return recommendation

    note = f"Noted for context: risk tolerance is {risk_tolerance}."
    return InsuranceTypeRecommendation(
        recommendation.recommendation,
        [*recommendation.reasons, note],
    )


# --- Registered accounts -----------------------------------------------


@dataclass(frozen=True)
class AccountRecommendation:
    account_type: str
    priority: int
    reason: str


def prioritize_registered_accounts(
    age: int | None,
    annual_income: Decimal | None,
    first_time_home_buyer: bool,
    monthly_cash_flow: Decimal,
    goal_types: set[str],
    existing_account_types: set[str],
    dependents: list[dict],
) -> list[AccountRecommendation]:
    """Evaluates FHSA, RRSP-vs-TFSA ordering, a per-dependent RESP
    check, and a non-registered fallback, in that order. Only emits an
    entry when it's actually relevant; every entry cites the specific
    signal and constant that drove it.

    `goal_types` / `existing_account_types` are plain string sets (not
    ORM enum instances) so this module stays as import-free of
    app.models as financial_calculations.py.

    `dependents` is a list of {"name": str, "resp_monthly_contribution":
    Decimal | None} -- each dependent whose RESP contribution falls
    short of the CESG max-grant threshold gets their own named entry.
    """
    recommendations: list[AccountRecommendation] = []
    next_priority = 1

    fhsa_age_eligible = age is None or (FHSA_MIN_AGE <= age <= FHSA_MAX_AGE)
    if (
        first_time_home_buyer
        and "home_purchase" in goal_types
        and "fhsa" not in existing_account_types
        and fhsa_age_eligible
    ):
        recommendations.append(
            AccountRecommendation(
                account_type="fhsa",
                priority=next_priority,
                reason=(
                    "First-time home buyer with a home-purchase goal and no "
                    f"FHSA yet -- up to ${FHSA_ANNUAL_LIMIT:,.0f}/year "
                    f"(${FHSA_LIFETIME_LIMIT:,.0f} lifetime) is "
                    "tax-deductible and withdraws tax-free for a "
                    "qualifying home purchase."
                ),
            )
        )
        next_priority += 1

    income_favors_rrsp = (
        annual_income is not None and annual_income >= RRSP_MIN_INCOME_FOR_PRIORITY
    )
    rrsp_first = "rrsp" if income_favors_rrsp else "tfsa"
    account_order = (
        ["rrsp", "tfsa"] if rrsp_first == "rrsp" else ["tfsa", "rrsp"]
    )
    for account_type in account_order:
        if account_type in existing_account_types:
            continue
        if account_type == "rrsp":
            reason = (
                f"Income of ${annual_income:,.2f} is at or above the "
                f"${RRSP_MIN_INCOME_FOR_PRIORITY:,.0f} rule-of-thumb "
                "threshold where the RRSP tax deduction is worth "
                "prioritizing."
                if income_favors_rrsp
                else "Still worth considering once income exceeds the "
                f"${RRSP_MIN_INCOME_FOR_PRIORITY:,.0f} rule-of-thumb "
                "threshold where the deduction becomes more valuable."
            )
        else:
            reason = (
                f"Flat ${TFSA_ANNUAL_LIMIT:,.0f}/year of tax-free "
                "contribution room, useful alongside RRSP contributions."
                if income_favors_rrsp
                else f"At this income level, TFSA's flat "
                f"${TFSA_ANNUAL_LIMIT:,.0f}/year tax-free room is "
                "typically worth more than the RRSP deduction."
            )
        recommendations.append(
            AccountRecommendation(account_type, next_priority, reason)
        )
        next_priority += 1

    for dependent in dependents:
        contribution = dependent.get("resp_monthly_contribution") or Decimal("0")
        annual_contribution = contribution * 12
        if annual_contribution >= RESP_CESG_ANNUAL_CONTRIBUTION_FOR_MAX_GRANT:
            continue

        name = dependent.get("name") or "this dependent"
        shortfall = RESP_CESG_ANNUAL_CONTRIBUTION_FOR_MAX_GRANT - annual_contribution
        extra_grant = _round(shortfall * RESP_CESG_MATCH_RATE)
        recommendations.append(
            AccountRecommendation(
                account_type="resp",
                priority=next_priority,
                reason=(
                    f"{name}'s RESP is contributing ${annual_contribution:,.2f}"
                    f"/year, short of the "
                    f"${RESP_CESG_ANNUAL_CONTRIBUTION_FOR_MAX_GRANT:,.0f} "
                    f"needed to capture the full {RESP_CESG_MATCH_RATE:.0%} "
                    f"CESG match -- increasing by ${shortfall:,.2f}/year "
                    f"captures an extra ${extra_grant:,.2f}/year in free "
                    "government grant money."
                ),
            )
        )
        next_priority += 1

    if monthly_cash_flow > 0:
        recommendations.append(
            AccountRecommendation(
                account_type="non_registered",
                priority=next_priority,
                reason=(
                    "Remaining monthly cash flow, once the registered-"
                    "account room above is used, can go to a "
                    "non-registered investment account."
                ),
            )
        )
        next_priority += 1

    return recommendations
