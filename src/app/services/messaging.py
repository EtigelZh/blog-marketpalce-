from src.app.messaging.rabbitmq import publish_email, publish_embedding_task


class MessagingService:
    async def send_registration_email(self, email: str) -> None:
        await publish_email(
            email=email,
            message_type="registration",
        )

    async def send_embedding_task(
        self,
        article_id: int,
        title: str,
        text: str,
    ) -> None:
        await publish_embedding_task(
            article_id=article_id,
            title=title,
            text=text,
        )
