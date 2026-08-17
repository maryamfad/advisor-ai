"""Fetches real daily closing prices from an external market-data
provider (Twelve Data).

The one deliberate exception to this codebase's "every service
function is pure" rule -- real market data is unavoidably I/O. Kept
small and clearly labeled as the exception, in its own module, so
network calls don't leak into the rest of app/services/, which stays
genuinely pure and DB-free.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import httpx

from app.core.config import settings

REQUEST_TIMEOUT_SECONDS = 10.0


class MarketDataUnavailableError(Exception):
    """Raised when the provider can't return usable price data for a
    symbol -- invalid symbol, rate limit hit, provider downtime, or no
    API key configured. The caller (the tracked-funds performance
    endpoint) is expected to turn this into a per-fund warning rather
    than failing the whole comparison request."""


@dataclass(frozen=True)
class PricePoint:
    price_date: date
    close: Decimal


def fetch_daily_prices(
    symbol: str, start_date: date, end_date: date
) -> list[PricePoint]:
    """Fetches daily closes for `symbol` between start_date and
    end_date (inclusive), oldest first. Raises
    MarketDataUnavailableError on any failure -- missing API key,
    network error, or a provider-reported error for this symbol --
    rather than letting a raw HTTP/parsing exception escape.
    """
    if not settings.market_data_api_key:
        raise MarketDataUnavailableError(
            "No market_data_api_key configured -- set one in .env to "
            "fetch live prices."
        )

    try:
        response = httpx.get(
            f"{settings.market_data_base_url}/time_series",
            params={
                "symbol": symbol,
                "interval": "1day",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "apikey": settings.market_data_api_key,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise MarketDataUnavailableError(
            f"Failed to fetch prices for '{symbol}': {exc}"
        ) from exc

    if payload.get("status") == "error" or "values" not in payload:
        message = payload.get("message", "unknown provider error")
        raise MarketDataUnavailableError(f"Provider error for '{symbol}': {message}")

    prices = [
        PricePoint(
            price_date=date.fromisoformat(row["datetime"]),
            close=Decimal(row["close"]),
        )
        for row in payload["values"]
    ]

    return sorted(prices, key=lambda p: p.price_date)
