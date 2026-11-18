"""Add the ISIC 2019 training images that are NOT already in HAM10000.

- Reads images straight from the zip (no unzip needed) and caches 300 px copies.
- Keeps the 7 HAM10000 classes. SCC (squamous cell carcinoma) is skipped so the
  backend, rule engine and tests keep working unchanged.
- Keeps the existing HAM10000 split exactly as it was, so old and new results
  stay comparable. New images are split 70/15/15 by lesion, stratified by class.

Run:  python add_isic2019.py
"""
import threading
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
from PIL import Image
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from common import CLASSES, DATA_DIR, PROCESSED_DIR, SEED, SPLITS_CSV

ISIC_DIR = DATA_DIR / "isic2019"
ZIP_PATH = ISIC_DIR / "ISIC_2019_Training_Input.zip"
GT_CSV = ISIC_DIR / "ISIC_2019_Training_GroundTruth.csv"
META_CSV = ISIC_DIR / "ISIC_2019_Training_Metadata.csv"
HAM_SPLITS = SPLITS_CSV.parent / "splits_ham.csv"

LABEL_MAP = {"MEL": "mel", "NV": "nv", "BCC": "bcc", "AK": "akiec",
             "BKL": "bkl", "DF": "df", "VASC": "vasc"}  # SCC and UNK are skipped


def main():
    for p in (ZIP_PATH, GT_CSV, META_CSV, HAM_SPLITS):
        if not p.exists():
            raise SystemExit(f"❌ Missing {p}")

    ham = pd.read_csv(HAM_SPLITS)
    ham["source"] = "HAM10000"
    ham_ids = set(ham["image_id"])
    print(f"HAM10000 split: {len(ham)} images (unchanged)")

    # ---- Labels: one-hot columns -> class code
    gt = pd.read_csv(GT_CSV)
    gt["label"] = gt[["MEL", "NV", "BCC", "AK", "BKL", "DF", "VASC", "SCC", "UNK"]].idxmax(axis=1)
    meta = pd.read_csv(META_CSV)
    df = gt[["image", "label"]].merge(meta[["image", "lesion_id", "age_approx", "sex",
                                            "anatom_site_general"]], on="image", how="left")
    print(f"ISIC 2019 ground truth: {len(df)} images")

    df = df[~df["image"].isin(ham_ids)]
    print(f"After removing images already in HAM10000: {len(df)}")
    skipped = (df["label"] == "SCC").sum()
    df = df[df["label"].isin(LABEL_MAP)].copy()
    print(f"After skipping {skipped} SCC images: {len(df)}")

    df["dx"] = df["label"].map(LABEL_MAP)
    df["image_id"] = df["image"]
    # MSK images have no lesion_id: treat each image as its own lesion.
    df["lesion_id"] = df["lesion_id"].fillna(df["image_id"])
    df["source"] = df["lesion_id"].astype(str).str.startswith("BCN").map(
        {True: "BCN_20000", False: "MSK"})
    df = df.rename(columns={"age_approx": "age", "anatom_site_general": "localization"})
    assert set(df["dx"]) <= set(CLASSES)

    # ---- Lesion-level split for the new images only
    lesions = df.groupby("lesion_id")["dx"].first().reset_index()
    train_l, rest_l = train_test_split(lesions, test_size=0.30, stratify=lesions["dx"],
                                       random_state=SEED)
    val_l, test_l = train_test_split(rest_l, test_size=0.50, stratify=rest_l["dx"],
                                     random_state=SEED)
    split_of = {**{l: "train" for l in train_l.lesion_id},
                **{l: "val" for l in val_l.lesion_id},
                **{l: "test" for l in test_l.lesion_id}}
    df["split"] = df["lesion_id"].map(split_of)
    assert df["split"].notna().all()
    assert not (set(train_l.lesion_id) & set(test_l.lesion_id)), "lesion leakage!"

    # ---- Read straight from the zip and cache resized copies
    with zipfile.ZipFile(ZIP_PATH) as zf:
        members = {Path(n).stem: n for n in zf.namelist() if n.lower().endswith(".jpg")}
    missing = set(df["image_id"]) - set(members)
    if missing:
        raise SystemExit(f"❌ {len(missing)} images not found in the zip, e.g. {sorted(missing)[:3]}. "
                         "Is the download complete?")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    local = threading.local()

    def resize(image_id: str):
        out = PROCESSED_DIR / f"{image_id}.jpg"
        if out.exists():
            return
        if not hasattr(local, "zf"):
            local.zf = zipfile.ZipFile(ZIP_PATH)  # one handle per thread (ZipFile is not thread-safe)
        with local.zf.open(members[image_id]) as fh, Image.open(fh) as im:
            im = im.convert("RGB")
            im.thumbnail((300, 300), Image.Resampling.LANCZOS)
            im.save(out, quality=95)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(tqdm(pool.map(resize, df["image_id"]), total=len(df), desc="Extracting + resizing"))

    # ---- Write the combined split
    cols = ["image_id", "lesion_id", "dx", "split", "age", "sex", "localization", "source"]
    combined = pd.concat([ham, df], ignore_index=True)
    combined = combined[[c for c in cols if c in combined.columns]]
    assert combined["image_id"].is_unique, "duplicate image ids!"
    combined.to_csv(SPLITS_CSV, index=False)

    print("\nImages per class and split (HAM10000 + ISIC 2019 extra):")
    table = pd.crosstab(combined["dx"], combined["split"])[["train", "val", "test"]]
    table["total"] = table.sum(axis=1)
    old = ham["dx"].value_counts()
    table["was (HAM only)"] = [old.get(c, 0) for c in table.index]
    table.loc["TOTAL"] = table.sum()
    print(table.to_string())
    print("\nImages by source:", combined["source"].value_counts().to_dict())
    print(f"✅ Wrote {SPLITS_CSV} ({len(combined)} images)")


if __name__ == "__main__":
    main()
