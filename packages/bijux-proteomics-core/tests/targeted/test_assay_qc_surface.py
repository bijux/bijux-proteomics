# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io import parse_experimental_design_table
from bijux_proteomics.targeted import (
    build_skyline_result_import_report,
    build_targeted_assay_qc_report,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def _design_entries() -> tuple:
    return parse_experimental_design_table(
        _format_fixture("skyline_targeted_qc.design.tsv")
    ).accepted_entries


def test_build_targeted_assay_qc_report_keeps_transition_consistency_visible() -> None:
    import_report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )
    report = build_targeted_assay_qc_report(import_report, _design_entries())

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
    assert report.summary.transition_qc_entry_count == 16
    assert report.summary.passing_transition_qc_entry_count == 10
    missing_transition_qc = next(
        entry
        for entry in report.transition_qc
        if entry.target_id == "PEPTIDEK/2"
        and entry.sample_id == "treat_r2"
        and entry.transition_id == "y8"
    )
    assert missing_transition_qc.detected is False
    assert missing_transition_qc.passed is False
    assert missing_transition_qc.failure_reasons == ("transition not observed",)


def test_build_targeted_assay_qc_report_keeps_fragment_ratios_visible() -> None:
    import_report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )
    report = build_targeted_assay_qc_report(import_report, _design_entries())

    assert report.summary.fragment_ratio_entry_count == 14
    first_ratio = report.fragment_ratios[0]
    assert first_ratio.target_id == "ACDMPEP/3"
    assert first_ratio.sample_id == "control_r1"
    assert first_ratio.transition_id == "y5"
    assert first_ratio.total_target_intensity == 76000.0
    assert round(first_ratio.relative_share, 6) == 0.921053
    assert round(first_ratio.reference_relative_share, 6) == 0.91386
    assert round(first_ratio.absolute_share_delta, 6) == 0.007193
    assert first_ratio.flagged is False
    failing_transition_qc = next(
        entry
        for entry in report.transition_qc
        if entry.target_id == "ACDMPEP/3"
        and entry.sample_id == "control_r1"
        and entry.transition_id == "y6"
    )
    assert failing_transition_qc.quality_flagged is True
    assert failing_transition_qc.passed is False
    assert failing_transition_qc.failure_reasons == ("source quality flag is not pass",)


def test_build_targeted_assay_qc_report_keeps_retention_consistency_visible() -> None:
    import_report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )
    report = build_targeted_assay_qc_report(import_report, _design_entries())

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
    target_qc_entry = next(
        entry
        for entry in report.target_qc
        if entry.target_id == "ACDMPEP/3" and entry.sample_id == "treat_r2"
    )
    assert target_qc_entry.reliable is False
    assert target_qc_entry.reliability_reasons == (
        "fewer than two passing transitions support the target",
        "replicate cv is above the configured threshold",
        "retention time deviates from the target reference window",
    )


def test_build_targeted_assay_qc_report_keeps_replicate_cv_visible() -> None:
    import_report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )
    report = build_targeted_assay_qc_report(import_report, _design_entries())

    assert report.summary.replicate_cv_entry_count == 4
    assert report.summary.flagged_replicate_cv_entry_count == 1
    flagged_entry = next(
        entry
        for entry in report.replicate_cv
        if entry.target_id == "ACDMPEP/3" and entry.condition == "treatment"
    )
    assert flagged_entry.detected_replicate_count == 2
    assert flagged_entry.mean_intensity == 35000.0
    assert round(flagged_entry.coefficient_of_variation or 0.0, 6) == 0.525279
    assert flagged_entry.flagged is True
    assert report.summary.target_qc_entry_count == 8
    assert report.summary.reliable_target_entry_count == 3


def test_build_targeted_assay_qc_report_flags_unreliable_targets_explicitly() -> None:
    import_report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )
    report = build_targeted_assay_qc_report(import_report, _design_entries())

    assert report.summary.unreliable_target_count == 2
    assert report.summary.unreliable_target_entry_count == 6
    sample_target_qc = next(
        entry
        for entry in report.target_qc
        if entry.target_id == "PEPTIDEK/2" and entry.sample_id == "treat_r1"
    )
    assert sample_target_qc.passing_transition_count == 1
    assert sample_target_qc.reliable is False
    assert sample_target_qc.reliability_reasons == (
        "fewer than two passing transitions support the target",
    )
    sample_level_flag = next(
        entry
        for entry in report.unreliable_targets
        if entry.target_id == "PEPTIDEK/2" and entry.sample_id == "treat_r1"
    )
    assert sample_level_flag.condition == "treatment"
    assert sample_level_flag.flagged_transition_ids == ("y8",)
    assert sample_level_flag.quality_flags == ("interference",)
    assert sample_level_flag.reasons == (
        "fewer than two passing transitions support the target",
        "fragment-ion ratios deviate from the target reference pattern",
        "source quality flags require review",
    )
    condition_level_flag = next(
        entry
        for entry in report.unreliable_targets
        if entry.target_id == "ACDMPEP/3"
        and entry.condition == "treatment"
        and entry.sample_id is None
    )
    assert condition_level_flag.reasons == (
        "replicate cv is above the configured threshold",
    )
