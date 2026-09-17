import json

import aio_pika
from aio_pika import DeliveryMode, Message

from src.app.config.settings import settings


async def publish_email(
    email: str,
    message_type: str,
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
            settings.rabbitmq_email_queue,
            durable=True,
        )

        body = {
            "type": message_type,
            "email": email,
        }

        message = Message(
            body=json.dumps(body).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json",
        )

        await channel.default_exchange.publish(
            message,
            routing_key=queue.name,
        )