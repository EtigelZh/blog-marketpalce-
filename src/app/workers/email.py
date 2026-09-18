from src.app.config.logging import configure_logging

configure_logging("email-worker")

from src.app.tasks.email import send_registration_email_task  # noqa: E402

__all__ = ["send_registration_email_task"]
