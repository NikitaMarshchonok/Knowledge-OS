"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";
import { Project } from "@/lib/types";
import { ProjectFormModal } from "@/components/project-form-modal";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.listProjects();
      setProjects(response);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load projects");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleCreateProject = async (payload: { name: string; description?: string }) => {
    try {
      setIsSubmitting(true);
      setError(null);
      const created = await api.createProject(payload);
      setProjects((prev) => [created, ...prev]);
      setIsModalOpen(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create project");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="page">
      <section className="card page-header">
        <div>
          <p className="eyebrow">Knowledge Platform</p>
          <h1>Projects</h1>
          <p className="subtle">Create and manage document knowledge spaces.</p>
        </div>
        <button className="button-primary" onClick={() => setIsModalOpen(true)}>
          New project
        </button>
      </section>

      {error ? <p className="error-banner">{error}</p> : null}

      <section className="card">
        {isLoading ? (
          <p className="subtle">Loading projects...</p>
        ) : projects.length === 0 ? (
          <p className="subtle">No projects found. Create your first project.</p>
        ) : (
          <div className="project-grid">
            {projects.map((project) => (
              <Link key={project.id} href={`/projects/${project.id}`} className="project-card">
                <h3>{project.name}</h3>
                <p className="subtle">{project.description || "No description"}</p>
                <span className="subtle">Updated {new Date(project.updated_at).toLocaleDateString()}</span>
              </Link>
            ))}
          </div>
        )}
      </section>

      <ProjectFormModal
        open={isModalOpen}
        isSubmitting={isSubmitting}
        onSubmit={handleCreateProject}
        onClose={() => setIsModalOpen(false)}
      />
    </main>
  );
}
