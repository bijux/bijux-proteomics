# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import build_diann_benchmark_report


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_build_diann_benchmark_report_preserves_counts_and_qvalue_filtering() -> None:
    report = build_diann_benchmark_report(_fixture("diann_biological_report.tsv"))

    assert report.summary.source_precursor_count == 31
    assert report.summary.imported_precursor_count == 31
    assert report.summary.source_filtered_precursor_count == 5
    assert report.summary.imported_filtered_precursor_count == 5
    assert report.summary.source_protein_group_count == 5
    assert report.summary.imported_protein_group_count == 5
    assert report.summary.source_excluded_q_value_count == 1
    assert report.summary.imported_excluded_q_value_count == 1
    assert report.summary.source_decoy_count == 0
    assert report.summary.imported_excluded_decoy_count == 0
    assert report.summary.precursor_count_matched is True
    assert report.summary.filtered_precursor_count_matched is True
    assert report.summary.protein_group_count_matched is True
    assert report.summary.q_value_filtering_matched is True
    assert report.summary.decoy_filtering_matched is True
