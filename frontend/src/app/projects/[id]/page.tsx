"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ChangeEvent, FormEvent, useEffect, useState } from "react";

import { DocumentsTable } from "@/components/documents-table";
import { ApiError, api } from "@/lib/api";
import { DocumentRecord, ProjectDetail, SearchResult } from "@/lib/types";

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

  useEffect(() => {
    if (!projectId) {
      return;
    }
    void loadProject(projectId);
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
    </main>
  );
}
