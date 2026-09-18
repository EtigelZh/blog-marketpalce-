import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker

from src.app.config.settings import settings

broker = RabbitmqBroker(
    url=(
        f"amqp://{settings.rabbitmq_user}:{settings.rabbitmq_password}"
        f"@{settings.rabbitmq_host}:{settings.rabbitmq_port}/"
    )
)

dramatiq.set_broker(broker)
