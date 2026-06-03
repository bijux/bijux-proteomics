# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.dia import (
    build_diann_library_coverage_report,
    render_dia_library_coverage_condition_tsv,
    render_dia_library_coverage_observed_outside_peptide_tsv,
    render_dia_library_coverage_observed_outside_protein_tsv,
    render_dia_library_coverage_peptide_tsv,
    render_dia_library_coverage_protein_tsv,
    render_dia_library_coverage_sample_tsv,
    render_dia_library_coverage_summary_tsv,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def _diann_fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "diann"
        / name
    )


def test_render_dia_library_coverage_tsv_surfaces_include_identity_ledgers() -> None:
    report = build_diann_library_coverage_report(
        _diann_fixture("diann_library_coverage.tsv"),
        _format_fixture("diann_library_coverage.msp"),
        design_path=_format_fixture("diann_library_coverage.design.tsv"),
    )

    summary_tsv = render_dia_library_coverage_summary_tsv(report)
    sample_tsv = render_dia_library_coverage_sample_tsv(report)
    condition_tsv = render_dia_library_coverage_condition_tsv(report)
    peptide_tsv = render_dia_library_coverage_peptide_tsv(report)
    protein_tsv = render_dia_library_coverage_protein_tsv(report)
    outside_peptide_tsv = render_dia_library_coverage_observed_outside_peptide_tsv(
        report
    )
    outside_protein_tsv = render_dia_library_coverage_observed_outside_protein_tsv(
        report
    )

    assert "library_peptide_count\tdetected_peptide_count" in summary_tsv
    assert "observed_outside_library_peptide_count" in summary_tsv
    assert "sample_id\tdetected_peptide_count\tdetected_protein_count" in sample_tsv
    assert "condition\tsample_ids\tdetected_peptide_count" in condition_tsv
    assert "canonical_peptide\tprotein_refs\tdetected_overall" in peptide_tsv
    assert "protein_ref\tdetected_overall\tdetected_sample_count" in protein_tsv
    assert (
        "canonical_peptide\tprotein_refs\tsample_ids\tcondition_ids"
        in outside_peptide_tsv
    )
    assert "protein_ref\tsample_ids\tcondition_ids" in outside_protein_tsv
    assert "control\tsample_A;sample_B\t4\t4" in condition_tsv
    assert "LIVNLY\tP44444\tfalse\t0\t0" in peptide_tsv
    assert "PEPALFA\tP11111\ttrue\t3\t2" in peptide_tsv
    assert "P44444\tfalse\t0\t0" in protein_tsv
    assert "P11111\ttrue\t3\t2" in protein_tsv
    assert "PEPNOVEL\tP55555\tsample_A\tcontrol\t1\t1" in outside_peptide_tsv
    assert "P55555\tsample_A\tcontrol\t1\t1" in outside_protein_tsv
