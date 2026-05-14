# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.workflows.runs import (
    DiaPrecursorQuantInput,
    run_dia_import_workflow_end_to_end,
)


def test_run_dia_import_workflow_end_to_end_tracks_quant_and_qc() -> None:
    rows = (
        DiaPrecursorQuantInput(
            precursor_id="P1_2",
            peptide="PEPTIDEK",
            protein_ref="P11111",
            sample_id="S1",
            intensity=1200.0,
        ),
        DiaPrecursorQuantInput(
            precursor_id="P1_2",
            peptide="PEPTIDEK",
            protein_ref="P11111",
            sample_id="S2",
            intensity=980.0,
        ),
        DiaPrecursorQuantInput(
            precursor_id="P2_3",
            peptide="PEPTIDER",
            protein_ref="Q22222",
            sample_id="S1",
            intensity=None,
        ),
    )

    report = run_dia_import_workflow_end_to_end(rows)

    assert report.status.value == "completed"
    assert report.precursor_count == 2
    assert report.peptide_count == 2
    assert report.protein_count == 2
    assert report.quantified_precursor_count == 1
    assert report.qc_missing_intensity_count == 1
    assert report.steps[0].step_id == "import-dia-results"
