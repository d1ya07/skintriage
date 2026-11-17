from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.ml import predictor
from app.models import User, UserRole
from app.schemas.triage import TriageOut
from app.services import triage_service

router = APIRouter(prefix="/triage", tags=["triage"])
patient_only = require_roles(UserRole.patient)


@router.post("", response_model=TriageOut, status_code=status.HTTP_201_CREATED)
def create_triage(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(patient_only),
):
    """Upload a skin photo and get an AI-assisted urgency level + specialist. Not a diagnosis."""
    data = file.file.read(settings.MAX_UPLOAD_BYTES + 1)
    tr = triage_service.run_triage(db, user, data)
    return triage_service.to_out(tr)


@router.get("/model-info")
def get_model_info(_: User = Depends(get_current_user)):
    try:
        return predictor.model_info()
    except predictor.ModelUnavailable:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "The triage model is not available right now")


@router.get("/me", response_model=list[TriageOut])
def my_results(db: Session = Depends(get_db), user: User = Depends(patient_only)):
    return [triage_service.to_out(t) for t in triage_service.list_for_patient(db, user.id)]


@router.get("/{triage_id}", response_model=TriageOut)
def get_result(triage_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return triage_service.to_out(triage_service.get_visible(db, user, triage_id))
