# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow.dia_differential_analysis import (
    build_diann_differential_analysis_report,
    render_dia_differential_matrix_tsv,
    render_dia_differential_missingness_tsv,
    render_dia_differential_qc_summary_tsv,
    render_dia_differential_results_tsv,
    render_dia_differential_volcano_plot_tsv,
    render_dia_normalization_balance_plot_tsv,
)


def _diann_fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "diann"
        / name
    )


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_render_dia_differential_exports_keep_matrix_results_and_plots_visible() -> None:
    design_report = parse_experimental_design_table(
        _format_fixture("diann_differential.design.tsv")
    )
    report = build_diann_differential_analysis_report(
        _diann_fixture("diann_differential_report.tsv"),
        design_report.accepted_entries,
    )

    raw_matrix_tsv = render_dia_differential_matrix_tsv(report.input_report.table)
    raw_missingness_tsv = render_dia_differential_missingness_tsv(
        report.input_report.table
    )
    normalized_matrix_tsv = render_dia_differential_matrix_tsv(report.normalized_table)
    normalized_missingness_tsv = render_dia_differential_missingness_tsv(
        report.normalized_table
    )
    differential_tsv = render_dia_differential_results_tsv(report)
    qc_summary_tsv = render_dia_differential_qc_summary_tsv(report)
    balance_tsv = render_dia_normalization_balance_plot_tsv(
        report.normalization_balance_plot
    )
    assert report.volcano_plot is not None
    volcano_tsv = render_dia_differential_volcano_plot_tsv(report.volcano_plot)

    assert "entity_id\tprotein_refs\tmember_peptides\tC1\tC2\tT1\tT2" in raw_matrix_tsv
    assert "PG001\tP11111\tPESTIDE\t100000\t110000\t400000\t420000" in raw_matrix_tsv
    assert "PG001\tP11111\tPESTIDE\tobserved\tobserved\tobserved\tobserved" in raw_missingness_tsv
    assert "PG001\tP11111\tPESTIDE" in normalized_matrix_tsv
    assert (
        "PG002\tP22222\tACDM[Oxidation]K\tobserved\tobserved\tobserved\tobserved"
        in normalized_missingness_tsv
    )
    assert "PG001\tcontrol\ttreatment\t\t2\t2" in differential_tsv
    assert "contrast_count\t1" in qc_summary_tsv
    assert "significant_entry_count\t2" in qc_summary_tsv
    assert "C1\tbefore\t600000\t200000\t100000" in balance_tsv
    assert "raw_p_value" in volcano_tsv
    assert "PG001\tP11111\t2.00208\t0.00729495\t0.0136062\t1.86626\ttrue" in volcano_tsv
