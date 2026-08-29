import json
import os
from pathlib import Path
from typing import Any

from risk_platform.domain import Event
from risk_platform.inference.service import RiskScorer
from risk_platform.models.bundle import ModelBundle

SCORER: RiskScorer | None = None


def init() -> None:
    global SCORER
    root = Path(os.environ["AZUREML_MODEL_DIR"])
    artifact = next(root.rglob("model_bundle.joblib"))
    SCORER = RiskScorer(ModelBundle.load(artifact))


def run(raw_data: str) -> dict[str, Any]:
    if SCORER is None:
        raise RuntimeError("model is not initialized")
    event = Event.model_validate(json.loads(raw_data))
    return SCORER.score(event).model_dump(mode="json")
