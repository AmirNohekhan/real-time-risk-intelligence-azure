from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RISK_", env_file=".env", extra="ignore")
    environment: str = "local"
    model_path: Path = Path("artifacts/model_bundle.joblib")
    data_dir: Path = Path("data")
    review_threshold: float = Field(default=0.45, ge=0, le=1)
    block_threshold: float = Field(default=0.65, ge=0, le=1)
    false_negative_cost: float = Field(default=20.0, gt=0)
    false_positive_cost: float = Field(default=1.0, gt=0)
    event_hub_namespace: str | None = None
    event_hub_name: str = "events"
    service_bus_namespace: str | None = None
    service_bus_queue: str = "investigation-cases"
    storage_account: str | None = None
    storage_container: str = "risk-data"

    @model_validator(mode="after")
    def validate_threshold_order(self) -> "Settings":
        if self.review_threshold >= self.block_threshold:
            raise ValueError("review_threshold must be less than block_threshold")
        return self
