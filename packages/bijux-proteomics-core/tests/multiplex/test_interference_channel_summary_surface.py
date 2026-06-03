# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import (
    TmtSearchResultSourceKind,
    build_tmt_interference_report,
    parse_tmt_reporter_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_interference_report_summarizes_interference_by_sample_channel() -> None:
    import_report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_interference.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    design_report = parse_experimental_design_table(_fixture("tmt.design.tsv"))

    report = build_tmt_interference_report(
        import_report,
        design_entries=tuple(design_report.accepted_entries),
    )

    assert report.summary.filtered_channel_row_count == 6
    assert report.summary.channel_summary_count == 6
    plex_a_126 = next(
        entry for entry in report.channel_summaries if entry.sample_id == "plex_a_126"
    )
    assert plex_a_126.observed_row_count == 2
    assert round(plex_a_126.mean_interference_fraction or 0.0, 6) == 0.215
    assert plex_a_126.max_interference_fraction == 0.35
    assert plex_a_126.flagged is True
    assert len(report.filtered_observations) == 6
    assert {entry.source_row_id for entry in report.filtered_observations} == {"2", "4"}
