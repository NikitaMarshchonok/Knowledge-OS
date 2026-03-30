from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass
class SearchCandidate:
    chunk_id: UUID
    document_id: UUID
    source_filename: str
    chunk_index: int
    content: str
    original_vector_score: float
    char_start: int
    char_end: int
    mime_type: str


@dataclass
class RerankedCandidate:
    candidate: SearchCandidate
    rerank_score: float


class Reranker(Protocol):
    def rerank(self, query: str, candidates: list[SearchCandidate], top_k: int) -> list[RerankedCandidate]: ...
