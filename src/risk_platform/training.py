import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier, IsolationForest
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from risk_platform.features import transform_frame
from risk_platform.models.bundle import ModelBundle


def temporal_split(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ordered = frame.sort_values("event_timestamp").reset_index(drop=True)
    a, b = int(len(ordered) * 0.7), int(len(ordered) * 0.85)
    return ordered.iloc[:a], ordered.iloc[a:b], ordered.iloc[b:]


def _cost_threshold(y: np.ndarray, p: np.ndarray, fn_cost: float, fp_cost: float) -> float:
    candidates = np.linspace(0.1, 0.9, 81)
    costs = [
        fn_cost * np.sum((p < t) & (y == 1)) + fp_cost * np.sum((p >= t) & (y == 0))
        for t in candidates
    ]
    return float(candidates[int(np.argmin(costs))])


def train(
    frame: pd.DataFrame, output: Path, fn_cost: float = 20, fp_cost: float = 1
) -> ModelBundle:
    train_df, validation_df, test_df = temporal_split(frame)
    x_train, x_val, x_test = map(transform_frame, (train_df, validation_df, test_df))
    y_train = train_df["label"].to_numpy()
    y_val = validation_df["label"].to_numpy()
    y_test = test_df["label"].to_numpy()
    base = HistGradientBoostingClassifier(
        max_iter=160,
        learning_rate=0.06,
        max_leaf_nodes=15,
        l2_regularization=1.0,
        class_weight="balanced",
        random_state=42,
    )
    calibrated = CalibratedClassifierCV(base, method="sigmoid", cv=3).fit(x_train, y_train)
    anomaly = IsolationForest(n_estimators=150, contamination=0.04, random_state=42, n_jobs=-1).fit(
        x_train[y_train == 0]
    )
    val_p = calibrated.predict_proba(x_val)[:, 1]
    threshold = _cost_threshold(y_val, val_p, fn_cost, fp_cost)
    p = calibrated.predict_proba(x_test)[:, 1]
    pred = p >= threshold
    metrics = {
        "roc_auc": float(roc_auc_score(y_test, p)),
        "pr_auc": float(average_precision_score(y_test, p)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "brier": float(brier_score_loss(y_test, p)),
        "optimized_threshold": threshold,
        "test_positive_rate": float(y_test.mean()),
    }
    raw = -anomaly.score_samples(x_train)
    bundle = ModelBundle(
        calibrated,
        anomaly,
        float(np.quantile(raw, 0.05)),
        float(np.quantile(raw, 0.99)),
        datetime.now(UTC).strftime("%Y%m%d.%H%M%S"),
        metrics,
    )
    bundle.save(output)
    metrics_path = output.with_suffix(".metrics.json")
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return bundle
