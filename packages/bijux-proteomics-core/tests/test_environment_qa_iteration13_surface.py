# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.external_exec_iteration13 import (
    EnvironmentQaSnapshot,
    run_environment_qa_for_proteomics_workflows,
)


def test_run_environment_qa_for_proteomics_workflows_reports_missing_readiness_inputs() -> None:
    report = run_environment_qa_for_proteomics_workflows(
        EnvironmentQaSnapshot(
            python_version="3.12.2",
            os_name="linux",
            cpu_count=2,
            free_disk_gb=10.0,
            available_tools=("python3",),
            container_runtime_available=False,
            provider_ids=(),
            writable_paths=("tmp",),
        )
    )

    assert report.ready is False
    codes = {issue.code for issue in report.issues}
    assert "insufficient_cpu" in codes
    assert "missing_tools" in codes
    assert "artifacts_not_writable" in codes
