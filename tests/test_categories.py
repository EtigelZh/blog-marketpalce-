from collections.abc import Awaitable, Callable
from typing import Any

from httpx import AsyncClient


async def test_create_and_list_categories(
    client: AsyncClient,
    register_and_login: Callable[..., Awaitable[dict[str, Any]]],
) -> None:
    await register_and_login(client, "cat-owner@example.com")

    create_response = await client.post("/categories", json={"name": "Ноутбуки"})
    assert create_response.status_code == 201
    assert create_response.json()["name"] == "Ноутбуки"

    list_response = await client.get("/categories")
    assert list_response.status_code == 200
    names = [category["name"] for category in list_response.json()]
    assert "Ноутбуки" in names


async def test_duplicate_category_name_conflicts(
    client: AsyncClient,
    register_and_login: Callable[..., Awaitable[dict[str, Any]]],
) -> None:
    await register_and_login(client, "cat-dup@example.com")

    await client.post("/categories", json={"name": "Смартфоны"})
    response = await client.post("/categories", json={"name": "Смартфоны"})

    assert response.status_code == 409
