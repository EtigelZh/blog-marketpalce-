import asyncio
import json

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from src.app.config.settings import settings
from src.app.services.email import send_registration_email


async def process_message(message: AbstractIncomingMessage) -> None:
    async with message.process():
        data = json.loads(message.body.decode())

        if data["type"] == "registration":
            await asyncio.to_thread(
                send_registration_email,
                data["email"],
            )


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

    print("Email worker started", flush=True)
    print(
        f"Waiting for messages in queue: {queue.name}",
        flush=True,
    )

    await queue.consume(process_message)

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())