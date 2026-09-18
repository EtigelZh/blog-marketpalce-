import asyncio
import json

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from loguru import logger
from sqlalchemy.dialects.postgresql import insert
from src.app.config.logging import configure_logging
from src.app.config.settings import settings
from src.app.database.models.article_embedding import ArticleEmbedding
from src.app.database.session import async_session_factory
from src.app.services.embedding import embed_text

configure_logging("embeddings-worker")


async def process_message(message: AbstractIncomingMessage) -> None:
    async with message.process():
        try:
            data = json.loads(message.body.decode())

            article_id = data["article_id"]
            title = data["title"]
            text = data["text"]

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

            logger.bind(article_id=article_id).info("Article embedding updated")
        except Exception:
            logger.exception("Failed to process embedding message")


async def main() -> None:
    connection = await aio_pika.connect_robust(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        login=settings.rabbitmq_user,
        password=settings.rabbitmq_password,
    )

    channel = await connection.channel()

    queue = await channel.declare_queue(
        settings.rabbitmq_embedding_queue,
        durable=True,
    )

    logger.info("Embeddings worker started")
    logger.bind(queue=queue.name).info("Waiting for messages")

    await queue.consume(process_message)

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
