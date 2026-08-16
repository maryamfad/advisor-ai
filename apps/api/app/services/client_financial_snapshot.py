"""Gathers a client's financial data plus every advice-engine output
computed from it, in one place.

Both the advice endpoint (app/api/routes/advice.py) and the financial
plan generator need the same inputs, so this factors out the query
assembly and calculation calls that advice.py used to do inline --
callers just map the resulting snapshot into whatever response shape
they need, instead of duplicating the same select() statements.

Deliberately NOT pure -- it takes a DB session -- unlike everything in
financial_calculations.py/financial_advice.py. Kept in app/services/
anyway, as the clearly-labeled DB-touching exception (the same
category market_data_client.py will be later), rather than living in
the route layer where it would inevitably get copy-pasted.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account, AccountType
from app.models.client import Client
from app.models.debt import Debt, DebtType
from app.models.dependent import Dependent
from app.models.financial_goal import FinancialGoal, GoalStatus
from app.models.financial_needs_analysis import FinancialNeedsAnalysis
from app.models.income_source import IncomeSource
from app.models.insurance_policy import InsurancePolicy, PolicyStatus, PolicyType
from app.models.risk_questionnaire import RiskQuestionnaire
from app.models.spouse import HouseholdMemberRole, Spouse
from app.models.transaction import Transaction
from app.services.financial_advice import (
    AccountRecommendation,
    InsuranceTypeRecommendation,
    calculate_insurance_gap,
    calculate_life_insurance_need,
    prioritize_registered_accounts,
    recommend_life_insurance_type,
)
from app.services.financial_calculations import (
    calculate_cash_flow,
    calculate_monthly_expenses,
    calculate_monthly_income,
    calculate_net_worth,
    calculate_savings_rate,
    normalize_income_to_monthly,
)

LIFE_INSURANCE_POLICY_TYPES = {PolicyType.TERM_LIFE, PolicyType.WHOLE_LIFE}
MORTGAGE_DEBT_TYPES = {DebtType.MORTGAGE_PRIMARY, DebtType.MORTGAGE_SECONDARY_HELOC}
LIABILITY_ACCOUNT_TYPES = {AccountType.CREDIT, AccountType.LOAN}


@dataclass(frozen=True)
class ClientFinancialSnapshot:
    # Raw data
    accounts: list[Account]
    transactions: list[Transaction]
    goals: list[FinancialGoal]
    active_policies: list[InsurancePolicy]
    debts: list[Debt]
    income_sources: list[IncomeSource]
    dependents: list[Dependent]
    spouse: Spouse | None
    latest_fna: FinancialNeedsAnalysis | None
    latest_completed_questionnaire: RiskQuestionnaire | None

    # Financial summary
    monthly_income: Decimal
    monthly_expenses: Decimal
    monthly_cash_flow: Decimal
    savings_rate: Decimal
    net_worth: Decimal
    annual_income: Decimal
    age: int | None
    risk_tolerance: str | None

    # Insurance
    total_debt_excluding_mortgage: Decimal
    mortgage_balance: Decimal
    existing_coverage: Decimal
    target_coverage: Decimal
    coverage_gap: Decimal
    insurance_type_recommendation: InsuranceTypeRecommendation

    # Registered accounts, per household member
    client_account_recommendations: list[AccountRecommendation]
    spouse_account_recommendations: list[AccountRecommendation]


def _calculate_age(date_of_birth: date | None) -> int | None:
    """Wall-clock-dependent, so kept here rather than in the pure
    app/services functions, which take an already-computed `age`."""
    if date_of_birth is None:
        return None

    today = date.today()
    age = today.year - date_of_birth.year
    if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
        age -= 1

    return age


def _monthly_income_from_sources(sources: list[IncomeSource]) -> Decimal:
    return sum(
        (normalize_income_to_monthly(s.gross_amount, s.frequency) for s in sources),
        start=Decimal("0.00"),
    )


def gather_client_financial_data(
    db: Session, client: Client
) -> ClientFinancialSnapshot:
    accounts = list(
        db.scalars(select(Account).where(Account.client_id == client.id)).all()
    )
    account_ids = [account.id for account in accounts]
    transactions = (
        list(
            db.scalars(
                select(Transaction).where(Transaction.account_id.in_(account_ids))
            ).all()
        )
        if account_ids
        else []
    )
    goals = list(
        db.scalars(
            select(FinancialGoal).where(FinancialGoal.client_id == client.id)
        ).all()
    )
    active_policies = list(
        db.scalars(
            select(InsurancePolicy).where(
                InsurancePolicy.client_id == client.id,
                InsurancePolicy.status == PolicyStatus.ACTIVE,
            )
        ).all()
    )
    debts = list(db.scalars(select(Debt).where(Debt.client_id == client.id)).all())
    income_sources = list(
        db.scalars(
            select(IncomeSource).where(IncomeSource.client_id == client.id)
        ).all()
    )
    latest_fna = db.scalar(
        select(FinancialNeedsAnalysis)
        .where(FinancialNeedsAnalysis.client_id == client.id)
        .order_by(FinancialNeedsAnalysis.conducted_at.desc())
        .limit(1)
    )
    latest_completed_questionnaire = db.scalar(
        select(RiskQuestionnaire)
        .where(
            RiskQuestionnaire.client_id == client.id,
            RiskQuestionnaire.completed_at.is_not(None),
        )
        .order_by(RiskQuestionnaire.completed_at.desc())
        .limit(1)
    )
    dependents = list(client.dependents)
    spouse = client.spouse

    # -- Financial summary --------------------------------------------

    current_income_sources = [s for s in income_sources if not s.is_future]
    if current_income_sources:
        monthly_income = _monthly_income_from_sources(current_income_sources)
    else:
        # No declared income sources on file -- fall back to
        # transaction-derived income rather than guessing.
        monthly_income = calculate_monthly_income(t.amount for t in transactions)

    monthly_expenses = calculate_monthly_expenses(t.amount for t in transactions)
    monthly_cash_flow = calculate_cash_flow(monthly_income, monthly_expenses)
    savings_rate = calculate_savings_rate(monthly_income, monthly_expenses)

    asset_balances = [
        a.balance for a in accounts if a.account_type not in LIABILITY_ACCOUNT_TYPES
    ]
    liability_balances = [
        a.balance for a in accounts if a.account_type in LIABILITY_ACCOUNT_TYPES
    ]
    net_worth = calculate_net_worth(asset_balances, liability_balances)
    annual_income = monthly_income * 12

    # -- Insurance ------------------------------------------------------

    total_debt_excluding_mortgage = sum(
        (d.balance for d in debts if d.debt_type not in MORTGAGE_DEBT_TYPES),
        start=Decimal("0.00"),
    )
    mortgage_balance = sum(
        (d.balance for d in debts if d.debt_type in MORTGAGE_DEBT_TYPES),
        start=Decimal("0.00"),
    )
    existing_coverage = sum(
        (
            p.coverage_amount
            for p in active_policies
            if p.policy_type in LIFE_INSURANCE_POLICY_TYPES and p.coverage_amount
        ),
        start=Decimal("0.00"),
    )

    if latest_fna is not None:
        target_coverage = calculate_life_insurance_need(
            wants_debt_payoff=latest_fna.wants_debt_payoff,
            total_debt_excluding_mortgage=total_debt_excluding_mortgage,
            wants_mortgage_payoff=latest_fna.wants_mortgage_payoff,
            mortgage_balance=mortgage_balance,
            wants_income_replacement=latest_fna.wants_income_replacement,
            annual_income=annual_income,
            income_replacement_amount=latest_fna.income_replacement_amount,
            income_replacement_percent=latest_fna.income_replacement_percent,
            income_replacement_years=latest_fna.income_replacement_years,
            wants_education_funding=latest_fna.wants_education_funding,
            education_funding_amount=latest_fna.education_funding_amount,
            wants_final_expenses=latest_fna.wants_final_expenses,
            final_expenses_amount=latest_fna.final_expenses_amount,
            wants_emergency_fund=latest_fna.wants_emergency_fund,
            monthly_expenses=monthly_expenses,
            emergency_fund_months=latest_fna.emergency_fund_months,
        )
    else:
        # No FNA on file -- no declared insurance needs to sum, so the
        # target is 0 rather than a guessed figure.
        target_coverage = Decimal("0.00")

    coverage_gap = calculate_insurance_gap(target_coverage, existing_coverage)

    age = _calculate_age(client.date_of_birth)
    # A formally scored questionnaire is authoritative over the FNA
    # form's self-rated checkbox when both are on file.
    if (
        latest_completed_questionnaire
        and latest_completed_questionnaire.risk_tolerance
    ):
        risk_tolerance = latest_completed_questionnaire.risk_tolerance.value
    elif latest_fna and latest_fna.risk_tolerance:
        risk_tolerance = latest_fna.risk_tolerance.value
    else:
        risk_tolerance = None

    insurance_type_recommendation = recommend_life_insurance_type(
        age=age,
        dependents_count=len(dependents),
        net_worth=net_worth,
        monthly_income=monthly_income,
        monthly_cash_flow=monthly_cash_flow,
        risk_tolerance=risk_tolerance,
    )

    # -- Registered accounts ---------------------------------------------

    active_goal_types = {
        g.goal_type.value for g in goals if g.status == GoalStatus.ACTIVE
    }

    resp_contribution_by_dependent: dict[int, Decimal] = {}
    for account in accounts:
        if (
            account.account_type == AccountType.RESP
            and account.resp_beneficiary_dependent_id is not None
            and account.monthly_contribution is not None
        ):
            dependent_id = account.resp_beneficiary_dependent_id
            resp_contribution_by_dependent[dependent_id] = (
                resp_contribution_by_dependent.get(dependent_id, Decimal("0.00"))
                + account.monthly_contribution
            )

    dependents_payload = [
        {
            "name": dependent.name,
            "resp_monthly_contribution": resp_contribution_by_dependent.get(
                dependent.id
            ),
        }
        for dependent in dependents
    ]

    client_existing_account_types = {
        a.account_type.value for a in accounts if a.owner == HouseholdMemberRole.CLIENT
    }
    client_account_recommendations = prioritize_registered_accounts(
        age=age,
        annual_income=annual_income if annual_income > 0 else None,
        first_time_home_buyer=client.first_time_home_buyer,
        monthly_cash_flow=monthly_cash_flow,
        goal_types=active_goal_types,
        existing_account_types=client_existing_account_types,
        # RESP recommendations are household-level, not per-earner --
        # only surfaced once, under the client, to avoid duplicating
        # the same underfunded-child recommendation under the spouse.
        dependents=dependents_payload,
    )

    spouse_account_recommendations: list[AccountRecommendation] = []
    if spouse is not None:
        spouse_income_sources = [
            s
            for s in income_sources
            if s.owner == HouseholdMemberRole.SPOUSE and not s.is_future
        ]
        spouse_monthly_income = _monthly_income_from_sources(spouse_income_sources)
        spouse_annual_income = spouse_monthly_income * 12
        spouse_existing_account_types = {
            a.account_type.value
            for a in accounts
            if a.owner == HouseholdMemberRole.SPOUSE
        }
        spouse_account_recommendations = prioritize_registered_accounts(
            age=_calculate_age(spouse.date_of_birth),
            annual_income=spouse_annual_income if spouse_annual_income > 0 else None,
            first_time_home_buyer=client.first_time_home_buyer,
            monthly_cash_flow=monthly_cash_flow,
            goal_types=active_goal_types,
            existing_account_types=spouse_existing_account_types,
            dependents=[],
        )

    return ClientFinancialSnapshot(
        accounts=accounts,
        transactions=transactions,
        goals=goals,
        active_policies=active_policies,
        debts=debts,
        income_sources=income_sources,
        dependents=dependents,
        spouse=spouse,
        latest_fna=latest_fna,
        latest_completed_questionnaire=latest_completed_questionnaire,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        monthly_cash_flow=monthly_cash_flow,
        savings_rate=savings_rate,
        net_worth=net_worth,
        annual_income=annual_income,
        age=age,
        risk_tolerance=risk_tolerance,
        total_debt_excluding_mortgage=total_debt_excluding_mortgage,
        mortgage_balance=mortgage_balance,
        existing_coverage=existing_coverage,
        target_coverage=target_coverage,
        coverage_gap=coverage_gap,
        insurance_type_recommendation=insurance_type_recommendation,
        client_account_recommendations=client_account_recommendations,
        spouse_account_recommendations=spouse_account_recommendations,
    )
