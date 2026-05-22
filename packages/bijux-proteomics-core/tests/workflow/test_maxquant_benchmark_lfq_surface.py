# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import build_maxquant_benchmark_report


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _bundle_fixture(name: str) -> Path:
    return _workflow_fixture("maxquant_biological") / name


def test_build_maxquant_benchmark_report_preserves_lfq_intensities() -> None:
    report = build_maxquant_benchmark_report(
        _bundle_fixture("evidence.txt"),
        peptides_txt_path=_bundle_fixture("peptides.txt"),
        protein_groups_txt_path=_bundle_fixture("proteinGroups.txt"),
        config_path=_bundle_fixture("maxquant_settings.txt"),
    )

    assert report.lfq_table.sample_ids == ("C1", "C2", "C3", "T1", "T2", "T3")
    assert report.summary.source_lfq_value_count == 30
    assert report.summary.imported_lfq_value_count == 30
    assert report.summary.exact_lfq_value_match_count == 30
    assert report.summary.max_lfq_absolute_difference == 0.0
    assert report.summary.lfq_values_matched is True

    comparison_lookup = {
        (entry.entity_id, entry.sample_id): entry for entry in report.lfq_comparisons
    }
    assert comparison_lookup[("P04637", "C1")].source_intensity == 200.0
    assert comparison_lookup[("P04637", "C1")].imported_intensity == 200.0
    assert comparison_lookup[("Q9Y243", "T2")].source_intensity == 220.0
    assert comparison_lookup[("Q9Y243", "T2")].imported_intensity == 220.0
