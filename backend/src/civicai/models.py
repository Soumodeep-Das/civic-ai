from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, Double, ForeignKey, Index, String, Text, Uuid, func, text
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
        CheckConstraint(
            "status IN ('submitted', 'under_review', 'in_progress', 'resolved', 'rejected')",
            name="ck_complaints_status",
        ),
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


class MunicipalUser(Base):
    __tablename__ = "municipal_users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('municipal_operator', 'municipal_admin')",
            name="ck_municipal_users_role",
        ),
        CheckConstraint("username = lower(username)", name="ck_municipal_users_username_lower"),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MunicipalSession(Base):
    __tablename__ = "municipal_sessions"

    session_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("municipal_users.user_id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    csrf_token: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SecurityAuditEvent(Base):
    __tablename__ = "security_audit_events"

    event_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    actor_user_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("municipal_users.user_id", ondelete="RESTRICT"))
    subject_user_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("municipal_users.user_id", ondelete="RESTRICT"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.clock_timestamp())


class ComplaintStatusEvent(Base):
    __tablename__ = "complaint_status_events"
    __table_args__ = (
        CheckConstraint("event_type IN ('created', 'status_changed')", name="ck_complaint_events_type"),
        CheckConstraint(
            "previous_status IS NULL OR previous_status IN "
            "('submitted', 'under_review', 'in_progress', 'resolved', 'rejected')",
            name="ck_complaint_events_previous_status",
        ),
        CheckConstraint(
            "new_status IN ('submitted', 'under_review', 'in_progress', 'resolved', 'rejected')",
            name="ck_complaint_events_new_status",
        ),
        CheckConstraint(
            "operator_note IS NULL OR (length(operator_note) <= 1000 AND operator_note ~ '[^[:space:]]')",
            name="ck_complaint_events_note",
        ),
    )

    event_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    complaint_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("complaints.complaint_id", ondelete="RESTRICT"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(20))
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    operator_note: Mapped[str | None] = mapped_column(String(1000))
    actor_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("municipal_users.user_id", ondelete="RESTRICT")
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.clock_timestamp()
    )


Index("ix_complaints_created_id_desc", Complaint.created_at.desc(), Complaint.complaint_id.desc())
Index("ix_complaints_status_created_desc", Complaint.status, Complaint.created_at.desc())
Index(
    "ix_complaint_events_complaint_time",
    ComplaintStatusEvent.complaint_id,
    ComplaintStatusEvent.occurred_at,
    ComplaintStatusEvent.event_id,
)
Index("ix_municipal_sessions_token_hash", MunicipalSession.token_hash, unique=True)
Index("ix_municipal_sessions_expires_at", MunicipalSession.expires_at)
Index("ix_security_audit_time", SecurityAuditEvent.occurred_at, SecurityAuditEvent.event_id)
