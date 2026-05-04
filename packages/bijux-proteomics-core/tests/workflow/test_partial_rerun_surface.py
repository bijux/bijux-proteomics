# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.workflow.reproducibility import (
    PartialWorkflowRerunRequest,
    WorkflowStepExecutionStatus,
    WorkflowStepRunState,
    plan_partial_workflow_rerun,
)


def test_plan_partial_workflow_rerun_expands_dependencies_and_preserves_evidence() -> (
    None
):
    plan = plan_partial_workflow_rerun(
        request=PartialWorkflowRerunRequest(
            prior_run_id="run-1",
            selected_step_ids=("search",),
        ),
        step_states=(
            WorkflowStepRunState(
                step_id="intake",
                status=WorkflowStepExecutionStatus.SUCCEEDED,
                output_artifacts=("a",),
                evidence_pointers=("ev-intake",),
            ),
            WorkflowStepRunState(
                step_id="search",
                status=WorkflowStepExecutionStatus.FAILED,
                depends_on=("intake",),
                output_artifacts=("b",),
                evidence_pointers=("ev-search",),
            ),
            WorkflowStepRunState(
                step_id="quant",
                status=WorkflowStepExecutionStatus.SKIPPED,
                depends_on=("search",),
                output_artifacts=("c",),
                evidence_pointers=("ev-quant",),
            ),
        ),
    )

    assert plan.rerun_step_ids == ("search", "quant")
    assert plan.reused_step_ids == ("intake",)
    assert plan.preserved_evidence_pointers == ("ev-intake",)
