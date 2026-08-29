import json
from pathlib import Path

import numpy as np
import pandas as pd

from risk_platform.features import FEATURE_NAMES, transform_frame


def population_stability_index(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    ref = np.histogram(reference, bins=edges)[0] / len(reference)
    cur = np.histogram(current, bins=edges)[0] / len(current)
    ref, cur = np.clip(ref, 1e-6, None), np.clip(cur, 1e-6, None)
    return float(np.sum((cur - ref) * np.log(cur / ref)))


def drift_report(reference: pd.DataFrame, current: pd.DataFrame) -> dict[str, object]:
    a, b = transform_frame(reference), transform_frame(current)
    feature_psi = {
        name: population_stability_index(a[name].to_numpy(), b[name].to_numpy())
        for name in FEATURE_NAMES
    }
    return {
        "feature_psi": feature_psi,
        "alerting_features": [k for k, v in feature_psi.items() if v >= 0.2],
        "missing_rate": {k: float(v) for k, v in current.isna().mean().items()},
        "rows": {"reference": len(reference), "current": len(current)},
    }


def write_report(report: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
