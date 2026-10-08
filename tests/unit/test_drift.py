import numpy as np
import pandas as pd
import pytest

from risk_platform.monitoring.drift import drift_report, population_stability_index


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


def test_psi_is_large_for_shifted_distribution() -> None:
    rng = np.random.default_rng(0)
    reference = rng.normal(0, 1, 2000)
    shifted = rng.normal(2, 1, 2000)
    assert population_stability_index(reference, shifted) > 0.2


def test_psi_is_zero_for_constant_reference() -> None:
    assert population_stability_index(np.full(50, 3.0), np.arange(50, dtype=float)) == 0.0
