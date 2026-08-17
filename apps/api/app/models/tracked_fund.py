import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.advisor import Advisor
    from app.models.client import Client


class FundType(enum.StrEnum):
    INDEX = "index"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    STOCK = "stock"
    OTHER = "other"


class TrackedFund(Base):
    """An advisor's shared, reusable catalog entry for a ticker (e.g.
    "SPY", "S&P 500 Index") -- not per-client. Advisor-scoped the same
    way Task is: no client_id, ownership checked directly against
    advisor_id."""

    __tablename__ = "tracked_funds"
    __table_args__ = (UniqueConstraint("advisor_id", "symbol"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    advisor_id: Mapped[int] = mapped_column(
        ForeignKey("advisors.id"),
        nullable=False,
        index=True,
    )

    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    display_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    fund_type: Mapped[FundType] = mapped_column(
        SAEnum(FundType, name="fund_type"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    advisor: Mapped["Advisor"] = relationship("Advisor")


class ClientTrackedFund(Base):
    """Selects which of the advisor's catalog entries appear on a
    given client's fund-comparison chart."""

    __tablename__ = "client_tracked_funds"
    __table_args__ = (UniqueConstraint("client_id", "tracked_fund_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    tracked_fund_id: Mapped[int] = mapped_column(
        ForeignKey("tracked_funds.id"),
        nullable=False,
        index=True,
    )

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="client_tracked_funds",
    )

    tracked_fund: Mapped["TrackedFund"] = relationship("TrackedFund")
