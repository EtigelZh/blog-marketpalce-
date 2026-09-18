from collections.abc import Awaitable, Callable
from typing import Any

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.database.models.deleted_article import DeletedArticle

from tests.conftest import FakeMessagingService

FAKE_IMAGE = ("test.png", b"\x89PNG\r\n\x1a\n", "image/png")


async def create_category(client: AsyncClient, name: str) -> int:
    response = await client.post("/categories", json={"name": name})
    category_id: int = response.json()["id"]
    return category_id


async def create_article(
    client: AsyncClient,
    title: str,
    text: str,
    category_id: int,
) -> dict[str, Any]:
    response = await client.post(
        "/articles",
        data={"title": title, "text": text, "category_id": category_id},
        files={"image": FAKE_IMAGE},
    )
    result: dict[str, Any] = response.json()
    assert response.status_code == 201, result
    return result


async def test_create_article_sets_timestamps_and_notifies_embedding_queue(
    client: AsyncClient,
    register_and_login: Callable[..., Awaitable[dict[str, Any]]],
    fake_messaging_service: FakeMessagingService,
) -> None:
    await register_and_login(client, "author@example.com")
    category_id = await create_category(client, "Гаджеты")

    article = await create_article(client, "Заголовок", "Текст статьи", category_id)

    assert article["created_at"] is not None
    assert article["updated_at"] is not None
    assert article["category_id"] == category_id
    assert fake_messaging_service.sent_embedding_tasks == [
        {
            "article_id": article["id"],
            "title": "Заголовок",
            "text": "Текст статьи",
        }
    ]


async def test_page_size_over_limit_is_rejected(
    client: AsyncClient,
    register_and_login: Callable[..., Awaitable[dict[str, Any]]],
) -> None:
    await register_and_login(client, "pagination@example.com")

    response = await client.get("/articles", params={"page_size": 51})

    assert response.status_code == 422


async def test_category_filter_returns_only_matching_articles(
    client: AsyncClient,
    register_and_login: Callable[..., Awaitable[dict[str, Any]]],
) -> None:
    await register_and_login(client, "filter@example.com")
    phones_id = await create_category(client, "Телефоны")
    laptops_id = await create_category(client, "Ноутбуки")

    await create_article(client, "Обзор телефона", "Текст про телефон", phones_id)
    await create_article(client, "Обзор ноутбука", "Текст про ноутбук", laptops_id)

    response = await client.get("/articles", params={"category_id": phones_id})

    titles = [item["title"] for item in response.json()]
    assert titles == ["Обзор телефона"]


async def test_fulltext_search_finds_relevant_article(
    client: AsyncClient,
    register_and_login: Callable[..., Awaitable[dict[str, Any]]],
) -> None:
    await register_and_login(client, "search@example.com")
    category_id = await create_category(client, "Аксессуары")

    await create_article(
        client,
        "Как выбрать наушники",
        "Беспроводные наушники с шумоподавлением для маркетплейса",
        category_id,
    )
    await create_article(
        client,
        "Как выбрать рюкзак",
        "Прочный рюкзак для ноутбука и документов",
        category_id,
    )

    response = await client.get("/articles", params={"search": "наушники"})

    titles = [item["title"] for item in response.json()]
    assert titles == ["Как выбрать наушники"]


async def test_get_missing_article_returns_404(client: AsyncClient) -> None:
    response = await client.get("/articles/999999")

    assert response.status_code == 404


async def test_update_by_non_owner_is_forbidden(
    client: AsyncClient,
    register_and_login: Callable[..., Awaitable[dict[str, Any]]],
) -> None:
    await register_and_login(client, "owner@example.com")
    category_id = await create_category(client, "Общее")
    article = await create_article(client, "Статья владельца", "Текст", category_id)

    await register_and_login(client, "intruder@example.com")

    response = await client.patch(
        f"/articles/{article['id']}",
        json={"title": "Взлом"},
    )

    assert response.status_code == 403


async def test_delete_moves_article_to_archive_table(
    client: AsyncClient,
    register_and_login: Callable[..., Awaitable[dict[str, Any]]],
    db_session: AsyncSession,
) -> None:
    await register_and_login(client, "deleter@example.com")
    category_id = await create_category(client, "Временное")
    article = await create_article(client, "Статья на удаление", "Текст", category_id)

    delete_response = await client.delete(f"/articles/{article['id']}")
    assert delete_response.status_code == 204

    get_response = await client.get(f"/articles/{article['id']}")
    assert get_response.status_code == 404

    result = await db_session.execute(
        select(DeletedArticle).where(DeletedArticle.article_id == article["id"])
    )
    archived = result.scalar_one()
    assert archived.title == "Статья на удаление"
