# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.targeted import (
    build_skyline_result_import_report,
    build_targeted_assay_qc_report,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_build_targeted_assay_qc_report_keeps_transition_consistency_visible() -> None:
    import_report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )
    report = build_targeted_assay_qc_report(import_report)

    assert report.source_name == "Skyline"
    assert report.summary.target_count == 2
    assert report.summary.sample_count == 4
    assert report.summary.transition_consistency_entry_count == 8
    assert report.transition_consistency[0].target_id == "ACDMPEP/3"
    assert report.transition_consistency[0].consistency_fraction == 1.0
    missing_transition_entry = next(
        entry
        for entry in report.transition_consistency
        if entry.target_id == "PEPTIDEK/2" and entry.sample_id == "treat_r2"
    )
    assert missing_transition_entry.detected_transition_count == 1
    assert missing_transition_entry.expected_transition_count == 2
    assert missing_transition_entry.consistency_fraction == 0.5


def test_build_targeted_assay_qc_report_keeps_fragment_ratios_visible() -> None:
    import_report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )
    report = build_targeted_assay_qc_report(import_report)

    assert report.summary.fragment_ratio_entry_count == 14
    first_ratio = report.fragment_ratios[0]
    assert first_ratio.target_id == "ACDMPEP/3"
    assert first_ratio.sample_id == "control_r1"
    assert first_ratio.transition_id == "y5"
    assert first_ratio.total_target_intensity == 76000.0
    assert round(first_ratio.relative_share, 6) == 0.921053


def test_build_targeted_assay_qc_report_keeps_retention_consistency_visible() -> None:
    import_report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )
    report = build_targeted_assay_qc_report(import_report)

    assert report.summary.retention_time_entry_count == 8
    assert report.summary.flagged_retention_time_entry_count == 2
    flagged_entry = next(
        entry
        for entry in report.retention_time_consistency
        if entry.target_id == "ACDMPEP/3" and entry.sample_id == "treat_r2"
    )
    assert flagged_entry.mean_retention_time_minutes == 20.2
    assert flagged_entry.reference_retention_time_minutes == 18.2
    assert flagged_entry.absolute_delta_minutes == 2.0
    assert flagged_entry.flagged is True
