from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.financial_needs_analysis import InvestorRating, RiskTolerance


class FinancialNeedsAnalysisBase(BaseModel):
    conducted_at: date

    # Household planning
    has_monthly_budget: bool | None = None
    has_regular_savings_plan: bool | None = None
    monthly_savings_capacity: Decimal | None = None
    biggest_financial_concern: str | None = None
    notes: str | None = None

    # Investor profile
    investment_knowledge: InvestorRating | None = None
    risk_tolerance: RiskTolerance | None = None
    investment_experience: InvestorRating | None = None

    # Goal priority ratings (1-10)
    priority_cash_flow: int | None = None
    priority_protection: int | None = None
    priority_retirement: int | None = None
    priority_emergency_fund: int | None = None
    priority_debt: int | None = None
    priority_estate_preservation: int | None = None

    # Declared life-insurance needs (the DIME checklist)
    wants_debt_payoff: bool = False
    wants_income_replacement: bool = False
    income_replacement_amount: Decimal | None = None
    income_replacement_percent: Decimal | None = None
    income_replacement_years: int | None = None
    wants_mortgage_payoff: bool = False
    wants_education_funding: bool = False
    education_funding_amount: Decimal | None = None
    wants_final_expenses: bool = False
    final_expenses_amount: Decimal | None = None
    wants_emergency_fund: bool = False
    emergency_fund_months: int | None = None


class FinancialNeedsAnalysisCreate(FinancialNeedsAnalysisBase):
    """Payload for POST /clients/{client_id}/financial-needs-analyses.
    client_id comes from the URL, never from the request body."""


class FinancialNeedsAnalysisUpdate(BaseModel):
    """Payload for PATCH /clients/{client_id}/financial-needs-analyses/{id}.
    All fields optional so the advisor can update just what changed."""

    conducted_at: date | None = None
    has_monthly_budget: bool | None = None
    has_regular_savings_plan: bool | None = None
    monthly_savings_capacity: Decimal | None = None
    biggest_financial_concern: str | None = None
    notes: str | None = None
    investment_knowledge: InvestorRating | None = None
    risk_tolerance: RiskTolerance | None = None
    investment_experience: InvestorRating | None = None
    priority_cash_flow: int | None = None
    priority_protection: int | None = None
    priority_retirement: int | None = None
    priority_emergency_fund: int | None = None
    priority_debt: int | None = None
    priority_estate_preservation: int | None = None
    wants_debt_payoff: bool | None = None
    wants_income_replacement: bool | None = None
    income_replacement_amount: Decimal | None = None
    income_replacement_percent: Decimal | None = None
    income_replacement_years: int | None = None
    wants_mortgage_payoff: bool | None = None
    wants_education_funding: bool | None = None
    education_funding_amount: Decimal | None = None
    wants_final_expenses: bool | None = None
    final_expenses_amount: Decimal | None = None
    wants_emergency_fund: bool | None = None
    emergency_fund_months: int | None = None


class FinancialNeedsAnalysisRead(FinancialNeedsAnalysisBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    created_at: datetime
