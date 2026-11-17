# SkinTriage model evaluation

Deployed model: **efficientnet_b0** (ONNX), trained 2026-11-17.
Test set: **1502 images** from HAM10000, held out at **lesion level** (no lesion appears in both training and test).
Probabilities are temperature-scaled (T = 1.363) exactly as in the live app.

## Overall performance (test set, 95% bootstrap CI, 1000 resamples)

| Metric | Value | 95% CI |
|---|---|---|
| Accuracy | 0.814 | 0.795 to 0.833 |
| Balanced accuracy (mean per-class recall) | 0.722 | 0.672 to 0.768 |
| Macro F1 | 0.691 | 0.644 to 0.730 |
| Weighted F1 | 0.813 | |
| Macro ROC-AUC (one-vs-rest) | 0.960 | |

## Per-class results

| Code | Class | Test images | Precision | Recall | F1 | AUC |
|---|---|---|---|---|---|---|
| akiec | Actinic keratosis / intraepithelial carcinoma | 52 | 0.558 | 0.827 | 0.667 | 0.983 |
| bcc | Basal cell carcinoma | 71 | 0.707 | 0.817 | 0.758 | 0.986 |
| bkl | Benign keratosis-like lesion | 167 | 0.690 | 0.467 | 0.557 | 0.940 |
| df | Dermatofibroma | 20 | 0.625 | 0.750 | 0.682 | 0.957 |
| mel | Melanoma | 167 | 0.547 | 0.623 | 0.583 | 0.907 |
| nv | Melanocytic nevus (mole) | 1004 | 0.914 | 0.906 | 0.910 | 0.952 |
| vasc | Vascular lesion | 21 | 0.700 | 0.667 | 0.683 | 0.994 |

## Calibration

| Metric | Before temperature scaling | After (T = 1.363) |
|---|---|---|
| Expected Calibration Error (15 bins) | 0.051 | 0.020 |
| Negative log-likelihood | 0.516 | 0.492 |
| Brier score | 0.261 | 0.256 |

## Triage safety (model + production rule engine)

| Measure | Value |
|---|---|
| Melanoma recall, model top-1 only | 62.3% |
| Melanomas flagged **high** urgency after rules | 76.6% |
| Melanomas flagged moderate or high | 84.4% |
| Malignant lesions (mel, bcc, akiec) flagged moderate or high | 89.0% (32 of 290 left at low) |
| Benign lesions flagged high (over-referral) | 15.7% |
| Benign lesions routed to low urgency | 78.0% |
| Overall urgency mix (low / moderate / high) | 65.0% / 13.3% / 21.6% |

## Figures

- `confusion_matrix.png`: counts and row-normalised confusion matrices
- `per_class_metrics.png`: precision, recall and F1 per class
- `roc_curves.png`: one-vs-rest ROC curves with per-class AUC
- `reliability_diagram.png`: calibration before and after temperature scaling
- `urgency_by_true_class.png`: how the rule engine routes each true class
- `training_curves.png`: training loss and validation metrics per epoch

## Limitations

- HAM10000 contains **dermatoscopic** images; ordinary phone photos are a different domain and performance on them is unknown.
- The dataset comes mainly from Austrian and Australian clinics and under-represents darker skin types.
- Rare classes (df, vasc) have few test images, so their metrics have wide uncertainty.
- Rule-engine thresholds are illustrative and have not been clinically validated.
