import os
import tempfile
from collections.abc import Callable
from pathlib import Path


def atomic_write(path: Path, writer: Callable[[Path], None]) -> None:
    """Write a file completely before atomically exposing it at its destination."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        writer(temporary_path)
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def atomic_write_text(path: Path, content: str) -> None:
    def write(temporary: Path) -> None:
        temporary.write_text(content, encoding="utf-8")

    atomic_write(path, write)
