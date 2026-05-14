# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.benchmarks import (
    WorkflowStartupBenchmarkInput,
    build_workflow_startup_benchmark_report,
)


def test_build_workflow_startup_benchmark_report_identifies_startup_bottleneck() -> (
    None
):
    report = build_workflow_startup_benchmark_report(
        WorkflowStartupBenchmarkInput(
            workflow_id="wf-dda-main",
            setup_seconds=3.2,
            artifact_initialization_seconds=5.8,
            bundle_initialization_seconds=2.4,
        )
    )

    assert report.total_startup_seconds == 11.4
    assert report.bottleneck_stage == "artifact_initialization"
