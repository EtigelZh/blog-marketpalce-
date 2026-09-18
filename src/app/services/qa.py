import asyncio

from loguru import logger
from openai import OpenAI
from src.app.config.settings import settings
from src.app.database.models.article import Article
from src.app.repositories.embedding import EmbeddingRepository
from src.app.services.embedding import embed_text

SYSTEM_PROMPT = (
    "Ты — ассистент блога маркетплейса. Отвечай на вопросы пользователя "
    "только на основе предоставленного контекста статей блога. Если в "
    "контексте нет ответа на вопрос, честно скажи, что не знаешь, и не "
    "придумывай факты. Отвечай на русском языке."
)

MAX_CONTEXT_CHARS_PER_ARTICLE = 2000


class QaService:
    def __init__(self, repository: EmbeddingRepository) -> None:
        self.repository = repository
        self.client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )

    async def ask(self, question: str) -> tuple[str, list[Article]]:
        query_embedding = await asyncio.to_thread(embed_text, question)

        articles = await self.repository.search(
            query_embedding=query_embedding,
            limit=settings.rag_top_k,
        )

        logger.bind(sources_count=len(articles)).info("Question asked")

        if not articles:
            return (
                "В базе знаний блога пока нет статей, чтобы ответить на этот вопрос.",
                [],
            )

        context = "\n\n".join(
            f"Статья: {article.title}\n{article.text[:MAX_CONTEXT_CHARS_PER_ARTICLE]}"
            for article in articles
        )

        try:
            answer = await asyncio.to_thread(self._generate_answer, question, context)
        except Exception:
            logger.exception("LLM call failed")
            raise

        return answer, articles

    def _generate_answer(self, question: str, context: str) -> str:
        completion = self.client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Контекст:\n{context}\n\nВопрос: {question}",
                },
            ],
        )

        return completion.choices[0].message.content or ""
