from pydantic import BaseModel


class QAMetricsResponse(BaseModel):
    total_questions: int
    success_count: int
    failed_count: int
    insufficient_evidence_count: int
    average_latency_ms: float
    positive_feedback_count: int
    negative_feedback_count: int
