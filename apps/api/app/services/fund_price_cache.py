"""Bridges market_data_client.py (raw HTTP, no DB) and
fund_comparison.py (pure math, no DB/HTTP): checks FundPriceHistory
for what's already cached before deciding whether to hit the
external, rate-limited provider at all.

Shared by the tracked-funds performance endpoint and the AI
assistant's compare_funds tool, so both go through the exact same
caching logic rather than duplicating it.
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fund_price_history import FundPriceHistory
from app.models.tracked_fund import TrackedFund
from app.services.market_data_client import PricePoint, fetch_daily_prices


def trading_weekdays(start_date: date, end_date: date) -> set[date]:
    """A simple Mon-Fri proxy for "trading days," without a holiday
    calendar -- used only to decide whether the cache already covers
    the requested range, not to validate provider data."""
    days = (end_date - start_date).days + 1
    return {
        start_date + timedelta(days=offset)
        for offset in range(days)
        if (start_date + timedelta(days=offset)).weekday() < 5
    }


def get_cached_or_fetch_prices(
    db: Session, fund: TrackedFund, start_date: date, end_date: date
) -> list[PricePoint]:
    cached = list(
        db.scalars(
            select(FundPriceHistory).where(
                FundPriceHistory.tracked_fund_id == fund.id,
                FundPriceHistory.price_date >= start_date,
                FundPriceHistory.price_date <= end_date,
            )
        ).all()
    )
    cached_dates = {row.price_date for row in cached}

    if trading_weekdays(start_date, end_date) <= cached_dates:
        # Every expected trading day in range is already cached --
        # skip the provider call entirely.
        rows = sorted(cached, key=lambda row: row.price_date)
        return [
            PricePoint(price_date=row.price_date, close=row.close_price)
            for row in rows
        ]

    fetched = fetch_daily_prices(fund.symbol, start_date, end_date)
    for point in fetched:
        if point.price_date in cached_dates:
            continue
        db.add(
            FundPriceHistory(
                tracked_fund_id=fund.id,
                price_date=point.price_date,
                close_price=point.close,
            )
        )
        cached_dates.add(point.price_date)
    db.commit()

    return sorted(fetched, key=lambda point: point.price_date)
