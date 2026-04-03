from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
    db: Session = Depends(get_db),
):
    total, items = service.list_ask_runs(
        db,
        offset=offset,
        limit=limit,
        project_id=project_id,
        status=status_filter,
    )
    return AskRunListResponse(total=total, offset=offset, limit=limit, items=items)


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
