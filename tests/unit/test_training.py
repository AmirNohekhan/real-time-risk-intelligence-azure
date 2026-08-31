from pathlib import Path

import pandas as pd
import pytest

from risk_platform.data.synthetic import generate_dataset
from risk_platform.training import train


def test_training_rejects_missing_contract_columns(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="label"):
        train(pd.DataFrame({"event_timestamp": ["2026-01-01"]}), tmp_path / "model.joblib")


def test_training_rejects_one_class_temporal_splits(tmp_path: Path) -> None:
    frame = generate_dataset(100)
    frame["label"] = 0
    with pytest.raises(ValueError, match="both binary label classes"):
        train(frame, tmp_path / "model.joblib")


@pytest.mark.parametrize(("fn_cost", "fp_cost"), [(0, 1), (1, 0), (-1, 1)])
def test_training_rejects_non_positive_costs(
    tmp_path: Path, fn_cost: float, fp_cost: float
) -> None:
    with pytest.raises(ValueError, match="positive"):
        train(generate_dataset(100), tmp_path / "model.joblib", fn_cost, fp_cost)
