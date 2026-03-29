from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Document, DocumentChunk
from app.schemas.document import DocumentIndexStatusRead, DocumentRead
from app.schemas.document_chunk import DocumentChunkRead
from app.services.document_indexing import DocumentIndexingError, index_document_task, schedule_document_indexing

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: UUID, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return document


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkRead])
def list_document_chunks(
    document_id: UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{document_id}/index-status", response_model=DocumentIndexStatusRead)
def get_document_index_status(document_id: UUID, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.post("/{document_id}/index", response_model=DocumentIndexStatusRead)
def index_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        document = schedule_document_indexing(document_id, db, reindex=False)
    except DocumentIndexingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    background_tasks.add_task(index_document_task, document.id, False)
    return document


@router.post("/{document_id}/reindex", response_model=DocumentIndexStatusRead)
def reindex_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        document = schedule_document_indexing(document_id, db, reindex=True)
    except DocumentIndexingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    background_tasks.add_task(index_document_task, document.id, True)
    return document
