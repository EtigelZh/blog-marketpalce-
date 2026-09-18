from datetime import UTC, datetime, timedelta

import jwt
from loguru import logger
from pwdlib import PasswordHash

from src.app.config.settings import settings
from src.app.database.models.user import User
from src.app.repositories.user import UserRepository
from src.app.services.messaging import MessagingService

password_hash = PasswordHash.recommended()


class AuthService:
    def __init__(
        self,
        repository: UserRepository,
        messaging_service: MessagingService,
    ) -> None:
        self.repository = repository
        self.messaging_service = messaging_service

    async def register(
        self,
        email: str,
        password: str,
    ) -> User:
        existing_user = await self.repository.get_by_email(email)

        if existing_user is not None:
            logger.bind(email=email).warning("Registration attempt with existing email")
            raise ValueError("User already exists")

        hashed_password = password_hash.hash(password)

        user = await self.repository.create(
            email=email,
            password_hash=hashed_password,
        )

        await self.messaging_service.send_registration_email(user.email)

        logger.bind(user_id=user.id, email=user.email).info("User registered")

        return user

    async def authenticate(
        self,
        email: str,
        password: str,
    ) -> User:
        user = await self.repository.get_by_email(email)

        if user is None:
            logger.bind(email=email).warning("Login attempt for unknown email")
            raise ValueError("Invalid credentials")

        if not password_hash.verify(password, user.password_hash):
            logger.bind(email=email).warning("Login attempt with wrong password")
            raise ValueError("Invalid credentials")

        logger.bind(user_id=user.id, email=user.email).info("User logged in")

        return user

    def create_access_token(self, user_id: int) -> str:
        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.jwt_expire_minutes,
        )

        payload = {
            "sub": str(user_id),
            "exp": expires_at,
        }

        return jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )

    def decode_access_token(self, token: str) -> int:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
        except jwt.InvalidTokenError as error:
            raise ValueError("Invalid token") from error

        user_id = payload.get("sub")

        if user_id is None:
            raise ValueError("Invalid token")

        try:
            return int(user_id)
        except (TypeError, ValueError) as error:
            raise ValueError("Invalid token") from error
