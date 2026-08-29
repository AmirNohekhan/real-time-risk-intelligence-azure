import json
from datetime import UTC, datetime

from risk_platform.config import Settings
from risk_platform.data.synthetic import generate_dataset, write_dataset
from risk_platform.domain import Event
from risk_platform.events.ports import (
    FileIdempotencyStore,
    JsonlCasePublisher,
    JsonlPredictionStore,
)
from risk_platform.events.processor import EventProcessor
from risk_platform.inference.service import RiskScorer
from risk_platform.models.bundle import ModelBundle
from risk_platform.training import train


def main() -> None:
    settings = Settings()
    if not settings.model_path.exists():
        data = generate_dataset()
        write_dataset(data, settings.data_dir / "raw/events/year=2025/events.parquet")
        train(data, settings.model_path)
    processor = EventProcessor(
        RiskScorer(ModelBundle.load(settings.model_path), settings),
        FileIdempotencyStore(settings.data_dir / "demo/idempotency.txt"),
        JsonlCasePublisher(settings.data_dir / "demo/cases.jsonl"),
        JsonlPredictionStore(settings.data_dir / "demo/predictions.jsonl"),
    )
    base = dict(
        event_timestamp=datetime.now(UTC),
        account_age_days=900,
        historical_event_count_30d=40,
        historical_avg_amount=80,
        events_24h=8,
        recent_failure_rate=0.02,
        historical_risk_count=0,
        country_code="US",
    )
    scenarios = [
        ("normal", dict(entity_id="demo-normal", amount=55, events_1h=1)),
        ("large_amount", dict(entity_id="demo-large", amount=9000, events_1h=1)),
        ("high_velocity", dict(entity_id="demo-velocity", amount=400, events_1h=18, events_24h=40)),
        (
            "new_context",
            dict(
                entity_id="demo-context",
                amount=700,
                events_1h=6,
                is_new_device=True,
                is_new_location=True,
            ),
        ),
        (
            "compound_risk",
            dict(
                entity_id="demo-compound",
                amount=12000,
                account_age_days=2,
                events_1h=25,
                events_24h=60,
                is_new_device=True,
                is_new_location=True,
                recent_failure_rate=0.8,
                historical_risk_count=6,
            ),
        ),
    ]
    for name, changes in scenarios:
        prediction = processor.process(Event(**(base | changes)))
        print(
            json.dumps(
                {
                    "scenario": name,
                    **(prediction.model_dump(mode="json") if prediction else {"duplicate": True}),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
