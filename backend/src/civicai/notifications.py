from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from civicai.emailing import EmailService, OutboundEmail
from civicai.models import CitizenAccount, Complaint


LOGGER = logging.getLogger("civicai.notifications")

STATUS_LABELS = {
    "submitted": "Submitted",
    "under_review": "Under review",
    "in_progress": "In progress",
    "resolved": "Resolved",
    "rejected": "Closed after review",
}

STATUS_EXPLANATIONS = {
    "under_review": "The municipal team is reviewing the information in your report.",
    "in_progress": "The municipal team has marked work on your report as in progress.",
    "resolved": "The municipal team has marked your report as resolved.",
    "rejected": "The municipal team has closed your report after review. Sign in to view its current status.",
}


def _active_owner(session: Session, complaint: Complaint) -> CitizenAccount | None:
    if complaint.citizen_account_id is None:
        return None
    account = session.get(CitizenAccount, complaint.citizen_account_id)
    if account is None or account.state != "active":
        return None
    return account


def _send_safely(
    email_service: EmailService,
    message: OutboundEmail,
    *,
    complaint: Complaint,
    event: str,
) -> bool:
    try:
        email_service.send(message)
    except Exception:
        # Never expose the address, complaint content or provider response in normal logs.
        # Email is secondary to the already-committed complaint workflow.
        LOGGER.warning(
            "Citizen complaint notification could not be submitted to the email provider",
            extra={"complaint_id": str(complaint.complaint_id), "notification_event": event},
        )
        return False
    return True


def notify_complaint_received(
    session: Session,
    complaint: Complaint,
    email_service: EmailService,
    public_base_url: str,
) -> bool:
    account = _active_owner(session, complaint)
    if account is None:
        return False
    reference = str(complaint.complaint_id)
    link = f"{public_base_url.rstrip('/')}/complaints/{reference}"
    return _send_safely(
        email_service,
        OutboundEmail(
            recipient=account.email,
            subject=f"CivicAI received complaint {reference[:8]}",
            text=(
                f"Dear {account.display_name},\n\n"
                "We have received your civic complaint.\n\n"
                f"Reference: {reference}\n"
                "Status: Submitted\n\n"
                "You can review its latest status by signing in to CivicAI:\n"
                f"{link}\n\n"
                "We will email you when the municipal team changes its status. "
                "This message does not include your photo, location or complaint details for privacy.\n\n"
                "Regards,\nCivicAI"
            ),
        ),
        complaint=complaint,
        event="complaint_received",
    )


def notify_complaint_status_changed(
    session: Session,
    complaint: Complaint,
    email_service: EmailService,
    public_base_url: str,
) -> bool:
    account = _active_owner(session, complaint)
    if account is None:
        return False
    reference = str(complaint.complaint_id)
    label = STATUS_LABELS[complaint.status]
    explanation = STATUS_EXPLANATIONS.get(
        complaint.status, "The municipal team has updated your report."
    )
    link = f"{public_base_url.rstrip('/')}/complaints/{reference}"
    return _send_safely(
        email_service,
        OutboundEmail(
            recipient=account.email,
            subject=f"CivicAI complaint {reference[:8]} is now {label}",
            text=(
                f"Dear {account.display_name},\n\n"
                f"Your civic complaint is now {label}.\n\n"
                f"Reference: {reference}\n"
                f"{explanation}\n\n"
                "View the latest status and citizen-safe history by signing in:\n"
                f"{link}\n\n"
                "This message does not include internal municipal notes, your photo, location or "
                "complaint details for privacy.\n\n"
                "Regards,\nCivicAI"
            ),
        ),
        complaint=complaint,
        event=f"status_changed:{complaint.status}",
    )
