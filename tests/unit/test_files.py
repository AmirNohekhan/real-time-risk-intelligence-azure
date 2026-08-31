from pathlib import Path

import pytest

from risk_platform.files import atomic_write, atomic_write_text


def test_atomic_write_text_replaces_existing_content(tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "artifact.json"
    destination.parent.mkdir()
    destination.write_text("old", encoding="utf-8")

    atomic_write_text(destination, "new")

    assert destination.read_text(encoding="utf-8") == "new"
    assert list(destination.parent.iterdir()) == [destination]


def test_atomic_write_preserves_existing_file_when_writer_fails(tmp_path: Path) -> None:
    destination = tmp_path / "artifact"
    destination.write_text("known-good", encoding="utf-8")

    def fail(temporary: Path) -> None:
        temporary.write_text("partial", encoding="utf-8")
        raise RuntimeError("interrupted")

    with pytest.raises(RuntimeError, match="interrupted"):
        atomic_write(destination, fail)

    assert destination.read_text(encoding="utf-8") == "known-good"
    assert list(tmp_path.iterdir()) == [destination]
