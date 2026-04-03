import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AskRunStatus(str, enum.Enum):
    success = "success"
    failed = "failed"
    insufficient_evidence = "insufficient_evidence"


class FeedbackRating(str, enum.Enum):
    positive = "positive"
    negative = "negative"


class AskRun(Base):
    __tablename__ = "ask_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[AskRunStatus] = mapped_column(Enum(AskRunStatus, name="ask_run_status"), nullable=False)
    llm_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rerank_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieved_chunk_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    reranked_chunk_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    cited_chunk_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project = relationship("Project")
    citations = relationship("AskRunCitation", back_populates="ask_run", cascade="all, delete-orphan")
    feedback = relationship("AskRunFeedback", back_populates="ask_run", uselist=False, cascade="all, delete-orphan")
