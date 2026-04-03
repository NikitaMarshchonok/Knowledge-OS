import re
import time
from typing import Iterable
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import AskRunStatus
from app.schemas.ask import AskDebugInfo, AskRequest, AskResponse, Citation
from app.schemas.search import SearchRequest, SearchResult
from app.services.embeddings.factory import get_embedding_provider
from app.services.evaluation import EvaluationError, EvaluationService
from app.services.llm.factory import get_llm_provider
from app.services.search_pipeline import SearchPipelineError, SearchPipelineService

SYSTEM_PROMPT = """You are a grounded enterprise knowledge assistant.
Answer ONLY from the provided context chunks.
Rules:
- Do not invent facts not present in context.
- If context is insufficient, say so clearly.
- Keep the answer concise and practical.
- Add inline citations like [C1], [C2] for claims tied to context chunks."""


class AnswerGenerationError(Exception):
    pass


class AnswerGenerationService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.search_service = SearchPipelineService()
        self.evaluation_service = EvaluationService()

    def ask(self, payload: AskRequest, db: Session) -> AskResponse:
        query = payload.query.strip()
        if not query:
            raise AnswerGenerationError("Query cannot be empty")

        started_at = time.perf_counter()
        embedding_provider = get_embedding_provider()
        try:
            ask_run = self.evaluation_service.create_ask_run(
                db,
                project_id=payload.project_id,
                query=query,
                top_k=payload.top_k,
                embedding_model=embedding_provider.model_name,
                rerank_model=self.settings.rerank_model_name if self.settings.reranking_enabled else None,
            )
        except EvaluationError as exc:
            raise AnswerGenerationError(str(exc)) from exc

        search_payload = SearchRequest(
            query=query,
            project_id=payload.project_id,
            top_k=payload.top_k,
            document_ids=payload.document_ids,
            mime_types=payload.mime_types,
            debug=True,
        )

        try:
            search_response = self.search_service.search(search_payload, db)
        except SearchPipelineError as exc:
            self._finalize_run(
                db=db,
                ask_run_id=ask_run.id,
                status=AskRunStatus.failed,
                answer=None,
                llm_model=None,
                error_message=str(exc),
                started_at=started_at,
                retrieved_chunk_ids=None,
                reranked_chunk_ids=None,
                cited_chunk_ids=[],
                citations=[],
            )
            raise AnswerGenerationError(str(exc)) from exc

        retrieved_chunk_ids = [str(chunk_id) for chunk_id in (search_response.debug.pre_rerank_chunk_ids if search_response.debug else [])]
        reranked_chunk_ids = [str(chunk_id) for chunk_id in (search_response.debug.post_rerank_chunk_ids if search_response.debug else [])]

        if not search_response.results:
            answer = "Insufficient evidence in indexed documents to answer this question."
            self._finalize_run(
                db=db,
                ask_run_id=ask_run.id,
                status=AskRunStatus.insufficient_evidence,
                answer=answer,
                llm_model=None,
                error_message=None,
                started_at=started_at,
                retrieved_chunk_ids=retrieved_chunk_ids,
                reranked_chunk_ids=reranked_chunk_ids,
                cited_chunk_ids=[],
                citations=[],
            )
            return AskResponse(
                ask_run_id=ask_run.id,
                answer=answer,
                citations=[],
                supporting_results=[],
                debug=self._build_debug(search_response.results) if payload.debug else None,
            )

        context_results = search_response.results[: payload.top_k]
        llm = get_llm_provider()
        user_prompt = self._build_user_prompt(query, context_results)
        try:
            answer = llm.generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=self.settings.llm_temperature,
            )
        except Exception as exc:
            self._finalize_run(
                db=db,
                ask_run_id=ask_run.id,
                status=AskRunStatus.failed,
                answer=None,
                llm_model=llm.model_name,
                error_message=f"Failed to generate answer: {exc}",
                started_at=started_at,
                retrieved_chunk_ids=retrieved_chunk_ids,
                reranked_chunk_ids=reranked_chunk_ids,
                cited_chunk_ids=[],
                citations=[],
            )
            raise AnswerGenerationError(f"Failed to generate answer: {exc}") from exc

        citations = self._collect_citations(answer, context_results)
        cited_chunk_ids = [str(citation.chunk_id) for citation in citations]
        self._finalize_run(
            db=db,
            ask_run_id=ask_run.id,
            status=AskRunStatus.success,
            answer=answer,
            llm_model=llm.model_name,
            error_message=None,
            started_at=started_at,
            retrieved_chunk_ids=retrieved_chunk_ids,
            reranked_chunk_ids=reranked_chunk_ids,
            cited_chunk_ids=cited_chunk_ids,
            citations=citations,
        )

        return AskResponse(
            ask_run_id=ask_run.id,
            answer=answer,
            citations=citations,
            supporting_results=context_results,
            debug=self._build_debug(context_results, llm.model_name) if payload.debug else None,
        )

    def _build_user_prompt(self, query: str, results: list[SearchResult]) -> str:
        context_lines = []
        for idx, result in enumerate(results, start=1):
            context_lines.append(
                f"[C{idx}] source={result.source_filename} "
                f"chunk_index={result.chunk_index} "
                f"char_range={result.char_start}-{result.char_end}\n"
                f"{result.content}"
            )

        context_block = "\n\n".join(context_lines)
        return (
            f"Question:\n{query}\n\n"
            "Context chunks:\n"
            f"{context_block}\n\n"
            "Write a concise grounded answer with inline citations [C#]."
        )

    def _collect_citations(self, answer: str, results: list[SearchResult]) -> list[Citation]:
        indexes = self._extract_citation_indexes(answer)
        if not indexes:
            indexes = list(range(1, min(3, len(results)) + 1))

        citations: list[Citation] = []
        for idx in indexes:
            result_idx = idx - 1
            if result_idx < 0 or result_idx >= len(results):
                continue
            result = results[result_idx]
            citations.append(
                Citation(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    source_filename=result.source_filename,
                    chunk_index=result.chunk_index,
                    char_start=result.char_start,
                    char_end=result.char_end,
                    snippet=self._snippet(result.content),
                )
            )
        return citations

    def _extract_citation_indexes(self, answer: str) -> list[int]:
        matches = re.findall(r"\[C(\d+)\]", answer)
        unique: list[int] = []
        seen: set[int] = set()
        for match in matches:
            index = int(match)
            if index not in seen:
                seen.add(index)
                unique.append(index)
        return unique

    def _snippet(self, content: str, max_len: int = 220) -> str:
        clean = " ".join(content.split())
        if len(clean) <= max_len:
            return clean
        return f"{clean[:max_len].rstrip()}..."

    def _build_debug(self, results: Iterable[SearchResult], model_name: str | None = None) -> AskDebugInfo:
        return AskDebugInfo(
            context_chunk_ids=[result.chunk_id for result in results],
            llm_model=model_name or self.settings.llm_model_name,
        )

    def _finalize_run(
        self,
        *,
        db: Session,
        ask_run_id: UUID,
        status: AskRunStatus,
        answer: str | None,
        llm_model: str | None,
        error_message: str | None,
        started_at: float,
        retrieved_chunk_ids: list[str] | None,
        reranked_chunk_ids: list[str] | None,
        cited_chunk_ids: list[str] | None,
        citations: list[Citation],
    ) -> None:
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        ask_run = self.evaluation_service.get_ask_run(db, ask_run_id=ask_run_id)
        self.evaluation_service.finalize_ask_run(
            db=db,
            ask_run=ask_run,
            status=status,
            answer=answer,
            llm_model=llm_model,
            latency_ms=elapsed_ms,
            error_message=error_message,
            retrieved_chunk_ids=retrieved_chunk_ids,
            reranked_chunk_ids=reranked_chunk_ids,
            cited_chunk_ids=cited_chunk_ids,
            citations=citations,
        )
