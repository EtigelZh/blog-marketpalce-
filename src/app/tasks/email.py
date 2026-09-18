import dramatiq
from loguru import logger

from src.app.config.settings import settings
from src.app.messaging.broker import broker  # noqa: F401
from src.app.services.email import send_registration_email


@dramatiq.actor(queue_name=settings.rabbitmq_email_queue, max_retries=3)
def send_registration_email_task(email: str) -> None:
    try:
        send_registration_email(email)
    except Exception:
        logger.bind(email=email).exception("Failed to send registration email")
        raise

    logger.bind(email=email).info("Registration email sent")
