from functools import lru_cache

from fastembed import TextEmbedding
from src.app.config.settings import settings


@lru_cache(maxsize=1)
def get_embedding_model() -> TextEmbedding:
    return TextEmbedding(model_name=settings.embedding_model_name)


def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    (embedding,) = model.embed([text])

    return [float(value) for value in embedding]
