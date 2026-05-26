# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow.label_based_differential_analysis import (
    build_silac_differential_analysis_report,
    export_label_based_differential_missingness_tsv,
    export_label_based_differential_matrix_tsv,
    export_label_based_differential_results_tsv,
    export_label_based_differential_volcano_plot_tsv,
    export_label_based_normalization_balance_plot_tsv,
    render_label_based_differential_missingness_tsv,
    render_label_based_differential_matrix_tsv,
    render_label_based_differential_results_tsv,
    render_label_based_differential_volcano_plot_tsv,
    render_label_based_normalization_balance_plot_tsv,
)


def _fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent / "fixtures" / "isotope_labeling" / name
    )


def test_render_labeled_differential_exports_keep_matrix_results_and_plots_visible() -> (
    None
):
    design_report = parse_experimental_design_table(
        _fixture("silac_differential.design.tsv")
    )
    report = build_silac_differential_analysis_report(
        _fixture("silac_differential_features.tsv"),
        tuple(design_report.accepted_entries),
    )

    raw_matrix_tsv = render_label_based_differential_matrix_tsv(report.input_report)
    raw_missingness_tsv = render_label_based_differential_missingness_tsv(
        report.input_report
    )
    normalized_matrix_tsv = render_label_based_differential_matrix_tsv(
        report.normalized_matrix
    )
    normalized_missingness_tsv = render_label_based_differential_missingness_tsv(
        report.normalized_matrix
    )
    results_tsv = render_label_based_differential_results_tsv(report)
    balance_tsv = render_label_based_normalization_balance_plot_tsv(
        report.normalization_balance_plot
    )
    assert report.volcano_plot is not None
    volcano_tsv = render_label_based_differential_volcano_plot_tsv(report.volcano_plot)

    assert "entity_id\tprotein_refs\tmember_peptides\tC1\tC2\tT1\tT2" in raw_matrix_tsv
    assert "P001\tP001\tPEPA/z2\t1\t1\t2\t2" in raw_matrix_tsv
    assert "P001\tP001\tPEPA/z2\tobserved\tobserved\tobserved\tobserved" in raw_missingness_tsv
    assert "P001\tP001\tPEPA" in normalized_matrix_tsv
    assert "P001\tP001\tPEPA/z2\tobserved\tobserved\tobserved\tobserved" in normalized_missingness_tsv
    assert "P001\tcontrol\ttreatment\t\t2\t2" in results_tsv
    assert "C1\tbefore\t3\t1\t0" in balance_tsv
    assert "P001\tP001\t1\t1\t1\t-0\tfalse" in volcano_tsv


def test_export_labeled_differential_ledgers_write_stable_tsv_outputs(
    tmp_path: Path,
) -> None:
    design_report = parse_experimental_design_table(
        _fixture("silac_differential.design.tsv")
    )
    report = build_silac_differential_analysis_report(
        _fixture("silac_differential_features.tsv"),
        tuple(design_report.accepted_entries),
    )

    raw_matrix_path = tmp_path / "labeled.raw.tsv"
    raw_missingness_path = tmp_path / "labeled.raw.missingness.tsv"
    normalized_matrix_path = tmp_path / "labeled.normalized.tsv"
    normalized_missingness_path = tmp_path / "labeled.normalized.missingness.tsv"
    results_path = tmp_path / "labeled.results.tsv"
    balance_path = tmp_path / "labeled.balance.tsv"
    volcano_path = tmp_path / "labeled.volcano.tsv"

    export_label_based_differential_matrix_tsv(report.input_report, raw_matrix_path)
    export_label_based_differential_missingness_tsv(
        report.input_report, raw_missingness_path
    )
    export_label_based_differential_matrix_tsv(
        report.normalized_matrix, normalized_matrix_path
    )
    export_label_based_differential_missingness_tsv(
        report.normalized_matrix, normalized_missingness_path
    )
    export_label_based_differential_results_tsv(report, results_path)
    export_label_based_normalization_balance_plot_tsv(
        report.normalization_balance_plot,
        balance_path,
    )
    assert report.volcano_plot is not None
    export_label_based_differential_volcano_plot_tsv(
        report.volcano_plot,
        volcano_path,
    )

    assert raw_matrix_path.exists()
    assert raw_missingness_path.exists()
    assert normalized_matrix_path.exists()
    assert normalized_missingness_path.exists()
    assert results_path.exists()
    assert balance_path.exists()
    assert volcano_path.exists()
    assert "member_peptides" in raw_matrix_path.read_text(encoding="utf-8")
    assert "observed" in raw_missingness_path.read_text(encoding="utf-8")
    assert "adjusted_p_value" in results_path.read_text(encoding="utf-8")
    assert "interquartile_range" in balance_path.read_text(encoding="utf-8")
    assert "raw_p_value" in volcano_path.read_text(
        encoding="utf-8"
    )
