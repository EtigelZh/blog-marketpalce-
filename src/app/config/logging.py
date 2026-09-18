import sys

from loguru import logger

from src.app.config.settings import settings


def configure_logging(service_name: str) -> None:
    logger.remove()

    if settings.debug:
        fmt = (
            "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> "
            "| <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
        )
        logger.add(sys.stdout, level=settings.log_level, format=fmt)
    else:
        logger.add(
            sys.stdout,
            level=settings.log_level,
            serialize=True,
            enqueue=True,
        )

    logger.add(
        f"logs/{service_name}.log",
        level=settings.log_level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        enqueue=True,
    )
