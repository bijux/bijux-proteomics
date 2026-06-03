# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import (
    build_multiplex_metadata_validation_report,
    export_multiplex_channel_assignment_tsv,
    export_multiplex_duplicate_assignment_tsv,
    export_multiplex_metadata_summary_tsv,
    export_multiplex_missing_condition_tsv,
    render_multiplex_channel_assignment_tsv,
    render_multiplex_duplicate_assignment_tsv,
    render_multiplex_metadata_summary_tsv,
    render_multiplex_missing_condition_tsv,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_multiplex_metadata_renderers_and_exports_emit_review_ledgers(
    tmp_path: Path,
) -> None:
    report = build_multiplex_metadata_validation_report(
        parse_experimental_design_table(_fixture("tmt_metadata_issues.design.tsv"))
    )

    summary_tsv = render_multiplex_metadata_summary_tsv(report)
    channel_tsv = render_multiplex_channel_assignment_tsv(report)
    duplicate_tsv = render_multiplex_duplicate_assignment_tsv(report)
    missing_condition_tsv = render_multiplex_missing_condition_tsv(report)

    assert "missing_channel_assignment_count" in summary_tsv
    assert "plex-b\t129N\t\t\t\tFalse" in channel_tsv
    assert "duplicate_channel_assignment\tplex-b\t127N" in duplicate_tsv
    assert "plex-b\t128N\tplex_b_128N\tpooled_reference" in missing_condition_tsv

    export_multiplex_metadata_summary_tsv(report, tmp_path / "metadata.summary.tsv")
    export_multiplex_channel_assignment_tsv(report, tmp_path / "metadata.channels.tsv")
    export_multiplex_duplicate_assignment_tsv(
        report,
        tmp_path / "metadata.duplicates.tsv",
    )
    export_multiplex_missing_condition_tsv(
        report,
        tmp_path / "metadata.conditions.tsv",
    )

    assert (tmp_path / "metadata.summary.tsv").read_text(
        encoding="utf-8"
    ) == summary_tsv
    assert (tmp_path / "metadata.channels.tsv").read_text(
        encoding="utf-8"
    ) == channel_tsv
    assert (tmp_path / "metadata.duplicates.tsv").read_text(
        encoding="utf-8"
    ) == duplicate_tsv
    assert (tmp_path / "metadata.conditions.tsv").read_text(
        encoding="utf-8"
    ) == missing_condition_tsv
