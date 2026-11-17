import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    # Tests must never call the real Anthropic API.
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")


def ask(client, text):
    return client.post("/api/chat", json={"messages": [{"role": "user", "content": text}]})


def test_platform_question_answered(client):
    r = ask(client, "How do I cancel an appointment?")
    assert r.status_code == 200
    body = r.json()
    assert body["refused"] is False
    assert "Cancel" in body["reply"]


@pytest.mark.parametrize(
    "question",
    [
        "Is this mole cancer?",
        "I have a red itchy rash on my arm, what is it?",
        "What cream should I use?",
        "Can I take 500 mg of amoxicillin?",
        "How do I get rid of acne?",
    ],
)
def test_clinical_questions_refused(client, question):
    body = ask(client, question).json()
    assert body["refused"] is True
    assert body["source"] == "guardrail"
    assert {a["to"] for a in body["actions"]} == {"/scan", "/doctors"}


def test_emergency_mentions_112(client):
    body = ask(client, "This is an emergency, my lips are swelling").json()
    assert body["refused"] is True
    assert "112" in body["reply"]


def test_last_message_must_be_user(client):
    r = client.post("/api/chat", json={"messages": [{"role": "assistant", "content": "hi"}]})
    assert r.status_code == 422


@pytest.mark.parametrize(
    "question, expected",
    [
        ("How do I cancel a booking?", "Cancel"),
        ("How do I book an appointment?", "Book appointment"),
        ("Can I change the time of my booking?", "reschedule"),
        ("What do the urgency levels mean?", "High means"),
    ],
)
def test_faq_picks_right_answer(client, question, expected):
    body = ask(client, question).json()
    assert body["refused"] is False
    assert expected in body["reply"]


def test_platform_question_about_scan_not_refused(client):
    assert ask(client, "How does the skin scan work?").json()["refused"] is False
