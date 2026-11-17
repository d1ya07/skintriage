from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models import (
    Appointment,
    AppointmentStatus,
    Doctor,
    Hospital,
    TriageResult,
    User,
    UserRole,
)
from app.schemas.admin import AdminStats
from app.schemas.doctor import DoctorOut
from app.schemas.doctor_portal import DoctorLinkIn
from app.schemas.user import UserAdminUpdate, UserOut

admin_only = require_roles(UserRole.admin)
router = APIRouter(prefix="/admin", tags=["admin"])


def _count(db: Session, model, *where) -> int:
    return db.scalar(select(func.count()).select_from(model).where(*where)) or 0


@router.get("/stats", response_model=AdminStats)
def stats(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    users_by_role = {r.value: 0 for r in UserRole}
    for role, n in db.execute(select(User.role, func.count()).group_by(User.role)).all():
        users_by_role[role.value] = n

    appts = {s.value: 0 for s in AppointmentStatus}
    for st, n in db.execute(
        select(Appointment.status, func.count()).group_by(Appointment.status)
    ).all():
        appts[st.value] = n

    return AdminStats(
        users_by_role=users_by_role,
        active_users=_count(db, User, User.is_active.is_(True)),
        hospitals=_count(db, Hospital),
        doctors=_count(db, Doctor),
        appointments_by_status=appts,
        triage_results=_count(db, TriageResult),
    )


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    return db.scalars(select(User).order_by(User.id)).all()


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserAdminUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(admin_only),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if user.id == current.id and (
        (data.role is not None and data.role != UserRole.admin) or data.is_active is False
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't demote or deactivate yourself")
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    return user


@router.patch("/doctors/{doctor_id}/link", response_model=DoctorOut)
def link_doctor_account(
    doctor_id: int,
    data: DoctorLinkIn,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
):
    """Connect a doctor login (user with role=doctor) to a directory profile, or unlink with null."""
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor not found")
    if data.user_id is None:
        doctor.user_id = None
    else:
        user = db.get(User, data.user_id)
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        if user.role != UserRole.doctor:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "That user doesn't have the doctor role")
        other = db.scalar(select(Doctor).where(Doctor.user_id == user.id, Doctor.id != doctor.id))
        if other:
            raise HTTPException(status.HTTP_409_CONFLICT, f"That user is already linked to {other.name}")
        doctor.user_id = user.id
    db.commit()
    db.refresh(doctor)
    return doctor
