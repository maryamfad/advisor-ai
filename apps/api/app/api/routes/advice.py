from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_owned_client
from app.models.account import Account, AccountType
from app.models.client import Client
from app.models.debt import Debt, DebtType
from app.models.financial_goal import FinancialGoal, GoalStatus
from app.models.financial_needs_analysis import FinancialNeedsAnalysis
from app.models.income_source import IncomeSource
from app.models.insurance_policy import InsurancePolicy, PolicyStatus, PolicyType
from app.models.risk_questionnaire import RiskQuestionnaire
from app.models.spouse import HouseholdMemberRole
from app.models.transaction import Transaction
from app.schemas.advice import (
    ClientAdvice,
    FinancialSummary,
    InsuranceRecommendation,
    OwnerRegisteredAccountRecommendations,
    RegisteredAccountRecommendation,
)
from app.services.financial_advice import (
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

router = APIRouter(prefix="/clients/{client_id}/advice", tags=["advice"])

LIFE_INSURANCE_POLICY_TYPES = {PolicyType.TERM_LIFE, PolicyType.WHOLE_LIFE}
MORTGAGE_DEBT_TYPES = {DebtType.MORTGAGE_PRIMARY, DebtType.MORTGAGE_SECONDARY_HELOC}


def _calculate_age(date_of_birth: date | None) -> int | None:
    """Wall-clock-dependent, so kept in the route layer rather than
    the pure app/services functions, which take an already-computed
    `age` parameter."""
    if date_of_birth is None:
        return None

    today = date.today()
    age = today.year - date_of_birth.year
    if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
        age -= 1

    return age


@router.get("", response_model=ClientAdvice)
def get_client_advice(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> ClientAdvice:
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

    # -- Financial summary --------------------------------------------

    current_income_sources = [s for s in income_sources if not s.is_future]
    if current_income_sources:
        monthly_income = sum(
            (
                normalize_income_to_monthly(source.gross_amount, source.frequency)
                for source in current_income_sources
            ),
            start=Decimal("0.00"),
        )
    else:
        # No declared income sources on file -- fall back to
        # transaction-derived income rather than guessing.
        monthly_income = calculate_monthly_income(t.amount for t in transactions)

    monthly_expenses = calculate_monthly_expenses(t.amount for t in transactions)
    monthly_cash_flow = calculate_cash_flow(monthly_income, monthly_expenses)
    savings_rate = calculate_savings_rate(monthly_income, monthly_expenses)

    liability_types = {AccountType.CREDIT, AccountType.LOAN}
    asset_balances = [
        a.balance for a in accounts if a.account_type not in liability_types
    ]
    liability_balances = [
        a.balance for a in accounts if a.account_type in liability_types
    ]
    net_worth = calculate_net_worth(asset_balances, liability_balances)

    financial_summary = FinancialSummary(
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        monthly_cash_flow=monthly_cash_flow,
        savings_rate=savings_rate,
        net_worth=net_worth,
    )

    # -- Insurance ------------------------------------------------------

    annual_income = monthly_income * 12
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
        # target is 0 rather than a guessed figure. The reason string
        # below says so explicitly.
        target_coverage = Decimal("0.00")

    coverage_gap = calculate_insurance_gap(target_coverage, existing_coverage)

    age = _calculate_age(client.date_of_birth)
    # A formally scored questionnaire is authoritative over the FNA
    # form's self-rated checkbox when both are on file.
    if latest_completed_questionnaire and latest_completed_questionnaire.risk_tolerance:
        risk_tolerance = latest_completed_questionnaire.risk_tolerance.value
    elif latest_fna and latest_fna.risk_tolerance:
        risk_tolerance = latest_fna.risk_tolerance.value
    else:
        risk_tolerance = None

    type_recommendation = recommend_life_insurance_type(
        age=age,
        dependents_count=len(dependents),
        net_worth=net_worth,
        monthly_income=monthly_income,
        monthly_cash_flow=monthly_cash_flow,
        risk_tolerance=risk_tolerance,
    )

    reasons = list(type_recommendation.reasons)
    if latest_fna is None:
        reasons.append(
            "No financial needs analysis on file -- estimated coverage need "
            "is $0 until the client's insurance priorities are recorded."
        )

    insurance = InsuranceRecommendation(
        recommended_type=type_recommendation.recommendation,
        reasons=reasons,
        estimated_coverage_need=target_coverage,
        existing_coverage=existing_coverage,
        coverage_gap=coverage_gap,
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
                resp_contribution_by_dependent.get(
                    dependent_id, Decimal("0.00")
                )
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

    registered_accounts: list[OwnerRegisteredAccountRecommendations] = []

    client_existing_account_types = {
        a.account_type.value
        for a in accounts
        if a.owner == HouseholdMemberRole.CLIENT
    }
    client_recommendations = prioritize_registered_accounts(
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
    registered_accounts.append(
        OwnerRegisteredAccountRecommendations(
            owner="client",
            recommendations=[
                RegisteredAccountRecommendation(
                    account_type=r.account_type,
                    priority=r.priority,
                    reason=r.reason,
                )
                for r in client_recommendations
            ],
        )
    )

    if client.spouse is not None:
        spouse_income_sources = [
            s for s in income_sources
            if s.owner == HouseholdMemberRole.SPOUSE and not s.is_future
        ]
        spouse_monthly_income = sum(
            (
                normalize_income_to_monthly(s.gross_amount, s.frequency)
                for s in spouse_income_sources
            ),
            start=Decimal("0.00"),
        )
        spouse_annual_income = spouse_monthly_income * 12
        spouse_existing_account_types = {
            a.account_type.value
            for a in accounts
            if a.owner == HouseholdMemberRole.SPOUSE
        }
        spouse_recommendations = prioritize_registered_accounts(
            age=_calculate_age(client.spouse.date_of_birth),
            annual_income=spouse_annual_income if spouse_annual_income > 0 else None,
            first_time_home_buyer=client.first_time_home_buyer,
            monthly_cash_flow=monthly_cash_flow,
            goal_types=active_goal_types,
            existing_account_types=spouse_existing_account_types,
            dependents=[],
        )
        registered_accounts.append(
            OwnerRegisteredAccountRecommendations(
                owner="spouse",
                recommendations=[
                    RegisteredAccountRecommendation(
                        account_type=r.account_type,
                        priority=r.priority,
                        reason=r.reason,
                    )
                    for r in spouse_recommendations
                ],
            )
        )

    return ClientAdvice(
        financial_summary=financial_summary,
        insurance=insurance,
        registered_accounts=registered_accounts,
    )
