"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ChangeEvent, FormEvent, useEffect, useState } from "react";

import { DocumentsTable } from "@/components/documents-table";
import { ApiError, api } from "@/lib/api";
import { AskResponse, AskRun, DocumentRecord, ProjectDetail, QAMetrics, SearchResult } from "@/lib/types";

function hasInFlightDocuments(documents: DocumentRecord[]): boolean {
  return documents.some(
    (document) => document.status === "uploaded" || document.status === "processing" || document.is_indexing
  );
}

export default function ProjectDetailsPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeIndexDocumentId, setActiveIndexDocumentId] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [askQuery, setAskQuery] = useState("");
  const [askResponse, setAskResponse] = useState<AskResponse | null>(null);
  const [isAsking, setIsAsking] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);
  const [askRuns, setAskRuns] = useState<AskRun[]>([]);
  const [isLoadingAskRuns, setIsLoadingAskRuns] = useState(false);
  const [selectedAskRun, setSelectedAskRun] = useState<AskRun | null>(null);
  const [isSubmittingFeedbackId, setIsSubmittingFeedbackId] = useState<string | null>(null);
  const [qaMetrics, setQaMetrics] = useState<QAMetrics | null>(null);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);

  const [error, setError] = useState<string | null>(null);

  const documents = project?.documents || [];
  const shouldPoll = hasInFlightDocuments(documents);

  const loadProject = async (id: string, options?: { silent?: boolean }) => {
    const silent = options?.silent ?? false;
    try {
      if (silent) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }
      setError(null);
      const [projectResponse, documentsResponse] = await Promise.all([api.getProject(id), api.listDocuments(id)]);
      setProject({ ...projectResponse, documents: documentsResponse });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load project");
    } finally {
      if (silent) {
        setIsRefreshing(false);
      } else {
        setIsLoading(false);
      }
    }
  };

  const loadEvaluation = async (id: string) => {
    try {
      setIsLoadingAskRuns(true);
      setEvaluationError(null);
      const [runsResponse, metricsResponse] = await Promise.all([
        api.listAskRuns({ project_id: id, limit: 10 }),
        api.getQAMetrics(id)
      ]);
      setAskRuns(runsResponse.items);
      setQaMetrics(metricsResponse);
    } catch (err) {
      setEvaluationError(err instanceof ApiError ? err.message : "Failed to load evaluation data");
    } finally {
      setIsLoadingAskRuns(false);
    }
  };

  const openAskRunDetails = async (askRunId: string) => {
    try {
      setEvaluationError(null);
      const details = await api.getAskRun(askRunId);
      setSelectedAskRun(details);
    } catch (err) {
      setEvaluationError(err instanceof ApiError ? err.message : "Failed to load ask run details");
    }
  };

  const submitFeedback = async (askRunId: string, rating: "positive" | "negative") => {
    try {
      setIsSubmittingFeedbackId(askRunId);
      setEvaluationError(null);
      await api.submitAskRunFeedback(askRunId, { rating });
      if (projectId) {
        await loadEvaluation(projectId);
      }
      if (selectedAskRun?.id === askRunId) {
        const details = await api.getAskRun(askRunId);
        setSelectedAskRun(details);
      }
    } catch (err) {
      setEvaluationError(err instanceof ApiError ? err.message : "Failed to submit feedback");
    } finally {
      setIsSubmittingFeedbackId(null);
    }
  };

  useEffect(() => {
    if (!projectId) {
      return;
    }
    void loadProject(projectId);
    void loadEvaluation(projectId);
  }, [projectId]);

  useEffect(() => {
    if (!projectId || !shouldPoll) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void loadProject(projectId, { silent: true });
    }, 3000);

    return () => window.clearInterval(intervalId);
  }, [projectId, shouldPoll]);

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !projectId) {
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      await api.uploadDocument(projectId, file);
      await loadProject(projectId, { silent: true });
      event.target.value = "";
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to upload document");
    } finally {
      setIsUploading(false);
    }
  };

  const handleIndexDocument = async (documentId: string) => {
    try {
      setActiveIndexDocumentId(documentId);
      setError(null);
      await api.indexDocument(documentId);
      await loadProject(projectId, { silent: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to start indexing");
    } finally {
      setActiveIndexDocumentId(null);
    }
  };

  const handleReindexDocument = async (documentId: string) => {
    try {
      setActiveIndexDocumentId(documentId);
      setError(null);
      await api.reindexDocument(documentId);
      await loadProject(projectId, { silent: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to start reindexing");
    } finally {
      setActiveIndexDocumentId(null);
    }
  };

  const handleSearch = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!projectId || !searchQuery.trim()) {
      return;
    }

    try {
      setIsSearching(true);
      setSearchError(null);
      const response = await api.search({
        query: searchQuery.trim(),
        project_id: projectId,
        top_k: 8
      });
      setSearchResults(response.results);
    } catch (err) {
      setSearchError(err instanceof ApiError ? err.message : "Search request failed");
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleAsk = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!projectId || !askQuery.trim()) {
      return;
    }

    try {
      setIsAsking(true);
      setAskError(null);
      const response = await api.ask({
        query: askQuery.trim(),
        project_id: projectId,
        top_k: 6
      });
      setAskResponse(response);
      await loadEvaluation(projectId);
    } catch (err) {
      setAskError(err instanceof ApiError ? err.message : "Ask request failed");
      setAskResponse(null);
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <main className="page">
      <section className="card page-header">
        <div>
          <Link href="/projects" className="back-link">
            ← Back to projects
          </Link>
          <h1>{project?.name || "Project"}</h1>
          <p className="subtle">{project?.description || "No project description yet."}</p>
        </div>
      </section>

      {error ? <p className="error-banner">{error}</p> : null}

      <section className="card upload-card">
        <div>
          <h2>Upload document</h2>
          <p className="subtle">
            Files are parsed/chunked after upload, then manually indexed into Qdrant for future retrieval.
          </p>
        </div>
        <label className="upload-input">
          <input type="file" onChange={handleFileChange} disabled={isUploading || isLoading} />
        </label>
        <div className="inline-actions">
          <button
            type="button"
            className="button-secondary"
            onClick={() => projectId && void loadProject(projectId, { silent: true })}
            disabled={isLoading || isUploading || isRefreshing}
          >
            {isRefreshing ? "Refreshing..." : "Refresh status"}
          </button>
          {shouldPoll ? (
            <span className="subtle">Auto-refresh is active while processing or indexing tasks are running.</span>
          ) : null}
        </div>
        {isUploading ? <p className="subtle">Uploading document...</p> : null}
      </section>

      <section className="card">
        <h2>Documents</h2>
        {isLoading ? (
          <p className="subtle">Loading project details...</p>
        ) : (
          <DocumentsTable
            documents={documents}
            activeIndexDocumentId={activeIndexDocumentId}
            onIndexDocument={handleIndexDocument}
            onReindexDocument={handleReindexDocument}
          />
        )}
      </section>

      <section className="card search-panel">
        <h2>Retrieval + Reranking v1</h2>
        <p className="subtle">Vector candidates are reranked before returning final top-k results.</p>

        <form className="search-form" onSubmit={handleSearch}>
          <input
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search indexed chunks in this project"
          />
          <button type="submit" className="button-primary" disabled={isSearching || !searchQuery.trim()}>
            {isSearching ? "Searching..." : "Search"}
          </button>
        </form>

        {searchError ? <p className="error-banner">{searchError}</p> : null}

        <div className="search-results">
          {!isSearching && searchResults.length === 0 ? (
            <p className="subtle">No search results yet. Index documents and run a query.</p>
          ) : null}

          {searchResults.map((result) => (
            <article key={result.chunk_id} className="search-result-card">
              <div className="search-result-head">
                <strong>{result.source_filename}</strong>
                <span className="subtle">#{result.final_rank}</span>
              </div>
              <p className="subtle">
                vector {result.original_vector_score.toFixed(4)} | rerank{" "}
                {result.rerank_score === null ? "n/a" : result.rerank_score.toFixed(4)}
              </p>
              <p className="subtle">
                chunk #{result.chunk_index} | chars {result.char_start}-{result.char_end} | {result.mime_type}
              </p>
              <p className="search-content">{result.content}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="card search-panel">
        <h2>Ask (Grounded Answer v1)</h2>
        <p className="subtle">Single-turn Q&A generated strictly from reranked retrieval context.</p>

        <form className="search-form" onSubmit={handleAsk}>
          <input
            value={askQuery}
            onChange={(event) => setAskQuery(event.target.value)}
            placeholder="Ask a question about indexed project documents"
          />
          <button type="submit" className="button-primary" disabled={isAsking || !askQuery.trim()}>
            {isAsking ? "Asking..." : "Ask"}
          </button>
        </form>

        {askError ? <p className="error-banner">{askError}</p> : null}

        {askResponse ? (
          <div className="search-results">
            <article className="search-result-card">
              <div className="search-result-head">
                <strong>Answer</strong>
              </div>
              <p className="search-content">{askResponse.answer}</p>
            </article>

            <article className="search-result-card">
              <div className="search-result-head">
                <strong>Citations ({askResponse.citations.length})</strong>
              </div>
              {askResponse.citations.length === 0 ? (
                <p className="subtle">No citation references were emitted by the model for this answer.</p>
              ) : (
                askResponse.citations.map((citation) => (
                  <div key={citation.chunk_id} style={{ marginBottom: "0.75rem" }}>
                    <p className="subtle">
                      {citation.source_filename} | chunk #{citation.chunk_index} | chars {citation.char_start}-
                      {citation.char_end}
                    </p>
                    <p className="search-content">{citation.snippet}</p>
                  </div>
                ))
              )}
            </article>
          </div>
        ) : null}
      </section>

      <section className="card search-panel">
        <h2>Evaluation Layer v1</h2>
        <p className="subtle">Internal ask-run observability, metrics, and feedback capture.</p>
        {evaluationError ? <p className="error-banner">{evaluationError}</p> : null}

        {qaMetrics ? (
          <p className="subtle">
            total {qaMetrics.total_questions} | success {qaMetrics.success_count} | failed {qaMetrics.failed_count} |
            insufficient {qaMetrics.insufficient_evidence_count} | avg latency {qaMetrics.average_latency_ms.toFixed(0)}ms |
            👍 {qaMetrics.positive_feedback_count} | 👎 {qaMetrics.negative_feedback_count}
          </p>
        ) : null}

        {isLoadingAskRuns ? (
          <p className="subtle">Loading ask runs...</p>
        ) : askRuns.length === 0 ? (
          <p className="subtle">No ask runs yet for this project.</p>
        ) : (
          <div className="search-results">
            {askRuns.map((run) => (
              <article key={run.id} className="search-result-card">
                <div className="search-result-head">
                  <strong>{run.query}</strong>
                  <span className="subtle">{run.status}</span>
                </div>
                <p className="subtle">
                  {new Date(run.created_at).toLocaleString()} | latency {run.latency_ms ?? "n/a"}ms | top_k {run.top_k}
                </p>
                <p className="search-content">{(run.answer || run.error_message || "").slice(0, 220)}</p>
                <div className="inline-actions">
                  <button
                    type="button"
                    className="button-secondary"
                    onClick={() => void openAskRunDetails(run.id)}
                    disabled={isSubmittingFeedbackId === run.id}
                  >
                    Details
                  </button>
                  <button
                    type="button"
                    className="button-secondary"
                    onClick={() => void submitFeedback(run.id, "positive")}
                    disabled={isSubmittingFeedbackId === run.id}
                  >
                    👍
                  </button>
                  <button
                    type="button"
                    className="button-secondary"
                    onClick={() => void submitFeedback(run.id, "negative")}
                    disabled={isSubmittingFeedbackId === run.id}
                  >
                    👎
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}

        {selectedAskRun ? (
          <article className="search-result-card" style={{ marginTop: "1rem" }}>
            <div className="search-result-head">
              <strong>Ask Run Details</strong>
              <span className="subtle">{selectedAskRun.id}</span>
            </div>
            <p className="subtle">
              model {selectedAskRun.llm_model || "n/a"} | embedding {selectedAskRun.embedding_model || "n/a"} | rerank{" "}
              {selectedAskRun.rerank_model || "n/a"}
            </p>
            <p className="search-content">{selectedAskRun.answer || selectedAskRun.error_message || "No answer captured."}</p>
            <p className="subtle">
              retrieved {selectedAskRun.retrieved_chunk_ids?.length || 0} | reranked{" "}
              {selectedAskRun.reranked_chunk_ids?.length || 0} | cited {selectedAskRun.cited_chunk_ids?.length || 0}
            </p>
            <div>
              <strong>Citations</strong>
              {selectedAskRun.citations.length === 0 ? (
                <p className="subtle">No citations stored for this run.</p>
              ) : (
                selectedAskRun.citations.map((citation) => (
                  <div key={`${citation.chunk_id}-${citation.chunk_index}`} style={{ marginTop: "0.5rem" }}>
                    <p className="subtle">
                      {citation.source_filename} | chunk #{citation.chunk_index} | chars {citation.char_start}-
                      {citation.char_end}
                    </p>
                    <p className="search-content">{citation.snippet}</p>
                  </div>
                ))
              )}
            </div>
          </article>
        ) : null}
      </section>
    </main>
  );
}
