import sys
from types import SimpleNamespace
from typing import Any

from risk_platform.cloud.azure import AzureCasePublisher
from risk_platform.domain import InvestigationCase


class FakeSender:
    def __init__(self) -> None:
        self.message: Any = None

    def __enter__(self) -> "FakeSender":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def send_messages(self, message: Any) -> None:
        self.message = message


class FakeClient:
    def __init__(self, sender: FakeSender) -> None:
        self.sender = sender

    def get_queue_sender(self, queue: str) -> FakeSender:
        return self.sender


def test_azure_case_publisher_deduplicates_by_event_id(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    def message(body: str, **kwargs: Any) -> object:
        captured.update(body=body, **kwargs)
        return object()

    monkeypatch.setitem(
        sys.modules, "azure.servicebus", SimpleNamespace(ServiceBusMessage=message)
    )
    sender = FakeSender()
    publisher = AzureCasePublisher.__new__(AzureCasePublisher)
    publisher.queue = "cases"
    publisher.client = FakeClient(sender)
    case = InvestigationCase(
        event_id="2ec5385f-43e8-46a4-ab77-82278b929340",
        correlation_id="31cb59a9-bb55-4fd7-be48-2494c36295c2",
        priority="standard",
        reason_codes=["TEST"],
        risk_score=0.5,
    )

    publisher.publish(case)

    assert captured["message_id"] == str(case.event_id)
    assert captured["correlation_id"] == str(case.correlation_id)
