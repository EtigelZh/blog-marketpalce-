from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.app.database.base import Base


class DeletedArticle(Base):
    __tablename__ = "deleted_articles"

    id: Mapped[int] = mapped_column(primary_key=True)

    article_id: Mapped[int] = mapped_column(nullable=False)

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    image: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False,
    )

    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(nullable=False)

    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    deleted_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
    )
