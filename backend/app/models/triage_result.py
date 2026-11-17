from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UrgencyLevel

if TYPE_CHECKING:
    from app.models.user import User


class TriageResult(Base):
    __tablename__ = "triage_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    image_path: Mapped[str] = mapped_column(String(500))
    predicted_condition: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[float] = mapped_column(Float)
    urgency_level: Mapped[UrgencyLevel] = mapped_column(
        Enum(UrgencyLevel, native_enum=False, length=20)
    )
    specialist_type: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    patient: Mapped["User"] = relationship(back_populates="triage_results")
