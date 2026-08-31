import pytest
from pydantic import ValidationError

from risk_platform.config import Settings


@pytest.mark.parametrize(
    "overrides",
    [
        {"review_threshold": 0.8, "block_threshold": 0.7},
        {"review_threshold": -0.1},
        {"block_threshold": 1.1},
        {"false_negative_cost": 0},
        {"false_positive_cost": -1},
    ],
)
def test_settings_reject_invalid_risk_policy(overrides: dict[str, float]) -> None:
    with pytest.raises(ValidationError):
        Settings(**overrides)  # type: ignore[arg-type]


def test_settings_accept_valid_risk_policy() -> None:
    settings = Settings(review_threshold=0.4, block_threshold=0.8)
    assert settings.review_threshold == 0.4
    assert settings.block_threshold == 0.8
