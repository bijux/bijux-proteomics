from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics_dev.tools.manage_models import (
    _resolve_command,
    find_latest_version,
)


def test_find_latest_version_requires_prepared_marker(tmp_path: Path) -> None:
    first = tmp_path / "2026-01-01"
    second = tmp_path / "2026-01-02"
    first.mkdir()
    second.mkdir()
    (first / ".prepared.ok").write_text("", encoding="utf-8")
    (second / ".prepared.ok").write_text("", encoding="utf-8")

    latest = find_latest_version(tmp_path)

    assert latest == second


def test_resolve_command_rejects_missing_executable() -> None:
    with pytest.raises(FileNotFoundError):
        _resolve_command(["definitely-not-a-real-bijux-command"])

