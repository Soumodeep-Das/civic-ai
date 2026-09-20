from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Double, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from civicai.database import Base


class Complaint(Base):
    __tablename__ = "complaints"
    __table_args__ = (
        CheckConstraint("description ~ '[^[:space:]]'", name="ck_complaints_description"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_complaints_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_complaints_longitude"),
        CheckConstraint(
            "location_precision IS NULL OR location_precision IN ('exact', 'approximate', 'broad')",
            name="ck_complaints_location_precision",
        ),
        CheckConstraint(
            "location_source IS NULL OR location_source IN ('search', 'device', 'map')",
            name="ck_complaints_location_source",
        ),
        CheckConstraint(
            "location_accuracy_m IS NULL OR (location_accuracy_m >= 0 AND location_accuracy_m <= 100000)",
            name="ck_complaints_location_accuracy",
        ),
        CheckConstraint(
            "location_accuracy_m IS NULL OR location_source = 'device'",
            name="ck_complaints_location_accuracy_source",
        ),
        CheckConstraint(
            "(location_source IS NULL AND location_accuracy_m IS NULL) OR "
            "(latitude IS NOT NULL AND longitude IS NOT NULL AND location_label IS NOT NULL "
            "AND location_precision IS NOT NULL AND location_source IS NOT NULL)",
            name="ck_complaints_location_quality_context",
        ),
        CheckConstraint(
            "location_label IS NULL OR location_label ~ '[^[:space:]]'",
            name="ck_complaints_location_label",
        ),
        CheckConstraint(
            "location_details IS NULL OR location_details ~ '[^[:space:]]'",
            name="ck_complaints_location_details",
        ),
        CheckConstraint(
            "(location_label IS NULL AND location_precision IS NULL AND location_details IS NULL) OR "
            "(latitude IS NOT NULL AND longitude IS NOT NULL AND "
            "location_label IS NOT NULL AND location_precision IS NOT NULL)",
            name="ck_complaints_location_context",
        ),
        CheckConstraint("status = 'submitted'", name="ck_complaints_status"),
    )

    complaint_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    description: Mapped[str] = mapped_column(Text)
    image_ref: Mapped[str | None] = mapped_column(String(200))
    latitude: Mapped[float | None] = mapped_column(Double)
    longitude: Mapped[float | None] = mapped_column(Double)
    location_label: Mapped[str | None] = mapped_column(String(300))
    location_precision: Mapped[str | None] = mapped_column(String(20))
    location_details: Mapped[str | None] = mapped_column(String(500))
    location_source: Mapped[str | None] = mapped_column(String(20))
    location_accuracy_m: Mapped[float | None] = mapped_column(Double)
    status: Mapped[str] = mapped_column(String(20), server_default=text("'submitted'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
