export type DocumentStatus = "uploaded" | "processing" | "indexed" | "failed";

export interface Project {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentRecord {
  id: string;
  project_id: string;
  filename: string;
  original_name: string;
  mime_type: string;
  size_bytes: number;
  storage_path: string;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends Project {
  documents: DocumentRecord[];
}
