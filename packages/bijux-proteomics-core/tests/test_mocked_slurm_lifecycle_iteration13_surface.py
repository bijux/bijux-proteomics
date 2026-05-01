# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.external_exec_iteration13 import (
    SlurmLifecycleState,
    run_mocked_slurm_lifecycle,
)


def test_run_mocked_slurm_lifecycle_reports_success_and_log_collection() -> None:
    report = run_mocked_slurm_lifecycle(
        job_id="12345",
        outcome=SlurmLifecycleState.SUCCEEDED,
        collected_logs=("artifacts/slurm.out", "artifacts/slurm.err"),
    )

    assert report.final_state is SlurmLifecycleState.SUCCEEDED
    assert report.events[0].state is SlurmLifecycleState.SUBMITTED
    assert len(report.collected_logs) == 2
