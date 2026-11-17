from fastapi import APIRouter

from app.api import (
    admin,
    appointments,
    auth,
    chat,
    doctor_portal,
    doctors,
    triage,
    uploads,
    users,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(doctors.router)
api_router.include_router(appointments.router)
api_router.include_router(uploads.router)
api_router.include_router(triage.router)
api_router.include_router(doctor_portal.router)
api_router.include_router(chat.router)
api_router.include_router(admin.router)
