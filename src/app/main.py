from fastapi import FastAPI
from loguru import logger
from src.app.config.logging import configure_logging
from src.app.config.settings import settings
from src.app.middleware.auth import AuthMiddleware
from src.app.routing.router import router

configure_logging("app")

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

logger.bind(app_name=settings.app_name).info("Service starting")

app.add_middleware(AuthMiddleware)

app.include_router(router)
