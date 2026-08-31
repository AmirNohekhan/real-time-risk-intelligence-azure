from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from risk_platform.data.synthetic import generate_dataset
from risk_platform.domain import Event
from risk_platform.events.ports import (
    FileIdempotencyStore,
    JsonlCasePublisher,
    JsonlPredictionStore,
)
from risk_platform.events.processor import EventProcessor
from risk_platform.inference.service import RiskScorer
from risk_platform.training import train


class FailingScorer:
    def score(self, event: Event) -> Any:
        raise RuntimeError("temporary scoring failure")


def test_processor_is_idempotent(tmp_path: Path) -> None:
    bundle = train(generate_dataset(600), tmp_path / "model.joblib")
    processor = EventProcessor(
        RiskScorer(bundle),
        FileIdempotencyStore(tmp_path / "ids"),
        JsonlCasePublisher(tmp_path / "cases"),
        JsonlPredictionStore(tmp_path / "predictions"),
    )
    event = Event(
        entity_id="x",
        event_timestamp=datetime.now(UTC),
        amount=20,
        account_age_days=50,
        historical_event_count_30d=20,
        historical_avg_amount=20,
        events_1h=1,
        events_24h=3,
        recent_failure_rate=0.1,
        historical_risk_count=0,
    )
    assert processor.process(event) is not None
    assert processor.process(event) is None
    assert len((tmp_path / "predictions").read_text().splitlines()) == 1


def test_processor_releases_claim_after_failure(tmp_path: Path) -> None:
    ids = FileIdempotencyStore(tmp_path / "ids")
    processor = EventProcessor(
        FailingScorer(),  # type: ignore[arg-type]
        ids,
        JsonlCasePublisher(tmp_path / "cases"),
        JsonlPredictionStore(tmp_path / "predictions"),
    )
    event = Event(
        entity_id="retryable",
        amount=20,
        account_age_days=50,
        historical_event_count_30d=20,
        historical_avg_amount=20,
        events_1h=1,
        events_24h=3,
        recent_failure_rate=0.1,
        historical_risk_count=0,
    )

    with pytest.raises(RuntimeError, match="temporary"):
        processor.process(event)

    assert ids.claim(str(event.event_id))
