from enum import StrEnum


class ComplaintStatus(StrEnum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


ALLOWED_STATUS_TRANSITIONS: dict[ComplaintStatus, frozenset[ComplaintStatus]] = {
    ComplaintStatus.SUBMITTED: frozenset({ComplaintStatus.UNDER_REVIEW, ComplaintStatus.REJECTED}),
    ComplaintStatus.UNDER_REVIEW: frozenset({ComplaintStatus.IN_PROGRESS, ComplaintStatus.REJECTED}),
    ComplaintStatus.IN_PROGRESS: frozenset({ComplaintStatus.UNDER_REVIEW, ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED}),
    ComplaintStatus.RESOLVED: frozenset({ComplaintStatus.UNDER_REVIEW}),
    ComplaintStatus.REJECTED: frozenset({ComplaintStatus.UNDER_REVIEW}),
}


class LocationPrecision(StrEnum):
    EXACT = "exact"
    APPROXIMATE = "approximate"
    BROAD = "broad"


class LocationSource(StrEnum):
    SEARCH = "search"
    DEVICE = "device"
    MAP = "map"


class MunicipalRole(StrEnum):
    OPERATOR = "municipal_operator"
    ADMIN = "municipal_admin"


class ComplaintNotFound(Exception):
    """No complaint exists with the requested identifier."""


class InvalidStatusTransition(Exception):
    def __init__(self, current: ComplaintStatus, requested: ComplaintStatus):
        self.current = current
        self.requested = requested


class StaleComplaintUpdate(Exception):
    """The complaint changed after the operator loaded it."""


def transition_is_allowed(current: ComplaintStatus, requested: ComplaintStatus) -> bool:
    return requested == current or requested in ALLOWED_STATUS_TRANSITIONS[current]
