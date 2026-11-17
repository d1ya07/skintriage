import io
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from PIL import Image

from app.core.config import settings
from app.ml import predictor
from app.models import Doctor, Hospital, TriageResult, UserRole

CLASSES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]


def probs(top: str, p: float, **others) -> dict:
    out = {c: 0.0 for c in CLASSES}
    out[top] = p
    out.update(others)
    rest = [c for c in CLASSES if c != top and c not in others]
    left = 1 - sum(out.values())
    for c in rest:
        out[c] = left / len(rest)
    return out


@pytest.fixture(autouse=True)
def tmp_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def fake_model(monkeypatch):
    """Replace the real ONNX model with a predictable one."""
    state = {"probs": probs("nv", 0.9)}
    monkeypatch.setattr(predictor, "predict", lambda img: state["probs"])
    monkeypatch.setattr(predictor, "model_version", lambda: "fake@test")
    return state


def image_bytes(size=(400, 300)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 150, 120)).save(buf, "JPEG")
    return buf.getvalue()


def triage(client, headers, data=None):
    return client.post(
        "/api/triage", files={"file": ("lesion.jpg", data or image_bytes(), "image/jpeg")}, headers=headers
    )


@pytest.fixture
def patient(make_user, auth_headers):
    make_user(email="pat@example.com")
    return auth_headers("pat@example.com")


def test_low_urgency_result(client, patient, fake_model):
    r = triage(client, patient)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["predicted_condition"] == "nv"
    assert body["urgency_level"] == "low"
    assert body["specialist_type"] == "General Physician"
    assert body["urgent_referral"] is False
    assert body["probabilities"][0]["code"] == "nv"  # sorted, highest first
    assert "not a diagnosis" in body["disclaimer"]
    assert body["model_version"] == "fake@test"


def test_melanoma_safety_net_flags_urgent(client, patient, fake_model, db):
    fake_model["probs"] = probs("nv", 0.62, mel=0.30)
    body = triage(client, patient).json()
    assert body["urgency_level"] == "high"
    assert body["urgent_referral"] is True
    assert body["specialist_type"] == "Dermato-oncologist"
    saved = db.get(TriageResult, body["id"])
    assert saved.reasons and any("Melanoma" in r for r in saved.reasons)
    assert abs(sum(saved.probabilities.values()) - 1) < 0.01


def test_history_and_access_rules(client, patient, fake_model, make_user, auth_headers):
    first = triage(client, patient).json()
    triage(client, patient)
    mine = client.get("/api/triage/me", headers=patient).json()
    assert len(mine) == 2

    make_user(email="other@example.com")
    other = auth_headers("other@example.com")
    assert client.get(f"/api/triage/{first['id']}", headers=other).status_code == 404
    assert client.get("/api/triage/me", headers=other).json() == []

    make_user(email="doc@example.com", role=UserRole.doctor)
    assert client.get(f"/api/triage/{first['id']}", headers=auth_headers("doc@example.com")).status_code == 200


def test_bad_image_saves_nothing(client, patient, fake_model, db):
    r = triage(client, patient, data=b"not an image")
    assert r.status_code == 400
    assert db.query(TriageResult).count() == 0


def test_model_unavailable_returns_503_and_cleans_up(client, patient, monkeypatch, tmp_uploads):
    def boom(img):
        raise predictor.ModelUnavailable("missing")

    monkeypatch.setattr(predictor, "predict", boom)
    r = triage(client, patient)
    assert r.status_code == 503
    assert list(tmp_uploads.rglob("*.jpg")) == []  # uploaded image removed


def test_only_patients_can_triage(client, make_user, auth_headers, fake_model):
    make_user(email="doc@example.com", role=UserRole.doctor)
    assert triage(client, auth_headers("doc@example.com")).status_code == 403


def test_booking_can_link_triage_result(client, patient, fake_model, db):
    tr = triage(client, patient).json()
    h = Hospital(name="H", city="Mohali", address="A")
    d = Doctor(name="Dr. X", specialty="Dermatologist", bio="", hospital=h)
    db.add(d)
    db.commit()
    day = datetime.now(ZoneInfo("Asia/Kolkata")).date() + timedelta(days=2)
    while day.weekday() == 6:
        day += timedelta(days=1)
    when = datetime.combine(day, time(11, 0), tzinfo=ZoneInfo("Asia/Kolkata"))
    r = client.post(
        "/api/appointments",
        json={"doctor_id": d.id, "scheduled_at": when.isoformat(), "reason": "Follow-up on scan",
              "triage_result_id": tr["id"]},
        headers=patient,
    )
    assert r.status_code == 201, r.text
    assert r.json()["triage_result_id"] == tr["id"]


def test_real_model_if_present():
    try:
        model = predictor.get_model()
    except predictor.ModelUnavailable:
        pytest.skip("no trained model in app/ml/artifacts")
    img = Image.new("RGB", (640, 480), (200, 150, 120))
    assert model.preprocess(img).shape == (1, 3, 224, 224)
    p = model.predict(img)
    assert set(p) == set(model.classes)
    assert abs(sum(p.values()) - 1) < 1e-5


def test_uncertain_flag_in_response(client, patient, fake_model):
    fake_model["probs"] = probs("bkl", 0.40)
    body = triage(client, patient).json()
    assert body["uncertain"] is True
    assert body["urgency_level"] == "moderate"
