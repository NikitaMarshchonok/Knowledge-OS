from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import ChatMessageRole
from app.schemas.ask import Citation
from app.schemas.search import SearchResult


class ChatSessionCreate(BaseModel):
    project_id: UUID
    title: str | None = Field(default=None, max_length=255)


class ChatSessionRead(BaseModel):
    id: UUID
    project_id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatMessageRead(BaseModel):
    id: UUID
    session_id: UUID
    role: ChatMessageRole
    content: str
    ask_run_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionDetail(ChatSessionRead):
    messages: list[ChatMessageRead] = Field(default_factory=list)


class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1)
    top_k: int = Field(default=6, ge=1, le=20)
    document_ids: list[UUID] | None = None
    mime_types: list[str] | None = None
    debug: bool = False


class ChatMessageExchangeResponse(BaseModel):
    session: ChatSessionRead
    user_message: ChatMessageRead
    assistant_message: ChatMessageRead
    citations: list[Citation]
    supporting_results: list[SearchResult]
