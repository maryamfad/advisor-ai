from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_advisor_id,
    get_db,
    get_owned_client,
    get_owned_client_tracked_fund,
    get_owned_tracked_fund,
)
from app.models.client import Client
from app.models.fund_price_history import FundPriceHistory
from app.models.tracked_fund import ClientTrackedFund, TrackedFund
from app.schemas.tracked_fund import (
    ClientTrackedFundCreate,
    ClientTrackedFundRead,
    FundPerformanceResponse,
    TrackedFundCreate,
    TrackedFundRead,
)
from app.services.fund_comparison import align_series
from app.services.market_data_client import (
    MarketDataUnavailableError,
    PricePoint,
    fetch_daily_prices,
)

# Advisor's shared, reusable catalog -- not nested under a client.
router = APIRouter(prefix="/tracked-funds", tags=["tracked-funds"])

# Per-client selection + performance comparison.
client_router = APIRouter(
    prefix="/clients/{client_id}/tracked-funds", tags=["tracked-funds"]
)

DEFAULT_PERFORMANCE_WINDOW_DAYS = 90


# -- Advisor catalog --------------------------------------------------------


@router.post("", response_model=TrackedFundRead, status_code=status.HTTP_201_CREATED)
def create_tracked_fund(
    payload: TrackedFundCreate,
    db: Session = Depends(get_db),
    advisor_id: int = Depends(get_current_advisor_id),
) -> TrackedFund:
    tracked_fund = TrackedFund(
        advisor_id=advisor_id,
        symbol=payload.symbol,
        display_name=payload.display_name,
        fund_type=payload.fund_type,
    )

    db.add(tracked_fund)
    db.commit()
    db.refresh(tracked_fund)

    return tracked_fund


@router.get("", response_model=list[TrackedFundRead])
def list_tracked_funds(
    db: Session = Depends(get_db),
    advisor_id: int = Depends(get_current_advisor_id),
) -> list[TrackedFund]:
    stmt = select(TrackedFund).where(TrackedFund.advisor_id == advisor_id)

    return list(db.scalars(stmt).all())


@router.delete("/{tracked_fund_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tracked_fund(
    db: Session = Depends(get_db),
    tracked_fund: TrackedFund = Depends(get_owned_tracked_fund),
) -> None:
    # Bulk deletes (no ORM cascade configured for a shared catalog
    # entry) so removing it doesn't leave orphaned client selections
    # or cached prices behind.
    db.query(ClientTrackedFund).filter(
        ClientTrackedFund.tracked_fund_id == tracked_fund.id
    ).delete(synchronize_session=False)
    db.query(FundPriceHistory).filter(
        FundPriceHistory.tracked_fund_id == tracked_fund.id
    ).delete(synchronize_session=False)

    db.delete(tracked_fund)
    db.commit()


# -- Per-client selection ----------------------------------------------------


@client_router.post(
    "", response_model=ClientTrackedFundRead, status_code=status.HTTP_201_CREATED
)
def select_tracked_fund_for_client(
    payload: ClientTrackedFundCreate,
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
    advisor_id: int = Depends(get_current_advisor_id),
) -> ClientTrackedFund:
    tracked_fund = db.get(TrackedFund, payload.tracked_fund_id)
    if tracked_fund is None or tracked_fund.advisor_id != advisor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tracked fund does not exist in this advisor's catalog.",
        )

    selection = ClientTrackedFund(
        client_id=client.id, tracked_fund_id=tracked_fund.id
    )

    db.add(selection)
    db.commit()
    db.refresh(selection)

    return selection


@client_router.get("", response_model=list[ClientTrackedFundRead])
def list_client_tracked_funds(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> list[ClientTrackedFund]:
    stmt = select(ClientTrackedFund).where(ClientTrackedFund.client_id == client.id)

    return list(db.scalars(stmt).all())


@client_router.delete("/{tracked_fund_id}", status_code=status.HTTP_204_NO_CONTENT)
def unselect_tracked_fund_for_client(
    db: Session = Depends(get_db),
    selection: ClientTrackedFund = Depends(get_owned_client_tracked_fund),
) -> None:
    # Removes the selection only -- the catalog entry survives.
    db.delete(selection)
    db.commit()


# -- Performance comparison --------------------------------------------------


def _trading_weekdays(start_date: date, end_date: date) -> set[date]:
    """A simple Mon-Fri proxy for "trading days," without a holiday
    calendar -- used only to decide whether the cache already covers
    the requested range, not to validate provider data."""
    days = (end_date - start_date).days + 1
    return {
        start_date + timedelta(days=offset)
        for offset in range(days)
        if (start_date + timedelta(days=offset)).weekday() < 5
    }


def _get_cached_or_fetch(
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

    if _trading_weekdays(start_date, end_date) <= cached_dates:
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


@client_router.get("/performance", response_model=FundPerformanceResponse)
def get_client_fund_performance(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> FundPerformanceResponse:
    resolved_end = end_date or date.today()
    resolved_start = start_date or (
        resolved_end - timedelta(days=DEFAULT_PERFORMANCE_WINDOW_DAYS)
    )

    selections = list(
        db.scalars(
            select(ClientTrackedFund).where(ClientTrackedFund.client_id == client.id)
        ).all()
    )

    series_by_symbol: dict[str, list[PricePoint]] = {}
    warnings: list[str] = []

    for selection in selections:
        fund = selection.tracked_fund
        try:
            prices = _get_cached_or_fetch(db, fund, resolved_start, resolved_end)
        except MarketDataUnavailableError as exc:
            warnings.append(f"{fund.symbol}: {exc}")
            continue

        if not prices:
            warnings.append(f"{fund.symbol}: no price data available for this range.")
            continue

        series_by_symbol[fund.symbol] = prices

    aligned = align_series(series_by_symbol)

    return FundPerformanceResponse(
        symbols=list(series_by_symbol.keys()),
        dates=aligned.dates,
        series=aligned.series,
        warnings=warnings,
    )
