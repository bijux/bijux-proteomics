# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.benchmarks import (
    DependencyUpdateRecord,
    WorkflowDependencyMapping,
    build_dependency_update_replay_report,
)


def test_build_dependency_update_replay_report_marks_affected_workflows() -> None:
    report = build_dependency_update_replay_report(
        updates=(
            DependencyUpdateRecord(
                dependency_id="diann",
                surface="quant_engine",
                previous_version="1.8.1",
                updated_version="1.9.0",
            ),
        ),
        mappings=(
            WorkflowDependencyMapping(
                workflow_id="wf-quant",
                dependency_surfaces=("quant_engine", "container_runtime"),
            ),
            WorkflowDependencyMapping(
                workflow_id="wf-qc",
                dependency_surfaces=("qc_rules",),
            ),
        ),
    )

    by_workflow = {action.workflow_id: action for action in report.actions}
    assert by_workflow["wf-quant"].replay_required is True
    assert by_workflow["wf-qc"].replay_required is False
