"""make documents firm wide

Revision ID: 271413fc3a46
Revises: d7aaf9bc765f
Create Date: 2026-10-17 13:05:28.227647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '271413fc3a46'
down_revision: Union[str, Sequence[str], None] = 'd7aaf9bc765f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('documents', sa.Column('advisor_id', sa.Integer(), nullable=True))

    # Backfill from the still-NOT-NULL client_id before tightening
    # advisor_id to NOT NULL below -- every existing row has a client,
    # so every row has an unambiguous advisor to backfill from.
    op.execute(
        "UPDATE documents SET advisor_id = clients.advisor_id "
        "FROM clients WHERE documents.client_id = clients.id"
    )

    op.alter_column('documents', 'advisor_id', nullable=False)
    op.create_index(
        op.f('ix_documents_advisor_id'), 'documents', ['advisor_id'], unique=False
    )
    op.create_foreign_key(
        'documents_advisor_id_fkey', 'documents', 'advisors', ['advisor_id'], ['id']
    )

    # A document may now belong to no client at all (firm-wide /
    # regulatory documents) -- see Task.client_id for the identical
    # existing pattern.
    op.alter_column('documents', 'client_id', nullable=True)

    # The native Postgres enum stores the Python enum MEMBER NAMES
    # (e.g. 'STATEMENT'), not their lowercase .value strings -- that's
    # what SQLAlchemy's Enum type sends by default for a plain
    # Enum/StrEnum, confirmed against the existing rows before writing
    # this migration. Match that casing, not DocumentCategory's
    # lowercase values, or every insert using these will fail with
    # "invalid input value for enum".
    #
    # Postgres 12+ allows ADD VALUE inside a transaction as long as
    # the new value isn't used by DML in the same transaction, which
    # is the case here.
    op.execute("ALTER TYPE document_category ADD VALUE 'REGULATORY'")
    op.execute("ALTER TYPE document_category ADD VALUE 'INVESTMENT'")


def downgrade() -> None:
    """Downgrade schema.

    The two new enum values are NOT removed -- Postgres has no
    `ALTER TYPE ... DROP VALUE`. Removing them for real would mean
    rebuilding the document_category type from scratch (create a new
    type without them, rewrite every row's column, drop the old type,
    rename), which itself fails if any row already uses 'regulatory'
    or 'investment'. Left as a documented no-op, same as
    d7aaf9bc765f's downgrade.
    """
    op.drop_constraint('documents_advisor_id_fkey', 'documents', type_='foreignkey')
    op.drop_index(op.f('ix_documents_advisor_id'), table_name='documents')
    op.drop_column('documents', 'advisor_id')

    # Fails loudly (by design) if any firm-wide document (client_id
    # IS NULL) exists -- there's no non-destructive way to decide what
    # client a firm-wide document should be reassigned to.
    op.alter_column('documents', 'client_id', nullable=False)
