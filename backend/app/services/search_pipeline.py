from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Document, DocumentChunk, Project
from app.schemas.search import SearchDebugInfo, SearchRequest, SearchResponse, SearchResult
from app.services.embeddings.factory import get_embedding_provider
from app.services.reranking.factory import get_reranker
from app.services.reranking.base import SearchCandidate
from app.services.vector_store.qdrant_service import QdrantIndexService


class SearchPipelineError(Exception):
    pass


class SearchPipelineService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def search(self, payload: SearchRequest, db: Session) -> SearchResponse:
        query = payload.query.strip()
        if not query:
            raise SearchPipelineError("Query cannot be empty")

        project = db.query(Project).filter(Project.id == payload.project_id).first()
        if project is None:
            raise SearchPipelineError("Project not found")

        if payload.document_ids:
            valid_count = (
                db.query(Document)
                .filter(Document.project_id == payload.project_id, Document.id.in_(payload.document_ids))
                .count()
            )
            if valid_count != len(payload.document_ids):
                raise SearchPipelineError("One or more document_ids do not belong to the project")

        embedding_provider = get_embedding_provider()
        query_vector = embedding_provider.embed_texts([query])[0]

        candidate_limit = payload.top_k
        if self.settings.reranking_enabled:
            candidate_limit = max(payload.top_k, self.settings.rerank_top_n)

        index_service = QdrantIndexService(vector_size=embedding_provider.dimension)
        index_service.ensure_collection()

        hits = index_service.search_chunks(
            query_vector=query_vector,
            limit=candidate_limit,
            project_id=payload.project_id,
            document_ids=payload.document_ids,
            mime_types=payload.mime_types,
        )

        candidates = self._enrich_hits(hits=hits, db=db)
        if not candidates:
            return SearchResponse(query=query, top_k=payload.top_k, total_results=0, results=[])

        pre_rerank_order = [candidate.chunk_id for candidate in candidates]

        if self.settings.reranking_enabled:
            reranker = get_reranker()
            reranked = reranker.rerank(query=query, candidates=candidates, top_k=payload.top_k)
            post_rerank_order = [item.candidate.chunk_id for item in reranked]
            final_results = [
                SearchResult(
                    chunk_id=item.candidate.chunk_id,
                    document_id=item.candidate.document_id,
                    source_filename=item.candidate.source_filename,
                    chunk_index=item.candidate.chunk_index,
                    content=item.candidate.content,
                    original_vector_score=item.candidate.original_vector_score,
                    rerank_score=item.rerank_score,
                    final_rank=index + 1,
                    char_start=item.candidate.char_start,
                    char_end=item.candidate.char_end,
                    mime_type=item.candidate.mime_type,
                )
                for index, item in enumerate(reranked)
            ]
        else:
            sliced = candidates[: payload.top_k]
            post_rerank_order = [candidate.chunk_id for candidate in sliced]
            final_results = [
                SearchResult(
                    chunk_id=candidate.chunk_id,
                    document_id=candidate.document_id,
                    source_filename=candidate.source_filename,
                    chunk_index=candidate.chunk_index,
                    content=candidate.content,
                    original_vector_score=candidate.original_vector_score,
                    rerank_score=None,
                    final_rank=index + 1,
                    char_start=candidate.char_start,
                    char_end=candidate.char_end,
                    mime_type=candidate.mime_type,
                )
                for index, candidate in enumerate(sliced)
            ]

        debug_info = None
        if payload.debug:
            debug_info = SearchDebugInfo(
                pre_rerank_chunk_ids=pre_rerank_order,
                post_rerank_chunk_ids=post_rerank_order,
            )

        return SearchResponse(
            query=query,
            top_k=payload.top_k,
            total_results=len(final_results),
            results=final_results,
            debug=debug_info,
        )

    def _enrich_hits(self, hits, db: Session) -> list[SearchCandidate]:
        ordered_chunk_ids: list[UUID] = []
        vector_score_map: dict[UUID, float] = {}

        for hit in hits:
            chunk_id_raw = (hit.payload or {}).get("chunk_id")
            if not chunk_id_raw:
                continue
            try:
                chunk_id = UUID(str(chunk_id_raw))
            except ValueError:
                continue

            ordered_chunk_ids.append(chunk_id)
            vector_score_map[chunk_id] = float(hit.score or 0.0)

        if not ordered_chunk_ids:
            return []

        rows = (
            db.query(DocumentChunk, Document)
            .join(Document, Document.id == DocumentChunk.document_id)
            .filter(DocumentChunk.id.in_(ordered_chunk_ids))
            .all()
        )
        row_map = {chunk.id: (chunk, document) for chunk, document in rows}

        enriched: list[SearchCandidate] = []
        for chunk_id in ordered_chunk_ids:
            row = row_map.get(chunk_id)
            if row is None:
                continue
            chunk, document = row
            enriched.append(
                SearchCandidate(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    source_filename=document.original_name,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    original_vector_score=vector_score_map[chunk_id],
                    char_start=chunk.char_start,
                    char_end=chunk.char_end,
                    mime_type=document.mime_type,
                )
            )

        return enriched
