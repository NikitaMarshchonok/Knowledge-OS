from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentChunkRead(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    char_start: int
    char_end: int
    token_estimate: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
