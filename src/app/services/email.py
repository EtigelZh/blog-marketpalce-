import smtplib
from email.message import EmailMessage

from src.app.config.settings import settings


def send_registration_email(email: str) -> None:
    message = EmailMessage()

    message["Subject"] = "Регистрация в Blog Marketplace"
    message["From"] = settings.smtp_from
    message["To"] = email

    message.set_content(
        "Здравствуйте!\n\n"
        "Вы успешно зарегистрировались в Blog Marketplace.\n\n"
        "Спасибо за регистрацию!"
    )

    with smtplib.SMTP(
        settings.smtp_host,
        settings.smtp_port,
    ) as server:
        server.send_message(message)
