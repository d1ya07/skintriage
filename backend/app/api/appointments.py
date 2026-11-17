from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models import User, UserRole
from app.schemas.appointment import AppointmentCreate, AppointmentOut
from app.services import appointment_service, notifications
from app.services.appointment_service import Scope

router = APIRouter(prefix="/appointments", tags=["appointments"])
patient_only = require_roles(UserRole.patient)


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def book(
    data: AppointmentCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(patient_only),
):
    appt = appointment_service.create(db, user, data)
    background.add_task(notifications.notify_booked, appt.id)
    return appt


@router.get("/me", response_model=list[AppointmentOut])
def my_appointments(
    scope: Scope = "all", db: Session = Depends(get_db), user: User = Depends(patient_only)
):
    return appointment_service.list_for_patient(db, user.id, scope)


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel(
    appointment_id: int,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(patient_only),
):
    appt = appointment_service.cancel(db, user, appointment_id)
    background.add_task(notifications.notify_cancelled, appt.id)
    return appt
