from src.app.messaging.rabbitmq import publish_email


class MessagingService:
    async def send_registration_email(self, email: str) -> None:
        await publish_email(
            email=email,
            message_type="registration",
        )