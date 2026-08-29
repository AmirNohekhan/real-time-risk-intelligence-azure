from datetime import datetime

import pytest
from pydantic import ValidationError

from risk_platform.decisioning import combine_scores, decide
from risk_platform.domain import Action, Event


def test_event_requires_timezone_and_valid_rates() -> None:
    with pytest.raises(ValidationError):
        Event(
            entity_id="x",
            event_timestamp=datetime(2025, 1, 1),
            amount=1,
            account_age_days=1,
            historical_event_count_30d=1,
            historical_avg_amount=1,
            events_1h=1,
            events_24h=1,
            recent_failure_rate=2,
            historical_risk_count=0,
        )


@pytest.mark.parametrize(
    ("score", "action"), [(0.1, Action.APPROVE), (0.5, Action.REVIEW), (0.8, Action.BLOCK)]
)
def test_decision_thresholds(score: float, action: Action) -> None:
    assert decide(score, 0.45, 0.75)[1] == action


def test_combination_is_bounded() -> None:
    assert combine_scores(1, 1) == 1
    assert combine_scores(0, 0) == 0
