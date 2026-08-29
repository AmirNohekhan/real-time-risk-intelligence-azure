# Operations runbook

## Failed events

Event Hubs processing is at-least-once. Application idempotency claims `event_id` before side effects; production uses an atomic create in a durable store. A Function batch is checkpointed only after successful completion. Repeated endpoint failures exhaust Function retries and are routed by the configured operational handler to `raw/errors/` with correlation ID and exception class (never payload PII). Service Bus retries cases up to ten deliveries, then moves them to its DLQ. Operators inspect, remediate, and resubmit with the original message ID.

## Model rollout

Register immutable model bundles with MLflow/Azure ML, deploy a green deployment at zero traffic, run contract/smoke tests, shift 5% traffic, observe latency/error/prediction distributions, then advance. Roll back traffic to the prior deployment if SLOs or drift guards fail. Retain the exact feature contract and thresholds with each release.

## Suggested alerts

- API p95 > 250 ms for 10 minutes; failures > 1%; no requests during expected traffic.
- Event Hub consumer lag or Service Bus active count growing for 15 minutes; DLQ count > 0.
- Any schema rejection spike; feature missingness > 1%; PSI >= 0.2.
- Prediction/action distribution shifts by 25%; delayed-label recall below the governed floor.
