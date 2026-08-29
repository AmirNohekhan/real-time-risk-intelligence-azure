# Architecture decision records

## ADR-001 — Event Hubs for facts; Service Bus for work
**Decision:** ingest immutable activity with Event Hubs; enqueue only actionable investigation cases on Service Bus. **Why:** streaming needs partitions, throughput, retention, and replay; work needs per-message completion, duplicate detection, retries, and DLQ. **Trade-off:** two operational systems, but their semantics stay honest.

## ADR-002 — Calibrated gradient boosting plus Isolation Forest
**Decision:** use nonlinear supervised boosting and a normal-only anomaly detector. **Why:** tabular interactions, CPU efficiency, calibrated business decisions, and novel-pattern coverage. **Trade-off:** anomaly scores are relative and require monitoring; deep models would add cost without evidence of benefit.

## ADR-003 — Synchronous online inference
**Decision:** score on the event-processing hot path through a managed endpoint. **Why:** action is needed before downstream fulfillment. **Trade-off:** latency and endpoint cost; batch scoring remains appropriate for portfolio rescoring.

## ADR-004 — ADLS Gen2 and Parquet
**Decision:** retain immutable raw events and partitioned analytical outputs in ADLS. **Why:** low-cost durable replay plus broad analytical interoperability. **Trade-off:** small-file compaction and lifecycle management are required at scale.

## ADR-005 — Terraform
**Decision:** provision shared Azure resources declaratively. **Why:** reviewable, repeatable environments and destruction plans. **Trade-off:** ML assets evolve faster and remain Azure ML YAML/CLI resources.

## ADR-006 — Idempotency at application and broker boundaries
**Decision:** claim event IDs before side effects and use Service Bus message IDs/duplicate detection. **Why:** Event Hubs and Functions are at-least-once. **Trade-off:** the local file ledger is single-process; cloud deployment needs a conditional-write store with TTL and replay policy.

