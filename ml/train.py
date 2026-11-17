"""Train EfficientNet-B0 on HAM10000.

Quick pipeline check (about 1 to 2 min):  python train.py --smoke
Full training:                             python train.py
"""
import argparse
import json
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from torch import nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from common import (
    ARCH, CKPT_DIR, CLASS_NAMES, CLASSES, IMG_SIZE, MEAN, SEED, SPLITS_CSV, STD,
    build_model, eval_transform, expected_calibration_error, get_device, make_dataset,
    softmax, train_transform,
)


def collect_logits(model, loader, device):
    model.eval()
    all_logits, all_labels = [], []
    with torch.no_grad():
        for x, y in tqdm(loader, desc="  eval", leave=False):
            all_logits.append(model(x.to(device)).float().cpu().numpy())
            all_labels.append(y.numpy())
    return np.concatenate(all_logits), np.concatenate(all_labels)


def scores(logits, labels):
    preds = logits.argmax(axis=1)
    return {
        "accuracy": float(accuracy_score(labels, preds)),
        "balanced_accuracy": float(balanced_accuracy_score(labels, preds)),
        "macro_f1": float(f1_score(labels, preds, average="macro")),
    }


def fit_temperature(logits: np.ndarray, labels: np.ndarray) -> float:
    """Temperature scaling (Guo et al., 2017): one scalar T that minimises validation NLL."""
    lg = torch.tensor(logits, dtype=torch.float64)
    lb = torch.tensor(labels)
    log_t = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    opt = torch.optim.LBFGS([log_t], lr=0.1, max_iter=200)

    def closure():
        opt.zero_grad()
        loss = nn.functional.cross_entropy(lg / log_t.exp(), lb)
        loss.backward()
        return loss

    opt.step(closure)
    return float(log_t.exp().item())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--smoke", action="store_true", help="tiny run to check the pipeline")
    args = ap.parse_args()

    torch.manual_seed(SEED)
    np.random.seed(SEED)
    device = get_device()
    print(f"Device: {device}")

    if not SPLITS_CSV.exists():
        raise SystemExit("❌ Run `python prepare_data.py` first.")
    df = pd.read_csv(SPLITS_CSV)
    train_df, val_df, test_df = (df[df.split == s] for s in ("train", "val", "test"))
    if args.smoke:
        train_df = train_df.sample(frac=1, random_state=SEED).groupby("dx").head(40)
        val_df = val_df.sample(min(150, len(val_df)), random_state=SEED)
        test_df = test_df.sample(min(150, len(test_df)), random_state=SEED)
        args.epochs = 1
        print("🧪 SMOKE TEST: tiny subset, 1 epoch. Numbers will be meaningless.")
    print(f"Images: train {len(train_df)}, val {len(val_df)}, test {len(test_df)}")

    loader_kw = dict(batch_size=args.batch_size, num_workers=args.workers,
                     persistent_workers=args.workers > 0)
    train_dl = DataLoader(make_dataset(train_df, train_transform()), shuffle=True, **loader_kw)
    val_dl = DataLoader(make_dataset(val_df, eval_transform()), shuffle=False, **loader_kw)
    test_dl = DataLoader(make_dataset(test_df, eval_transform()), shuffle=False, **loader_kw)

    # Class weights: inverse-sqrt frequency (softer than full inverse, more stable training).
    counts = np.array([(train_df.dx == c).sum() for c in CLASSES], dtype=float)
    weights = (counts.sum() / (len(CLASSES) * np.maximum(counts, 1))) ** 0.5
    weights = weights / weights.mean()
    print("Class weights:", {c: round(float(w), 2) for c, w in zip(CLASSES, weights)})

    model = build_model().to(device)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=device))
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    CKPT_DIR.mkdir(exist_ok=True)
    best_path = CKPT_DIR / "model_best.pt"
    best_bal_acc, history = -1.0, []
    start = time.time()

    for epoch in range(1, args.epochs + 1):
        model.train()
        running, seen = 0.0, 0
        bar = tqdm(train_dl, desc=f"Epoch {epoch}/{args.epochs}")
        for x, y in bar:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()
            running += loss.item() * len(y)
            seen += len(y)
            bar.set_postfix(loss=f"{running / seen:.3f}")
        scheduler.step()

        val_logits, val_labels = collect_logits(model, val_dl, device)
        s = scores(val_logits, val_labels)
        s.update(epoch=epoch, train_loss=running / seen)
        history.append(s)
        flag = ""
        if s["balanced_accuracy"] > best_bal_acc:
            best_bal_acc = s["balanced_accuracy"]
            torch.save({"state_dict": model.state_dict(), "classes": CLASSES, "arch": ARCH,
                        "img_size": IMG_SIZE, "mean": MEAN, "std": STD, "epoch": epoch,
                        "val": s}, best_path)
            flag = "  ⭐ best so far, saved"
        print(f"  val acc {s['accuracy']:.3f} | balanced acc {s['balanced_accuracy']:.3f} | "
              f"macro F1 {s['macro_f1']:.3f}{flag}")

    print(f"\nTraining took {(time.time() - start) / 60:.1f} min")

    # ---- Reload the best epoch, calibrate on validation, quick test check.
    ckpt = torch.load(best_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["state_dict"])
    val_logits, val_labels = collect_logits(model, val_dl, device)
    temperature = fit_temperature(val_logits, val_labels)
    ece_before = expected_calibration_error(softmax(val_logits), val_labels)
    ece_after = expected_calibration_error(softmax(val_logits, temperature), val_labels)
    print(f"Temperature T = {temperature:.3f} | val ECE {ece_before:.3f} -> {ece_after:.3f}")

    test_logits, test_labels = collect_logits(model, test_dl, device)
    test_scores = scores(test_logits, test_labels)
    print(f"TEST: acc {test_scores['accuracy']:.3f} | balanced acc {test_scores['balanced_accuracy']:.3f} "
          f"| macro F1 {test_scores['macro_f1']:.3f}")

    meta = {
        "arch": ARCH,
        "classes": CLASSES,
        "class_names": CLASS_NAMES,
        "img_size": IMG_SIZE,
        "mean": MEAN,
        "std": STD,
        "temperature": temperature,
        "best_epoch": ckpt["epoch"],
        "val": ckpt["val"],
        "val_ece_before": ece_before,
        "val_ece_after": ece_after,
        "test_quick": test_scores,
        "smoke_test": args.smoke,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset": "HAM10000 (Tschandl et al., 2018), lesion-level 70/15/15 split",
    }
    (CKPT_DIR / "model_meta.json").write_text(json.dumps(meta, indent=2))
    (CKPT_DIR / "history.json").write_text(json.dumps(history, indent=2))
    print(f"✅ Saved {best_path} and model_meta.json")
    print("Next: python export_onnx.py")


if __name__ == "__main__":
    main()
