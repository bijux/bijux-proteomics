# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.multiplex import (
    TmtReporterChannelColumn,
    TmtReporterColumnMapping,
    TmtSearchResultSourceKind,
    parse_tmt_reporter_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_reporter_import_infers_maxquant_channel_columns_and_groups() -> None:
    report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_evidence.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )

    assert report.summary.accepted_row_count == 4
    assert report.summary.rejected_row_count == 0
    assert report.summary.multiplex_group_count == 2
    assert [entry.multiplex_channel for entry in report.channel_columns] == [
        "126",
        "127N",
        "128N",
    ]
    first = report.accepted_rows[0]
    assert first.source_row_id == "1"
    assert first.multiplex_group == "plex-a"
    assert first.modified_peptide == "PEPTIDE"
    assert first.protein_refs == ("P001",)


def test_tmt_reporter_import_respects_explicit_channel_overrides_for_generic_tables() -> (
    None
):
    report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_evidence.tsv"),
        source_kind=TmtSearchResultSourceKind.GENERIC,
        mapping=TmtReporterColumnMapping(
            peptide="Modified sequence",
            protein_refs="Leading proteins",
            multiplex_group="Experiment",
            source_row_id="id",
        ),
        channel_columns=(
            TmtReporterChannelColumn(
                multiplex_channel="126",
                column_name="Reporter intensity corrected 126",
            ),
            TmtReporterChannelColumn(
                multiplex_channel="127N",
                column_name="Reporter intensity corrected 127N",
            ),
        ),
    )

    assert report.summary.accepted_row_count == 4
    assert [entry.multiplex_channel for entry in report.channel_columns] == [
        "126",
        "127N",
    ]


def test_tmt_reporter_import_preserves_isolation_interference_fraction() -> None:
    report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_interference.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )

    assert report.summary.accepted_row_count == 4
    assert report.accepted_rows[0].isolation_interference_fraction == 0.08
    assert report.accepted_rows[1].isolation_interference_fraction == 0.35
    assert report.accepted_rows[-1].isolation_interference_fraction == 0.42
