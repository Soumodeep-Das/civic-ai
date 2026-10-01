import { ComplaintStatus } from "../api/complaints";

export const statusLabels: Record<ComplaintStatus, string> = { submitted: "Submitted", under_review: "Under review", in_progress: "In progress", resolved: "Resolved", rejected: "Rejected" };
export function StatusBadge({ status }: { status: ComplaintStatus }) { return <span className={`status-badge status-${status}`}><span className="status-marker" aria-hidden="true" />{statusLabels[status]}</span>; }
