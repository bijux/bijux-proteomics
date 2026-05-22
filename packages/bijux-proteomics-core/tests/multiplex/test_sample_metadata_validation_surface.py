# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import build_multiplex_metadata_validation_report


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_multiplex_metadata_validation_report_summarizes_valid_design_assignments() -> None:
    design_report = parse_experimental_design_table(_fixture("tmt.design.tsv"))

    report = build_multiplex_metadata_validation_report(design_report)

    assert report.summary.multiplex_group_count == 2
    assert report.summary.multiplex_channel_count == 8
    assert report.summary.assigned_channel_count == 8
    assert report.summary.duplicate_assignment_count == 0
    assert report.summary.missing_condition_count == 0
    first = report.channel_assignments[0]
    assert first.multiplex_group == "plex-a"
    assert first.multiplex_channel == "126"
    assert first.sample_id == "plex_a_126"
    assert first.assigned is True
