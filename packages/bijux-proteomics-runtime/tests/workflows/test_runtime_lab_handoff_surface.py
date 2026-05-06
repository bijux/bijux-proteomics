# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_lab.handoffs.ptm import (
    PtmLabAssayRisk,
    PtmLabValidationPacket,
    PtmLabValidationTargetEntry,
)
from bijux_proteomics_runtime.workflows.runs import run_lab_handoff_workflow_end_to_end


def test_run_lab_handoff_workflow_end_to_end_tracks_unresolved_risks() -> None:
    packet = PtmLabValidationPacket(
        entries=(
            PtmLabValidationTargetEntry(
                site_key="P11111:S5:Phospho",
                target_peptides=("S[Phospho]PEPTIDEK",),
                ambiguous_site=False,
                assay_risk=PtmLabAssayRisk.LOW,
                recommended_controls=("matrix_control",),
                evidence_needs=("site_localization_fragments",),
            ),
            PtmLabValidationTargetEntry(
                site_key="P22222:T9:Phospho",
                target_peptides=("T[Phospho]IDEK",),
                ambiguous_site=True,
                assay_risk=PtmLabAssayRisk.HIGH,
                recommended_controls=("co_localization_control",),
                evidence_needs=("orthogonal_confirmation",),
            ),
        ),
        unresolved_risk_count=1,
    )

    report = run_lab_handoff_workflow_end_to_end(packet)

    assert report.status.value == "completed"
    assert report.review_target_count == 2
    assert report.planned_assay_count == 2
    assert report.unresolved_risk_count == 1
    assert report.export_file_count == 3
    assert report.steps[-1].step_id == "report-unresolved-risk"
