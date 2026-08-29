from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RISK_", env_file=".env", extra="ignore")
    environment: str = "local"
    model_path: Path = Path("artifacts/model_bundle.joblib")
    data_dir: Path = Path("data")
    review_threshold: float = 0.45
    block_threshold: float = 0.65
    false_negative_cost: float = 20.0
    false_positive_cost: float = 1.0
    event_hub_namespace: str | None = None
    event_hub_name: str = "events"
    service_bus_namespace: str | None = None
    service_bus_queue: str = "investigation-cases"
    storage_account: str | None = None
    storage_container: str = "risk-data"
