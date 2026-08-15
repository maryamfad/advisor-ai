import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.client import Client


class HouseholdMemberRole(enum.StrEnum):
    """Whose income/account/policy a row belongs to. Shared by Account
    and IncomeSource so a couple's data lives in the same tables
    instead of duplicating them per person."""

    CLIENT = "client"
    SPOUSE = "spouse"


class Spouse(Base):
    __tablename__ = "spouses"

    id: Mapped[int] = mapped_column(primary_key=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    employer: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    retirement_age: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    life_expectancy_age: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="spouse",
    )
