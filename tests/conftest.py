import asyncio
import os
import subprocess
from collections.abc import AsyncGenerator, Awaitable, Callable
from pathlib import Path
from typing import Any

os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5433")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("POSTGRES_DB", "blog_marketplace_test")
os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-32-bytes-long")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_PUBLIC_ENDPOINT", "http://localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "test")
os.environ.setdefault("MINIO_SECRET_KEY", "test")
os.environ.setdefault("LLM_API_KEY", "test")

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.app.config.settings import settings
from src.app.database.models.article import Article
from src.app.database.session import engine, get_session
from src.app.dependencies import (
    get_messaging_service,
    get_qa_service,
    get_storage_service,
)
from src.app.main import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class FakeMessagingService:
    def __init__(self) -> None:
        self.sent_emails: list[str] = []
        self.sent_embedding_tasks: list[dict[str, Any]] = []

    async def send_registration_email(self, email: str) -> None:
        self.sent_emails.append(email)

    async def send_embedding_task(self, article_id: int, title: str, text: str) -> None:
        self.sent_embedding_tasks.append(
            {"article_id": article_id, "title": title, "text": text}
        )


class FakeStorageService:
    def upload_image(self, content: bytes, filename: str, content_type: str) -> str:
        return f"http://fake-storage.local/{filename}"


class FakeQaService:
    def __init__(self, answer: str, sources: list[Article]) -> None:
        self.answer = answer
        self.sources = sources

    async def ask(self, question: str) -> tuple[str, list[Article]]:
        return self.answer, self.sources


def _recreate_test_database() -> None:
    async def _run() -> None:
        connection = await asyncpg.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database="postgres",
        )
        try:
            await connection.execute(
                f'DROP DATABASE IF EXISTS "{settings.postgres_db}" WITH (FORCE)'
            )
            await connection.execute(f'CREATE DATABASE "{settings.postgres_db}"')
        finally:
            await connection.close()

    asyncio.run(_run())


@pytest.fixture(scope="session", autouse=True)
def test_database() -> None:
    _recreate_test_database()

    subprocess.run(
        ["poetry", "run", "alembic", "upgrade", "head"],
        check=True,
        cwd=PROJECT_ROOT,
    )


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    async with engine.connect() as connection:
        await connection.begin()

        session_maker = async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        async with session_maker() as session:
            yield session

        await connection.rollback()

    await engine.dispose()


@pytest_asyncio.fixture
async def fake_messaging_service() -> FakeMessagingService:
    return FakeMessagingService()


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
    fake_messaging_service: FakeMessagingService,
) -> AsyncGenerator[AsyncClient]:
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_messaging_service] = lambda: fake_messaging_service
    app.dependency_overrides[get_storage_service] = lambda: FakeStorageService()

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest.fixture
def qa_service_override() -> Callable[[str, list[Article]], FakeQaService]:
    def _set(answer: str, sources: list[Article]) -> FakeQaService:
        fake = FakeQaService(answer, sources)
        app.dependency_overrides[get_qa_service] = lambda: fake
        return fake

    return _set


@pytest.fixture
def register_and_login() -> Callable[..., Awaitable[dict[str, Any]]]:
    async def _do(
        client: AsyncClient,
        email: str,
        password: str = "password123",
    ) -> dict[str, Any]:
        register_response = await client.post(
            "/auth/register",
            json={"email": email, "password": password},
        )
        assert register_response.status_code == 201

        login_response = await client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        assert login_response.status_code == 200

        result: dict[str, Any] = register_response.json()
        return result

    return _do
