# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.dia import (
    build_diann_run_qc_report,
    render_dia_run_qc_correlation_tsv,
    render_dia_run_qc_intensity_distribution_tsv,
    render_dia_run_qc_outlier_tsv,
    render_dia_run_qc_run_table_tsv,
    render_dia_run_qc_summary_tsv,
)


def _bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "diann"
    )


def test_render_dia_run_qc_summary_and_run_table_tsv() -> None:
    report = build_diann_run_qc_report(_bundle_root() / "diann_run_qc_report.tsv")

    summary_tsv = render_dia_run_qc_summary_tsv(report)
    run_table_tsv = render_dia_run_qc_run_table_tsv(report)

    assert summary_tsv.startswith("source_name\trun_count\tsample_count")
    assert "DIA-NN\t3\t3\t4\t3\t4\t1\t5\t" in summary_tsv
    assert run_table_tsv.startswith(
        "run_name\tsample_name\tprecursor_id_count\tprecursor_key_count"
    )
    assert (
        "raw_C\tsample_C\t1\t1\t1\t1\t1\t1\t4.8451\t0.75\t0.75\t5\ttrue"
        in run_table_tsv
    )


def test_render_dia_run_qc_distribution_correlation_and_outlier_tsv() -> None:
    report = build_diann_run_qc_report(_bundle_root() / "diann_run_qc_report.tsv")

    intensity_tsv = render_dia_run_qc_intensity_distribution_tsv(report)
    correlation_tsv = render_dia_run_qc_correlation_tsv(report)
    outlier_tsv = render_dia_run_qc_outlier_tsv(report)

    assert intensity_tsv.startswith("run_name\tsample_name\tbucket\tcount")
    assert "raw_A\tsample_A\t1e6+\t2" in intensity_tsv
    assert "raw_C\tsample_C\t<1e5\t1" in intensity_tsv
    assert correlation_tsv.startswith(
        "run_name_a\tsample_name_a\trun_name_b\tsample_name_b"
    )
    assert "raw_A\tsample_A\traw_B\tsample_B\t4\t0.995812" in correlation_tsv
    assert "raw_A\tsample_A\traw_C\tsample_C\t1\t" in correlation_tsv
    assert outlier_tsv.startswith("run_name\tsample_name\treason_code\treason")
    assert (
        "raw_C\tsample_C\tlow_precursor_coverage\tprecursor coverage is far below the study median\tlow_precursor_count_fraction\t0.5\t0.25"
        in outlier_tsv
    )
    assert (
        "raw_C\tsample_C\tinsufficient_shared_precursor_overlap\tshared precursor overlap is too small for stable correlation review\tminimum_shared_precursor_key_count\t2\t1"
        in outlier_tsv
    )
