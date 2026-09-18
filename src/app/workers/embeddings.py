from src.app.config.logging import configure_logging

configure_logging("embeddings-worker")

from src.app.tasks.embeddings import process_embedding_task  # noqa: E402

__all__ = ["process_embedding_task"]
