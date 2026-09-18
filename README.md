# Blog Marketplace API

Backend блога маркетплейса на FastAPI: JWT-аутентификация, статьи с
категориями, полнотекстовым поиском и пагинацией, фейковое удаление,
асинхронная обработка задач через RabbitMQ/Dramatiq и RAG-помощник,
отвечающий на вопросы по базе статей блога.

## Стек

- **FastAPI** + **SQLAlchemy 2.0 (async)** + **asyncpg**
- **PostgreSQL 18** + **pgvector** (векторный поиск) + полнотекстовый поиск
  на GIN-индексе (`to_tsvector`/`plainto_tsquery`)
- **RabbitMQ** + **Dramatiq** — асинхронная отправка писем и векторизация
  статей
- **MinIO** (S3-совместимое хранилище) — изображения статей
- **fastembed** — локальные эмбеддинги (без внешнего API)
- **Groq** (OpenAI-совместимый API) — генерация ответов в RAG
- **JWT** (`pyjwt`) в httponly cookie + собственный middleware
- **Loguru** — структурированные логи (цветные в dev, JSON в проде + файл
  с ротацией)
- **Alembic** — миграции
- **pytest** + **httpx** — тесты на реальном Postgres/pgvector
- **ruff**, **mypy (strict)**, **bandit**, **radon**, **pre-commit**
- **Docker / Docker Compose**

## Архитектура

```
                       ┌──────────┐
   браузер / Postman ─▶│   app    │─── JWT cookie, REST API, /docs (Swagger)
                       └────┬─────┘
                            │ enqueue (Dramatiq .send())
                ┌───────────┼────────────┐
                ▼                        ▼
         RabbitMQ: emails        RabbitMQ: article_embeddings
                │                        │
                ▼                        ▼
         ┌─────────────┐         ┌──────────────────┐
         │   worker    │         │ embeddings-worker │
         └──────┬──────┘         └─────────┬─────────┘
                │ SMTP                     │ embed_text() + upsert
                ▼                          ▼
             Mailpit                  pgvector (article_embeddings)

   db (Postgres + pgvector)  ◀── ORM ──▶  app
   minio (S3)                ◀── image upload ──▶  app
```

- Создание/изменение статьи не блокирует ответ — задача на векторизацию
  уходит в очередь, `embeddings-worker` считает эмбеддинг и делает upsert
  в `article_embeddings`.
- `POST /qa/ask`: вопрос векторизуется той же моделью → косинусный поиск
  по `article_embeddings` → топ-N статей в контекст → запрос к LLM →
  ответ с указанием статей-источников.
- `DELETE /articles/{id}` переносит строку из `articles` в отдельную
  таблицу `deleted_articles` одной транзакцией — не просто флаг.
- Middleware проверяет JWT-cookie на каждом запросе, кроме публичных
  путей (регистрация/логин, чтение статей/категорий, `/qa/ask`, `/docs`).

## Быстрый старт

1. `cp .env.example .env`
2. (Нужно для `/qa/ask`) получите бесплатный ключ на
   [console.groq.com](https://console.groq.com) → API Keys → Create API
   Key, впишите в `.env`: `LLM_API_KEY=gsk_...`. Без ключа всё остальное
   API работает, `/qa/ask` вернёт 500.
3. `docker compose up -d --build`
4. `docker compose exec app alembic upgrade head`
5. Swagger: **http://localhost:8000/docs**

При первом сообщении в очередь эмбеддингов `fastembed` скачивает модель
(~250 МБ, один раз, кешируется в volume `fastembed_cache`) — первая
статья обработается дольше обычного.

### Полезные адреса

| Сервис | URL | Логин/пароль |
|---|---|---|
| Swagger | http://localhost:8000/docs | — |
| Mailpit (письма) | http://localhost:8025 | — |
| RabbitMQ Management | http://localhost:15672 | guest / guest |
| MinIO Console | http://localhost:9001 | minio / minio12345 |
| Postgres | localhost:5433 | postgres / postgres |

## Эндпоинты

| Метод/путь | Auth | Описание |
|---|---|---|
| `POST /auth/register` | нет | Регистрация, письмо уходит асинхронно |
| `POST /auth/login` | нет | Логин, JWT в httponly cookie `access_token` |
| `GET /articles` | нет | Список: `page_number`, `page_size` (≤50), `category_id`, `search` |
| `POST /articles` | да | Создание (`multipart/form-data`: `title`, `text`, `category_id`, `image`) |
| `GET /articles/{id}` | нет | Получить статью |
| `PATCH /articles/{id}` | да, только автор | Изменить статью |
| `DELETE /articles/{id}` | да, только автор | Фейковое удаление |
| `GET /categories` | нет | Список категорий |
| `POST /categories` | да | Создание категории |
| `POST /qa/ask` | нет | `{"question": "..."}` → `{"answer": "...", "sources": [...]}` |

Проверить всё можно прямо в Swagger (`/docs`).

## Тесты

Тесты используют реальный Postgres с pgvector (не моки БД), внешние
сервисы (RabbitMQ/MinIO/LLM) подменяются фейками.

```bash
docker compose up -d db        # нужен только Postgres
poetry install
poetry run pytest -v
```

Тесты сами создают базу `blog_marketplace_test` и прогоняют миграции;
каждый тест изолирован транзакцией — можно гонять `pytest` сколько
угодно раз подряд.

## Контроль качества кода

```bash
poetry run pre-commit install   # один раз
make check                       # lint + fmt + type + security + radon + test
```

`make help` — список отдельных целей (`lint`, `type`, `security`, ...).

## Переменные окружения

Полный список — в `.env.example`. Из нестандартного:

- `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` — провайдер LLM для
  `/qa/ask` (по умолчанию Groq, любой OpenAI-совместимый меняется этими
  тремя переменными).
- `EMBEDDING_MODEL_NAME` / `EMBEDDING_DIMENSIONS` — модель эмбеддингов
  (`fastembed`, локально). При смене модели нужно менять и
  `EMBEDDING_DIMENSIONS`, и пересоздавать таблицу `article_embeddings`.
- `RAG_TOP_K` — сколько статей подмешивать в контекст LLM.
