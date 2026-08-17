from datetime import date
from decimal import Decimal

import pytest

from app.services.fund_comparison import align_series, normalize_to_percent_return
from app.services.market_data_client import PricePoint


def _points(*pairs: tuple[str, str]) -> list[PricePoint]:
    return [
        PricePoint(price_date=date.fromisoformat(d), close=Decimal(c))
        for d, c in pairs
    ]


class TestNormalizeToPercentReturn:
    def test_empty_list_returns_empty(self) -> None:
        assert normalize_to_percent_return([]) == []

    def test_first_point_is_zero_percent(self) -> None:
        result = normalize_to_percent_return(_points(("2026-01-01", "100")))
        assert result[0].percent_return == Decimal("0.00")

    def test_gain_is_positive(self) -> None:
        result = normalize_to_percent_return(
            _points(("2026-01-01", "100"), ("2026-01-02", "110"))
        )
        assert result[1].percent_return == Decimal("10.00")

    def test_loss_is_negative(self) -> None:
        result = normalize_to_percent_return(
            _points(("2026-01-01", "100"), ("2026-01-02", "90"))
        )
        assert result[1].percent_return == Decimal("-10.00")

    def test_baseline_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="first price is 0"):
            normalize_to_percent_return(_points(("2026-01-01", "0")))

    def test_preserves_dates(self) -> None:
        result = normalize_to_percent_return(
            _points(("2026-01-01", "100"), ("2026-01-02", "105"))
        )
        assert [p.price_date for p in result] == [
            date(2026, 1, 1),
            date(2026, 1, 2),
        ]


class TestAlignSeries:
    def test_empty_dict_returns_empty(self) -> None:
        result = align_series({})
        assert result.dates == []
        assert result.series == {}

    def test_single_fund_case(self) -> None:
        result = align_series(
            {"SPY": _points(("2026-01-01", "100"), ("2026-01-02", "110"))}
        )
        assert result.dates == [date(2026, 1, 1), date(2026, 1, 2)]
        assert result.series["SPY"] == [Decimal("0.00"), Decimal("10.00")]

    def test_common_dates_only_when_ranges_mismatch(self) -> None:
        result = align_series(
            {
                "SPY": _points(
                    ("2026-01-01", "100"),
                    ("2026-01-02", "110"),
                    ("2026-01-03", "120"),
                ),
                "VFV": _points(
                    ("2026-01-02", "50"),
                    ("2026-01-03", "55"),
                ),
            }
        )
        # 2026-01-01 dropped -- VFV has no data that day
        assert result.dates == [date(2026, 1, 2), date(2026, 1, 3)]
        assert len(result.series["SPY"]) == 2
        assert len(result.series["VFV"]) == 2

    def test_gap_in_the_middle_excluded(self) -> None:
        result = align_series(
            {
                "SPY": _points(
                    ("2026-01-01", "100"),
                    ("2026-01-02", "110"),
                    ("2026-01-03", "120"),
                ),
                "VFV": _points(
                    ("2026-01-01", "50"),
                    ("2026-01-03", "55"),
                ),
            }
        )
        assert result.dates == [date(2026, 1, 1), date(2026, 1, 3)]

    def test_each_symbol_normalized_against_its_own_baseline(self) -> None:
        result = align_series(
            {
                "SPY": _points(("2026-01-01", "100"), ("2026-01-02", "150")),
                "VFV": _points(("2026-01-01", "50"), ("2026-01-02", "55")),
            }
        )
        assert result.series["SPY"] == [Decimal("0.00"), Decimal("50.00")]
        assert result.series["VFV"] == [Decimal("0.00"), Decimal("10.00")]
