import json
from pathlib import Path
from threading import Lock
from typing import Protocol

from risk_platform.domain import InvestigationCase, Prediction
from risk_platform.files import atomic_write_text


class IdempotencyStore(Protocol):
    def claim(self, event_id: str) -> bool: ...

    def release(self, event_id: str) -> None: ...


class CasePublisher(Protocol):
    def publish(self, case: InvestigationCase) -> None: ...


class PredictionStore(Protocol):
    def write(self, prediction: Prediction) -> None: ...


class FileIdempotencyStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()
        self._seen: set[str] = set()
        if path.exists():
            self._seen.update(path.read_text(encoding="utf-8").splitlines())

    def claim(self, event_id: str) -> bool:
        with self._lock:
            if event_id in self._seen:
                return False
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(event_id + "\n")
            self._seen.add(event_id)
            return True

    def release(self, event_id: str) -> None:
        """Release a failed claim so the event can be retried."""
        with self._lock:
            if event_id not in self._seen:
                return
            remaining = self._seen - {event_id}
            atomic_write_text(
                self.path, "".join(f"{seen_id}\n" for seen_id in sorted(remaining))
            )
            self._seen = remaining


class JsonlCasePublisher:
    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()
        self._stored = _load_event_ids(path)

    def publish(self, case: InvestigationCase) -> None:
        event_id = str(case.event_id)
        with self._lock:
            if event_id in self._stored:
                return
            _append_json_line(self.path, case.model_dump_json())
            self._stored.add(event_id)


class JsonlPredictionStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()
        self._stored = _load_event_ids(path)

    def write(self, prediction: Prediction) -> None:
        event_id = str(prediction.event_id)
        with self._lock:
            if event_id in self._stored:
                return
            _append_json_line(self.path, prediction.model_dump_json())
            self._stored.add(event_id)


def _load_event_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    event_ids: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            event_ids.add(str(json.loads(line)["event_id"]))
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            raise ValueError(f"invalid JSONL record at {path}:{line_number}") from error
    return event_ids


def _append_json_line(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(payload + "\n")
