import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from risk_platform.monitoring.drift import drift_report, population_stability_index, write_report


def test_psi_rejects_unusable_samples() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        population_stability_index(np.array([]), np.array([1.0]))
    with pytest.raises(ValueError, match="finite"):
        population_stability_index(np.array([1.0, np.nan]), np.array([1.0]))
    with pytest.raises(ValueError, match="bins"):
        population_stability_index(np.array([1.0]), np.array([1.0]), bins=1)


def test_psi_is_zero_for_identical_samples() -> None:
    sample = np.arange(100, dtype=float)
    assert population_stability_index(sample, sample) == pytest.approx(0.0)


def test_drift_report_rejects_empty_windows() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        drift_report(pd.DataFrame(), pd.DataFrame({"event_timestamp": ["2026-01-01"]}))


def test_psi_is_large_for_shifted_samples() -> None:
    reference = np.arange(1000, dtype=float)
    assert population_stability_index(reference, reference + 800) >= 0.2


def test_psi_is_zero_for_constant_reference() -> None:
    assert population_stability_index(np.ones(50), np.arange(50, dtype=float)) == 0.0


def test_write_report_round_trips_json(tmp_path: Path) -> None:
    report = {"feature_psi": {"log_amount": 0.05}, "alerting_features": []}
    path = tmp_path / "drift.json"
    write_report(report, path)
    assert json.loads(path.read_text()) == report
