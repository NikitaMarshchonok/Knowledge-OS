import {
  AskRun,
  AskRunListResponse,
  AskResponse,
  DocumentChunk,
  DocumentIndexStatus,
  DocumentRecord,
  Project,
  ProjectDetail,
  QAMetrics,
  SearchResponse
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.headers || {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    const contentType = response.headers.get("content-type") || "";
    let message = `Request failed with status ${response.status}`;
    if (contentType.includes("application/json")) {
      const json = await response.json();
      message = json.detail || message;
    }
    throw new ApiError(message, response.status);
  }

  return response.json() as Promise<T>;
}

export const api = {
  listProjects: () => request<Project[]>("/projects"),
  createProject: (payload: { name: string; description?: string }) =>
    request<Project>("/projects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }),
  getProject: (projectId: string) => request<ProjectDetail>(`/projects/${projectId}`),
  listDocuments: (projectId: string) => request<DocumentRecord[]>(`/projects/${projectId}/documents`),
  getDocument: (documentId: string) => request<DocumentRecord>(`/documents/${documentId}`),
  getDocumentIndexStatus: (documentId: string) => request<DocumentIndexStatus>(`/documents/${documentId}/index-status`),
  indexDocument: (documentId: string) =>
    request<DocumentIndexStatus>(`/documents/${documentId}/index`, {
      method: "POST"
    }),
  reindexDocument: (documentId: string) =>
    request<DocumentIndexStatus>(`/documents/${documentId}/reindex`, {
      method: "POST"
    }),
  search: (payload: {
    query: string;
    project_id: string;
    top_k?: number;
    document_ids?: string[];
    mime_types?: string[];
    debug?: boolean;
  }) =>
    request<SearchResponse>("/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }),
  ask: (payload: {
    query: string;
    project_id: string;
    top_k?: number;
    document_ids?: string[];
    mime_types?: string[];
    debug?: boolean;
  }) =>
    request<AskResponse>("/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }),
  listAskRuns: (params?: {
    offset?: number;
    limit?: number;
    project_id?: string;
    status?: "success" | "failed" | "insufficient_evidence";
  }) => {
    const search = new URLSearchParams();
    if (params?.offset !== undefined) {
      search.set("offset", String(params.offset));
    }
    if (params?.limit !== undefined) {
      search.set("limit", String(params.limit));
    }
    if (params?.project_id) {
      search.set("project_id", params.project_id);
    }
    if (params?.status) {
      search.set("status", params.status);
    }
    const query = search.toString();
    return request<AskRunListResponse>(`/ask-runs${query ? `?${query}` : ""}`);
  },
  getAskRun: (askRunId: string) => request<AskRun>(`/ask-runs/${askRunId}`),
  submitAskRunFeedback: (askRunId: string, payload: { rating: "positive" | "negative"; comment?: string }) =>
    request(`/ask-runs/${askRunId}/feedback`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }),
  getQAMetrics: (projectId?: string) =>
    request<QAMetrics>(`/metrics/qa${projectId ? `?project_id=${encodeURIComponent(projectId)}` : ""}`),
  listDocumentChunks: (documentId: string, params?: { offset?: number; limit?: number }) => {
    const search = new URLSearchParams();
    if (params?.offset !== undefined) {
      search.set("offset", String(params.offset));
    }
    if (params?.limit !== undefined) {
      search.set("limit", String(params.limit));
    }
    const query = search.toString();
    return request<DocumentChunk[]>(`/documents/${documentId}/chunks${query ? `?${query}` : ""}`);
  },
  uploadDocument: async (projectId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    return request<DocumentRecord>(`/projects/${projectId}/documents/upload`, {
      method: "POST",
      body: formData
    });
  }
};

export { ApiError };
