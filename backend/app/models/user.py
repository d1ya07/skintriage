from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.doctor import Doctor
    from app.models.triage_result import TriageResult


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=20),
        default=UserRole.patient,
        server_default=UserRole.patient.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    skin_type: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    triage_results: Mapped[list["TriageResult"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    doctor_profile: Mapped[Optional["Doctor"]] = relationship(back_populates="user")
