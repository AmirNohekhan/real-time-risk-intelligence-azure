from datetime import UTC, datetime

import pandas as pd

from risk_platform.domain import Event
from risk_platform.features import FEATURE_NAMES, reason_codes, transform_frame


def test_features_are_finite_and_stable() -> None:
    frame = pd.DataFrame(
        [
            {
                "event_timestamp": datetime.now(UTC),
                "amount": 100,
                "account_age_days": 0,
                "historical_event_count_30d": 0,
                "historical_avg_amount": 0,
                "events_1h": 2,
                "events_24h": 3,
                "is_new_device": True,
                "is_new_location": False,
                "recent_failure_rate": 0.1,
                "historical_risk_count": 0,
            }
        ]
    )
    result = transform_frame(frame)
    assert list(result) == FEATURE_NAMES
    assert result.notna().all().all()


def test_reason_codes_are_explainable() -> None:
    event = Event(
        entity_id="x",
        amount=1000,
        account_age_days=2,
        historical_event_count_30d=2,
        historical_avg_amount=20,
        events_1h=10,
        events_24h=12,
        is_new_device=True,
        recent_failure_rate=0.5,
        historical_risk_count=3,
    )
    assert {"AMOUNT_DEVIATION", "HIGH_VELOCITY", "NEW_DEVICE"}.issubset(reason_codes(event, 0.8))
