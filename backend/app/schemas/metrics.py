from pydantic import BaseModel


class QAMetricsResponse(BaseModel):
    total_questions: int
    success_count: int
    failed_count: int
    insufficient_evidence_count: int
    average_latency_ms: float
    latency_p50_ms: float
    latency_p95_ms: float
    positive_feedback_count: int
    negative_feedback_count: int
    feedback_count: int
    feedback_rate: float
    insufficient_evidence_reasons: dict[str, int]
    failure_reasons: dict[str, int]
    top_insufficient_evidence_reason: str | None = None
    top_failure_reason: str | None = None
