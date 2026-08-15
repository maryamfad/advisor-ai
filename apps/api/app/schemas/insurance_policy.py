from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.insurance_policy import PolicyStatus, PolicyType, PremiumFrequency
from app.models.spouse import HouseholdMemberRole


class InsurancePolicyBase(BaseModel):
    policy_type: PolicyType
    insured_owner: HouseholdMemberRole = HouseholdMemberRole.CLIENT
    policy_owner: str | None = None
    beneficiary: str | None = None
    provider: str
    policy_number: str | None = None
    coverage_amount: Decimal | None = None
    surrender_value: Decimal | None = None
    premium: Decimal | None = None
    premium_frequency: PremiumFrequency | None = None
    policy_year: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: PolicyStatus = PolicyStatus.ACTIVE


class InsurancePolicyCreate(InsurancePolicyBase):
    """Payload for POST /clients/{client_id}/insurance-policies.
    client_id comes from the URL, never from the request body."""


class InsurancePolicyUpdate(BaseModel):
    """Payload for PATCH /clients/{client_id}/insurance-policies/{id}.
    All fields optional so the advisor can update just what changed."""

    policy_type: PolicyType | None = None
    insured_owner: HouseholdMemberRole | None = None
    policy_owner: str | None = None
    beneficiary: str | None = None
    provider: str | None = None
    policy_number: str | None = None
    coverage_amount: Decimal | None = None
    surrender_value: Decimal | None = None
    premium: Decimal | None = None
    premium_frequency: PremiumFrequency | None = None
    policy_year: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: PolicyStatus | None = None


class InsurancePolicyRead(InsurancePolicyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    created_at: datetime
