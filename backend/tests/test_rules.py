import pytest
import yaml
from pydantic import ValidationError

from app.ml.rules import DEFAULT_RULES_PATH, RulesConfig, evaluate, load_rules
from app.models.enums import UrgencyLevel

CLASSES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]


def probs(top: str, p: float, **others) -> dict:
    """Build a valid probability dict: `top` gets p, named others get their value, rest share what's left."""
    out = {c: 0.0 for c in CLASSES}
    out[top] = p
    out.update(others)
    rest = [c for c in CLASSES if c != top and c not in others]
    remaining = 1 - sum(out.values())
    for c in rest:
        out[c] = remaining / len(rest)
    return out


def test_default_rules_load_and_cover_all_classes():
    rules = load_rules()
    assert set(rules.conditions) == set(CLASSES)


@pytest.mark.parametrize(
    "cls, urgency, specialist",
    [
        ("mel", "high", "Dermato-oncologist"),
        ("bcc", "moderate", "Dermatologic Surgeon"),
        ("akiec", "moderate", "Dermatologist"),
        ("bkl", "low", "Dermatologist"),
        ("df", "low", "Dermatologist"),
        ("nv", "low", "General Physician"),
        ("vasc", "low", "Dermatologist"),
    ],
)
def test_base_mapping_for_confident_predictions(cls, urgency, specialist):
    d = evaluate(probs(cls, 0.90))
    assert d.predicted_class == cls
    assert d.urgency.value == urgency
    assert d.specialist == specialist
    assert d.urgent_referral == (urgency == "high")


def test_melanoma_safety_net_escalates_a_mole():
    d = evaluate(probs("nv", 0.65, mel=0.30))
    assert d.predicted_class == "nv"
    assert d.urgency == UrgencyLevel.high
    assert d.specialist == "Dermato-oncologist"
    assert d.urgent_referral
    assert any("Melanoma probability" in r for r in d.reasons)


def test_combined_malignancy_net_raises_to_moderate():
    d = evaluate(probs("nv", 0.55, mel=0.15, bcc=0.15, akiec=0.10))
    assert d.urgency == UrgencyLevel.moderate
    assert any("Combined probability" in r for r in d.reasons)


def test_low_confidence_raises_to_moderate():
    d = evaluate(probs("bkl", 0.40))
    assert d.urgency == UrgencyLevel.moderate
    assert d.specialist == "Dermatologist"
    assert any("not confident" in r for r in d.reasons)


def test_rules_never_lower_urgency():
    # Low-confidence melanoma stays HIGH (low-confidence rule only raises to moderate)
    d = evaluate(probs("mel", 0.45))
    assert d.urgency == UrgencyLevel.high


def test_invalid_probabilities_rejected():
    with pytest.raises(ValueError):
        evaluate({"nv": 0.5, "mel": 0.5})  # missing classes
    with pytest.raises(ValueError):
        evaluate({c: 0.5 for c in CLASSES})  # sums to 3.5


def test_config_with_unknown_specialist_rejected():
    raw = yaml.safe_load(DEFAULT_RULES_PATH.read_text())
    raw["conditions"]["nv"]["specialist"] = "Astrologer"
    with pytest.raises(ValidationError, match="Unknown specialist"):
        RulesConfig.model_validate(raw)


def test_config_safety_net_with_unknown_class_rejected():
    raw = yaml.safe_load(DEFAULT_RULES_PATH.read_text())
    raw["safety_nets"][0]["classes"] = ["scc"]
    with pytest.raises(ValidationError, match="unknown class"):
        RulesConfig.model_validate(raw)


def test_thresholds_are_configurable(tmp_path):
    raw = yaml.safe_load(DEFAULT_RULES_PATH.read_text())
    raw["safety_nets"][0]["min_probability"] = 0.10  # stricter melanoma net
    f = tmp_path / "rules.yaml"
    f.write_text(yaml.safe_dump(raw))
    strict = load_rules(f)
    d = evaluate(probs("nv", 0.80, mel=0.12), rules=strict)
    assert d.urgency == UrgencyLevel.high
