"""Pure math for comparing multiple funds/tickers on one chart:
rebasing each to a "% return since inception of the queried range"
series, then aligning them onto a shared date axis.

Genuinely DB/network-free, unlike market_data_client.py in this same
package -- takes already-fetched PricePoint lists, never calls out to
the provider itself.
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.services.market_data_client import PricePoint

TWO_PLACES = Decimal("0.01")


def _round(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class PercentReturnPoint:
    price_date: date
    percent_return: Decimal


def normalize_to_percent_return(prices: list[PricePoint]) -> list[PercentReturnPoint]:
    """Rebases a price series to "% return since the first point," so
    funds with very different absolute prices are visually comparable
    on one chart. Empty input returns an empty list."""
    if not prices:
        return []

    baseline = prices[0].close
    if baseline == 0:
        raise ValueError("Cannot normalize a series whose first price is 0.")

    return [
        PercentReturnPoint(
            price_date=point.price_date,
            percent_return=_round((point.close - baseline) / baseline * 100),
        )
        for point in prices
    ]


@dataclass(frozen=True)
class AlignedComparison:
    dates: list[date]
    series: dict[str, list[Decimal]]


def align_series(
    series_by_symbol: dict[str, list[PricePoint]],
) -> AlignedComparison:
    """Inner-joins multiple funds' series onto their common trading
    dates (markets have holidays; different funds/providers can have
    gaps), producing one shared date axis plus one normalized
    percent-return series per symbol, in that axis's order.

    Each symbol is normalized against its own first available price
    (not the first common date), so "% return" reflects that fund's
    actual performance over the full range it has data for.
    """
    if not series_by_symbol:
        return AlignedComparison(dates=[], series={})

    date_sets = [{p.price_date for p in prices} for prices in series_by_symbol.values()]
    common_dates = sorted(set.intersection(*date_sets)) if date_sets else []

    series: dict[str, list[Decimal]] = {}
    for symbol, prices in series_by_symbol.items():
        normalized_by_date = {
            point.price_date: point.percent_return
            for point in normalize_to_percent_return(prices)
        }
        series[symbol] = [normalized_by_date[d] for d in common_dates]

    return AlignedComparison(dates=common_dates, series=series)
