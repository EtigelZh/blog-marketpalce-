import json
from typing import Any

import aio_pika
from aio_pika import DeliveryMode, Message
from src.app.config.settings import settings


async def publish_message(
    queue_name: str,
    body: dict[str, Any],
) -> None:
    connection = await aio_pika.connect_robust(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        login=settings.rabbitmq_user,
        password=settings.rabbitmq_password,
    )

    async with connection:
        channel = await connection.channel()

        queue = await channel.declare_queue(
            queue_name,
            durable=True,
        )

        message = Message(
            body=json.dumps(body).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json",
        )

        await channel.default_exchange.publish(
            message,
            routing_key=queue.name,
        )


async def publish_email(
    email: str,
    message_type: str,
) -> None:
    await publish_message(
        settings.rabbitmq_email_queue,
        {
            "type": message_type,
            "email": email,
        },
    )


async def publish_embedding_task(
    article_id: int,
    title: str,
    text: str,
) -> None:
    await publish_message(
        settings.rabbitmq_embedding_queue,
        {
            "article_id": article_id,
            "title": title,
            "text": text,
        },
    )
