import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml import predictor
from app.ml.rules import evaluate, get_rules
from app.models import TriageResult, User, UserRole
from app.models.enums import UrgencyLevel
from app.schemas.triage import ClassProbability, TriageOut
from app.services import storage

log = logging.getLogger(__name__)


def to_out(tr: TriageResult) -> TriageOut:
    rules = get_rules()
    cond = rules.conditions.get(tr.predicted_condition)
    probs = tr.probabilities or {tr.predicted_condition: tr.confidence}
    ranked = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    return TriageOut(
        id=tr.id,
        image_url=f"/api/uploads/images/{tr.image_path}",
        predicted_condition=tr.predicted_condition,
        predicted_label=cond.label if cond else tr.predicted_condition,
        confidence=tr.confidence,
        urgency_level=tr.urgency_level,
        specialist_type=tr.specialist_type,
        urgent_referral=tr.urgency_level == UrgencyLevel.high,
        uncertain=tr.confidence < rules.uncertain_below,
        advice=cond.advice if cond else "",
        reasons=tr.reasons or [],
        probabilities=[
            ClassProbability(
                code=c,
                label=rules.conditions[c].label if c in rules.conditions else c,
                probability=round(p, 4),
            )
            for c, p in ranked
        ],
        model_version=tr.model_version,
        created_at=tr.created_at,
    )


def run_triage(db: Session, patient: User, data: bytes) -> TriageResult:
    stored, img = storage.save_image(patient.id, data)
    try:
        probs = predictor.predict(img)
        version = predictor.model_version()
    except predictor.ModelUnavailable:
        storage.delete_image(stored.path)
        log.exception("Triage model not available")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "The triage model is not available right now")
    except Exception:
        storage.delete_image(stored.path)
        log.exception("Prediction failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Couldn't analyse that image")

    decision = evaluate(probs)
    tr = TriageResult(
        patient_id=patient.id,
        image_path=stored.path,
        predicted_condition=decision.predicted_class,
        confidence=decision.confidence,
        urgency_level=decision.urgency,
        specialist_type=decision.specialist,
        probabilities=decision.probabilities,
        reasons=decision.reasons,
        model_version=version,
    )
    db.add(tr)
    db.commit()
    db.refresh(tr)
    return tr


def list_for_patient(db: Session, patient_id: int) -> list[TriageResult]:
    stmt = (
        select(TriageResult)
        .where(TriageResult.patient_id == patient_id)
        .order_by(TriageResult.created_at.desc(), TriageResult.id.desc())
    )
    return list(db.scalars(stmt).all())


def get_visible(db: Session, user: User, triage_id: int) -> TriageResult:
    tr = db.get(TriageResult, triage_id)
    if not tr or (user.role == UserRole.patient and tr.patient_id != user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Triage result not found")
    return tr
