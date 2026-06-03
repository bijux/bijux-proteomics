# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.dia import build_diann_run_qc_report


def _bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "diann"
    )


def test_build_diann_run_qc_report_keeps_run_identity_counts_visible() -> None:
    report = build_diann_run_qc_report(_bundle_root() / "diann_run_qc_report.tsv")

    assert report.source_name == "DIA-NN"
    assert report.policy.low_correlation_threshold == 0.9
    assert report.summary.run_count == 3
    assert report.summary.sample_count == 3
    assert report.summary.union_precursor_key_count == 4
    assert report.summary.union_protein_group_id_count == 3
    assert report.summary.union_protein_id_count == 4
    assert report.summary.flagged_run_count == 1
    assert report.summary.weak_run_flag_count == 5
    assert "pairwise correlation" in report.note

    first_run = report.run_entries[0]
    assert first_run.run_name == "raw_A"
    assert first_run.sample_name == "sample_A"
    assert first_run.precursor_id_count == 4
    assert first_run.precursor_key_count == 4
    assert first_run.protein_group_id_count == 3
    assert first_run.protein_id_count == 4
    assert first_run.observed_precursor_quantity_count == 4
    assert first_run.observed_protein_quantity_count == 3
    assert first_run.median_log10_precursor_quantity is not None
    assert first_run.precursor_missing_fraction == 0.0
    assert first_run.protein_missing_fraction == 0.0

    weak_run = report.run_entries[2]
    assert weak_run.run_name == "raw_C"
    assert weak_run.precursor_id_count == 1
    assert weak_run.precursor_key_count == 1
    assert weak_run.protein_group_id_count == 1
    assert weak_run.protein_id_count == 1
    assert weak_run.precursor_missing_fraction == 0.75
    assert weak_run.protein_missing_fraction == 0.75
    assert weak_run.weak_run_flag_count == 5

    intensity_distribution = {
        (entry.run_name, entry.bucket): entry.count
        for entry in report.intensity_distribution
    }
    assert intensity_distribution[("raw_A", "1e6+")] == 2
    assert intensity_distribution[("raw_A", "1e5-1e6")] == 2
    assert intensity_distribution[("raw_C", "<1e5")] == 1

    correlations = {
        (entry.run_name_a, entry.run_name_b): entry
        for entry in report.pairwise_correlations
    }
    assert correlations[("raw_A", "raw_B")].shared_precursor_key_count == 4
    assert correlations[("raw_A", "raw_B")].pearson_correlation is not None
    assert correlations[("raw_A", "raw_C")].shared_precursor_key_count == 1
    assert correlations[("raw_A", "raw_C")].pearson_correlation is None

    assert len(report.outlier_runs) == 1
    assert report.outlier_runs[0].run_name == "raw_C"
    assert len(report.outlier_runs[0].flags) == 5
    assert (
        "precursor coverage is far below the study median"
        in report.outlier_runs[0].reasons
    )
    first_flag = report.outlier_runs[0].flags[0]
    assert first_flag.threshold_name in {
        "high_missing_fraction",
        "low_precursor_count_fraction",
        "low_protein_count_fraction",
        "minimum_shared_precursor_key_count",
    }
    assert first_flag.threshold_value >= 0.4
    assert weak_run.flagged is True


def test_build_diann_run_qc_report_respects_decoy_and_q_value_filters() -> None:
    report = build_diann_run_qc_report(
        _bundle_root() / "diann_run_qc_report.tsv",
        include_decoys=False,
        max_q_value=0.0035,
    )

    assert report.summary.run_count == 2
    assert report.summary.union_precursor_key_count == 4
    assert tuple(entry.run_name for entry in report.run_entries) == ("raw_A", "raw_B")
