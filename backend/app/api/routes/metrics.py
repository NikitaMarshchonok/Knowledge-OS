from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.metrics import QAMetricsResponse
from app.services.metrics import MetricsService

router = APIRouter(tags=["metrics"])
service = MetricsService()


@router.get("/metrics/qa", response_model=QAMetricsResponse)
def get_qa_metrics(project_id: UUID | None = None, db: Session = Depends(get_db)):
    return service.get_qa_metrics(db, project_id=project_id)
