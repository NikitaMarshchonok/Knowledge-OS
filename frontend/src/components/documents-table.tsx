import { DocumentRecord } from "@/lib/types";
import { StatusBadge } from "@/components/status-badge";

interface DocumentsTableProps {
  documents: DocumentRecord[];
  activeIndexDocumentId: string | null;
  onIndexDocument: (documentId: string) => Promise<void>;
  onReindexDocument: (documentId: string) => Promise<void>;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  const kb = bytes / 1024;
  if (kb < 1024) {
    return `${kb.toFixed(1)} KB`;
  }
  return `${(kb / 1024).toFixed(1)} MB`;
}

export function DocumentsTable({
  documents,
  activeIndexDocumentId,
  onIndexDocument,
  onReindexDocument
}: DocumentsTableProps) {
  if (documents.length === 0) {
    return <p className="subtle">No documents uploaded yet.</p>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Size</th>
            <th>Status</th>
            <th>Chunks</th>
            <th>Processed</th>
            <th>Indexed</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((document) => {
            const isBusy = document.is_indexing || activeIndexDocumentId === document.id;
            const canIndex = document.status === "processed" && document.chunk_count > 0 && !isBusy;
            const canReindex = document.status === "indexed" && document.chunk_count > 0 && !isBusy;

            return (
              <tr key={document.id}>
                <td>
                  <div>{document.original_name}</div>
                  {document.processing_error ? <small className="error-inline">{document.processing_error}</small> : null}
                  {document.indexing_error ? <small className="error-inline">{document.indexing_error}</small> : null}
                </td>
                <td>{document.mime_type}</td>
                <td>{formatBytes(document.size_bytes)}</td>
                <td>
                  <StatusBadge status={document.status} />
                  {document.is_indexing ? <small className="subtle">Indexing in progress...</small> : null}
                </td>
                <td>{document.chunk_count}</td>
                <td>{document.processed_at ? new Date(document.processed_at).toLocaleString() : "-"}</td>
                <td>{document.indexed_at ? new Date(document.indexed_at).toLocaleString() : "-"}</td>
                <td>
                  <div className="table-actions">
                    <button
                      type="button"
                      className="button-secondary button-small"
                      disabled={!canIndex}
                      onClick={() => void onIndexDocument(document.id)}
                    >
                      Index
                    </button>
                    <button
                      type="button"
                      className="button-secondary button-small"
                      disabled={!canReindex}
                      onClick={() => void onReindexDocument(document.id)}
                    >
                      Reindex
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
