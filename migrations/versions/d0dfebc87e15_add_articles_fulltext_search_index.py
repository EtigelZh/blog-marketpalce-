"""add articles fulltext search index

Revision ID: d0dfebc87e15
Revises: f0ea64808b65
Create Date: 2026-09-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd0dfebc87e15'
down_revision: Union[str, Sequence[str], None] = 'f0ea64808b65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "CREATE INDEX ix_articles_fts ON articles "
        "USING gin (to_tsvector('russian', title || ' ' || text))"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX ix_articles_fts")
