# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.dia import (
    DiaPrecursorQValueFilterTiming,
    build_diann_precursor_matrix_report,
    render_dia_precursor_matrix_summary_tsv,
    render_dia_precursor_metadata_tsv,
    render_dia_precursor_missingness_tsv,
    render_dia_precursor_q_value_matrix_tsv,
    render_dia_precursor_quantity_matrix_tsv,
)


def _bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "diann"
    )


def test_render_dia_precursor_quantity_and_q_value_matrices() -> None:
    report = build_diann_precursor_matrix_report(_bundle_root() / "diann_report.tsv")

    quantity_tsv = render_dia_precursor_quantity_matrix_tsv(report)
    missingness_tsv = render_dia_precursor_missingness_tsv(report)
    q_value_tsv = render_dia_precursor_q_value_matrix_tsv(report)

    assert quantity_tsv.startswith(
        "precursor_key\tpeptide_sequence\tmodified_peptide\tcanonical_peptide"
    )
    assert (
        "PESTIDE|z2|PG001\tPESTIDE\tPESTIDE\tPESTIDE\t2\tPG001\tP11111;P11112"
        in quantity_tsv
    )
    assert "\t1.25e+06\t1.3e+06\n" in quantity_tsv
    assert "\tobserved\tobserved\n" in missingness_tsv
    assert "target_decoy_label\tsample_A\tsample_B" in missingness_tsv
    assert "\t0.0021\t0.0024\n" in q_value_tsv


def test_render_dia_precursor_matrix_summary_tsv() -> None:
    report = build_diann_precursor_matrix_report(_bundle_root() / "diann_report.tsv")

    summary_tsv = render_dia_precursor_matrix_summary_tsv(report)

    assert summary_tsv.startswith(
        "source_name\tsample_count\trun_count\tprecursor_row_count"
    )
    assert "DIA-NN\t2\t2\t2\t3\t1\t2\t0\t1\t0\t" in summary_tsv


def test_render_dia_precursor_metadata_tsv_and_filter_policy() -> None:
    report = build_diann_precursor_matrix_report(
        _bundle_root() / "diann_report.tsv",
        include_decoys=True,
        max_q_value=0.01,
        q_value_filter_timing=DiaPrecursorQValueFilterTiming.AFTER_MATRIX_CONSTRUCTION,
    )

    metadata_tsv = render_dia_precursor_metadata_tsv(report)
    summary_tsv = render_dia_precursor_matrix_summary_tsv(report)

    assert metadata_tsv.startswith(
        "precursor_key\tpeptide_sequence\tmodified_peptide\tcanonical_peptide"
    )
    assert "excluded_q_value_observation_count" in metadata_tsv
    assert "after_matrix_construction" in summary_tsv
