"""add pgvector article embeddings

Revision ID: 36e67844de9b
Revises: 1a2bc3be7ed0
Create Date: 2026-09-17 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '36e67844de9b'
down_revision: Union[str, Sequence[str], None] = '1a2bc3be7ed0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIMENSIONS = 384


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        'article_embeddings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('embedding', Vector(EMBEDDING_DIMENSIONS), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('article_id'),
    )

    op.execute(
        "CREATE INDEX ix_article_embeddings_hnsw ON article_embeddings "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('article_embeddings')
    op.execute("DROP EXTENSION IF EXISTS vector")
