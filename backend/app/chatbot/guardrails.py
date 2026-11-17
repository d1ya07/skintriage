import re

EMERGENCY_PATTERNS = [
    r"\bemergenc\w*\b",
    r"\b(can'?t|cannot) breathe\b",
    r"\bsevere (bleeding|pain|allergic)\b",
    r"\banaphyla\w*\b",
    r"\bunconscious\b",
    r"\b(face|throat|lips?) (is |are )?swell\w*\b",
]

CLINICAL_PATTERNS = [
    r"\b(diagnos\w*|prognos\w*)\b(?!.*\b(app|platform|skintriage)\b)",
    r"\bis (it|this|that|my)( \w+){0,2} (cancer\w*|melanoma|serious|dangerous|malignant|benign|normal|contagious|infected)\b",
    r"\b(should i (be )?(worried|concerned)|am i (sick|ok|okay))\b",
    r"\bwhat (cream|ointment|medicine|medication|treatment|drug|pill)s?\b",
    r"\b(dose|dosage|\d+\s?mg|prescri\w*|antibiotic\w*|steroid\w*)\b",
    r"\b(i have|i've got|i got|there'?s|my)\b.{0,40}\b(rash|mole|lump|spot|lesion|itch\w*|bump|wound|blister|bleed\w*|swelling|infection|patch|growth)\b",
    r"\bhow (do|can|should) i (treat|cure|heal|get rid of)\b",
    r"\b(what|which) (disease|condition|infection) (is|do i have)\b",
]

_emergency = [re.compile(p, re.IGNORECASE) for p in EMERGENCY_PATTERNS]
_clinical = [re.compile(p, re.IGNORECASE) for p in CLINICAL_PATTERNS]

CLINICAL_MARKER = "[CLINICAL]"

REFUSAL = (
    "I can only help with questions about using SkinTriage, so I can't give medical advice or "
    "interpret symptoms. For a skin concern, try the Skin Scan for an AI-assisted urgency check, "
    "or book an appointment with a specialist who can examine you properly."
)

EMERGENCY_REPLY = (
    "If this is a medical emergency, call 112 or go to the nearest emergency department right away. "
    "SkinTriage is not designed for emergencies."
)

CLINICAL_ACTIONS = [
    {"label": "Start a skin scan", "to": "/scan"},
    {"label": "Find a doctor", "to": "/doctors"},
]


def is_emergency(text: str) -> bool:
    return any(p.search(text) for p in _emergency)


def is_clinical(text: str) -> bool:
    return any(p.search(text) for p in _clinical)
