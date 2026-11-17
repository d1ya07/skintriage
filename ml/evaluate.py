"""Phase 4: full evaluation of the DEPLOYED model (the ONNX file the backend uses)
on the held-out, lesion-level TEST split. Writes figures, tables and a markdown
summary to ml/reports/ for the project report.

Run from ml/:  python evaluate.py
"""
import json
import sys
from datetime import datetime, timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import onnxruntime as ort  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    roc_auc_score,
    roc_curve,
)
from torch.utils.data import DataLoader  # noqa: E402
from tqdm import tqdm  # noqa: E402

from common import (  # noqa: E402
    ARTIFACT_DIR,
    CKPT_DIR,
    CLASS_NAMES,
    CLASSES,
    REPORTS_DIR,
    SEED,
    SPLITS_CSV,
    eval_transform,
    expected_calibration_error,
    make_dataset,
    softmax,
)

BACKEND_DIR = ARTIFACT_DIR.parents[2]
MALIGNANT = ["mel", "bcc", "akiec"]
BENIGN = ["bkl", "df", "nv", "vasc"]
N_BOOT = 1000
plt.rcParams.update({"figure.dpi": 150, "savefig.bbox": "tight", "font.size": 9})


# ------------------------------------------------------------------ helpers
def bootstrap_ci(labels, preds, fn, n=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    idx = np.arange(len(labels))
    vals = []
    for _ in range(n):
        s = rng.choice(idx, size=len(idx), replace=True)
        vals.append(fn(labels[s], preds[s]))
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(lo), float(hi)


def brier(probs, labels):
    onehot = np.eye(probs.shape[1])[labels]
    return float(((probs - onehot) ** 2).sum(axis=1).mean())


def reliability_bins(probs, labels, n_bins=15):
    conf = probs.max(axis=1)
    correct = (probs.argmax(axis=1) == labels).astype(float)
    edges = np.linspace(0, 1, n_bins + 1)
    centers, accs, confs, counts = [], [], [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        centers.append((lo + hi) / 2)
        counts.append(int(m.sum()))
        accs.append(correct[m].mean() if m.any() else np.nan)
        confs.append(conf[m].mean() if m.any() else np.nan)
    return edges, np.array(centers), np.array(accs), np.array(confs), np.array(counts)


def collect_logits(test_df):
    meta = json.loads((ARTIFACT_DIR / "model_meta.json").read_text())
    sess = ort.InferenceSession(
        str(ARTIFACT_DIR / meta.get("onnx_file", "skin_model.onnx")), providers=["CPUExecutionProvider"]
    )
    input_name = sess.get_inputs()[0].name
    dl = DataLoader(make_dataset(test_df, eval_transform()), batch_size=32, num_workers=4)
    logits, labels = [], []
    for x, y in tqdm(dl, desc="Running deployed ONNX model on test set"):
        logits.append(sess.run(None, {input_name: x.numpy()})[0])
        labels.append(y.numpy())
    return np.concatenate(logits).astype(np.float64), np.concatenate(labels), meta


# ------------------------------------------------------------------ figures
def plot_confusion(labels, preds):
    cm = confusion_matrix(labels, preds, labels=range(len(CLASSES)))
    cm_norm = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, mat, title, fmt in [
        (axes[0], cm, "Confusion matrix (counts)", "d"),
        (axes[1], cm_norm, "Confusion matrix (row-normalised = recall)", ".2f"),
    ]:
        im = ax.imshow(mat, cmap="Blues")
        ax.set_xticks(range(len(CLASSES)), CLASSES)
        ax.set_yticks(range(len(CLASSES)), CLASSES)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_title(title)
        thresh = mat.max() / 2
        for i in range(len(CLASSES)):
            for j in range(len(CLASSES)):
                ax.text(j, i, format(mat[i, j], fmt), ha="center", va="center",
                        color="white" if mat[i, j] > thresh else "black", fontsize=8)
        fig.colorbar(im, ax=ax, fraction=0.046)
    fig.savefig(REPORTS_DIR / "confusion_matrix.png")
    plt.close(fig)
    return cm


def plot_reliability(probs_raw, probs_cal, labels, ece_raw, ece_cal):
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), gridspec_kw={"height_ratios": [3, 1]}, sharex=True)
    for col, (p, title, ece) in enumerate([
        (probs_raw, "Before temperature scaling", ece_raw),
        (probs_cal, "After temperature scaling", ece_cal),
    ]):
        edges, centers, accs, confs, counts = reliability_bins(p, labels)
        width = edges[1] - edges[0]
        ax = axes[0, col]
        ax.bar(centers, np.nan_to_num(accs), width=width * 0.95, edgecolor="black", label="Accuracy")
        gap_bottom = np.minimum(np.nan_to_num(accs), np.nan_to_num(confs))
        gap = np.abs(np.nan_to_num(confs) - np.nan_to_num(accs))
        ax.bar(centers, gap, bottom=gap_bottom, width=width * 0.95, color="red", alpha=0.3,
               edgecolor="red", label="Gap")
        ax.plot([0, 1], [0, 1], "k--", label="Perfect calibration")
        ax.set_title(f"{title}\nECE = {ece:.3f}")
        ax.set_ylabel("Accuracy")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.legend(loc="upper left")
        axes[1, col].bar(centers, counts, width=width * 0.95, color="gray")
        axes[1, col].set_xlabel("Confidence (top-class probability)")
        axes[1, col].set_ylabel("Images")
    fig.savefig(REPORTS_DIR / "reliability_diagram.png")
    plt.close(fig)


