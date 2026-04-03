from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import AskRunStatus, FeedbackRating


class AskRunCitationRead(BaseModel):
    id: UUID
    chunk_id: UUID
    document_id: UUID
    source_filename: str
    chunk_index: int
    char_start: int
    char_end: int
    snippet: str
    citation_order: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AskRunFeedbackRead(BaseModel):
    id: UUID
    ask_run_id: UUID
    rating: FeedbackRating
    comment: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AskRunRead(BaseModel):
    id: UUID
    project_id: UUID
    query: str
    answer: str | None
    status: AskRunStatus
    llm_model: str | None
    embedding_model: str | None
    rerank_model: str | None
    latency_ms: int | None
    top_k: int
    error_message: str | None
    retrieved_chunk_ids: list[str] | None
    reranked_chunk_ids: list[str] | None
    cited_chunk_ids: list[str] | None
    created_at: datetime
    updated_at: datetime
    citations: list[AskRunCitationRead] = Field(default_factory=list)
    feedback: AskRunFeedbackRead | None = None

    model_config = ConfigDict(from_attributes=True)


class AskRunListResponse(BaseModel):
    total: int
    offset: int
    limit: int
    items: list[AskRunRead]


class AskRunFeedbackCreate(BaseModel):
    rating: FeedbackRating
    comment: str | None = None
