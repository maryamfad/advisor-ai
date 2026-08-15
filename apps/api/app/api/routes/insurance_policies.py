from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    get_owned_client,
    get_owned_insurance_policy,
)
from app.models.client import Client
from app.models.insurance_policy import InsurancePolicy
from app.schemas.insurance_policy import (
    InsurancePolicyCreate,
    InsurancePolicyRead,
    InsurancePolicyUpdate,
)

router = APIRouter(
    prefix="/clients/{client_id}/insurance-policies", tags=["insurance-policies"]
)


@router.post(
    "", response_model=InsurancePolicyRead, status_code=status.HTTP_201_CREATED
)
def create_insurance_policy(
    payload: InsurancePolicyCreate,
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> InsurancePolicy:
    policy = InsurancePolicy(
        client_id=client.id,
        policy_type=payload.policy_type,
        insured_owner=payload.insured_owner,
        policy_owner=payload.policy_owner,
        beneficiary=payload.beneficiary,
        provider=payload.provider,
        policy_number=payload.policy_number,
        coverage_amount=payload.coverage_amount,
        surrender_value=payload.surrender_value,
        premium=payload.premium,
        premium_frequency=payload.premium_frequency,
        policy_year=payload.policy_year,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=payload.status,
    )

    db.add(policy)
    db.commit()
    db.refresh(policy)

    return policy


@router.get("", response_model=list[InsurancePolicyRead])
def list_insurance_policies(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> list[InsurancePolicy]:
    stmt = select(InsurancePolicy).where(InsurancePolicy.client_id == client.id)

    return list(db.scalars(stmt).all())


@router.get("/{insurance_policy_id}", response_model=InsurancePolicyRead)
def get_insurance_policy(
    policy: InsurancePolicy = Depends(get_owned_insurance_policy),
) -> InsurancePolicy:
    return policy


@router.patch("/{insurance_policy_id}", response_model=InsurancePolicyRead)
def update_insurance_policy(
    payload: InsurancePolicyUpdate,
    db: Session = Depends(get_db),
    policy: InsurancePolicy = Depends(get_owned_insurance_policy),
) -> InsurancePolicy:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(policy, field, value)

    db.commit()
    db.refresh(policy)

    return policy


@router.delete("/{insurance_policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_insurance_policy(
    db: Session = Depends(get_db),
    policy: InsurancePolicy = Depends(get_owned_insurance_policy),
) -> None:
    db.delete(policy)
    db.commit()
