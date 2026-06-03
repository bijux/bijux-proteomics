# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import (
    build_diann_vs_dda_psm_comparison_report,
    render_dia_dda_comparison_summary_tsv,
    render_dia_dda_conflicting_evidence_tsv,
    render_dia_dda_differential_comparison_tsv,
    render_dia_dda_exclusive_evidence_tsv,
    render_dia_dda_peptide_overlap_tsv,
    render_dia_dda_protein_overlap_tsv,
    render_dia_dda_shared_intensity_correlation_tsv,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_render_dia_dda_comparison_exports_keep_overlap_conflict_and_differential_visible() -> (
    None
):
    report = build_diann_vs_dda_psm_comparison_report(
        _workflow_fixture("dia_dda_comparison_diann.tsv"),
        _workflow_fixture("dia_dda_comparison_dda_psms.tsv"),
        dia_differential_tsv_path=_workflow_fixture(
            "dia_dda_comparison_dia_differential.tsv"
        ),
        dda_differential_tsv_path=_workflow_fixture(
            "dia_dda_comparison_dda_differential.tsv"
        ),
    )

    summary_tsv = render_dia_dda_comparison_summary_tsv(report)
    protein_tsv = render_dia_dda_protein_overlap_tsv(report)
    peptide_tsv = render_dia_dda_peptide_overlap_tsv(report)
    correlation_tsv = render_dia_dda_shared_intensity_correlation_tsv(report)
    exclusive_tsv = render_dia_dda_exclusive_evidence_tsv(report)
    conflict_tsv = render_dia_dda_conflicting_evidence_tsv(report)
    differential_tsv = render_dia_dda_differential_comparison_tsv(report)

    assert (
        "DIA-NN\tDDA PSM\t4\t4\t2\t2\t2\t4\t4\t2\t1\t1\t1\t6\t1\t5\t2\t3\t4\t1\t1\t1\t1"
        in summary_tsv
    )
    assert "P55555\tdia_only\t2\t0\t2e+06\t0" in protein_tsv
    assert (
        "CONFLICTSEQ\tconflicting\t2\t2\t1.02e+06\t930000\tP77777\tP88888"
        in peptide_tsv
    )
    assert "protein\tP22222\t2\t1.23e+06\t826000\t1" in correlation_tsv
    assert "dia\tpeptide\tDIAONLY\t2\t1.46e+06\tP55555" in exclusive_tsv
    assert (
        "peptide\tCONFLICTSEQ\tconflicting\tprotein_assignment_mismatch" in conflict_tsv
    )
    assert (
        "protein\tP44444\tcontrol\ttreatment\ttreatment_vs_control\tconflicting\t1.1\t-1.2\t0.02\t0.03\ttrue\ttrue\topposite\tdifferential_direction_mismatch"
        in differential_tsv
    )
