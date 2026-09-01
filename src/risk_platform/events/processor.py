from uuid import NAMESPACE_URL, UUID, uuid5

from risk_platform.domain import Action, Event, InvestigationCase, Prediction
from risk_platform.events.ports import CasePublisher, IdempotencyStore, PredictionStore
from risk_platform.inference.service import RiskScorer


def investigation_case_id(event_id: UUID) -> UUID:
    """Return a stable case identity so retries address the same investigation."""
    return uuid5(NAMESPACE_URL, f"risk-platform:investigation:{event_id}")


class EventProcessor:
    def __init__(
        self,
        scorer: RiskScorer,
        idempotency: IdempotencyStore,
        cases: CasePublisher,
        predictions: PredictionStore,
    ):
        self.scorer, self.idempotency, self.cases, self.predictions = (
            scorer,
            idempotency,
            cases,
            predictions,
        )

    def process(self, event: Event) -> Prediction | None:
        event_id = str(event.event_id)
        if not self.idempotency.claim(event_id):
            return None
        try:
            prediction = self.scorer.score(event)
            self.predictions.write(prediction)
            if prediction.recommended_action in {Action.REVIEW, Action.BLOCK}:
                self.cases.publish(
                    InvestigationCase(
                        case_id=investigation_case_id(event.event_id),
                        event_id=event.event_id,
                        correlation_id=event.correlation_id,
                        priority="critical"
                        if prediction.recommended_action == Action.BLOCK
                        else "standard",
                        reason_codes=prediction.reason_codes,
                        risk_score=prediction.final_risk_score,
                        payload={"model_version": prediction.model_version},
                    )
                )
            return prediction
        except Exception:
            self.idempotency.release(event_id)
            raise
