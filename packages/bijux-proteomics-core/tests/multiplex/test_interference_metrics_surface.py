# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import (
    TmtInterferencePolicy,
    TmtSearchResultSourceKind,
    build_tmt_interference_report,
    parse_tmt_reporter_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_interference_report_preserves_source_row_channel_observations() -> None:
    import_report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_interference.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    design_report = parse_experimental_design_table(_fixture("tmt.design.tsv"))

    report = build_tmt_interference_report(
        import_report,
        design_entries=tuple(design_report.accepted_entries),
    )

    assert report.summary.multiplex_group_count == 2
    assert report.summary.observed_channel_row_count == 12
    assert report.summary.missing_interference_count == 0
    assert report.summary.threshold_exceeded_count == 6
    assert report.observations[0].multiplex_channel == "126"
    assert report.observations[0].sample_id == "plex_a_126"
    assert report.observations[0].isolation_interference_fraction == 0.08
    assert report.observations[-1].sample_id == "plex_b_128N"
    assert report.observations[-1].threshold_exceeded is True
    assert "mapped sample-channel level" in report.note


def test_tmt_interference_report_marks_threshold_exceeded_observations() -> None:
    import_report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_interference.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    design_report = parse_experimental_design_table(_fixture("tmt.design.tsv"))

    report = build_tmt_interference_report(
        import_report,
        design_entries=tuple(design_report.accepted_entries),
        policy=TmtInterferencePolicy(interference_fraction_threshold=0.4),
    )

    exceeded = [entry for entry in report.observations if entry.threshold_exceeded]
    assert len(exceeded) == 3
    assert {entry.source_row_id for entry in exceeded} == {"4"}
    assert all(entry.isolation_interference_fraction == 0.42 for entry in exceeded)
