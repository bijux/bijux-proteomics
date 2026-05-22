# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import build_maxquant_benchmark_report


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _bundle_fixture(name: str) -> Path:
    return _workflow_fixture("maxquant_biological") / name


def test_build_maxquant_benchmark_report_preserves_differential_results() -> None:
    design_entries = tuple(
        parse_experimental_design_table(_bundle_fixture("design.tsv")).accepted_entries
    )
    report = build_maxquant_benchmark_report(
        _bundle_fixture("evidence.txt"),
        peptides_txt_path=_bundle_fixture("peptides.txt"),
        protein_groups_txt_path=_bundle_fixture("proteinGroups.txt"),
        config_path=_bundle_fixture("maxquant_settings.txt"),
        design_entries=design_entries,
        condition_a="control",
        condition_b="treatment",
    )

    assert report.differential_report is not None
    assert report.summary.differential_comparison_applied is True
    assert report.summary.source_differential_entry_count == 5
    assert report.summary.imported_differential_entry_count == 5
    assert report.summary.exact_differential_match_count == 5
    assert report.summary.max_differential_log2_fold_change_difference == 0.0
    assert report.summary.max_differential_p_value_difference == 0.0
    assert report.summary.max_differential_adjusted_p_value_difference == 0.0
    assert report.summary.differential_matched is True

    comparison_lookup = {
        entry.entity_id: entry for entry in report.differential_comparisons
    }
    assert comparison_lookup["P04637"].source_log2_fold_change > 0.0
    assert comparison_lookup["Q9Y243"].source_log2_fold_change < 0.0
    assert comparison_lookup["P04637"].imported_adjusted_p_value == comparison_lookup[
        "P04637"
    ].source_adjusted_p_value
