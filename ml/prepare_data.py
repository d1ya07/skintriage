"""Find HAM10000 in data/raw, make a lesion-level stratified split, and cache resized images.

Run:  python prepare_data.py
"""
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from PIL import Image
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from common import CLASSES, PROCESSED_DIR, RAW_DIR, SEED, SPLITS_CSV


def load_metadata() -> pd.DataFrame:
    candidates = sorted(RAW_DIR.rglob("HAM10000_metadata*"))
    if not candidates:
        raise SystemExit(f"❌ HAM10000_metadata.csv not found anywhere under {RAW_DIR}")
    path = candidates[0]
    sep = "\t" if path.suffix == ".tab" else ","
    df = pd.read_csv(path, sep=sep)
    print(f"Metadata: {path.relative_to(RAW_DIR)}  ({len(df)} rows)")
    return df


def main():
    meta = load_metadata()

    images = {}
    for p in RAW_DIR.rglob("*.jpg"):
        images.setdefault(p.stem, p)  # Kaggle ships duplicate folders; keep the first copy
    print(f"Found {len(images)} unique .jpg images")

    meta = meta[meta["image_id"].isin(images)].copy()
    missing = set(meta["dx"]) - set(CLASSES)
    if missing:
        raise SystemExit(f"❌ Unexpected classes in metadata: {missing}")
    if len(meta) < 10000:
        print(f"⚠️  Only {len(meta)} images matched metadata (expected 10015). Is the download complete?")

    # ---- Split by LESION, not by image, so the same lesion never appears in two splits.
    lesions = meta.groupby("lesion_id")["dx"].first().reset_index()
    train_l, rest_l = train_test_split(
        lesions, test_size=0.30, stratify=lesions["dx"], random_state=SEED
    )
    val_l, test_l = train_test_split(
        rest_l, test_size=0.50, stratify=rest_l["dx"], random_state=SEED
    )
    split_of = {**{l: "train" for l in train_l.lesion_id},
                **{l: "val" for l in val_l.lesion_id},
                **{l: "test" for l in test_l.lesion_id}}
    meta["split"] = meta["lesion_id"].map(split_of)

    assert not (set(train_l.lesion_id) & set(test_l.lesion_id)), "lesion leakage!"

    # ---- Cache downsized copies (600x450 -> 300x225) for much faster training.
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    def resize(image_id: str):
        out = PROCESSED_DIR / f"{image_id}.jpg"
        if out.exists():
            return
        with Image.open(images[image_id]) as im:
            im = im.convert("RGB")
            im.thumbnail((300, 300), Image.Resampling.LANCZOS)
            im.save(out, quality=95)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(tqdm(pool.map(resize, meta["image_id"]), total=len(meta), desc="Resizing"))

    cols = ["image_id", "lesion_id", "dx", "split", "age", "sex", "localization"]
    meta[[c for c in cols if c in meta.columns]].to_csv(SPLITS_CSV, index=False)

    print("\nImages per class and split:")
    table = pd.crosstab(meta["dx"], meta["split"])[["train", "val", "test"]]
    table.loc["TOTAL"] = table.sum()
    print(table.to_string())
    print(f"\nLesions: train {len(train_l)}, val {len(val_l)}, test {len(test_l)}")
    print(f"✅ Wrote {SPLITS_CSV}")


if __name__ == "__main__":
    main()
