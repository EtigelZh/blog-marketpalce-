import asyncio
import json

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from loguru import logger
from src.app.config.logging import configure_logging
from src.app.config.settings import settings
from src.app.services.email import send_registration_email

configure_logging("email-worker")


async def process_message(message: AbstractIncomingMessage) -> None:
    async with message.process():
        try:
            data = json.loads(message.body.decode())

            if data["type"] == "registration":
                await asyncio.to_thread(
                    send_registration_email,
                    data["email"],
                )
                logger.bind(email=data["email"]).info("Registration email sent")
        except Exception:
            logger.exception("Failed to process email message")


async def main() -> None:
    connection = await aio_pika.connect_robust(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        login=settings.rabbitmq_user,
        password=settings.rabbitmq_password,
    )

    channel = await connection.channel()

    queue = await channel.declare_queue(
        settings.rabbitmq_email_queue,
        durable=True,
    )

    logger.info("Email worker started")
    logger.bind(queue=queue.name).info("Waiting for messages")

    await queue.consume(process_message)

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
