from decimal import Decimal

from pydantic import BaseModel


class FinancialSummary(BaseModel):
    monthly_income: Decimal
    monthly_expenses: Decimal
    monthly_cash_flow: Decimal
    savings_rate: Decimal
    net_worth: Decimal


class InsuranceRecommendation(BaseModel):
    recommended_type: str
    reasons: list[str]
    estimated_coverage_need: Decimal
    existing_coverage: Decimal
    coverage_gap: Decimal


class RegisteredAccountRecommendation(BaseModel):
    account_type: str
    priority: int
    reason: str


class OwnerRegisteredAccountRecommendations(BaseModel):
    owner: str
    recommendations: list[RegisteredAccountRecommendation]


class ClientRecommendation(BaseModel):
    financial_summary: FinancialSummary
    insurance: InsuranceRecommendation
    registered_accounts: list[OwnerRegisteredAccountRecommendations]
