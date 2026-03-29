import { DocumentRecord } from "@/lib/types";
import { StatusBadge } from "@/components/status-badge";

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

export function DocumentsTable({ documents }: { documents: DocumentRecord[] }) {
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
            <th>Uploaded</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((document) => (
            <tr key={document.id}>
              <td>{document.original_name}</td>
              <td>{document.mime_type}</td>
              <td>{formatBytes(document.size_bytes)}</td>
              <td>
                <StatusBadge status={document.status} />
              </td>
              <td>{new Date(document.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
