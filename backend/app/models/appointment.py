from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AppointmentStatus

if TYPE_CHECKING:
    from app.models.doctor import Doctor
    from app.models.triage_result import TriageResult
    from app.models.user import User


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    triage_result_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("triage_results.id", ondelete="SET NULL")
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    reason: Mapped[str] = mapped_column(String(500))
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, native_enum=False, length=20),
        default=AppointmentStatus.booked,
        server_default=AppointmentStatus.booked.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    patient: Mapped["User"] = relationship(back_populates="appointments")
    doctor: Mapped["Doctor"] = relationship(back_populates="appointments")
    triage_result: Mapped[Optional["TriageResult"]] = relationship()
