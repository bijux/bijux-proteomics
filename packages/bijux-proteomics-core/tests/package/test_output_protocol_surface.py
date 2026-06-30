# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

import bijux_proteomics._atomic_files as atomic_files
from bijux_proteomics.interfaces.support.output_protocol import artifact_output


def test_emit_json_writes_sorted_json_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_path = tmp_path / "artifact.json"
    echoed: list[str] = []
    monkeypatch.setattr(artifact_output.click, "echo", echoed.append)

    artifact_output._emit_json({"b": 2, "a": 1}, out_path=output_path)

    assert output_path.read_text(encoding="utf-8") == '{\n  "a": 1,\n  "b": 2\n}\n'
    assert echoed == ['{\n  "a": 1,\n  "b": 2\n}']


def test_write_text_output_replace_failure_leaves_no_partial_text_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "artifact.html"

    def interrupted_replace(source: Path, destination: Path) -> None:
        raise RuntimeError(f"interrupted before replacing {destination}")

    monkeypatch.setattr(atomic_files.os, "replace", interrupted_replace)

    with pytest.raises(RuntimeError, match="interrupted before replacing"):
        artifact_output._write_text_output(output_path, "<html>report</html>\n")

    assert not output_path.exists()
    assert not tuple(tmp_path.glob(".*.bijux-write-*.tmp"))
