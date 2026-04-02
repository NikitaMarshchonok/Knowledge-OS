export type DocumentStatus = "uploaded" | "processing" | "processed" | "indexed" | "failed";

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
  processing_error: string | null;
  processed_at: string | null;
  chunk_count: number;
  extracted_text_path: string | null;
  page_count: number | null;
  is_indexing: boolean;
  indexing_error: string | null;
  indexed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentIndexStatus {
  id: string;
  status: DocumentStatus;
  is_indexing: boolean;
  indexing_error: string | null;
  indexed_at: string | null;
  chunk_count: number;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  char_start: number;
  char_end: number;
  token_estimate: number;
  created_at: string;
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  source_filename: string;
  chunk_index: number;
  content: string;
  original_vector_score: number;
  rerank_score: number | null;
  final_rank: number;
  char_start: number;
  char_end: number;
  mime_type: string;
}

export interface SearchDebugInfo {
  pre_rerank_chunk_ids: string[];
  post_rerank_chunk_ids: string[];
}

export interface SearchResponse {
  query: string;
  top_k: number;
  total_results: number;
  results: SearchResult[];
  debug: SearchDebugInfo | null;
}

export interface AskCitation {
  chunk_id: string;
  document_id: string;
  source_filename: string;
  chunk_index: number;
  char_start: number;
  char_end: number;
  snippet: string;
}

export interface AskDebugInfo {
  context_chunk_ids: string[];
  llm_model: string;
}

export interface AskResponse {
  answer: string;
  citations: AskCitation[];
  supporting_results: SearchResult[];
  debug: AskDebugInfo | null;
}

export interface ProjectDetail extends Project {
  documents: DocumentRecord[];
}
