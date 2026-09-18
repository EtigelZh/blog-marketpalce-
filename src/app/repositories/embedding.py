from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.database.models.article import Article
from src.app.database.models.article_embedding import ArticleEmbedding


class EmbeddingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search(
        self,
        query_embedding: list[float],
        limit: int,
    ) -> list[Article]:
        query = (
            select(Article)
            .join(ArticleEmbedding, ArticleEmbedding.article_id == Article.id)
            .order_by(ArticleEmbedding.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )

        result = await self.session.execute(query)

        return list(result.scalars().all())
