from datetime import datetime, UTC
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import Document, DocumentChunk, DocumentStatus
from app.services.chunking import chunk_text
from app.services.document_parser import DocumentParserService

settings = get_settings()


def _build_extracted_text_path(document: Document) -> Path:
    storage_path = Path(document.storage_path)
    extracted_dir = storage_path.parent / "processed"
    extracted_dir.mkdir(parents=True, exist_ok=True)
    return extracted_dir / f"{document.id}.txt"


def process_document(document_id: UUID, db: Session) -> None:
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        return

    document.status = DocumentStatus.processing
    document.processing_error = None
    db.commit()
    db.refresh(document)

    try:
        parser_service = DocumentParserService()
        parsed = parser_service.parse_document(document.storage_path, document.mime_type)

        extracted_text_path = _build_extracted_text_path(document)
        extracted_text_path.write_text(parsed.text, encoding="utf-8")

        db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()

        chunks = chunk_text(
            parsed.text,
            chunk_size=settings.default_chunk_size,
            chunk_overlap=settings.default_chunk_overlap,
        )

        db.add_all(
            [
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    char_start=chunk.char_start,
                    char_end=chunk.char_end,
                    token_estimate=chunk.token_estimate,
                )
                for chunk in chunks
            ]
        )

        document.extracted_text_path = str(extracted_text_path)
        document.chunk_count = len(chunks)
        document.page_count = parsed.page_count
        document.processed_at = datetime.now(UTC)
        document.status = DocumentStatus.processed
        document.processing_error = None
        document.is_indexing = False
        document.indexing_error = None
        document.indexed_at = None
        db.commit()
    except Exception as exc:
        document.status = DocumentStatus.failed
        document.processing_error = str(exc)
        db.commit()


def process_document_task(document_id: UUID) -> None:
    db = SessionLocal()
    try:
        process_document(document_id, db)
    finally:
        db.close()
