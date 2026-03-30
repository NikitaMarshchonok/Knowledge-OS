from uuid import UUID

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    project_id: UUID
    top_k: int = Field(default=8, ge=1, le=50)
    document_ids: list[UUID] | None = None
    mime_types: list[str] | None = None
    debug: bool = False


class SearchResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    source_filename: str
    chunk_index: int
    content: str
    original_vector_score: float
    rerank_score: float | None = None
    final_rank: int
    char_start: int
    char_end: int
    mime_type: str


class SearchDebugInfo(BaseModel):
    pre_rerank_chunk_ids: list[UUID]
    post_rerank_chunk_ids: list[UUID]


class SearchResponse(BaseModel):
    query: str
    top_k: int
    total_results: int
    results: list[SearchResult]
    debug: SearchDebugInfo | None = None
