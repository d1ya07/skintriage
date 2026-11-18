# SkinTriage model evaluation

Deployed model: **efficientnet_b0** (ONNX), trained 2026-11-18.
Test set: **3703 images** from HAM10000 + ISIC 2019 (BCN_20000, MSK), held out at **lesion level** (no lesion appears in both training and test).
Probabilities are temperature-scaled (T = 1.900) exactly as in the live app.

## Overall performance (test set, 95% bootstrap CI, 1000 resamples)

| Metric | Value | 95% CI |
|---|---|---|
| Accuracy | 0.739 | 0.725 to 0.754 |
| Balanced accuracy (mean per-class recall) | 0.656 | 0.624 to 0.687 |
| Macro F1 | 0.636 | 0.605 to 0.665 |
| Weighted F1 | 0.736 | |
| Macro ROC-AUC (one-vs-rest) | 0.932 | |

## Per-class results

| Code | Class | Test images | Precision | Recall | F1 | AUC |
|---|---|---|---|---|---|---|
| akiec | Actinic keratosis / intraepithelial carcinoma | 180 | 0.397 | 0.517 | 0.449 | 0.934 |
| bcc | Basal cell carcinoma | 505 | 0.691 | 0.820 | 0.750 | 0.966 |
| bkl | Benign keratosis-like lesion | 418 | 0.637 | 0.495 | 0.557 | 0.900 |
| df | Dermatofibroma | 37 | 0.576 | 0.514 | 0.543 | 0.928 |
| mel | Melanoma | 677 | 0.655 | 0.549 | 0.598 | 0.875 |
| nv | Melanocytic nevus (mole) | 1851 | 0.845 | 0.866 | 0.856 | 0.934 |
| vasc | Vascular lesion | 35 | 0.604 | 0.829 | 0.699 | 0.990 |

## Calibration

| Metric | Before temperature scaling | After (T = 1.900) |
|---|---|---|
| Expected Calibration Error (15 bins) | 0.116 | 0.016 |
| Negative log-likelihood | 0.834 | 0.699 |
| Brier score | 0.389 | 0.363 |

## Triage safety (model + production rule engine)

| Measure | Value |
|---|---|
| Melanoma recall, model top-1 only | 54.9% |
| Melanomas flagged **high** urgency after rules | 74.0% |
| Melanomas flagged moderate or high | 88.0% |
| Malignant lesions (mel, bcc, akiec) flagged moderate or high | 91.6% (114 of 1362 left at low) |
| Benign lesions flagged high (over-referral) | 18.6% |
| Benign lesions routed to low urgency | 68.5% |
| Overall urgency mix (low / moderate / high) | 46.4% / 27.2% / 26.4% |

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
