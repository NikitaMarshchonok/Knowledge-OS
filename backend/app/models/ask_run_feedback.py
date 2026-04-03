import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.ask_run import FeedbackRating


class AskRunFeedback(Base):
    __tablename__ = "ask_run_feedback"
    __table_args__ = (UniqueConstraint("ask_run_id", name="uq_ask_run_feedback_ask_run_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ask_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ask_runs.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[FeedbackRating] = mapped_column(Enum(FeedbackRating, name="feedback_rating"), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    ask_run = relationship("AskRun", back_populates="feedback")
