import json
from typing import Any

from risk_platform.domain import InvestigationCase


class AzureCasePublisher:
    def __init__(self, namespace: str, queue: str):
        from azure.identity import DefaultAzureCredential
        from azure.servicebus import ServiceBusClient

        self.queue = queue
        self.client = ServiceBusClient(
            f"{namespace}.servicebus.windows.net", DefaultAzureCredential()
        )

    def publish(self, case: InvestigationCase) -> None:
        from azure.servicebus import ServiceBusMessage

        with self.client.get_queue_sender(self.queue) as sender:
            sender.send_messages(
                ServiceBusMessage(
                    case.model_dump_json(),
                    message_id=str(case.case_id),
                    correlation_id=str(case.correlation_id),
                )
            )


class EventHubPublisher:
    def __init__(self, namespace: str, hub: str):
        from azure.eventhub import EventHubProducerClient
        from azure.identity import DefaultAzureCredential

        self.client = EventHubProducerClient(
            f"{namespace}.servicebus.windows.net", hub, credential=DefaultAzureCredential()
        )

    def publish(self, payload: dict[str, Any]) -> None:
        from azure.eventhub import EventData

        batch = self.client.create_batch()
        batch.add(EventData(json.dumps(payload)))
        self.client.send_batch(batch)
