from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.database.models.user import User
from src.app.database.session import get_session
from src.app.repositories.article import ArticleRepository
from src.app.repositories.category import CategoryRepository
from src.app.repositories.embedding import EmbeddingRepository
from src.app.repositories.user import UserRepository
from src.app.services.article import ArticleService
from src.app.services.auth import AuthService
from src.app.services.category import CategoryService
from src.app.services.messaging import MessagingService
from src.app.services.qa import QaService
from src.app.services.storage import StorageService

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_messaging_service() -> MessagingService:
    return MessagingService()


def get_category_repository(
    session: SessionDep,
) -> CategoryRepository:
    return CategoryRepository(session)


def get_category_service(
    repository: Annotated[
        CategoryRepository,
        Depends(get_category_repository),
    ],
) -> CategoryService:
    return CategoryService(repository)


def get_article_repository(
    session: SessionDep,
) -> ArticleRepository:
    return ArticleRepository(session)


def get_article_service(
    repository: Annotated[
        ArticleRepository,
        Depends(get_article_repository),
    ],
    category_service: Annotated[
        CategoryService,
        Depends(get_category_service),
    ],
    messaging_service: Annotated[
        MessagingService,
        Depends(get_messaging_service),
    ],
) -> ArticleService:
    return ArticleService(
        repository=repository,
        category_service=category_service,
        messaging_service=messaging_service,
    )


def get_user_repository(
    session: SessionDep,
) -> UserRepository:
    return UserRepository(session)


def get_auth_service(
    repository: Annotated[
        UserRepository,
        Depends(get_user_repository),
    ],
    messaging_service: Annotated[
        MessagingService,
        Depends(get_messaging_service),
    ],
) -> AuthService:
    return AuthService(
        repository=repository,
        messaging_service=messaging_service,
    )


async def get_current_user(
    access_token: Annotated[
        str | None,
        Cookie(),
    ],
    auth_service: Annotated[
        AuthService,
        Depends(get_auth_service),
    ],
) -> User:
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        user_id = auth_service.decode_access_token(access_token)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from error

    user = await auth_service.repository.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user

def get_storage_service() -> StorageService:
    return StorageService()


def get_embedding_repository(
    session: SessionDep,
) -> EmbeddingRepository:
    return EmbeddingRepository(session)


def get_qa_service(
    repository: Annotated[
        EmbeddingRepository,
        Depends(get_embedding_repository),
    ],
) -> QaService:
    return QaService(repository)
