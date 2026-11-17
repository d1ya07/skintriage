"""Shared paths, class list, transforms, model and dataset."""
from pathlib import Path

import numpy as np

ML_DIR = Path(__file__).resolve().parent
DATA_DIR = ML_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed" / "images"
SPLITS_CSV = DATA_DIR / "processed" / "splits.csv"
CKPT_DIR = ML_DIR / "checkpoints"
REPORTS_DIR = ML_DIR / "reports"
ARTIFACT_DIR = ML_DIR.parent / "backend" / "app" / "ml" / "artifacts"

CLASSES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
CLASS_NAMES = {
    "akiec": "Actinic keratosis / intraepithelial carcinoma",
    "bcc": "Basal cell carcinoma",
    "bkl": "Benign keratosis-like lesion",
    "df": "Dermatofibroma",
    "mel": "Melanoma",
    "nv": "Melanocytic nevus (mole)",
    "vasc": "Vascular lesion",
}

ARCH = "efficientnet_b0"
IMG_SIZE = 224
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]
SEED = 42


def get_device():
    import torch

    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def build_model(num_classes: int = len(CLASSES), pretrained: bool = True):
    from torch import nn
    from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

    model = efficientnet_b0(weights=EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model


def train_transform():
    from torchvision import transforms as T

    return T.Compose([
        T.RandomResizedCrop(IMG_SIZE, scale=(0.6, 1.0)),
        T.RandomHorizontalFlip(),
        T.RandomVerticalFlip(),
        T.RandomRotation(20),
        T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.02),
        T.ToTensor(),
        T.Normalize(MEAN, STD),
    ])


def eval_transform():
    # The backend reproduces exactly this with Pillow + numpy.
    from torchvision import transforms as T

    return T.Compose([
        T.Resize(IMG_SIZE),
        T.CenterCrop(IMG_SIZE),
        T.ToTensor(),
        T.Normalize(MEAN, STD),
    ])


class HamDataset:
    """Module-level class so DataLoader workers can pickle it (macOS starts workers with 'spawn')."""

    def __init__(self, df, transform):
        self.ids = df["image_id"].tolist()
        self.labels = [CLASSES.index(d) for d in df["dx"]]
        self.transform = transform

    def __len__(self):
        return len(self.ids)

    def __getitem__(self, i):
        import torch
        from PIL import Image

        with Image.open(PROCESSED_DIR / f"{self.ids[i]}.jpg") as im:
            img = im.convert("RGB")
        return self.transform(img), torch.tensor(self.labels[i])


def make_dataset(df, transform):
    return HamDataset(df, transform)


def softmax(logits: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    z = logits / temperature
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def expected_calibration_error(probs: np.ndarray, labels: np.ndarray, n_bins: int = 15) -> float:
    conf = probs.max(axis=1)
    pred = probs.argmax(axis=1)
    correct = (pred == labels).astype(float)
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (conf > lo) & (conf <= hi)
        if mask.any():
            ece += mask.mean() * abs(correct[mask].mean() - conf[mask].mean())
    return float(ece)
