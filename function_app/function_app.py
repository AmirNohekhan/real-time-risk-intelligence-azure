import json
import os
from typing import Any

import azure.functions as func
import httpx
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage

app = func.FunctionApp()


def _score(payload: dict[str, Any]) -> dict[str, Any]:
    endpoint = os.environ["RISK_ENDPOINT_URL"]
    credential = DefaultAzureCredential()
    token = credential.get_token("https://ml.azure.com/.default").token
    response = httpx.post(endpoint, json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=10)
    response.raise_for_status()
    result: dict[str, Any] = response.json()
    return result


def _enqueue_case(prediction: dict[str, Any]) -> None:
    namespace = os.environ["RISK_SERVICE_BUS_NAMESPACE"]
    queue = os.getenv("RISK_SERVICE_BUS_QUEUE", "investigation-cases")
    client = ServiceBusClient(f"{namespace}.servicebus.windows.net", DefaultAzureCredential())
    message = ServiceBusMessage(json.dumps(prediction), message_id=prediction["event_id"],
                                correlation_id=prediction["correlation_id"])
    with client, client.get_queue_sender(queue) as sender:
        sender.send_messages(message)


@app.event_hub_message_trigger(arg_name="event", event_hub_name="risk-events",
    connection="RISK_EVENT_HUB_CONNECTION", consumer_group="$Default")
def process_event(event: func.EventHubEvent) -> None:
    """Validate at the AML boundary, score once per Event Hubs checkpoint, and enqueue work."""
    payload = json.loads(event.get_body().decode("utf-8"))
    prediction = _score(payload)
    if prediction["recommended_action"] in {"REVIEW", "BLOCK"}:
        _enqueue_case(prediction)
