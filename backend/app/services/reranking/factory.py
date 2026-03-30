from app.core.config import get_settings
from app.services.embeddings.factory import get_embedding_provider
from app.services.reranking.base import Reranker
from app.services.reranking.local_reranker import LocalEmbeddingReranker


class UnsupportedRerankerProviderError(Exception):
    pass


def get_reranker() -> Reranker:
    settings = get_settings()

    if settings.rerank_provider == "local_embedding":
        return LocalEmbeddingReranker(embedding_provider=get_embedding_provider())

    raise UnsupportedRerankerProviderError(f"Unsupported reranker provider: {settings.rerank_provider}")
