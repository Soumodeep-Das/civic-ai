from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_serializer, field_validator, model_validator

from civicai.domain import ComplaintStatus, LocationPrecision, LocationSource

Description = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
LocationLabel = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
LocationDetails = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
SearchQuery = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)]


class ComplaintCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: Description
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False)
    location_label: LocationLabel | None = None
    location_precision: LocationPrecision | None = None
    location_details: LocationDetails | None = None
    location_source: LocationSource | None = None
    location_accuracy_m: float | None = Field(default=None, ge=0, le=100_000, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_location_context(self):
        context_present = any((
            self.location_label, self.location_precision, self.location_details,
            self.location_source, self.location_accuracy_m is not None,
        ))
        if context_present and (
            self.latitude is None
            or self.longitude is None
            or self.location_label is None
            or self.location_precision is None
        ):
            raise ValueError("Location context requires coordinates, label and precision")
        if self.location_accuracy_m is not None and self.location_source != LocationSource.DEVICE:
            raise ValueError("Location accuracy is valid only for device locations")
        return self


class ComplaintRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    complaint_id: UUID
    image_ref: str | None
    description: str
    latitude: float | None
    longitude: float | None
    location_label: str | None
    location_precision: LocationPrecision | None
    location_details: str | None
    location_source: LocationSource | None
    location_accuracy_m: float | None
    status: ComplaintStatus
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_utc(self, value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


OperatorNote = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class ComplaintStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_status: ComplaintStatus
    expected_updated_at: datetime
    operator_note: OperatorNote | None = None

    @field_validator("expected_updated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("expected_updated_at must include a timezone")
        return value


class ComplaintStatusEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID
    complaint_id: UUID
    event_type: Literal["created", "status_changed"]
    previous_status: ComplaintStatus | None
    new_status: ComplaintStatus
    operator_note: str | None
    actor_id: UUID | None
    occurred_at: datetime

    @field_serializer("occurred_at")
    def serialize_utc(self, value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class AdminComplaintDetail(ComplaintRead):
    history: list[ComplaintStatusEventRead]


class AdminComplaintPage(BaseModel):
    items: list[ComplaintRead]
    page: int
    page_size: int
    total: int
    total_pages: int


class DashboardStatistics(BaseModel):
    total: int
    submitted: int
    under_review: int
    in_progress: int
    resolved: int
    rejected: int
    submitted_last_7_days: int
    with_photo: int
    with_location: int


class LocationSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: SearchQuery


class LocationSearchResult(BaseModel):
    provider_id: str
    label: str
    latitude: float
    longitude: float
    precision: LocationPrecision


class LocationReverseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)


class LocationCapabilities(BaseModel):
    autocomplete: bool
    reverse_geocoding: bool = True
