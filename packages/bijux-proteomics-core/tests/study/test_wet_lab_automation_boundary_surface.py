# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.study.laboratory_plans import (
    WetLabAutomationBoundaryInput,
    enforce_wet_lab_automation_boundary,
)


def test_enforce_wet_lab_automation_boundary_refuses_execution_without_adapter_proof() -> (
    None
):
    report = enforce_wet_lab_automation_boundary(
        WetLabAutomationBoundaryInput(
            planning_payload_id="plan-10",
            requested_execution=True,
            adapter_proof_id=None,
        )
    )

    assert report.allowed_execution is False
    assert report.execution_label == "refused"
    assert "no adapter proof" in report.reason
