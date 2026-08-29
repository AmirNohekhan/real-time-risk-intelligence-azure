from datetime import UTC, datetime
from time import perf_counter

from risk_platform.config import Settings
from risk_platform.decisioning import combine_scores, decide
from risk_platform.domain import Event, Prediction
from risk_platform.features import reason_codes, transform_event
from risk_platform.models.bundle import ModelBundle


class RiskScorer:
    def __init__(self, bundle: ModelBundle, settings: Settings | None = None):
        self.bundle, self.settings = bundle, settings or Settings()

    def score(self, event: Event) -> Prediction:
        started = perf_counter()
        features = transform_event(event)
        supervised = float(self.bundle.predict_supervised(features)[0])
        anomaly = float(self.bundle.predict_anomaly(features)[0])
        final = combine_scores(supervised, anomaly)
        category, action = decide(
            final, self.settings.review_threshold, self.settings.block_threshold
        )
        return Prediction(
            event_id=event.event_id,
            correlation_id=event.correlation_id,
            supervised_risk_probability=supervised,
            anomaly_score=anomaly,
            final_risk_score=final,
            risk_category=category,
            recommended_action=action,
            reason_codes=reason_codes(event, anomaly),
            model_version=self.bundle.version,
            prediction_timestamp=datetime.now(UTC),
            latency_ms=(perf_counter() - started) * 1000,
        )
