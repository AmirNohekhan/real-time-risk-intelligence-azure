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

    def publish(self, case: InvestigationCase) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(case.model_dump_json() + "\n")


class JsonlPredictionStore:
    def __init__(self, path: Path):
        self.path = path

    def write(self, prediction: Prediction) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(prediction.model_dump_json() + "\n")
