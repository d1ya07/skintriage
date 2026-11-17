from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import UrgencyLevel

DISCLAIMER = (
    "This is an AI-assisted triage suggestion, not a diagnosis. "
    "Always consult a qualified medical professional."
)


class ClassProbability(BaseModel):
    code: str
    label: str
    probability: float


class TriageOut(BaseModel):
    id: int
    image_url: str
    predicted_condition: str
    predicted_label: str
    confidence: float
    urgency_level: UrgencyLevel
    specialist_type: Optional[str]
    urgent_referral: bool
    uncertain: bool = False
    advice: str
    reasons: list[str]
    probabilities: list[ClassProbability]
    model_version: Optional[str]
    created_at: datetime
    disclaimer: str = DISCLAIMER
