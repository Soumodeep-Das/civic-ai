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
        CheckConstraint("status = 'submitted'", name="ck_complaints_status"),
    )

    complaint_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    description: Mapped[str] = mapped_column(Text)
    latitude: Mapped[float | None] = mapped_column(Double)
    longitude: Mapped[float | None] = mapped_column(Double)
    status: Mapped[str] = mapped_column(String(20), server_default=text("'submitted'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
