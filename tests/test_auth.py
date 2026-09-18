from collections.abc import Awaitable, Callable
from typing import Any

from httpx import AsyncClient

from tests.conftest import FakeMessagingService


async def test_register_sends_confirmation_email(
    client: AsyncClient,
    fake_messaging_service: FakeMessagingService,
) -> None:
    response = await client.post(
        "/auth/register",
        json={"email": "new-user@example.com", "password": "password123"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "new-user@example.com"
    assert fake_messaging_service.sent_emails == ["new-user@example.com"]


async def test_register_duplicate_email_conflicts(
    client: AsyncClient,
    register_and_login: Callable[..., Awaitable[dict[str, Any]]],
) -> None:
    await register_and_login(client, "duplicate@example.com")

    response = await client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "password123"},
    )

    assert response.status_code == 409


async def test_login_with_wrong_password_is_rejected(
    client: AsyncClient,
    register_and_login: Callable[..., Awaitable[dict[str, Any]]],
) -> None:
    await register_and_login(client, "wrong-pass@example.com")

    response = await client.post(
        "/auth/login",
        json={"email": "wrong-pass@example.com", "password": "not-the-password"},
    )

    assert response.status_code == 401


async def test_protected_endpoint_requires_cookie(client: AsyncClient) -> None:
    response = await client.post(
        "/categories",
        json={"name": "Электроника"},
    )

    assert response.status_code == 401


async def test_protected_endpoint_works_with_valid_cookie(
    client: AsyncClient,
    register_and_login: Callable[..., Awaitable[dict[str, Any]]],
) -> None:
    await register_and_login(client, "authorized@example.com")

    response = await client.post(
        "/categories",
        json={"name": "Электроника"},
    )

    assert response.status_code == 201
