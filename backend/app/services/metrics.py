from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import AskRun, AskRunFeedback, AskRunStatus, FeedbackRating
from app.schemas.metrics import QAMetricsResponse


class MetricsService:
    def get_qa_metrics(self, db: Session, project_id: UUID | None = None) -> QAMetricsResponse:
        runs_query = db.query(AskRun)
        if project_id is not None:
            runs_query = runs_query.filter(AskRun.project_id == project_id)

        total_questions = runs_query.count()
        success_count = runs_query.filter(AskRun.status == AskRunStatus.success).count()
        failed_count = runs_query.filter(AskRun.status == AskRunStatus.failed).count()
        insufficient_evidence_count = runs_query.filter(AskRun.status == AskRunStatus.insufficient_evidence).count()

        avg_latency = runs_query.with_entities(func.avg(AskRun.latency_ms)).scalar()
        average_latency_ms = float(avg_latency or 0.0)

        feedback_query = db.query(AskRunFeedback).join(AskRun, AskRun.id == AskRunFeedback.ask_run_id)
        if project_id is not None:
            feedback_query = feedback_query.filter(AskRun.project_id == project_id)

        positive_feedback_count = feedback_query.filter(AskRunFeedback.rating == FeedbackRating.positive).count()
        negative_feedback_count = feedback_query.filter(AskRunFeedback.rating == FeedbackRating.negative).count()

        return QAMetricsResponse(
            total_questions=total_questions,
            success_count=success_count,
            failed_count=failed_count,
            insufficient_evidence_count=insufficient_evidence_count,
            average_latency_ms=average_latency_ms,
            positive_feedback_count=positive_feedback_count,
            negative_feedback_count=negative_feedback_count,
        )
