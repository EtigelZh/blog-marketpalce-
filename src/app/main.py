from fastapi import FastAPI
from src.app.config.settings import settings
from src.app.middleware.auth import AuthMiddleware
from src.app.routing.router import router

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.add_middleware(AuthMiddleware)

app.include_router(router)
