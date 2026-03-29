from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk, Project
from app.schemas.search import SearchRequest, SearchResponse, SearchResult
from app.services.embeddings.factory import get_embedding_provider
from app.services.vector_store.qdrant_service import QdrantIndexService


class RetrievalError(Exception):
    pass


class RetrievalService:
    def search(self, payload: SearchRequest, db: Session) -> SearchResponse:
        query = payload.query.strip()
        if not query:
            raise RetrievalError("Query cannot be empty")

        project = db.query(Project).filter(Project.id == payload.project_id).first()
        if project is None:
            raise RetrievalError("Project not found")

        if payload.document_ids:
            valid_count = (
                db.query(Document)
                .filter(Document.project_id == payload.project_id, Document.id.in_(payload.document_ids))
                .count()
            )
            if valid_count != len(payload.document_ids):
                raise RetrievalError("One or more document_ids do not belong to the project")

        embedding_provider = get_embedding_provider()
        query_vector = embedding_provider.embed_texts([query])[0]

        index_service = QdrantIndexService(vector_size=embedding_provider.dimension)
        index_service.ensure_collection()

        hits = index_service.search_chunks(
            query_vector=query_vector,
            limit=payload.top_k,
            project_id=payload.project_id,
            document_ids=payload.document_ids,
            mime_types=payload.mime_types,
        )

        if not hits:
            return SearchResponse(query=query, top_k=payload.top_k, total_results=0, results=[])

        chunk_ids: list[UUID] = []
        for hit in hits:
            chunk_id_raw = (hit.payload or {}).get("chunk_id")
            if not chunk_id_raw:
                continue
            try:
                chunk_ids.append(UUID(str(chunk_id_raw)))
            except ValueError:
                continue

        if not chunk_ids:
            return SearchResponse(query=query, top_k=payload.top_k, total_results=0, results=[])

        chunk_rows = (
            db.query(DocumentChunk, Document)
            .join(Document, Document.id == DocumentChunk.document_id)
            .filter(DocumentChunk.id.in_(chunk_ids))
            .all()
        )
        chunk_map = {row_chunk.id: (row_chunk, row_document) for row_chunk, row_document in chunk_rows}

        results: list[SearchResult] = []
        for hit in hits:
            payload_map = hit.payload or {}
            chunk_id_raw = payload_map.get("chunk_id")
            if not chunk_id_raw:
                continue

            try:
                chunk_id = UUID(str(chunk_id_raw))
            except ValueError:
                continue

            row = chunk_map.get(chunk_id)
            if row is None:
                continue

            chunk_row, document_row = row

            results.append(
                SearchResult(
                    chunk_id=chunk_row.id,
                    document_id=document_row.id,
                    source_filename=str(payload_map.get("source_filename") or document_row.original_name),
                    chunk_index=int(payload_map.get("chunk_index") or chunk_row.chunk_index),
                    content=chunk_row.content,
                    score=float(hit.score or 0.0),
                    char_start=int(payload_map.get("char_start") or chunk_row.char_start),
                    char_end=int(payload_map.get("char_end") or chunk_row.char_end),
                    mime_type=str(payload_map.get("mime_type") or document_row.mime_type),
                )
            )

        return SearchResponse(
            query=query,
            top_k=payload.top_k,
            total_results=len(results),
            results=results,
        )
