from typing import Any

import numpy as np
import pandas as pd
import pytest

from risk_platform.models.bundle import ModelBundle


class StubEstimator:
    def __init__(self, *, probabilities: Any = None, scores: Any = None):
        self.probabilities = probabilities
        self.scores = scores

    def predict_proba(self, features: pd.DataFrame) -> Any:
        return self.probabilities

    def score_samples(self, features: pd.DataFrame) -> Any:
        return self.scores


def bundle(classifier: StubEstimator, anomaly: StubEstimator) -> ModelBundle:
    return ModelBundle(classifier, anomaly, 0.0, 1.0, "test", {})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "probabilities",
    [np.array([[0.2, np.nan]]), np.array([[0.2, 1.2]]), np.array([[0.2]])],
)
def test_supervised_prediction_rejects_invalid_output(probabilities: np.ndarray) -> None:
    model = bundle(StubEstimator(probabilities=probabilities), StubEstimator(scores=[-0.5]))
    with pytest.raises(ValueError, match="classifier"):
        model.predict_supervised(pd.DataFrame({"x": [1]}))


@pytest.mark.parametrize("scores", [np.array([np.inf]), np.array([0.1, 0.2])])
def test_anomaly_prediction_rejects_invalid_output(scores: np.ndarray) -> None:
    model = bundle(StubEstimator(probabilities=[[0.8, 0.2]]), StubEstimator(scores=scores))
    with pytest.raises(ValueError, match="anomaly detector"):
        model.predict_anomaly(pd.DataFrame({"x": [1]}))


def test_valid_predictions_are_returned_and_scaled() -> None:
    model = bundle(StubEstimator(probabilities=[[0.8, 0.2]]), StubEstimator(scores=[-0.5]))
    assert model.predict_supervised(pd.DataFrame({"x": [1]})).tolist() == [0.2]
    assert model.predict_anomaly(pd.DataFrame({"x": [1]})).tolist() == [0.5]
