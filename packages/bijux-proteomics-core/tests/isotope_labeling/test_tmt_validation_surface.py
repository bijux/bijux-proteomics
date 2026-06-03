# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.isotope_labeling import build_tmt_validation_report
from bijux_proteomics.multiplex import (
    TmtSearchResultSourceKind,
    build_tmt_reporter_feature_bundle,
    parse_tmt_reporter_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_validation_report_preserves_missing_channels_and_weak_evidence() -> None:
    import_report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_evidence.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    design_entries = parse_experimental_design_table(
        _fixture("tmt.design.tsv")
    ).accepted_entries
    feature_bundle = build_tmt_reporter_feature_bundle(
        import_report,
        design_entries=design_entries,
    )

    report = build_tmt_validation_report(feature_bundle)

    assert report.summary.multiplex_group_count == 2
    assert report.summary.expected_channel_count == 8
    assert report.summary.missing_channel_count == 2
    assert report.summary.abnormal_distribution_count == 0
    assert report.summary.weak_channel_count == 2
    missing = next(
        entry
        for entry in report.channel_entries
        if entry.multiplex_group == "plex-a" and entry.multiplex_channel == "129N"
    )
    assert missing.present is False
    assert missing.source_column_present is False
    assert missing.observed_row_count == 0
    assert missing.total_intensity == 0.0
    weak = next(
        entry
        for entry in report.weak_evidence
        if entry.multiplex_group == "plex-a" and entry.multiplex_channel == "129N"
    )
    assert weak.issue_kind == "channel_missing"
