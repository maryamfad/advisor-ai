from collections.abc import Generator
from datetime import timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.services.fund_price_cache as fund_price_cache_module
from app.db import SessionLocal
from app.models.advisor import Advisor
from app.models.client import Client as ClientModel
from app.services import ai_tools
from app.services.market_data_client import MarketDataUnavailableError, PricePoint


def _headers(advisor_id: int) -> dict[str, str]:
    return {"X-Advisor-Id": str(advisor_id)}


def _create_client(api_client: TestClient, advisor_id: int, email: str) -> dict:
    return api_client.post(
        "/clients",
        json={"first_name": "Sarah", "last_name": "Chen", "email": email},
        headers=_headers(advisor_id),
    ).json()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _fetch_client(db_session: Session, client_id: int) -> ClientModel:
    client = db_session.get(ClientModel, client_id)
    assert client is not None
    return client


class TestToolsRegistry:
    def test_every_tool_has_a_name_matching_the_registry_key(self) -> None:
        for name, tool in ai_tools.TOOLS_BY_NAME.items():
            assert tool.name == name

    def test_every_tool_has_a_non_empty_description(self) -> None:
        for tool in ai_tools.AI_TOOLS:
            assert tool.description.strip()

    def test_every_tool_input_schema_is_a_valid_object_schema(self) -> None:
        for tool in ai_tools.AI_TOOLS:
            assert tool.input_schema["type"] == "object"
            assert "properties" in tool.input_schema
            assert "required" in tool.input_schema

    def test_compare_funds_schema_requires_symbols_and_dates(self) -> None:
        schema = ai_tools.TOOLS_BY_NAME["compare_funds"].input_schema
        assert set(schema["required"]) == {"symbols", "start_date", "end_date"}


class TestGetFinancialSummary:
    def test_reflects_declared_income_and_transactions(
        self, api_client: TestClient, advisor: Advisor, db_session
    ) -> None:
        client = _create_client(api_client, advisor.id, "tool1@example.com")
        api_client.post(
            f"/clients/{client['id']}/income-sources",
            json={
                "source": "Salary",
                "gross_amount": "5000.00",
                "frequency": "monthly",
            },
            headers=_headers(advisor.id),
        )

        client_orm = _fetch_client(db_session, client["id"])
        result = ai_tools.get_financial_summary(db_session, client_orm)

        assert result["monthly_income"] == "5000.00"
        assert "net_worth" in result


class TestGetInsuranceRecommendation:
    def test_reflects_fna_dime_checklist(
        self, api_client: TestClient, advisor: Advisor, db_session
    ) -> None:
        client = _create_client(api_client, advisor.id, "tool2@example.com")
        api_client.post(
            f"/clients/{client['id']}/financial-needs-analyses",
            json={
                "conducted_at": "2026-01-01",
                "wants_final_expenses": True,
                "final_expenses_amount": "12000.00",
            },
            headers=_headers(advisor.id),
        )

        client_orm = _fetch_client(db_session, client["id"])
        result = ai_tools.get_insurance_recommendation(db_session, client_orm)

        assert result["estimated_coverage_need"] == "12000.00"
        assert result["recommended_type"] in {
            "term",
            "permanent",
            "term_with_permanent_review",
        }


class TestGetRegisteredAccountRecommendations:
    def test_returns_client_and_spouse_keys(
        self, api_client: TestClient, advisor: Advisor, db_session
    ) -> None:
        client = _create_client(api_client, advisor.id, "tool3@example.com")

        client_orm = _fetch_client(db_session, client["id"])
        result = ai_tools.get_registered_account_recommendations(db_session, client_orm)

        assert "client" in result
        assert "spouse" in result
        assert result["spouse"] == []  # no spouse on file


