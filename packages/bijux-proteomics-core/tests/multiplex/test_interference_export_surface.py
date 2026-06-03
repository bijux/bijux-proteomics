# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import (
    TmtSearchResultSourceKind,
    build_tmt_interference_report,
    export_tmt_filtered_interference_tsv,
    export_tmt_interference_channel_summary_tsv,
    export_tmt_interference_observation_tsv,
    export_tmt_interference_summary_tsv,
    parse_tmt_reporter_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_interference_exports_write_summary_observations_and_channel_review(
    tmp_path: Path,
) -> None:
    import_report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_interference.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    design_report = parse_experimental_design_table(_fixture("tmt.design.tsv"))
    report = build_tmt_interference_report(
        import_report,
        design_entries=tuple(design_report.accepted_entries),
    )

    summary_path = tmp_path / "tmt.interference.summary.tsv"
    observation_path = tmp_path / "tmt.interference.observations.tsv"
    filtered_path = tmp_path / "tmt.interference.filtered.tsv"
    channel_summary_path = tmp_path / "tmt.interference.channels.tsv"

    export_tmt_interference_summary_tsv(report, summary_path)
    export_tmt_interference_observation_tsv(report, observation_path)
    export_tmt_filtered_interference_tsv(report, filtered_path)
    export_tmt_interference_channel_summary_tsv(report, channel_summary_path)

    assert "filtered_channel_row_count" in summary_path.read_text(encoding="utf-8")
    assert (
        "source_row_id\tmultiplex_group\tmultiplex_channel"
        in observation_path.read_text(encoding="utf-8")
    )
    assert "threshold and should be considered unreliable" in filtered_path.read_text(
        encoding="utf-8"
    )
    assert "mean_interference_fraction" in channel_summary_path.read_text(
        encoding="utf-8"
    )
