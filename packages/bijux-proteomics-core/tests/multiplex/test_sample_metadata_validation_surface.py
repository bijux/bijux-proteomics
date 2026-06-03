# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import build_multiplex_metadata_validation_report


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_multiplex_metadata_validation_report_summarizes_valid_design_assignments() -> (
    None
):
    design_report = parse_experimental_design_table(_fixture("tmt.design.tsv"))

    report = build_multiplex_metadata_validation_report(design_report)

    assert report.summary.multiplex_group_count == 2
    assert report.summary.multiplex_channel_count == 8
    assert report.summary.assigned_channel_count == 8
    assert report.summary.missing_channel_assignment_count == 0
    assert report.summary.duplicate_assignment_count == 0
    assert report.summary.missing_condition_count == 0
    first = report.channel_assignments[0]
    assert first.multiplex_group == "plex-a"
    assert first.multiplex_channel == "126"
    assert first.sample_id == "plex_a_126"
    assert first.assigned is True


def test_multiplex_metadata_validation_report_preserves_missing_group_channel_assignments() -> (
    None
):
    design_report = parse_experimental_design_table(
        _fixture("tmt_missing_channel.design.tsv")
    )

    report = build_multiplex_metadata_validation_report(design_report)

    assert report.summary.multiplex_group_count == 2
    assert report.summary.multiplex_channel_count == 8
    assert report.summary.assigned_channel_count == 7
    assert report.summary.missing_channel_assignment_count == 1
    missing = next(
        entry
        for entry in report.channel_assignments
        if entry.multiplex_group == "plex-b" and entry.multiplex_channel == "129N"
    )
    assert missing.sample_id is None
    assert missing.assigned is False


def test_multiplex_metadata_validation_report_flags_duplicate_assignments_and_missing_conditions() -> (
    None
):
    design_report = parse_experimental_design_table(
        _fixture("tmt_metadata_issues.design.tsv")
    )

    report = build_multiplex_metadata_validation_report(design_report)

    assert report.summary.missing_channel_assignment_count == 1
    assert report.summary.duplicate_assignment_count == 2
    assert report.summary.missing_condition_count == 1
    duplicate_issue_kinds = {entry.issue_kind for entry in report.duplicate_assignments}
    assert duplicate_issue_kinds == {
        "duplicate_channel_assignment",
        "duplicate_sample_assignment",
    }
    missing_condition = report.missing_conditions[0]
    assert missing_condition.multiplex_group == "plex-b"
    assert missing_condition.multiplex_channel == "128N"
    assert missing_condition.sample_id == "plex_b_128N"
