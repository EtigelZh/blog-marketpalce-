from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.models.article import Article
from src.app.database.models.article_embedding import ArticleEmbedding
from src.app.database.models.category import Category
from src.app.database.models.user import User
from src.app.repositories.embedding import EmbeddingRepository


async def test_search_finds_article_with_closest_embedding(
    db_session: AsyncSession,
) -> None:
    user = User(email="embedding-test@example.com", password_hash="hash")
    category = Category(name="Тест эмбеддингов")
    db_session.add_all([user, category])
    await db_session.flush()

    close_article = Article(
        title="Близкая статья",
        text="Текст близкой статьи",
        image="http://example.com/a.png",
        category_id=category.id,
        author_id=user.id,
    )
    far_article = Article(
        title="Далёкая статья",
        text="Текст далёкой статьи",
        image="http://example.com/b.png",
        category_id=category.id,
        author_id=user.id,
    )
    db_session.add_all([close_article, far_article])
    await db_session.flush()

    query_vector = [1.0, 0.0] + [0.0] * 382

    db_session.add_all(
        [
            ArticleEmbedding(article_id=close_article.id, embedding=query_vector),
            ArticleEmbedding(article_id=far_article.id, embedding=[0.0, 1.0] + [0.0] * 382),
        ]
    )
    await db_session.flush()

    repository = EmbeddingRepository(db_session)
    results = await repository.search(query_embedding=query_vector, limit=1)

    assert [article.id for article in results] == [close_article.id]