class TestGetRiskTolerance:
    def test_no_data_returns_none_source(
        self, api_client: TestClient, advisor: Advisor, db_session
    ) -> None:
        client = _create_client(api_client, advisor.id, "tool4@example.com")

        client_orm = _fetch_client(db_session, client["id"])
        result = ai_tools.get_risk_tolerance(db_session, client_orm)

        assert result == {"risk_tolerance": None, "source": None}

    def test_fna_only_returns_fna_source(
        self, api_client: TestClient, advisor: Advisor, db_session
    ) -> None:
        client = _create_client(api_client, advisor.id, "tool5@example.com")
        api_client.post(
            f"/clients/{client['id']}/financial-needs-analyses",
            json={"conducted_at": "2026-01-01", "risk_tolerance": "medium"},
            headers=_headers(advisor.id),
        )

        client_orm = _fetch_client(db_session, client["id"])
        result = ai_tools.get_risk_tolerance(db_session, client_orm)

        assert result == {
            "risk_tolerance": "medium",
            "source": "financial_needs_analysis",
        }


class TestGenerateFinancialPlanPreview:
    def test_does_not_persist_a_plan(
        self, api_client: TestClient, advisor: Advisor, db_session
    ) -> None:
        client = _create_client(api_client, advisor.id, "tool6@example.com")
        api_client.post(
            f"/clients/{client['id']}/financial-needs-analyses",
            json={
                "conducted_at": "2026-01-01",
                "wants_final_expenses": True,
                "final_expenses_amount": "10000.00",
            },
            headers=_headers(advisor.id),
        )

        client_orm = _fetch_client(db_session, client["id"])
        result = ai_tools.generate_financial_plan_preview(db_session, client_orm)

        assert result["action_items"]
        assert "narrative_summary" in result

        plans_response = api_client.get(
            f"/clients/{client['id']}/financial-plans", headers=_headers(advisor.id)
        )
        assert plans_response.json() == []  # preview only -- nothing persisted


class TestCompareFunds:
    def _fake_fetch(self, symbol, start_date, end_date) -> list[PricePoint]:
        if symbol == "BADTICKER":
            raise MarketDataUnavailableError("simulated provider error")
        days = (end_date - start_date).days + 1
        return [
            PricePoint(
                price_date=start_date + timedelta(days=i), close=Decimal("100") + i
            )
            for i in range(days)
            if (start_date + timedelta(days=i)).weekday() < 5
        ]

    def test_unselected_symbol_appears_in_warnings(
        self, api_client: TestClient, advisor: Advisor, db_session
    ) -> None:
        client = _create_client(api_client, advisor.id, "tool7@example.com")

        client_orm = _fetch_client(db_session, client["id"])
        result = ai_tools.compare_funds(
            db_session,
            client_orm,
            symbols=["SPY"],
            start_date="2026-01-05",
            end_date="2026-01-09",
        )

        assert result["symbols"] == []
        assert any("not selected" in w for w in result["warnings"])

    def test_selected_symbol_returns_series(
        self, api_client: TestClient, advisor: Advisor, db_session, monkeypatch
    ) -> None:
        client = _create_client(api_client, advisor.id, "tool8@example.com")
        fund = api_client.post(
            "/tracked-funds",
            json={"symbol": "SPY", "display_name": "S&P 500", "fund_type": "etf"},
            headers=_headers(advisor.id),
        ).json()
        api_client.post(
            f"/clients/{client['id']}/tracked-funds",
            json={"tracked_fund_id": fund["id"]},
            headers=_headers(advisor.id),
        )

        monkeypatch.setattr(
            fund_price_cache_module, "fetch_daily_prices", self._fake_fetch
        )

        client_orm = _fetch_client(db_session, client["id"])
        result = ai_tools.compare_funds(
            db_session,
            client_orm,
            symbols=["SPY"],
            start_date="2026-01-05",
            end_date="2026-01-09",
        )

        assert result["symbols"] == ["SPY"]
        assert len(result["dates"]) == 5
        assert result["warnings"] == []