def plot_roc(probs, labels, aucs):
    fig, ax = plt.subplots(figsize=(6, 5.5))
    for i, c in enumerate(CLASSES):
        fpr, tpr, _ = roc_curve(labels == i, probs[:, i])
        ax.plot(fpr, tpr, label=f"{c} (AUC {aucs[c]:.3f})")
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.8)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("ROC curves (one-vs-rest)")
    ax.legend(loc="lower right")
    fig.savefig(REPORTS_DIR / "roc_curves.png")
    plt.close(fig)


def plot_per_class(per_class):
    x = np.arange(len(CLASSES))
    fig, ax = plt.subplots(figsize=(9, 4))
    for k, metric in enumerate(["precision", "recall", "f1"]):
        ax.bar(x + (k - 1) * 0.27, [per_class[c][metric] for c in CLASSES], width=0.27, label=metric)
    ax.set_xticks(x, [f"{c}\n(n={per_class[c]['support']})" for c in CLASSES])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Score")
    ax.set_title("Per-class precision, recall and F1 (test set)")
    ax.legend()
    fig.savefig(REPORTS_DIR / "per_class_metrics.png")
    plt.close(fig)


def plot_training_curves():
    path = CKPT_DIR / "history.json"
    if not path.exists():
        return False
    h = json.loads(path.read_text())
    ep = [r["epoch"] for r in h]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].plot(ep, [r["train_loss"] for r in h], marker="o")
    axes[0].set_title("Training loss")
    axes[0].set_xlabel("Epoch")
    for key in ["accuracy", "balanced_accuracy", "macro_f1"]:
        axes[1].plot(ep, [r[key] for r in h], marker="o", label=key)
    axes[1].set_title("Validation metrics")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylim(0, 1)
    axes[1].legend()
    fig.savefig(REPORTS_DIR / "training_curves.png")
    plt.close(fig)
    return True


def plot_urgency(crosstab):
    fig, ax = plt.subplots(figsize=(8, 4))
    bottom = np.zeros(len(crosstab))
    colors = {"low": "#10b981", "moderate": "#f59e0b", "high": "#ef4444"}
    pct = crosstab.div(crosstab.sum(axis=1), axis=0)
    for level in ["low", "moderate", "high"]:
        vals = pct[level].values if level in pct else np.zeros(len(pct))
        ax.bar(pct.index, vals, bottom=bottom, color=colors[level], label=level)
        bottom += vals
    ax.set_ylabel("Share of test images")
    ax.set_title("Urgency assigned by the rule engine, by TRUE class")
    ax.legend(title="Urgency")
    fig.savefig(REPORTS_DIR / "urgency_by_true_class.png")
    plt.close(fig)


# ------------------------------------------------------------------ triage safety
def triage_safety(probs_cal, labels):
    sys.path.insert(0, str(BACKEND_DIR))
    from app.ml.rules import evaluate as rules_evaluate  # the exact production rule engine

    urg = np.array([
        rules_evaluate({c: float(p) for c, p in zip(CLASSES, row)}).urgency.value for row in probs_cal
    ])
    true = np.array([CLASSES[i] for i in labels])
    preds = np.array([CLASSES[i] for i in probs_cal.argmax(axis=1)])
    is_mal = np.isin(true, MALIGNANT)
    is_ben = np.isin(true, BENIGN)
    mel = true == "mel"

    crosstab = pd.crosstab(pd.Series(true, name="true_class"), pd.Series(urg, name="urgency"))
    for col in ["low", "moderate", "high"]:
        if col not in crosstab:
            crosstab[col] = 0
    crosstab = crosstab[["low", "moderate", "high"]].reindex(CLASSES, fill_value=0)

    safety = {
        "melanoma_recall_model_only": float((preds[mel] == "mel").mean()),
        "melanoma_flagged_high_with_rules": float((urg[mel] == "high").mean()),
        "melanoma_flagged_moderate_or_high": float((urg[mel] != "low").mean()),
        "malignant_flagged_moderate_or_high": float((urg[is_mal] != "low").mean()),
        "malignant_left_at_low": int((urg[is_mal] == "low").sum()),
        "benign_flagged_high": float((urg[is_ben] == "high").mean()),
        "benign_routed_low": float((urg[is_ben] == "low").mean()),
        "urgency_distribution": {k: float((urg == k).mean()) for k in ["low", "moderate", "high"]},
        "n_test": int(len(labels)),
        "n_melanoma": int(mel.sum()),
        "n_malignant": int(is_mal.sum()),
        "n_benign": int(is_ben.sum()),
    }
    return safety, crosstab


