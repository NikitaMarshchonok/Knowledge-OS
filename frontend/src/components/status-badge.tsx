import { DocumentStatus } from "@/lib/types";

const statusClass: Record<DocumentStatus, string> = {
  uploaded: "status status-uploaded",
  processing: "status status-processing",
  processed: "status status-processed",
  indexed: "status status-indexed",
  failed: "status status-failed"
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  return <span className={statusClass[status]}>{status}</span>;
}
