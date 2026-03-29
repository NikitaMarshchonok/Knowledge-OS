"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ChangeEvent, useEffect, useState } from "react";

import { DocumentsTable } from "@/components/documents-table";
import { ApiError, api } from "@/lib/api";
import { ProjectDetail } from "@/lib/types";

export default function ProjectDetailsPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadProject = async (id: string) => {
    try {
      setIsLoading(true);
      setError(null);
      const [projectResponse, documentsResponse] = await Promise.all([api.getProject(id), api.listDocuments(id)]);
      setProject({ ...projectResponse, documents: documentsResponse });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load project");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!projectId) {
      return;
    }
    loadProject(projectId);
  }, [projectId]);

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !projectId) {
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      const document = await api.uploadDocument(projectId, file);
      setProject((prev) => {
        if (!prev) {
          return prev;
        }
        return {
          ...prev,
          documents: [document, ...prev.documents]
        };
      });
      event.target.value = "";
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to upload document");
    } finally {
      setIsUploading(false);
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
          <p className="subtle">Files are stored locally for now and tracked with lifecycle statuses.</p>
        </div>
        <label className="upload-input">
          <input type="file" onChange={handleFileChange} disabled={isUploading || isLoading} />
        </label>
        {isUploading ? <p className="subtle">Uploading document...</p> : null}
      </section>

      <section className="card">
        <h2>Documents</h2>
        {isLoading ? <p className="subtle">Loading project details...</p> : <DocumentsTable documents={project?.documents || []} />}
      </section>
    </main>
  );
}
