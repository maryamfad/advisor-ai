from decimal import Decimal

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    get_owned_client,
    get_owned_financial_plan,
    get_owned_financial_plan_action_item,
)
from app.models.account import AccountType
from app.models.client import Client
from app.models.financial_goal import GoalStatus, GoalType
from app.models.financial_needs_analysis import FinancialNeedsAnalysis
from app.models.financial_plan import (
    ActionItemCategory,
    FinancialPlan,
    FinancialPlanActionItem,
)
from app.schemas.financial_plan import (
    FinancialPlanActionItemRead,
    FinancialPlanActionItemUpdate,
    FinancialPlanRead,
)
from app.services.client_financial_snapshot import (
    ClientFinancialSnapshot,
    gather_client_financial_data,
)
from app.services.financial_plan_generator import (
    ActionItem,
    generate_action_items,
    generate_narrative_summary,
)

router = APIRouter(
    prefix="/clients/{client_id}/financial-plans", tags=["financial-plans"]
)

# Accounts an advisor can actually draw on without penalty/delay if an
# emergency hits -- the classic "liquid" account types.
LIQUID_ACCOUNT_TYPES = {AccountType.CHECKING, AccountType.SAVINGS}


def _priority_ratings(fna: FinancialNeedsAnalysis | None) -> dict[str, int] | None:
    if fna is None:
        return None

    candidate = {
        "emergency_fund": fna.priority_emergency_fund,
        "debt": fna.priority_debt,
        "protection": fna.priority_protection,
        "retirement": fna.priority_retirement,
    }
    return {key: value for key, value in candidate.items() if value is not None}


def _recommendation_payload(owner: str, recommendation) -> dict:
    return {
        "owner": owner,
        "account_type": recommendation.account_type,
        "priority": recommendation.priority,
        "reason": recommendation.reason,
    }


def _goal_payload(goal) -> dict:
    return {
        "name": goal.name,
        "target_amount": goal.target_amount,
        "current_amount": goal.current_amount,
        "monthly_contribution": goal.monthly_contribution,
    }


def _build_generator_inputs(snapshot: ClientFinancialSnapshot) -> dict:
    liquid_savings = sum(
        (
            a.balance
            for a in snapshot.accounts
            if a.account_type in LIQUID_ACCOUNT_TYPES
        ),
        start=Decimal("0.00"),
    )

    debts = [
        {
            "description": d.description,
            "balance": d.balance,
            "interest_rate": d.interest_rate,
        }
        for d in snapshot.debts
    ]

    active_goals = [g for g in snapshot.goals if g.status == GoalStatus.ACTIVE]
    non_retirement_goals = [
        _goal_payload(g) for g in active_goals if g.goal_type != GoalType.RETIREMENT
    ]
    retirement_goal_row = next(
        (g for g in active_goals if g.goal_type == GoalType.RETIREMENT), None
    )
    retirement_goal = (
        _goal_payload(retirement_goal_row) if retirement_goal_row is not None else None
    )

    return {
        "monthly_expenses": snapshot.monthly_expenses,
        "liquid_savings": liquid_savings,
        "emergency_fund_months": (
            snapshot.latest_fna.emergency_fund_months if snapshot.latest_fna else None
        ),
        "debts": debts,
        "insurance_recommended_type": (
            snapshot.insurance_type_recommendation.recommendation
        ),
        "insurance_coverage_gap": snapshot.coverage_gap,
        "registered_account_recommendations": (
            snapshot.client_account_recommendations
            + snapshot.spouse_account_recommendations
        ),
        "goals": non_retirement_goals,
        "retirement_goal": retirement_goal,
        "priority_ratings": _priority_ratings(snapshot.latest_fna),
    }


def _build_summary_snapshot(
    snapshot: ClientFinancialSnapshot, items: list[ActionItem]
) -> dict:
    return {
        "monthly_income": str(snapshot.monthly_income),
        "monthly_expenses": str(snapshot.monthly_expenses),
        "monthly_cash_flow": str(snapshot.monthly_cash_flow),
        "savings_rate": str(snapshot.savings_rate),
        "net_worth": str(snapshot.net_worth),
        "insurance_recommended_type": (
            snapshot.insurance_type_recommendation.recommendation
        ),
        "insurance_coverage_gap": str(snapshot.coverage_gap),
        "registered_account_recommendations": [
            _recommendation_payload("client", r)
            for r in snapshot.client_account_recommendations
        ]
        + [
            _recommendation_payload("spouse", r)
            for r in snapshot.spouse_account_recommendations
        ],
        "action_item_count": len(items),
    }


@router.post("", response_model=FinancialPlanRead, status_code=status.HTTP_201_CREATED)
def create_financial_plan(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> FinancialPlan:
    snapshot = gather_client_financial_data(db, client)
    items = generate_action_items(**_build_generator_inputs(snapshot))
    narrative = generate_narrative_summary(
        monthly_cash_flow=snapshot.monthly_cash_flow,
        savings_rate=snapshot.savings_rate,
        net_worth=snapshot.net_worth,
        action_items=items,
    )

    plan = FinancialPlan(
        client_id=client.id,
        summary_snapshot=_build_summary_snapshot(snapshot, items),
        narrative_summary=narrative,
    )
    db.add(plan)
    db.flush()  # assigns plan.id before the action items reference it

    for item in items:
        db.add(
            FinancialPlanActionItem(
                financial_plan_id=plan.id,
                priority=item.priority,
                category=ActionItemCategory(item.category),
                title=item.title,
                description=item.description,
                target_amount=item.target_amount,
            )
        )

    db.commit()
    db.refresh(plan)

    return plan


@router.get("", response_model=list[FinancialPlanRead])
def list_financial_plans(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> list[FinancialPlan]:
    stmt = (
        select(FinancialPlan)
        .where(FinancialPlan.client_id == client.id)
        .order_by(FinancialPlan.generated_at.desc())
    )

    return list(db.scalars(stmt).all())


@router.get("/{plan_id}", response_model=FinancialPlanRead)
def get_financial_plan(
    plan: FinancialPlan = Depends(get_owned_financial_plan),
) -> FinancialPlan:
    return plan


@router.patch(
    "/{plan_id}/action-items/{item_id}", response_model=FinancialPlanActionItemRead
)
def update_financial_plan_action_item(
    payload: FinancialPlanActionItemUpdate,
    db: Session = Depends(get_db),
    action_item: FinancialPlanActionItem = Depends(
        get_owned_financial_plan_action_item
    ),
) -> FinancialPlanActionItem:
    action_item.status = payload.status

    db.commit()
    db.refresh(action_item)

    return action_item


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_financial_plan(
    db: Session = Depends(get_db),
    plan: FinancialPlan = Depends(get_owned_financial_plan),
) -> None:
    db.delete(plan)
    db.commit()
