import csv
import io
from datetime import datetime, timezone
from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AskRunStatus
from app.schemas.ask_run import AskRunFeedbackCreate, AskRunFeedbackRead, AskRunListResponse, AskRunRead
from app.services.evaluation import EvaluationError, EvaluationService

router = APIRouter(tags=["ask-runs"])
service = EvaluationService()


@router.get("/ask-runs", response_model=AskRunListResponse)
def list_ask_runs(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    project_id: UUID | None = None,
    status_filter: AskRunStatus | None = Query(default=None, alias="status"),
    error_reason: str | None = Query(default=None, min_length=1),
    sort: Literal["recent", "problematic"] = Query(default="recent"),
    time_window: Literal["24h", "7d", "30d", "all"] = Query(default="all"),
    db: Session = Depends(get_db),
):
    total, items = service.list_ask_runs(
        db,
        offset=offset,
        limit=limit,
        project_id=project_id,
        status=status_filter,
        error_reason=error_reason,
        sort=sort,
        time_window=time_window,
    )
    return AskRunListResponse(total=total, offset=offset, limit=limit, items=items)


@router.get("/ask-runs/export")
def export_ask_runs(
    project_id: UUID | None = None,
    status_filter: AskRunStatus | None = Query(default=None, alias="status"),
    error_reason: str | None = Query(default=None, min_length=1),
    sort: Literal["recent", "problematic"] = Query(default="recent"),
    time_window: Literal["24h", "7d", "30d", "all"] = Query(default="all"),
    db: Session = Depends(get_db),
):
    items = service.list_ask_runs_for_export(
        db,
        project_id=project_id,
        status=status_filter,
        error_reason=error_reason,
        sort=sort,
        time_window=time_window,
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "project_id",
            "status",
            "query",
            "answer",
            "error_reason",
            "error_message",
            "latency_ms",
            "llm_model",
            "embedding_model",
            "rerank_model",
            "top_k",
            "retrieved_chunks_count",
            "reranked_chunks_count",
            "cited_chunks_count",
            "created_at",
            "updated_at",
        ]
    )
    for run in items:
        writer.writerow(
            [
                str(run.id),
                str(run.project_id),
                run.status.value,
                run.query,
                run.answer or "",
                run.error_reason or "",
                run.error_message or "",
                run.latency_ms if run.latency_ms is not None else "",
                run.llm_model or "",
                run.embedding_model or "",
                run.rerank_model or "",
                run.top_k,
                len(run.retrieved_chunk_ids or []),
                len(run.reranked_chunk_ids or []),
                len(run.cited_chunk_ids or []),
                run.created_at.isoformat(),
                run.updated_at.isoformat(),
            ]
        )
    filename = f"ask-runs-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.csv"
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/ask-runs/{ask_run_id}", response_model=AskRunRead)
def get_ask_run(ask_run_id: UUID, db: Session = Depends(get_db)):
    try:
        return service.get_ask_run(db, ask_run_id)
    except EvaluationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/ask-runs/{ask_run_id}/feedback", response_model=AskRunFeedbackRead)
def submit_feedback(ask_run_id: UUID, payload: AskRunFeedbackCreate, db: Session = Depends(get_db)):
    try:
        return service.submit_feedback(
            db,
            ask_run_id=ask_run_id,
            rating=payload.rating,
            comment=payload.comment,
        )
    except EvaluationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
