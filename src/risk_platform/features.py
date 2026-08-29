import numpy as np
import pandas as pd

from risk_platform.domain import Event

FEATURE_NAMES = [
    "log_amount",
    "log_account_age",
    "log_frequency_30d",
    "amount_deviation",
    "velocity_1h",
    "velocity_24h",
    "new_device",
    "new_location",
    "recent_failure_rate",
    "historical_risk_rate",
    "hour_sin",
    "hour_cos",
    "is_weekend",
]


def _safe_ratio(a: pd.Series, b: pd.Series) -> pd.Series:
    return a / b.clip(lower=1.0)


def transform_frame(frame: pd.DataFrame) -> pd.DataFrame:
    ts = pd.to_datetime(frame["event_timestamp"], utc=True)
    out = pd.DataFrame(index=frame.index)
    out["log_amount"] = np.log1p(frame["amount"].clip(lower=0))
    out["log_account_age"] = np.log1p(frame["account_age_days"].clip(lower=0))
    out["log_frequency_30d"] = np.log1p(frame["historical_event_count_30d"].clip(lower=0))
    out["amount_deviation"] = _safe_ratio(frame["amount"], frame["historical_avg_amount"])
    out["velocity_1h"] = np.log1p(frame["events_1h"])
    out["velocity_24h"] = np.log1p(frame["events_24h"])
    out["new_device"] = frame["is_new_device"].astype(int)
    out["new_location"] = frame["is_new_location"].astype(int)
    out["recent_failure_rate"] = frame["recent_failure_rate"]
    out["historical_risk_rate"] = _safe_ratio(
        frame["historical_risk_count"], frame["historical_event_count_30d"]
    )
    hour = ts.dt.hour + ts.dt.minute / 60
    out["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    out["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    out["is_weekend"] = (ts.dt.dayofweek >= 5).astype(int)
    return out[FEATURE_NAMES].replace([np.inf, -np.inf], 0).fillna(0).astype(float)


def transform_event(event: Event) -> pd.DataFrame:
    return transform_frame(pd.DataFrame([event.model_dump(mode="json")]))


def reason_codes(event: Event, anomaly_score: float) -> list[str]:
    reasons: list[str] = []
    if event.amount > max(500, 3 * event.historical_avg_amount):
        reasons.append("AMOUNT_DEVIATION")
    if event.events_1h >= 8:
        reasons.append("HIGH_VELOCITY")
    if event.is_new_device:
        reasons.append("NEW_DEVICE")
    if event.is_new_location:
        reasons.append("NEW_LOCATION")
    if event.recent_failure_rate >= 0.35:
        reasons.append("RECENT_FAILURES")
    if event.historical_risk_count >= 3:
        reasons.append("RISK_HISTORY")
    if event.account_age_days < 14:
        reasons.append("NEW_ACCOUNT")
    if anomaly_score >= 0.65:
        reasons.append("BEHAVIORAL_ANOMALY")
    return reasons[:5] or ["NO_MATERIAL_RISK_SIGNAL"]
