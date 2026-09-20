from enum import StrEnum


class ComplaintStatus(StrEnum):
    SUBMITTED = "submitted"


class LocationPrecision(StrEnum):
    EXACT = "exact"
    APPROXIMATE = "approximate"
    BROAD = "broad"


class LocationSource(StrEnum):
    SEARCH = "search"
    DEVICE = "device"
    MAP = "map"


class ComplaintNotFound(Exception):
    """No complaint exists with the requested identifier."""
