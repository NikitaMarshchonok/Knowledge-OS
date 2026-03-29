from functools import lru_cache

from app.core.config import get_settings
from app.services.embeddings.base import EmbeddingProvider
from app.services.embeddings.fastembed_provider import FastEmbedProvider


class UnsupportedEmbeddingProviderError(Exception):
    pass


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()

    if settings.embedding_provider == "fastembed":
        return FastEmbedProvider(
            model_name=settings.embedding_model_name,
            batch_size=settings.embedding_batch_size,
        )

    raise UnsupportedEmbeddingProviderError(f"Unsupported embedding provider: {settings.embedding_provider}")
