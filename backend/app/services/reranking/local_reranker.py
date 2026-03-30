import math

from app.services.embeddings.base import EmbeddingProvider
from app.services.reranking.base import RerankedCandidate, Reranker, SearchCandidate


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class LocalEmbeddingReranker(Reranker):
    def __init__(self, embedding_provider: EmbeddingProvider) -> None:
        self.embedding_provider = embedding_provider

    def rerank(self, query: str, candidates: list[SearchCandidate], top_k: int) -> list[RerankedCandidate]:
        if not candidates:
            return []

        query_vector = self.embedding_provider.embed_texts([query])[0]
        candidate_vectors = self.embedding_provider.embed_texts([candidate.content for candidate in candidates])

        scored = [
            RerankedCandidate(candidate=candidate, rerank_score=_cosine_similarity(query_vector, candidate_vector))
            for candidate, candidate_vector in zip(candidates, candidate_vectors, strict=True)
        ]

        scored.sort(key=lambda item: item.rerank_score, reverse=True)
        return scored[:top_k]
