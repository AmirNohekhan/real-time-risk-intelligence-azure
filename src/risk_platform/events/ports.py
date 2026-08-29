from pathlib import Path
from typing import Protocol

from risk_platform.domain import InvestigationCase, Prediction


class IdempotencyStore(Protocol):
    def claim(self, event_id: str) -> bool: ...


class CasePublisher(Protocol):
    def publish(self, case: InvestigationCase) -> None: ...


class PredictionStore(Protocol):
    def write(self, prediction: Prediction) -> None: ...


class FileIdempotencyStore:
    def __init__(self, path: Path):
        self.path = path
        self._seen: set[str] = set()
        if path.exists():
            self._seen.update(path.read_text(encoding="utf-8").splitlines())

    def claim(self, event_id: str) -> bool:
        if event_id in self._seen:
            return False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._seen.add(event_id)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(event_id + "\n")
        return True


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
