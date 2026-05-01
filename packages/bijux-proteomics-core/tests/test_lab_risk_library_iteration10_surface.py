# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab_planning_iteration10 import (
    LabRiskAssessmentContext,
    LabRiskKind,
    evaluate_lab_risks,
)


def test_evaluate_lab_risks_triggers_material_control_and_instrument_boundaries() -> (
    None
):
    report = evaluate_lab_risks(
        LabRiskAssessmentContext(
            available_material_ng=200.0,
            required_material_ng=500.0,
            control_count=0,
            replicate_count=1,
            instrument_capacity_hours=5.0,
            requested_hours=7.0,
            ambiguous_target_peptide_count=2,
        )
    )

    kinds = {risk.kind for risk in report.triggered_risks}
    assert LabRiskKind.INSUFFICIENT_MATERIAL in kinds
    assert LabRiskKind.MISSING_CONTROLS in kinds
    assert LabRiskKind.POOR_REPLICATION in kinds
    assert LabRiskKind.INSTRUMENT_LIMIT in kinds
    assert LabRiskKind.AMBIGUOUS_TARGET_PEPTIDES in kinds
