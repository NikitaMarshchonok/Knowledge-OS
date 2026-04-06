from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.search import SearchResult


class AskRequest(BaseModel):
    query: str = Field(min_length=1)
    project_id: UUID
    top_k: int = Field(default=6, ge=1, le=20)
    document_ids: list[UUID] | None = None
    mime_types: list[str] | None = None
    debug: bool = False


class Citation(BaseModel):
    chunk_id: UUID
    document_id: UUID
    source_filename: str
    chunk_index: int
    char_start: int
    char_end: int
    snippet: str


class AskDebugInfo(BaseModel):
    context_chunk_ids: list[UUID]
    llm_model: str


class AskResponse(BaseModel):
    ask_run_id: UUID
    answer: str
    citations: list[Citation]
    supporting_results: list[SearchResult]
    debug: AskDebugInfo | None = None
