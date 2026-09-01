from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from risk_platform.domain import Action, InvestigationCase, Prediction, RiskCategory
from risk_platform.events.ports import JsonlCasePublisher, JsonlPredictionStore


def prediction(event_id: object) -> Prediction:
    return Prediction(
        event_id=event_id,
        correlation_id=uuid4(),
        supervised_risk_probability=0.5,
        anomaly_score=0.5,
        final_risk_score=0.5,
        risk_category=RiskCategory.MEDIUM,
        recommended_action=Action.REVIEW,
        reason_codes=["TEST"],
        model_version="test",
        prediction_timestamp=datetime.now(UTC),
        latency_ms=1,
    )  # type: ignore[arg-type]


def test_prediction_store_deduplicates_event_across_restarts(tmp_path: Path) -> None:
    path = tmp_path / "predictions.jsonl"
    item = prediction(uuid4())

    JsonlPredictionStore(path).write(item)
    JsonlPredictionStore(path).write(item.model_copy(update={"correlation_id": uuid4()}))

    assert len(path.read_text(encoding="utf-8").splitlines()) == 1


def test_case_publisher_deduplicates_by_event_not_case(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    event_id = uuid4()
    first = InvestigationCase(
        event_id=event_id,
        correlation_id=uuid4(),
        priority="standard",
        reason_codes=["TEST"],
        risk_score=0.5,
    )

    publisher = JsonlCasePublisher(path)
    publisher.publish(first)
    publisher.publish(first.model_copy(update={"case_id": uuid4()}))

    assert len(path.read_text(encoding="utf-8").splitlines()) == 1


def test_event_store_rejects_corrupt_existing_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "predictions.jsonl"
    path.write_text("not-json\n", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid JSONL record"):
        JsonlPredictionStore(path)
