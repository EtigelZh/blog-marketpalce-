from collections.abc import Callable

from httpx import AsyncClient
from src.app.database.models.article import Article

from tests.conftest import FakeQaService


async def test_ask_returns_answer_and_sources(
    client: AsyncClient,
    qa_service_override: Callable[[str, list[Article]], FakeQaService],
) -> None:
    source_article = Article(
        id=1,
        title="Как выбрать смартфон",
        text="При выборе смартфона обращайте внимание на характеристики.",
        image="http://example.com/phone.png",
        category_id=1,
        author_id=1,
    )
    qa_service_override("Обращайте внимание на характеристики.", [source_article])

    response = await client.post(
        "/qa/ask",
        json={"question": "Как выбрать смартфон на маркетплейсе?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Обращайте внимание на характеристики."
    assert body["sources"] == [{"id": 1, "title": "Как выбрать смартфон"}]
