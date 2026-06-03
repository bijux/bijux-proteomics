# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.targeted import (
    TargetedResultSourceKind,
    build_skyline_result_import_report,
    build_transition_table_result_import_report,
    render_targeted_result_observation_tsv,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_build_skyline_result_import_report_reads_targeted_identifiers() -> None:
    report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_results.tsv")
    )

    assert report.source_kind is TargetedResultSourceKind.SKYLINE_EXPORT
    assert report.summary.observation_count == 6
    assert report.summary.precursor_count == 2
    assert report.summary.transition_count == 4
    assert report.summary.sample_count == 2
    assert report.summary.retention_time_count == 6
    assert report.summary.quality_flag_count == 6
    assert report.observations[0].precursor_id == "ACDMPEP/3"
    assert report.observations[0].precursor_charge == 3
    assert report.observations[0].transition_id == "y5"
    assert report.observations[0].retention_time_minutes == 18.1
    assert report.observations[0].provenance.source_engine == "skyline"
    assert report.observations[0].provenance.source_row_numbers[0] >= 2
    assert report.observations[-1].quality_flag == "interference"
    assert "source_engine" in render_targeted_result_observation_tsv(report)


def test_build_transition_table_result_import_report_reads_transition_table_metadata() -> (
    None
):
    report = build_transition_table_result_import_report(
        _format_fixture("targeted_transition_results.tsv")
    )

    assert report.source_kind is TargetedResultSourceKind.TRANSITION_TABLE
    assert report.summary.observation_count == 6
    assert report.summary.precursor_count == 2
    assert report.summary.transition_count == 4
    assert report.summary.sample_count == 2
    assert report.summary.retention_time_count == 6
    assert report.summary.quality_flag_count == 6
    assert report.observations[0].transition_id == "tr_y7_a"
    assert report.observations[0].precursor_charge == 2
    assert report.observations[0].retention_time_minutes == 12.5
    assert report.observations[0].provenance.source_engine == "transition-table"
    assert report.observations[-1].quality_flag == "low_signal"
    assert "precursor_charge" in render_targeted_result_observation_tsv(report)
    assert "original_identifiers" in render_targeted_result_observation_tsv(report)
