"""Loads the ONNX skin-lesion model once and turns a PIL image into class probabilities.

Preprocessing reproduces ml/common.py eval_transform exactly:
  Resize(shorter side = 224, bilinear) -> CenterCrop(224) -> /255 -> Normalize(mean, std)
"""
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

ARTIFACT_DIR = Path(__file__).with_name("artifacts")


class ModelUnavailable(RuntimeError):
    pass


class SkinModel:
    def __init__(self, model_dir: Path = ARTIFACT_DIR):
        meta_path = model_dir / "model_meta.json"
        if not meta_path.exists():
            raise ModelUnavailable(f"{meta_path} not found")
        self.meta = json.loads(meta_path.read_text())
        onnx_path = model_dir / self.meta.get("onnx_file", "skin_model.onnx")
        if not onnx_path.exists():
            raise ModelUnavailable(f"{onnx_path} not found")

        import onnxruntime as ort

        self.session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.classes: list[str] = self.meta["classes"]
        self.img_size: int = int(self.meta["img_size"])
        self.mean = np.array(self.meta["mean"], dtype=np.float32).reshape(3, 1, 1)
        self.std = np.array(self.meta["std"], dtype=np.float32).reshape(3, 1, 1)
        self.temperature = float(self.meta.get("temperature", 1.0))
        self.version = f"{self.meta.get('arch', 'model')}@{str(self.meta.get('trained_at', ''))[:10]}"

    def preprocess(self, img: Image.Image) -> np.ndarray:
        img = img.convert("RGB")
        s = self.img_size
        w, h = img.size
        if w <= h:
            new_w, new_h = s, int(s * h / w)
        else:
            new_w, new_h = int(s * w / h), s
        img = img.resize((new_w, new_h), Image.Resampling.BILINEAR)
        left = int(round((new_w - s) / 2.0))
        top = int(round((new_h - s) / 2.0))
        img = img.crop((left, top, left + s, top + s))
        x = np.asarray(img, dtype=np.float32) / 255.0  # HWC
        x = x.transpose(2, 0, 1)  # CHW
        x = (x - self.mean) / self.std
        return x[None].astype(np.float32)  # NCHW

    def predict(self, img: Image.Image) -> dict[str, float]:
        logits = self.session.run(None, {self.input_name: self.preprocess(img)})[0][0]
        z = logits.astype(np.float64) / self.temperature  # temperature-scaled (calibrated)
        z -= z.max()
        p = np.exp(z)
        p /= p.sum()
        return {c: float(v) for c, v in zip(self.classes, p)}


@lru_cache
def get_model() -> SkinModel:
    return SkinModel()


def predict(img: Image.Image) -> dict[str, float]:
    return get_model().predict(img)


def model_version() -> str:
    return get_model().version


def model_info() -> dict:
    m = get_model()
    keys = ["arch", "classes", "class_names", "img_size", "temperature", "best_epoch",
            "val", "val_ece_before", "val_ece_after", "test_quick", "trained_at", "dataset"]
    return {k: m.meta.get(k) for k in keys} | {"version": m.version}
