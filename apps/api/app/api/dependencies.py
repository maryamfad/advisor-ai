from collections.abc import Generator

from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_advisor_id(
    x_advisor_id: int | None = Header(default=None),
) -> int:
    """Resolve the acting advisor's id.

    TEMPORARY: real authentication (JWT-based, Phase 16 of the roadmap)
    hasn't been built yet. Until then we trust an X-Advisor-Id header so
    the rest of the API can be scoped by advisor ownership from day one,
    matching the rule that authorization is decided by the API layer,
    never inferred by a client or by the AI. Every /clients route below
    filters by this id -- replace only this function when real auth lands;
    the routes and their ownership checks don't need to change.
    """
    if x_advisor_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Advisor-Id header (temporary stand-in for auth).",
        )

    return x_advisor_id
