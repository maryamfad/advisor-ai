from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.tracked_fund import FundType


class TrackedFundBase(BaseModel):
    symbol: str
    display_name: str
    fund_type: FundType


class TrackedFundCreate(TrackedFundBase):
    """Payload for POST /tracked-funds. advisor_id comes from the
    authenticated advisor, never from the request body."""


class TrackedFundRead(TrackedFundBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    advisor_id: int
    created_at: datetime


class ClientTrackedFundCreate(BaseModel):
    """Payload for POST /clients/{client_id}/tracked-funds. Must
    reference a tracked_fund_id already in this advisor's catalog."""

    tracked_fund_id: int


class ClientTrackedFundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    tracked_fund_id: int
    added_at: datetime
    tracked_fund: TrackedFundRead


class FundPerformanceResponse(BaseModel):
    """Chart-ready data only -- no chart image/rendering happens in
    this backend. A fund that failed to fetch is named in `warnings`
    and simply absent from `symbols`/`series`, rather than failing the
    whole request."""

    symbols: list[str]
    dates: list[date]
    series: dict[str, list[Decimal]]
    warnings: list[str]