# ------------------------------------------------------------------ main
def main():
    REPORTS_DIR.mkdir(exist_ok=True)
    df = pd.read_csv(SPLITS_CSV)
    test_df = df[df.split == "test"].reset_index(drop=True)

    logits, labels, meta = collect_logits(test_df)
    T = float(meta.get("temperature", 1.0))
    probs_raw = softmax(logits)
    probs = softmax(logits, T)
    preds = probs.argmax(axis=1)

    # ---- overall
    overall = {
        "accuracy": float(accuracy_score(labels, preds)),
        "balanced_accuracy": float(balanced_accuracy_score(labels, preds)),
        "macro_f1": float(f1_score(labels, preds, average="macro")),
        "weighted_f1": float(f1_score(labels, preds, average="weighted")),
        "macro_auc_ovr": float(roc_auc_score(labels, probs, multi_class="ovr", average="macro")),
    }
    ci = {
        "accuracy": bootstrap_ci(labels, preds, accuracy_score),
        "balanced_accuracy": bootstrap_ci(labels, preds, balanced_accuracy_score),
        "macro_f1": bootstrap_ci(labels, preds, lambda a, b: f1_score(a, b, average="macro")),
    }

    # ---- per class
    rep = classification_report(labels, preds, labels=range(len(CLASSES)), target_names=CLASSES,
                                output_dict=True, zero_division=0)
    aucs = {c: float(roc_auc_score(labels == i, probs[:, i])) for i, c in enumerate(CLASSES)}
    per_class = {
        c: {"name": CLASS_NAMES[c], "precision": rep[c]["precision"], "recall": rep[c]["recall"],
            "f1": rep[c]["f1-score"], "support": int(rep[c]["support"]), "auc": aucs[c]}
        for c in CLASSES
    }

    # ---- calibration
    calibration = {
        "temperature": T,
        "ece_before": expected_calibration_error(probs_raw, labels),
        "ece_after": expected_calibration_error(probs, labels),
        "nll_before": float(log_loss(labels, probs_raw, labels=range(len(CLASSES)))),
        "nll_after": float(log_loss(labels, probs, labels=range(len(CLASSES)))),
        "brier_before": brier(probs_raw, labels),
        "brier_after": brier(probs, labels),
        "mean_confidence_after": float(probs.max(axis=1).mean()),
    }

    # ---- figures
    cm = plot_confusion(labels, preds)
    plot_reliability(probs_raw, probs, labels, calibration["ece_before"], calibration["ece_after"])
    plot_roc(probs, labels, aucs)
    plot_per_class(per_class)
    has_curves = plot_training_curves()

    # ---- rule engine safety
    safety, crosstab = triage_safety(probs, labels)
    plot_urgency(crosstab)

    # ---- save tables
    results = {"evaluated_at": datetime.now(timezone.utc).isoformat(), "model": {
        k: meta.get(k) for k in ["arch", "trained_at", "best_epoch", "img_size"]},
        "overall": overall, "overall_95ci": ci, "per_class": per_class,
        "calibration": calibration, "triage_safety": safety}
    (REPORTS_DIR / "metrics.json").write_text(json.dumps(results, indent=2))
    pd.DataFrame(per_class).T.to_csv(REPORTS_DIR / "per_class_metrics.csv")
    pd.DataFrame(cm, index=CLASSES, columns=CLASSES).to_csv(REPORTS_DIR / "confusion_matrix.csv")
    crosstab.to_csv(REPORTS_DIR / "urgency_by_true_class.csv")

    # ---- markdown summary
    pc_rows = "\n".join(
        f"| {c} | {v['name']} | {v['support']} | {v['precision']:.3f} | {v['recall']:.3f} | "
        f"{v['f1']:.3f} | {v['auc']:.3f} |" for c, v in per_class.items()
    )
    s = safety
    md = f"""# SkinTriage model evaluation

Deployed model: **{meta.get('arch')}** (ONNX), trained {str(meta.get('trained_at', ''))[:10]}.
Test set: **{len(labels)} images** from HAM10000, held out at **lesion level** (no lesion appears in both training and test).
Probabilities are temperature-scaled (T = {T:.3f}) exactly as in the live app.

## Overall performance (test set, 95% bootstrap CI, {N_BOOT} resamples)

| Metric | Value | 95% CI |
|---|---|---|
| Accuracy | {overall['accuracy']:.3f} | {ci['accuracy'][0]:.3f} to {ci['accuracy'][1]:.3f} |
| Balanced accuracy (mean per-class recall) | {overall['balanced_accuracy']:.3f} | {ci['balanced_accuracy'][0]:.3f} to {ci['balanced_accuracy'][1]:.3f} |
| Macro F1 | {overall['macro_f1']:.3f} | {ci['macro_f1'][0]:.3f} to {ci['macro_f1'][1]:.3f} |
| Weighted F1 | {overall['weighted_f1']:.3f} | |
| Macro ROC-AUC (one-vs-rest) | {overall['macro_auc_ovr']:.3f} | |

## Per-class results

| Code | Class | Test images | Precision | Recall | F1 | AUC |
|---|---|---|---|---|---|---|
{pc_rows}

## Calibration

| Metric | Before temperature scaling | After (T = {T:.3f}) |
|---|---|---|
| Expected Calibration Error (15 bins) | {calibration['ece_before']:.3f} | {calibration['ece_after']:.3f} |
| Negative log-likelihood | {calibration['nll_before']:.3f} | {calibration['nll_after']:.3f} |
| Brier score | {calibration['brier_before']:.3f} | {calibration['brier_after']:.3f} |

## Triage safety (model + production rule engine)

| Measure | Value |
|---|---|
| Melanoma recall, model top-1 only | {s['melanoma_recall_model_only']:.1%} |
| Melanomas flagged **high** urgency after rules | {s['melanoma_flagged_high_with_rules']:.1%} |
| Melanomas flagged moderate or high | {s['melanoma_flagged_moderate_or_high']:.1%} |
| Malignant lesions (mel, bcc, akiec) flagged moderate or high | {s['malignant_flagged_moderate_or_high']:.1%} ({s['malignant_left_at_low']} of {s['n_malignant']} left at low) |
| Benign lesions flagged high (over-referral) | {s['benign_flagged_high']:.1%} |
| Benign lesions routed to low urgency | {s['benign_routed_low']:.1%} |
| Overall urgency mix (low / moderate / high) | {s['urgency_distribution']['low']:.1%} / {s['urgency_distribution']['moderate']:.1%} / {s['urgency_distribution']['high']:.1%} |

## Figures

- `confusion_matrix.png`: counts and row-normalised confusion matrices
- `per_class_metrics.png`: precision, recall and F1 per class
- `roc_curves.png`: one-vs-rest ROC curves with per-class AUC
- `reliability_diagram.png`: calibration before and after temperature scaling
- `urgency_by_true_class.png`: how the rule engine routes each true class
{"- `training_curves.png`: training loss and validation metrics per epoch" if has_curves else ""}

## Limitations

- HAM10000 contains **dermatoscopic** images; ordinary phone photos are a different domain and performance on them is unknown.
- The dataset comes mainly from Austrian and Australian clinics and under-represents darker skin types.
- Rare classes (df, vasc) have few test images, so their metrics have wide uncertainty.
- Rule-engine thresholds are illustrative and have not been clinically validated.
"""
    (REPORTS_DIR / "report.md").write_text(md)

    print(f"\nAccuracy {overall['accuracy']:.3f} | Balanced acc {overall['balanced_accuracy']:.3f} "
          f"| Macro F1 {overall['macro_f1']:.3f} | Macro AUC {overall['macro_auc_ovr']:.3f}")
    print(f"ECE {calibration['ece_before']:.3f} -> {calibration['ece_after']:.3f}")
    print(f"Melanoma: model recall {s['melanoma_recall_model_only']:.1%}, "
          f"flagged HIGH by rules {s['melanoma_flagged_high_with_rules']:.1%}")
    print(f"Benign over-referral to HIGH: {s['benign_flagged_high']:.1%}")
    print(f"\n✅ Report written to {REPORTS_DIR}/report.md (+ PNG figures and CSV tables)")


if __name__ == "__main__":
    main()
