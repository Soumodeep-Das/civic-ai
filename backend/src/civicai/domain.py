from enum import StrEnum


class ComplaintStatus(StrEnum):
    SUBMITTED = "submitted"


class ComplaintNotFound(Exception):
    """No complaint exists with the requested identifier."""
