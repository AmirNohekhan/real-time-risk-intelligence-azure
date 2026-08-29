from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Action(StrEnum):
    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class RiskCategory(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    schema_version: str = "1.0"
    event_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    entity_id: str = Field(min_length=1, max_length=128)
    event_type: str = Field(default="activity", min_length=1, max_length=64)
    amount: float = Field(ge=0, le=10_000_000)
    account_age_days: int = Field(ge=0, le=40_000)
    historical_event_count_30d: int = Field(ge=0, le=1_000_000)
    historical_avg_amount: float = Field(ge=0, le=10_000_000)
    events_1h: int = Field(ge=0, le=100_000)
    events_24h: int = Field(ge=0, le=1_000_000)
    is_new_device: bool = False
    is_new_location: bool = False
    recent_failure_rate: float = Field(ge=0, le=1)
    historical_risk_count: int = Field(ge=0, le=1_000_000)
    country_code: str = Field(default="US", pattern=r"^[A-Z]{2}$")

    @field_validator("event_timestamp")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("event_timestamp must include a timezone")
        return value


class Prediction(BaseModel):
    event_id: UUID
    correlation_id: UUID
    supervised_risk_probability: float = Field(ge=0, le=1)
    anomaly_score: float = Field(ge=0, le=1)
    final_risk_score: float = Field(ge=0, le=1)
    risk_category: RiskCategory
    recommended_action: Action
    reason_codes: list[str]
    model_version: str
    prediction_timestamp: datetime
    latency_ms: float = Field(ge=0)


class InvestigationCase(BaseModel):
    case_id: UUID = Field(default_factory=uuid4)
    event_id: UUID
    correlation_id: UUID
    priority: str
    reason_codes: list[str]
    risk_score: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = Field(default_factory=dict)
