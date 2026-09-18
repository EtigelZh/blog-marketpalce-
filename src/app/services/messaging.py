from src.app.tasks.email import send_registration_email_task
from src.app.tasks.embeddings import process_embedding_task


class MessagingService:
    async def send_registration_email(self, email: str) -> None:
        send_registration_email_task.send(email)

    async def send_embedding_task(
        self,
        article_id: int,
        title: str,
        text: str,
    ) -> None:
        process_embedding_task.send(article_id, title, text)
