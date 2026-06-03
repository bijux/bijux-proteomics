# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

import bijux_proteomics._atomic_files as atomic_files
from bijux_proteomics._atomic_files import atomic_copy_file, atomic_write_text


def test_atomic_write_text_commits_complete_text(tmp_path: Path) -> None:
    output_path = tmp_path / "artifact.json"

    atomic_write_text(output_path, '{"status":"ok"}\n')

    assert output_path.read_text(encoding="utf-8") == '{"status":"ok"}\n'
    assert not tuple(tmp_path.glob(".*.bijux-write-*.tmp"))


def test_atomic_write_text_replace_failure_leaves_no_partial_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_path = tmp_path / "artifact.json"

    def interrupted_replace(source: Path, destination: Path) -> None:
        raise RuntimeError(f"interrupted before replacing {destination}")

    monkeypatch.setattr(atomic_files.os, "replace", interrupted_replace)

    with pytest.raises(RuntimeError, match="interrupted before replacing"):
        atomic_write_text(output_path, '{"status":"partial"}\n')

    assert not output_path.exists()
    assert not tuple(tmp_path.glob(".*.bijux-write-*.tmp"))


def test_atomic_copy_file_replace_failure_preserves_previous_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "source.json"
    destination_path = tmp_path / "destination.json"
    source_path.write_text('{"version":2}\n', encoding="utf-8")
    destination_path.write_text('{"version":1}\n', encoding="utf-8")

    def interrupted_replace(source: Path, destination: Path) -> None:
        raise RuntimeError(f"interrupted before replacing {destination}")

    monkeypatch.setattr(atomic_files.os, "replace", interrupted_replace)

    with pytest.raises(RuntimeError, match="interrupted before replacing"):
        atomic_copy_file(source_path, destination_path)

    assert destination_path.read_text(encoding="utf-8") == '{"version":1}\n'
    assert not tuple(tmp_path.glob(".*.bijux-write-*.tmp"))
