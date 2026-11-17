"""See how the rule engine handles a few example predictions.
Run from backend/:  python scripts/try_rules.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ml.rules import evaluate  # noqa: E402

CASES = {
    "Confident mole": dict(nv=0.90, bkl=0.04, mel=0.03, bcc=0.01, akiec=0.01, df=0.005, vasc=0.005),
    "Mole, but melanoma 30%": dict(nv=0.60, mel=0.30, bkl=0.05, bcc=0.02, akiec=0.01, df=0.01, vasc=0.01),
    "Clear melanoma": dict(mel=0.82, nv=0.12, bkl=0.03, bcc=0.01, akiec=0.01, df=0.005, vasc=0.005),
    "Uncertain benign keratosis": dict(bkl=0.42, nv=0.30, df=0.12, vasc=0.06, mel=0.05, bcc=0.03, akiec=0.02),
    "Basal cell carcinoma": dict(bcc=0.71, bkl=0.12, akiec=0.08, nv=0.05, mel=0.02, df=0.01, vasc=0.01),
}

for name, probs in CASES.items():
    d = evaluate(probs)
    flag = "  🚨 URGENT REFERRAL" if d.urgent_referral else ""
    print(f"\n=== {name} ===")
    print(f"  {d.predicted_label} ({d.confidence:.0%}) -> {d.urgency.value.upper()}, {d.specialist}{flag}")
    for r in d.reasons:
        print(f"   - {r}")
