import asyncio

import dramatiq
from loguru import logger
from sqlalchemy.dialects.postgresql import insert

from src.app.config.settings import settings
from src.app.database.models.article_embedding import ArticleEmbedding
from src.app.database.session import async_session_factory
from src.app.messaging.broker import broker  # noqa: F401
from src.app.services.embedding import embed_text


async def _update_embedding(article_id: int, title: str, text: str) -> None:
    embedding = await asyncio.to_thread(embed_text, f"{title}\n{text}")

    async with async_session_factory() as session:
        statement = insert(ArticleEmbedding).values(
            article_id=article_id,
            embedding=embedding,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[ArticleEmbedding.article_id],
            set_={"embedding": statement.excluded.embedding},
        )

        await session.execute(statement)
        await session.commit()


@dramatiq.actor(queue_name=settings.rabbitmq_embedding_queue, max_retries=3)
def process_embedding_task(article_id: int, title: str, text: str) -> None:
    try:
        asyncio.run(_update_embedding(article_id, title, text))
    except Exception:
        logger.bind(article_id=article_id).exception("Failed to process embedding message")
        raise

    logger.bind(article_id=article_id).info("Article embedding updated")
