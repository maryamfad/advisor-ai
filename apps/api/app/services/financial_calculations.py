"""Deterministic financial calculations.

Every function here is pure: plain Decimal/primitive inputs in, a
Decimal (or None where "not computable") out. No database session, no
ORM model, no LLM involved.

This is deliberate, per the project's AI safety principles (see
docs/ai-safety.md): the AI is never allowed to compute a financial
number itself, only to call a tool that runs one of these functions
and then explain the result. Keeping this module framework-agnostic
also means every function is trivially unit-testable without spinning
up a database.
"""

import math
from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Decimal

TWO_PLACES = Decimal("0.01")


def _round(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_monthly_income(transaction_amounts: Iterable[Decimal]) -> Decimal:
    """Sum of all positive (money-in) transaction amounts."""
    total = sum((a for a in transaction_amounts if a > 0), Decimal("0"))
    return _round(total)


def calculate_monthly_expenses(transaction_amounts: Iterable[Decimal]) -> Decimal:
    """Sum of all negative (money-out) transaction amounts, expressed
    as a positive number (i.e. "how much was spent", not a signed
    delta)."""
    total = sum((-a for a in transaction_amounts if a < 0), Decimal("0"))
    return _round(total)


def calculate_cash_flow(
    monthly_income: Decimal, monthly_expenses: Decimal
) -> Decimal:
    """Income minus expenses. Positive = surplus, negative = deficit."""
    return _round(monthly_income - monthly_expenses)


def calculate_savings_rate(
    monthly_income: Decimal, monthly_expenses: Decimal
) -> Decimal:
    """Percentage of income not spent. Returns 0 if income is zero or
    negative, rather than dividing by zero."""
    if monthly_income <= 0:
        return Decimal("0")

    savings = monthly_income - monthly_expenses

    return _round((savings / monthly_income) * 100)


def calculate_net_worth(
    asset_balances: Iterable[Decimal],
    liability_balances: Iterable[Decimal],
) -> Decimal:
    """Total assets (checking/savings/investment/retirement account
    balances) minus total liabilities (credit/loan balances, given as
    positive amounts owed)."""
    assets = sum(asset_balances, Decimal("0"))
    liabilities = sum(liability_balances, Decimal("0"))

    return _round(assets - liabilities)


def calculate_goal_projection(
    current_amount: Decimal,
    target_amount: Decimal,
    monthly_contribution: Decimal,
) -> int | None:
    """Whole months needed to reach target_amount at the given monthly
    contribution rate.

    Returns 0 if the goal is already met, and None if it's
    mathematically impossible to project (no contribution, or a
    contribution that isn't actually moving the balance toward the
    target) rather than raising or returning a misleading number.
    """
    remaining = target_amount - current_amount

    if remaining <= 0:
        return 0

    if monthly_contribution <= 0:
        return None

    return math.ceil(remaining / monthly_contribution)


def calculate_budget_variance(
    monthly_limit: Decimal, actual_spent: Decimal
) -> Decimal:
    """Budget limit minus actual spend. Positive = under budget,
    negative = over budget."""
    return _round(monthly_limit - actual_spent)
