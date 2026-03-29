from datetime import UTC, datetime
from uuid import UUID

from qdrant_client import models as qdrant_models
from sqlalchemy.orm import Session, selectinload

from app.db.session import SessionLocal
from app.models import Document, DocumentChunk, DocumentStatus
from app.services.embeddings.factory import get_embedding_provider
from app.services.vector_store.qdrant_service import QdrantIndexService


class DocumentIndexingError(Exception):
    pass


def schedule_document_indexing(document_id: UUID, db: Session, reindex: bool = False) -> Document:
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise DocumentIndexingError("Document not found")

    if document.is_indexing:
        raise DocumentIndexingError("Document is already indexing")

    if document.status not in {DocumentStatus.processed, DocumentStatus.indexed}:
        raise DocumentIndexingError("Document must be processed before indexing")

    if document.status == DocumentStatus.indexed and not reindex:
        raise DocumentIndexingError("Document is already indexed; use reindex endpoint")

    if document.chunk_count <= 0:
        raise DocumentIndexingError("Document has no chunks to index")

    document.is_indexing = True
    document.indexing_error = None
    db.commit()
    db.refresh(document)
    return document


def index_document(document_id: UUID, db: Session, reindex: bool = False, already_scheduled: bool = False) -> None:
    document = (
        db.query(Document)
        .options(selectinload(Document.chunks))
        .filter(Document.id == document_id)
        .first()
    )
    if document is None:
        return

    previous_status = document.status
    if not already_scheduled:
        schedule_document_indexing(document_id, db, reindex=reindex)
        db.refresh(document)

    try:
        chunks = sorted(document.chunks, key=lambda chunk: chunk.chunk_index)
        if not chunks:
            raise DocumentIndexingError("Document has no chunks to index")

        embedding_provider = get_embedding_provider()
        index_service = QdrantIndexService(vector_size=embedding_provider.dimension)
        index_service.ensure_collection()

        # Always remove document vectors first for deterministic reindex behavior.
        index_service.delete_document_vectors(document.id)

        texts = [chunk.content for chunk in chunks]
        embeddings = embedding_provider.embed_texts(texts)
        if len(embeddings) != len(chunks):
            raise DocumentIndexingError("Embedding provider returned mismatched vector count")

        points: list[qdrant_models.PointStruct] = []
        for chunk, vector in zip(chunks, embeddings, strict=True):
            payload = {
                "chunk_id": str(chunk.id),
                "document_id": str(document.id),
                "project_id": str(document.project_id),
                "chunk_index": chunk.chunk_index,
                "source_filename": document.original_name,
                "char_start": chunk.char_start,
                "char_end": chunk.char_end,
                "mime_type": document.mime_type,
                "embedding_model": embedding_provider.model_name,
            }
            points.append(
                qdrant_models.PointStruct(
                    id=str(chunk.id),
                    vector=vector,
                    payload=payload,
                )
            )

        index_service.upsert_chunk_vectors(points)

        document.status = DocumentStatus.indexed
        document.indexed_at = datetime.now(UTC)
        document.is_indexing = False
        document.indexing_error = None
        db.commit()
    except Exception as exc:
        document.status = previous_status
        document.is_indexing = False
        document.indexing_error = str(exc)
        db.commit()


def index_document_task(document_id: UUID, reindex: bool = False) -> None:
    db = SessionLocal()
    try:
        index_document(document_id, db, reindex=reindex, already_scheduled=True)
    finally:
        db.close()
