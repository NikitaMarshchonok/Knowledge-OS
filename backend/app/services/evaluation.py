from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import AskRun, AskRunCitation, AskRunFeedback, AskRunStatus, FeedbackRating
from app.schemas.ask import Citation


class EvaluationError(Exception):
    pass


class EvaluationService:
    def create_ask_run(
        self,
        db: Session,
        *,
        project_id: UUID,
        query: str,
        top_k: int,
        embedding_model: str | None,
        rerank_model: str | None,
    ) -> AskRun:
        ask_run = AskRun(
            project_id=project_id,
            query=query,
            top_k=top_k,
            status=AskRunStatus.failed,
            embedding_model=embedding_model,
            rerank_model=rerank_model,
        )
        db.add(ask_run)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise EvaluationError("Failed to persist ask run") from exc
        db.refresh(ask_run)
        return ask_run

    def finalize_ask_run(
        self,
        db: Session,
        *,
        ask_run: AskRun,
        status: AskRunStatus,
        answer: str | None,
        llm_model: str | None,
        latency_ms: int,
        error_message: str | None,
        retrieved_chunk_ids: list[str] | None,
        reranked_chunk_ids: list[str] | None,
        cited_chunk_ids: list[str] | None,
        citations: list[Citation],
    ) -> AskRun:
        ask_run.status = status
        ask_run.answer = answer
        ask_run.llm_model = llm_model
        ask_run.latency_ms = latency_ms
        ask_run.error_message = error_message
        ask_run.retrieved_chunk_ids = retrieved_chunk_ids
        ask_run.reranked_chunk_ids = reranked_chunk_ids
        ask_run.cited_chunk_ids = cited_chunk_ids

        for order, citation in enumerate(citations, start=1):
            db.add(
                AskRunCitation(
                    ask_run_id=ask_run.id,
                    chunk_id=citation.chunk_id,
                    document_id=citation.document_id,
                    source_filename=citation.source_filename,
                    chunk_index=citation.chunk_index,
                    char_start=citation.char_start,
                    char_end=citation.char_end,
                    snippet=citation.snippet,
                    citation_order=order,
                )
            )

        db.commit()
        return self.get_ask_run(db, ask_run.id)

    def list_ask_runs(
        self,
        db: Session,
        *,
        offset: int,
        limit: int,
        project_id: UUID | None = None,
        status: AskRunStatus | None = None,
    ) -> tuple[int, list[AskRun]]:
        query = db.query(AskRun)
        if project_id is not None:
            query = query.filter(AskRun.project_id == project_id)
        if status is not None:
            query = query.filter(AskRun.status == status)

        total = query.count()
        items = (
            query.options(selectinload(AskRun.citations), selectinload(AskRun.feedback))
            .order_by(AskRun.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return total, items

    def get_ask_run(self, db: Session, ask_run_id: UUID) -> AskRun:
        ask_run = (
            db.query(AskRun)
            .options(selectinload(AskRun.citations), selectinload(AskRun.feedback))
            .filter(AskRun.id == ask_run_id)
            .first()
        )
        if ask_run is None:
            raise EvaluationError("Ask run not found")
        return ask_run

    def submit_feedback(
        self,
        db: Session,
        *,
        ask_run_id: UUID,
        rating: FeedbackRating,
        comment: str | None,
    ) -> AskRunFeedback:
        ask_run = db.query(AskRun).filter(AskRun.id == ask_run_id).first()
        if ask_run is None:
            raise EvaluationError("Ask run not found")

        feedback = db.query(AskRunFeedback).filter(AskRunFeedback.ask_run_id == ask_run_id).first()
        if feedback is None:
            feedback = AskRunFeedback(ask_run_id=ask_run_id, rating=rating, comment=comment)
            db.add(feedback)
        else:
            feedback.rating = rating
            feedback.comment = comment

        db.commit()
        db.refresh(feedback)
        return feedback
