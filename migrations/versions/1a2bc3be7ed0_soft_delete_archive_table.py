"""soft delete archive table

Revision ID: 1a2bc3be7ed0
Revises: d0dfebc87e15
Create Date: 2026-09-17 12:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a2bc3be7ed0'
down_revision: Union[str, Sequence[str], None] = 'd0dfebc87e15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'deleted_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('image', sa.String(length=500), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    op.execute(
        "INSERT INTO deleted_articles "
        "(article_id, title, text, image, category_id, author_id, "
        "created_at, updated_at, deleted_at) "
        "SELECT id, title, text, image, category_id, author_id, "
        "created_at, updated_at, now() "
        "FROM articles WHERE is_deleted = true"
    )

    op.execute("DELETE FROM articles WHERE is_deleted = true")

    op.drop_column('articles', 'is_deleted')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'articles',
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column('articles', 'is_deleted', server_default=None)
    op.drop_table('deleted_articles')
