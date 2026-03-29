import { DocumentRecord, Project, ProjectDetail } from "@/lib/types";

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
