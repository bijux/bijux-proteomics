# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab_planning_iteration10 import (
    TargetedWorkflowBoundaryInput,
    TargetedWorkflowMethod,
    evaluate_targeted_workflow_boundary,
)


def test_evaluate_targeted_workflow_boundary_refuses_when_required_assumptions_missing() -> (
    None
):
    report = evaluate_targeted_workflow_boundary(
        TargetedWorkflowBoundaryInput(
            method=TargetedWorkflowMethod.PRM,
            has_transition_list=True,
            has_retention_windows=False,
            has_collision_energy_profile=False,
            has_instrument_method_template=True,
        )
    )

    assert report.supported is False
    assert report.refusal_reason is not None
    assert "retention_windows" in report.refusal_reason
