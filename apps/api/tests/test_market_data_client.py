from datetime import date

import pytest

from app.services import market_data_client
from app.services.market_data_client import (
    MarketDataUnavailableError,
    fetch_daily_prices,
)


def test_fetch_daily_prices_raises_without_api_key(monkeypatch) -> None:
    monkeypatch.setattr(market_data_client.settings, "market_data_api_key", None)

    with pytest.raises(MarketDataUnavailableError, match="No market_data_api_key"):
        fetch_daily_prices("SPY", date(2026, 1, 1), date(2026, 1, 31))
