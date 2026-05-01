# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.runtime_iteration07 import run_local_external_tool


def test_run_local_external_tool_executes_and_validates_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "tool-output.txt"
    report = run_local_external_tool(
        command=("sh", "-c", f"printf 'ok' > {artifact}"),
        timeout_seconds=5.0,
        env_overrides={"BIJUX_TEST_FLAG": "1"},
        expected_artifacts=(str(artifact),),
    )

    assert report.disposition.value == "completed"
    assert report.exit_code == 0
    assert report.validated_artifacts == (str(artifact),)
    assert report.missing_artifacts == ()


def test_run_local_external_tool_refuses_missing_binary() -> None:
    report = run_local_external_tool(
        command=("definitely_missing_binary_xyz", "--version"),
        timeout_seconds=1.0,
    )

    assert report.disposition.value == "refused"
    assert report.exit_code is None
