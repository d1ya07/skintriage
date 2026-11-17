"""Export the best checkpoint to ONNX for the backend, and check it matches PyTorch.

Run:  python export_onnx.py
"""
import json
import shutil

import numpy as np
import onnxruntime as ort
import pandas as pd
import torch
from PIL import Image

from common import ARTIFACT_DIR, CKPT_DIR, PROCESSED_DIR, SPLITS_CSV, build_model, eval_transform


def main():
    ckpt = torch.load(CKPT_DIR / "model_best.pt", map_location="cpu", weights_only=False)
    model = build_model(len(ckpt["classes"]), pretrained=False)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    onnx_path = ARTIFACT_DIR / "skin_model.onnx"
    dummy = torch.randn(1, 3, ckpt["img_size"], ckpt["img_size"])
    common = dict(input_names=["input"], output_names=["logits"],
                  dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}})
    try:
        torch.onnx.export(model, (dummy,), str(onnx_path), opset_version=18,
                          external_data=False, **common)
    except Exception as e:  # older/newer exporter differences: fall back to the classic exporter
        print(f"(new exporter failed: {type(e).__name__}; using classic exporter)")
        torch.onnx.export(model, (dummy,), str(onnx_path), opset_version=17, dynamo=False, **common)

    # ---- Parity check on real test images
    df = pd.read_csv(SPLITS_CSV)
    sample = df[df.split == "test"].head(16)
    tf = eval_transform()
    x = torch.stack([tf(Image.open(PROCESSED_DIR / f"{i}.jpg").convert("RGB")) for i in sample.image_id])
    with torch.no_grad():
        torch_out = model(x).numpy()
    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    onnx_out = sess.run(None, {"input": x.numpy()})[0]
    diff = float(np.abs(torch_out - onnx_out).max())
    print(f"Max |PyTorch - ONNX| logit difference: {diff:.2e}")
    if diff > 1e-3:
        raise SystemExit("❌ ONNX output doesn't match PyTorch")

    meta = json.loads((CKPT_DIR / "model_meta.json").read_text())
    meta["onnx_file"] = onnx_path.name
    (ARTIFACT_DIR / "model_meta.json").write_text(json.dumps(meta, indent=2))
    extra = ARTIFACT_DIR / "skin_model.onnx.data"
    size_mb = onnx_path.stat().st_size / 1e6
    print(f"✅ Exported {onnx_path} ({size_mb:.1f} MB) + model_meta.json")
    if extra.exists():
        print(f"   Note: weights are in {extra.name}; keep it next to the .onnx file.")
    if meta.get("smoke_test"):
        print("⚠️  This is a SMOKE-TEST model. Run the full `python train.py` before using it for real.")


if __name__ == "__main__":
    main()
