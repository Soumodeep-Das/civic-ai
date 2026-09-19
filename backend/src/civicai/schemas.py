from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_serializer

from civicai.domain import ComplaintStatus

Description = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ComplaintCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: Description
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False)


class ComplaintRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    complaint_id: UUID
    description: str
    latitude: float | None
    longitude: float | None
    status: ComplaintStatus
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_utc(self, value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
