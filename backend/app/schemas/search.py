from uuid import UUID

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    project_id: UUID
    top_k: int = Field(default=8, ge=1, le=50)
    document_ids: list[UUID] | None = None
    mime_types: list[str] | None = None


class SearchResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    source_filename: str
    chunk_index: int
    content: str
    score: float
    char_start: int
    char_end: int
    mime_type: str


class SearchResponse(BaseModel):
    query: str
    top_k: int
    total_results: int
    results: list[SearchResult]
