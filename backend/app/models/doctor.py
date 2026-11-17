from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.hospital import Hospital
    from app.models.user import User


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    specialty: Mapped[str] = mapped_column(String(100), index=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"), index=True)
    bio: Mapped[Optional[str]] = mapped_column(Text)
    # optional link to a login account (doctor-facing view, Phase 4)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), unique=True
    )

    hospital: Mapped["Hospital"] = relationship(back_populates="doctors")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor")
    user: Mapped[Optional["User"]] = relationship(back_populates="doctor_profile")
