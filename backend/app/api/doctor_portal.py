from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models import Doctor, User, UserRole
from app.schemas.doctor import DoctorOut
from app.schemas.doctor_portal import DoctorAppointmentOut, DoctorMeOut
from app.services import doctor_portal_service as svc
from app.services import notifications

router = APIRouter(prefix="/doctor", tags=["doctor portal"])


def current_doctor(
    user: User = Depends(require_roles(UserRole.doctor)), db: Session = Depends(get_db)
) -> Doctor:
    return svc.get_doctor_for_user(db, user)


@router.get("/me", response_model=DoctorMeOut)
def me(doctor: Doctor = Depends(current_doctor), db: Session = Depends(get_db)):
    return DoctorMeOut(doctor=DoctorOut.model_validate(doctor), stats=svc.stats(db, doctor.id))


@router.get("/appointments", response_model=list[DoctorAppointmentOut])
def appointments(
    scope: svc.Scope = "upcoming",
    doctor: Doctor = Depends(current_doctor),
    db: Session = Depends(get_db),
):
    return [svc.to_out(a) for a in svc.list_for_doctor(db, doctor.id, scope)]


@router.post("/appointments/{appointment_id}/confirm", response_model=DoctorAppointmentOut)
def confirm(
    appointment_id: int,
    background: BackgroundTasks,
    doctor: Doctor = Depends(current_doctor),
    db: Session = Depends(get_db),
):
    appt = svc.confirm(db, doctor, appointment_id)
    background.add_task(notifications.notify_confirmed, appt.id)
    return svc.to_out(appt)


@router.post("/appointments/{appointment_id}/complete", response_model=DoctorAppointmentOut)
def complete(appointment_id: int, doctor: Doctor = Depends(current_doctor), db: Session = Depends(get_db)):
    return svc.to_out(svc.complete(db, doctor, appointment_id))
