from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_serializer, field_validator, model_validator

from civicai.domain import ComplaintStatus, LocationPrecision, LocationSource, MunicipalRole

Description = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
LocationLabel = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
LocationDetails = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
SearchQuery = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)]
DepartmentName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
DepartmentSlug = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, min_length=2, max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
DepartmentDescription = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


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


class DepartmentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    department_id: UUID
    slug: str
    display_name: str
    is_active: bool


class AssigneeSummary(BaseModel):
    user_id: UUID
    username: str
    is_active: bool


class AdminComplaintRead(ComplaintRead):
    department: DepartmentSummary | None = None
    assignee: AssigneeSummary | None = None


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


class ComplaintAssignmentEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_id: UUID
    complaint_id: UUID
    event_type: str
    previous_department_id: UUID | None
    new_department_id: UUID | None
    previous_assignee_user_id: UUID | None
    new_assignee_user_id: UUID | None
    actor_user_id: UUID
    reason: str | None
    occurred_at: datetime

    @field_serializer("occurred_at")
    def serialize_event_time(self, value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class AdminComplaintDetail(AdminComplaintRead):
    history: list[ComplaintStatusEventRead]
    assignment_history: list[ComplaintAssignmentEventRead]


class AdminComplaintPage(BaseModel):
    items: list[AdminComplaintRead]
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


Username = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_lower=True, min_length=3, max_length=64, pattern=r"^[a-z0-9._-]+$"),
]
Password = Annotated[str, StringConstraints(min_length=12, max_length=128)]


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: Username
    password: Annotated[str, StringConstraints(min_length=1, max_length=128)]


class MunicipalUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: UUID
    username: str
    role: MunicipalRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None

    @field_serializer("created_at", "updated_at", "last_login_at")
    def serialize_user_time(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class AuthSessionRead(BaseModel):
    user: MunicipalUserRead
    csrf_token: str
    expires_at: datetime

    @field_serializer("expires_at")
    def serialize_expiry(self, value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class MunicipalUserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: Username
    password: Password
    role: MunicipalRole = MunicipalRole.OPERATOR


class MunicipalUserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: MunicipalRole | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def require_change(self):
        if self.role is None and self.is_active is None:
            raise ValueError("At least one account change is required")
        return self


class MunicipalDepartmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: DepartmentSlug
    display_name: DepartmentName
    description: DepartmentDescription | None = None


class MunicipalDepartmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: DepartmentName | None = None
    description: DepartmentDescription | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def require_department_change(self):
        if self.display_name is None and self.description is None and self.is_active is None:
            raise ValueError("At least one department change is required")
        return self


class DepartmentMemberRead(BaseModel):
    user_id: UUID
    username: str
    role: MunicipalRole
    is_active: bool


class MunicipalDepartmentRead(DepartmentSummary):
    description: str | None
    created_at: datetime
    updated_at: datetime
    members: list[DepartmentMemberRead] = Field(default_factory=list)

    @field_serializer("created_at", "updated_at")
    def serialize_department_time(self, value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class DepartmentMembershipCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID


class ComplaintAssignmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    department_id: UUID | None
    assignee_user_id: UUID | None = None
    expected_updated_at: datetime
    reason: OperatorNote | None = None

    @field_validator("expected_updated_at")
    @classmethod
    def require_assignment_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("expected_updated_at must include a timezone")
        return value


class ComplaintClaimRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_updated_at: datetime

    @field_validator("expected_updated_at")
    @classmethod
    def require_claim_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("expected_updated_at must include a timezone")
        return value


class DepartmentWorkload(BaseModel):
    department: DepartmentSummary
    unresolved: int
    assigned: int
    unassigned: int


class WorkQueueStatistics(BaseModel):
    unassigned_department: int
    assigned_to_me: int
    unassigned_in_my_departments: int
    in_progress_assigned_to_me: int
    departments: list[DepartmentWorkload]


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
