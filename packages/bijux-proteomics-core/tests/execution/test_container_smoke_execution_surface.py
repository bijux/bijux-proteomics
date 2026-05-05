# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.providers.support import run_container_smoke_execution


def test_run_container_smoke_execution_captures_logs_and_artifacts() -> None:
    report = run_container_smoke_execution(
        image_tag="bijux-proteomics:runtime",
        command=("python3", "-m", "bijux_proteomics.cli", "--help"),
        expected_artifact_paths=("artifacts/smoke.log",),
    )

    assert report.passed is True
    assert report.exit_code == 0
    assert report.artifact_paths == ("artifacts/smoke.log",)
