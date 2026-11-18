"""Compare the OLD (HAM10000 only) and NEW (HAM10000 + ISIC 2019) models.

Fair comparison: both models on the SAME images.
  1. HAM10000 test images (the exact test set the old model was reported on)
  2. The full new test set (HAM10000 + ISIC 2019)

Run:  python compare_models.py
"""
import json

import numpy as np
import onnxruntime as ort
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, recall_score
from torch.utils.data import DataLoader
from tqdm import tqdm

from common import ARTIFACT_DIR, CKPT_DIR, CLASSES, REPORTS_DIR, SPLITS_CSV, eval_transform, make_dataset, softmax

MODELS = {
    "old (HAM only)": (CKPT_DIR / "ham_only" / "onnx_skin_model.onnx",
                       CKPT_DIR / "ham_only" / "onnx_model_meta.json"),
    "new (HAM + ISIC)": (ARTIFACT_DIR / "skin_model.onnx", ARTIFACT_DIR / "model_meta.json"),
}


def run(onnx_path, meta_path, df):
    meta = json.loads(meta_path.read_text())
    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    name = sess.get_inputs()[0].name
    dl = DataLoader(make_dataset(df, eval_transform()), batch_size=32, num_workers=4)
    logits, labels = [], []
    for x, y in tqdm(dl, leave=False):
        logits.append(sess.run(None, {name: x.numpy()})[0])
        labels.append(y.numpy())
    probs = softmax(np.concatenate(logits).astype(np.float64), float(meta.get("temperature", 1.0)))
    return probs, np.concatenate(labels)


def triage(probs, labels):
    try:
        from evaluate import triage_safety
        s, _ = triage_safety(probs, labels)
        return {"melanoma_flagged_high": s["melanoma_flagged_high_with_rules"],
                "malignant_moderate_or_high": s["malignant_flagged_moderate_or_high"],
                "benign_flagged_high": s["benign_flagged_high"]}
    except Exception as e:  # rule engine not importable: skip, metrics still valid
        return {"note": f"triage check skipped ({type(e).__name__})"}


def scores(probs, labels):
    preds = probs.argmax(axis=1)
    rec = recall_score(labels, preds, labels=range(len(CLASSES)), average=None, zero_division=0)
    out = {
        "accuracy": accuracy_score(labels, preds),
        "balanced_accuracy": balanced_accuracy_score(labels, preds),
        "macro_f1": f1_score(labels, preds, average="macro"),
        **{f"recall_{c}": float(r) for c, r in zip(CLASSES, rec)},
    }
    out.update(triage(probs, labels))
    return {k: (round(float(v), 3) if isinstance(v, (float, np.floating)) else v) for k, v in out.items()}


def main():
    df = pd.read_csv(SPLITS_CSV)
    test = df[df.split == "test"].reset_index(drop=True)
    sets = {
        f"HAM10000 test ({(test.source == 'HAM10000').sum()} images)":
            test[test.source == "HAM10000"].reset_index(drop=True),
        f"Full new test ({len(test)} images)": test,
    }
    results = {}
    for set_name, sdf in sets.items():
        results[set_name] = {}
        for model_name, (onnx_path, meta_path) in MODELS.items():
            print(f"Running {model_name} on {set_name} ...")
            results[set_name][model_name] = scores(*run(onnx_path, meta_path, sdf))

    md = ["# Old vs new model\n"]
    for set_name, r in results.items():
        table = pd.DataFrame(r)
        table["change"] = [
            (f"{table.iloc[i, 1] - table.iloc[i, 0]:+.3f}"
             if all(isinstance(v, (int, float)) for v in table.iloc[i, :2]) else "")
            for i in range(len(table))
        ]
        print(f"\n===== {set_name} =====")
        print(table.to_string())
        md += [f"## {set_name}\n", table.to_markdown(), "\n"]

    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "model_comparison.json").write_text(json.dumps(results, indent=2))
    (REPORTS_DIR / "model_comparison.md").write_text("\n".join(md))
    print(f"\n✅ Saved {REPORTS_DIR / 'model_comparison.md'}")


if __name__ == "__main__":
    main()
