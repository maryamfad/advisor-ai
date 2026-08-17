from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.tracked_fund import TrackedFund


class FundPriceHistory(Base):
    """A local cache of fetched daily closes, so repeated chart
    requests (e.g. several clients viewing the same index) don't
    re-hit the external provider and burn its rate limit. Only the
    days actually missing from this table for the requested range get
    fetched from market_data_client."""

    __tablename__ = "fund_price_history"
    __table_args__ = (UniqueConstraint("tracked_fund_id", "price_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    tracked_fund_id: Mapped[int] = mapped_column(
        ForeignKey("tracked_funds.id"),
        nullable=False,
        index=True,
    )

    price_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    close_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 4),
        nullable=False,
    )

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    tracked_fund: Mapped["TrackedFund"] = relationship("TrackedFund")
