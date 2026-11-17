"""Configurable rule engine: model probabilities -> urgency level + specialist type.

Rules live in rules.yaml and are validated on load. The engine only ever RAISES
urgency (safety nets, low confidence), never lowers it, and explains every step.
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, model_validator

from app.models.enums import UrgencyLevel

DEFAULT_RULES_PATH = Path(__file__).with_name("rules.yaml")
_ORDER = {UrgencyLevel.low: 0, UrgencyLevel.moderate: 1, UrgencyLevel.high: 2}


# ---------------------------------------------------------------- config schema
class ConditionRule(BaseModel):
    label: str
    urgency: UrgencyLevel
    specialist: str
    advice: str


class SafetyNet(BaseModel):
    name: str
    classes: list[str] = Field(min_length=1)
    min_probability: float = Field(gt=0, le=1)
    urgency: UrgencyLevel
    specialist: str
    reason: str


class LowConfidenceRule(BaseModel):
    below: float = Field(gt=0, le=1)
    min_urgency: UrgencyLevel
    specialist: str
    reason: str


class RulesConfig(BaseModel):
    version: int
    specialists: list[str] = Field(min_length=1)
    conditions: dict[str, ConditionRule] = Field(min_length=1)
    safety_nets: list[SafetyNet] = []
    low_confidence: Optional[LowConfidenceRule] = None
    uncertain_below: float = Field(default=0.60, gt=0, le=1)

    @model_validator(mode="after")
    def check_references(self) -> "RulesConfig":
        allowed = set(self.specialists)
        used = [c.specialist for c in self.conditions.values()]
        used += [n.specialist for n in self.safety_nets]
        if self.low_confidence:
            used.append(self.low_confidence.specialist)
        unknown = sorted(set(used) - allowed)
        if unknown:
            raise ValueError(f"Unknown specialist(s) in rules: {unknown}. Add them to `specialists`.")
        for net in self.safety_nets:
            bad = sorted(set(net.classes) - set(self.conditions))
            if bad:
                raise ValueError(f"Safety net '{net.name}' refers to unknown class(es): {bad}")
        return self


# ---------------------------------------------------------------- decision
class TriageDecision(BaseModel):
    predicted_class: str
    predicted_label: str
    confidence: float
    urgency: UrgencyLevel
    specialist: str
    urgent_referral: bool
    uncertain: bool
    advice: str
    reasons: list[str]
    probabilities: dict[str, float]


def load_rules(path: Path = DEFAULT_RULES_PATH) -> RulesConfig:
    with open(path) as f:
        return RulesConfig.model_validate(yaml.safe_load(f))


@lru_cache
def get_rules() -> RulesConfig:
    return load_rules()


def reload_rules() -> RulesConfig:
    get_rules.cache_clear()
    return get_rules()


def evaluate(probabilities: dict[str, float], rules: Optional[RulesConfig] = None) -> TriageDecision:
    rules = rules or get_rules()

    missing = set(rules.conditions) - set(probabilities)
    extra = set(probabilities) - set(rules.conditions)
    if missing or extra:
        raise ValueError(f"Probabilities don't match rule classes (missing={sorted(missing)}, extra={sorted(extra)})")
    total = sum(probabilities.values())
    if not 0.99 <= total <= 1.01 or any(p < 0 for p in probabilities.values()):
        raise ValueError(f"Probabilities must be non-negative and sum to 1 (got {total:.3f})")

    # 1) Base rule from the top prediction
    top = max(probabilities, key=probabilities.get)
    conf = probabilities[top]
    base = rules.conditions[top]
    urgency, specialist = base.urgency, base.specialist
    reasons = [
        f"Top suggestion: {base.label} ({conf:.0%}), mapped to {urgency.value} urgency "
        f"and {specialist}"
    ]

    # 2) Safety nets can only raise urgency
    for net in rules.safety_nets:
        p = sum(probabilities[c] for c in net.classes)
        if p >= net.min_probability and _ORDER[net.urgency] > _ORDER[urgency]:
            urgency, specialist = net.urgency, net.specialist
            reasons.append(
                net.reason.format(p=p, threshold=net.min_probability)
                + f": raised to {urgency.value} urgency, {specialist}"
            )

    # 3) Low confidence raises to a minimum urgency
    lc = rules.low_confidence
    if lc and conf < lc.below:
        msg = lc.reason.format(p=conf, threshold=lc.below)
        if _ORDER[lc.min_urgency] > _ORDER[urgency]:
            urgency, specialist = lc.min_urgency, lc.specialist
            msg += f": raised to {urgency.value} urgency, {specialist}"
        reasons.append(msg)

    uncertain = conf < rules.uncertain_below
    if uncertain:
        reasons.append(
            f"Uncertain result: the top match is only {conf:.0%}, so the image may not be one of the "
            f"{len(rules.conditions)} lesion types the model was trained on (for example acne, rashes or bites)"
        )

    return TriageDecision(
        predicted_class=top,
        predicted_label=base.label,
        confidence=round(conf, 4),
        urgency=urgency,
        specialist=specialist,
        urgent_referral=urgency == UrgencyLevel.high,
        uncertain=uncertain,
        advice=base.advice,
        reasons=reasons,
        probabilities={k: round(v, 4) for k, v in probabilities.items()},
    )
