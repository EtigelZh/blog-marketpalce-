from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.app.config.settings import settings
import jwt


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public_paths = {
            "/",
            "/auth/register",
            "/auth/login",
            "/docs",
            "/openapi.json",
            "/redoc",
        }

        if request.url.path in public_paths:
            return await call_next(request)

        token = request.cookies.get("access_token")

        if token is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "Not authenticated"},
            )

        try:
            jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
        except jwt.InvalidTokenError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token"},
            )

        return await call_next(request)