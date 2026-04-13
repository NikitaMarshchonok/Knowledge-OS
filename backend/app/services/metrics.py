from collections import Counter
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
        p50_latency = (
            runs_query.filter(AskRun.latency_ms.isnot(None))
            .with_entities(func.percentile_cont(0.5).within_group(AskRun.latency_ms.asc()))
            .scalar()
        )
        p95_latency = (
            runs_query.filter(AskRun.latency_ms.isnot(None))
            .with_entities(func.percentile_cont(0.95).within_group(AskRun.latency_ms.asc()))
            .scalar()
        )
        latency_p50_ms = float(p50_latency or 0.0)
        latency_p95_ms = float(p95_latency or 0.0)

        feedback_query = db.query(AskRunFeedback).join(AskRun, AskRun.id == AskRunFeedback.ask_run_id)
        if project_id is not None:
            feedback_query = feedback_query.filter(AskRun.project_id == project_id)

        positive_feedback_count = feedback_query.filter(AskRunFeedback.rating == FeedbackRating.positive).count()
        negative_feedback_count = feedback_query.filter(AskRunFeedback.rating == FeedbackRating.negative).count()
        feedback_count = positive_feedback_count + negative_feedback_count
        feedback_rate = float(feedback_count / total_questions) if total_questions > 0 else 0.0

        reason_rows = (
            runs_query.with_entities(AskRun.status, AskRun.error_message).filter(AskRun.error_message.isnot(None)).all()
        )
        insufficient_counter: Counter[str] = Counter()
        failure_counter: Counter[str] = Counter()
        for run_status, error_message in reason_rows:
            if not error_message:
                continue
            reason = self._normalize_error_reason(error_message)
            if run_status == AskRunStatus.insufficient_evidence:
                insufficient_counter[reason] += 1
            elif run_status == AskRunStatus.failed:
                failure_counter[reason] += 1

        insufficient_evidence_reasons = dict(insufficient_counter.most_common())
        failure_reasons = dict(failure_counter.most_common())
        top_insufficient_evidence_reason = next(iter(insufficient_evidence_reasons), None)
        top_failure_reason = next(iter(failure_reasons), None)

        return QAMetricsResponse(
            total_questions=total_questions,
            success_count=success_count,
            failed_count=failed_count,
            insufficient_evidence_count=insufficient_evidence_count,
            average_latency_ms=average_latency_ms,
            latency_p50_ms=latency_p50_ms,
            latency_p95_ms=latency_p95_ms,
            positive_feedback_count=positive_feedback_count,
            negative_feedback_count=negative_feedback_count,
            feedback_count=feedback_count,
            feedback_rate=feedback_rate,
            insufficient_evidence_reasons=insufficient_evidence_reasons,
            failure_reasons=failure_reasons,
            top_insufficient_evidence_reason=top_insufficient_evidence_reason,
            top_failure_reason=top_failure_reason,
        )

    def _normalize_error_reason(self, error_message: str) -> str:
        if ":" not in error_message:
            return error_message.strip()[:80]
        _, reason = error_message.split(":", 1)
        cleaned = reason.strip()
        return cleaned[:80] if cleaned else "unknown"
