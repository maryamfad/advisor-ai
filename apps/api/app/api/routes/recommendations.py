from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_owned_client
from app.models.client import Client
from app.schemas.recommendations import (
    ClientRecommendation,
    FinancialSummary,
    InsuranceRecommendation,
    OwnerRegisteredAccountRecommendations,
    RegisteredAccountRecommendation,
)
from app.services.client_financial_snapshot import (
    ClientFinancialSnapshot,
    gather_client_financial_data,
)
from app.services.financial_recommendations import AccountRecommendation

router = APIRouter(
    prefix="/clients/{client_id}/recommendations", tags=["recommendations"]
)


def _to_recommendation_schemas(
    recommendations: list[AccountRecommendation],
) -> list[RegisteredAccountRecommendation]:
    return [
        RegisteredAccountRecommendation(
            account_type=r.account_type, priority=r.priority, reason=r.reason
        )
        for r in recommendations
    ]


@router.get("", response_model=ClientRecommendation)
def get_client_recommendations(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> ClientRecommendation:
    snapshot: ClientFinancialSnapshot = gather_client_financial_data(db, client)

    financial_summary = FinancialSummary(
        monthly_income=snapshot.monthly_income,
        monthly_expenses=snapshot.monthly_expenses,
        monthly_cash_flow=snapshot.monthly_cash_flow,
        savings_rate=snapshot.savings_rate,
        net_worth=snapshot.net_worth,
    )

    reasons = list(snapshot.insurance_type_recommendation.reasons)
    if snapshot.latest_fna is None:
        reasons.append(
            "No financial needs analysis on file -- estimated coverage need "
            "is $0 until the client's insurance priorities are recorded."
        )

    insurance = InsuranceRecommendation(
        recommended_type=snapshot.insurance_type_recommendation.recommendation,
        reasons=reasons,
        estimated_coverage_need=snapshot.target_coverage,
        existing_coverage=snapshot.existing_coverage,
        coverage_gap=snapshot.coverage_gap,
    )

    registered_accounts = [
        OwnerRegisteredAccountRecommendations(
            owner="client",
            recommendations=_to_recommendation_schemas(
                snapshot.client_account_recommendations
            ),
        )
    ]
    if snapshot.spouse is not None:
        registered_accounts.append(
            OwnerRegisteredAccountRecommendations(
                owner="spouse",
                recommendations=_to_recommendation_schemas(
                    snapshot.spouse_account_recommendations
                ),
            )
        )

    return ClientRecommendation(
        financial_summary=financial_summary,
        insurance=insurance,
        registered_accounts=registered_accounts,
    )
