"""enable pgvector extension

Revision ID: d7aaf9bc765f
Revises: 077229f1ee25
Create Date: 2026-10-16 22:52:09.158500

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7aaf9bc765f'
down_revision: Union[str, Sequence[str], None] = '077229f1ee25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Downgrade schema.

    Deliberately a no-op: langchain_postgres.PGVector's own tables
    (created lazily on first use, not by this migration) use the
    `vector` column type, so dropping the extension here would break
    them if any policy-document chunks have been ingested. Alembic
    can't know whether that's happened.
    """
