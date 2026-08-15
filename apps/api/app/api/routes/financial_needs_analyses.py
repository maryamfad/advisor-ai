from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    get_owned_client,
    get_owned_financial_needs_analysis,
)
from app.models.client import Client
from app.models.financial_needs_analysis import FinancialNeedsAnalysis
from app.schemas.financial_needs_analysis import (
    FinancialNeedsAnalysisCreate,
    FinancialNeedsAnalysisRead,
    FinancialNeedsAnalysisUpdate,
)

router = APIRouter(
    prefix="/clients/{client_id}/financial-needs-analyses",
    tags=["financial-needs-analyses"],
)


@router.post(
    "",
    response_model=FinancialNeedsAnalysisRead,
    status_code=status.HTTP_201_CREATED,
)
def create_financial_needs_analysis(
    payload: FinancialNeedsAnalysisCreate,
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> FinancialNeedsAnalysis:
    fna = FinancialNeedsAnalysis(
        client_id=client.id,
        conducted_at=payload.conducted_at,
        has_monthly_budget=payload.has_monthly_budget,
        has_regular_savings_plan=payload.has_regular_savings_plan,
        monthly_savings_capacity=payload.monthly_savings_capacity,
        biggest_financial_concern=payload.biggest_financial_concern,
        notes=payload.notes,
        investment_knowledge=payload.investment_knowledge,
        risk_tolerance=payload.risk_tolerance,
        investment_experience=payload.investment_experience,
        priority_cash_flow=payload.priority_cash_flow,
        priority_protection=payload.priority_protection,
        priority_retirement=payload.priority_retirement,
        priority_emergency_fund=payload.priority_emergency_fund,
        priority_debt=payload.priority_debt,
        priority_estate_preservation=payload.priority_estate_preservation,
        wants_debt_payoff=payload.wants_debt_payoff,
        wants_income_replacement=payload.wants_income_replacement,
        income_replacement_amount=payload.income_replacement_amount,
        income_replacement_percent=payload.income_replacement_percent,
        income_replacement_years=payload.income_replacement_years,
        wants_mortgage_payoff=payload.wants_mortgage_payoff,
        wants_education_funding=payload.wants_education_funding,
        education_funding_amount=payload.education_funding_amount,
        wants_final_expenses=payload.wants_final_expenses,
        final_expenses_amount=payload.final_expenses_amount,
        wants_emergency_fund=payload.wants_emergency_fund,
        emergency_fund_months=payload.emergency_fund_months,
    )

    db.add(fna)
    db.commit()
    db.refresh(fna)

    return fna


@router.get("", response_model=list[FinancialNeedsAnalysisRead])
def list_financial_needs_analyses(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> list[FinancialNeedsAnalysis]:
    stmt = (
        select(FinancialNeedsAnalysis)
        .where(FinancialNeedsAnalysis.client_id == client.id)
        .order_by(FinancialNeedsAnalysis.conducted_at.desc())
    )

    return list(db.scalars(stmt).all())


@router.get(
    "/{financial_needs_analysis_id}", response_model=FinancialNeedsAnalysisRead
)
def get_financial_needs_analysis(
    fna: FinancialNeedsAnalysis = Depends(get_owned_financial_needs_analysis),
) -> FinancialNeedsAnalysis:
    return fna


@router.patch(
    "/{financial_needs_analysis_id}", response_model=FinancialNeedsAnalysisRead
)
def update_financial_needs_analysis(
    payload: FinancialNeedsAnalysisUpdate,
    db: Session = Depends(get_db),
    fna: FinancialNeedsAnalysis = Depends(get_owned_financial_needs_analysis),
) -> FinancialNeedsAnalysis:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(fna, field, value)

    db.commit()
    db.refresh(fna)

    return fna


@router.delete(
    "/{financial_needs_analysis_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_financial_needs_analysis(
    db: Session = Depends(get_db),
    fna: FinancialNeedsAnalysis = Depends(get_owned_financial_needs_analysis),
) -> None:
    db.delete(fna)
    db.commit()
