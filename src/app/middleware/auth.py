import jwt
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from src.app.config.settings import settings
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        public_paths = {
            "/",
            "/auth/register",
            "/auth/login",
            "/docs",
            "/openapi.json",
            "/redoc",
        }

        path = request.url.path

        is_public_read = request.method == "GET" and (
            path == "/categories"
            or path == "/articles"
            or path.startswith("/articles/")
        )

        is_public_qa = request.method == "POST" and path == "/qa/ask"

        if path in public_paths or is_public_read or is_public_qa:
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
