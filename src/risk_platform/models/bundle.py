from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator


@dataclass
class ModelBundle:
    classifier: BaseEstimator
    anomaly_detector: BaseEstimator
    anomaly_low: float
    anomaly_high: float
    version: str
    metrics: dict[str, float]

    def predict_supervised(self, features: pd.DataFrame) -> np.ndarray:
        probabilities = np.asarray(self.classifier.predict_proba(features), dtype=float)
        if probabilities.ndim != 2 or probabilities.shape != (len(features), 2):
            raise ValueError("classifier must return one two-class probability row per input")
        positive = probabilities[:, 1]
        if not np.isfinite(positive).all() or ((positive < 0) | (positive > 1)).any():
            raise ValueError("classifier returned invalid probabilities")
        return positive

    def predict_anomaly(self, features: pd.DataFrame) -> np.ndarray:
        raw = -np.asarray(self.anomaly_detector.score_samples(features), dtype=float)
        if raw.shape != (len(features),) or not np.isfinite(raw).all():
            raise ValueError("anomaly detector must return one finite score per input")
        if not np.isfinite([self.anomaly_low, self.anomaly_high]).all():
            raise ValueError("anomaly calibration bounds must be finite")
        scaled = (raw - self.anomaly_low) / max(self.anomaly_high - self.anomaly_low, 1e-9)
        return np.clip(scaled, 0, 1)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: Path) -> "ModelBundle":
        obj: Any = joblib.load(path)
        if not isinstance(obj, cls):
            raise TypeError("artifact is not a ModelBundle")
        return obj
