from datetime import timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

import app.api.routes.tracked_funds as tracked_funds_module
from app.models.advisor import Advisor
from app.services.market_data_client import MarketDataUnavailableError, PricePoint


def _headers(advisor_id: int) -> dict[str, str]:
    return {"X-Advisor-Id": str(advisor_id)}


def _create_client(api_client: TestClient, advisor_id: int, email: str) -> dict:
    return api_client.post(
        "/clients",
        json={"first_name": "Sarah", "last_name": "Chen", "email": email},
        headers=_headers(advisor_id),
    ).json()


def _create_tracked_fund(
    api_client: TestClient, advisor_id: int, symbol: str = "SPY"
) -> dict:
    return api_client.post(
        "/tracked-funds",
        json={"symbol": symbol, "display_name": f"{symbol} ETF", "fund_type": "etf"},
        headers=_headers(advisor_id),
    ).json()


def _fake_fetch(symbol: str, start_date, end_date) -> list[PricePoint]:
    if symbol == "BADTICKER":
        raise MarketDataUnavailableError("simulated provider error")

    days = (end_date - start_date).days + 1
    return [
        PricePoint(price_date=start_date + timedelta(days=i), close=Decimal("100") + i)
        for i in range(days)
        if (start_date + timedelta(days=i)).weekday() < 5
    ]


# -- Advisor catalog ----------------------------------------------------------


def test_create_and_list_catalog(api_client: TestClient, advisor: Advisor) -> None:
    created = _create_tracked_fund(api_client, advisor.id)
    assert created["symbol"] == "SPY"

    response = api_client.get("/tracked-funds", headers=_headers(advisor.id))

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_delete_catalog_entry_cascades_to_client_selection(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "fund1@example.com")
    fund = _create_tracked_fund(api_client, advisor.id)
    api_client.post(
        f"/clients/{client['id']}/tracked-funds",
        json={"tracked_fund_id": fund["id"]},
        headers=_headers(advisor.id),
    )

    delete_response = api_client.delete(
        f"/tracked-funds/{fund['id']}", headers=_headers(advisor.id)
    )
    assert delete_response.status_code == 204

    list_response = api_client.get(
        f"/clients/{client['id']}/tracked-funds", headers=_headers(advisor.id)
    )
    assert list_response.json() == []


def test_advisor_cannot_delete_another_advisors_catalog_entry(
    api_client: TestClient, advisor: Advisor
) -> None:
    fund = _create_tracked_fund(api_client, advisor.id)
    other_advisor_id = advisor.id + 999999

    response = api_client.delete(
        f"/tracked-funds/{fund['id']}", headers=_headers(other_advisor_id)
    )

    assert response.status_code == 404


# -- Per-client selection -------------------------------------------------------


def test_select_and_list_for_client(api_client: TestClient, advisor: Advisor) -> None:
    client = _create_client(api_client, advisor.id, "fund2@example.com")
    fund = _create_tracked_fund(api_client, advisor.id)

    response = api_client.post(
        f"/clients/{client['id']}/tracked-funds",
        json={"tracked_fund_id": fund["id"]},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 201
    assert response.json()["tracked_fund"]["symbol"] == "SPY"

    list_response = api_client.get(
        f"/clients/{client['id']}/tracked-funds", headers=_headers(advisor.id)
    )
    assert len(list_response.json()) == 1


def test_select_unknown_fund_returns_400(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "fund3@example.com")

    response = api_client.post(
        f"/clients/{client['id']}/tracked-funds",
        json={"tracked_fund_id": 999999999},
        headers=_headers(advisor.id),
    )

    assert response.status_code == 400


def test_unselect_removes_selection_not_catalog_entry(
    api_client: TestClient, advisor: Advisor
) -> None:
    client = _create_client(api_client, advisor.id, "fund5@example.com")
    fund = _create_tracked_fund(api_client, advisor.id)
    api_client.post(
        f"/clients/{client['id']}/tracked-funds",
        json={"tracked_fund_id": fund["id"]},
        headers=_headers(advisor.id),
    )

    delete_response = api_client.delete(
        f"/clients/{client['id']}/tracked-funds/{fund['id']}",
        headers=_headers(advisor.id),
    )
    assert delete_response.status_code == 204

    catalog_response = api_client.get("/tracked-funds", headers=_headers(advisor.id))
    assert len(catalog_response.json()) == 1  # catalog entry survives


# -- Performance comparison ------------------------------------------------------


def test_performance_cache_miss_fetches_and_caches(
    api_client: TestClient, advisor: Advisor, monkeypatch
) -> None:
    client = _create_client(api_client, advisor.id, "fund6@example.com")
    fund = _create_tracked_fund(api_client, advisor.id, symbol="SPY")
    api_client.post(
        f"/clients/{client['id']}/tracked-funds",
        json={"tracked_fund_id": fund["id"]},
        headers=_headers(advisor.id),
    )

    call_count = {"n": 0}

    def counting_fetch(symbol, start_date, end_date):
        call_count["n"] += 1
        return _fake_fetch(symbol, start_date, end_date)

    monkeypatch.setattr(tracked_funds_module, "fetch_daily_prices", counting_fetch)

    response = api_client.get(
        f"/clients/{client['id']}/tracked-funds/performance"
        "?start_date=2026-01-05&end_date=2026-01-09",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["symbols"] == ["SPY"]
    assert len(body["dates"]) == 5  # Mon-Fri, no weekend in range
    assert call_count["n"] == 1


def test_performance_cache_hit_skips_second_fetch(
    api_client: TestClient, advisor: Advisor, monkeypatch
) -> None:
    client = _create_client(api_client, advisor.id, "fund7@example.com")
    fund = _create_tracked_fund(api_client, advisor.id, symbol="SPY")
    api_client.post(
        f"/clients/{client['id']}/tracked-funds",
        json={"tracked_fund_id": fund["id"]},
        headers=_headers(advisor.id),
    )

    call_count = {"n": 0}

    def counting_fetch(symbol, start_date, end_date):
        call_count["n"] += 1
        return _fake_fetch(symbol, start_date, end_date)

    monkeypatch.setattr(tracked_funds_module, "fetch_daily_prices", counting_fetch)

    url = (
        f"/clients/{client['id']}/tracked-funds/performance"
        "?start_date=2026-01-05&end_date=2026-01-09"
    )
    first = api_client.get(url, headers=_headers(advisor.id))
    second = api_client.get(url, headers=_headers(advisor.id))

    assert first.status_code == second.status_code == 200
    assert call_count["n"] == 1


def test_performance_failing_fund_appears_in_warnings(
    api_client: TestClient, advisor: Advisor, monkeypatch
) -> None:
    client = _create_client(api_client, advisor.id, "fund8@example.com")
    good_fund = _create_tracked_fund(api_client, advisor.id, symbol="SPY")
    bad_fund = _create_tracked_fund(api_client, advisor.id, symbol="BADTICKER")
    for fund in (good_fund, bad_fund):
        api_client.post(
            f"/clients/{client['id']}/tracked-funds",
            json={"tracked_fund_id": fund["id"]},
            headers=_headers(advisor.id),
        )

    monkeypatch.setattr(tracked_funds_module, "fetch_daily_prices", _fake_fetch)

    response = api_client.get(
        f"/clients/{client['id']}/tracked-funds/performance"
        "?start_date=2026-01-05&end_date=2026-01-09",
        headers=_headers(advisor.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["symbols"] == ["SPY"]
    assert any("BADTICKER" in warning for warning in body["warnings"])
