"use client";

import { FormEvent, useState } from "react";

interface ProjectFormModalProps {
  open: boolean;
  isSubmitting: boolean;
  onSubmit: (payload: { name: string; description?: string }) => Promise<void>;
  onClose: () => void;
}

export function ProjectFormModal({ open, isSubmitting, onSubmit, onClose }: ProjectFormModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  if (!open) {
    return null;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSubmit({
      name,
      description: description.trim() || undefined
    });
    setName("");
    setDescription("");
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-label="Create project">
      <div className="modal-card">
        <h2>Create project</h2>
        <form onSubmit={handleSubmit} className="form-stack">
          <label>
            Name
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Customer Support Knowledge"
              required
            />
          </label>

          <label>
            Description
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Scope and goals for this project"
              rows={4}
            />
          </label>

          <div className="modal-actions">
            <button type="button" className="button-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="button-primary" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
