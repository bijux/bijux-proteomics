# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io import TargetPanelKind, parse_target_panel_table


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_parse_target_panel_table_accepts_peptide_and_protein_targets() -> None:
    report = parse_target_panel_table(_format_fixture("target_panel.tsv"))

    assert report.rejected_rows == ()
    assert len(report.accepted_entries) == 6
    assert report.accepted_entries[0].target_id == "dia-pepalfa"
    assert report.accepted_entries[0].target_kind is TargetPanelKind.PEPTIDE
    assert report.accepted_entries[0].peptide_sequence == "PEPALFA"
    assert report.accepted_entries[0].protein_ref == "P11111"
    assert report.accepted_entries[0].metadata["panel_group"] == "dia"
    assert report.accepted_entries[1].target_kind is TargetPanelKind.PROTEIN
    assert report.accepted_entries[1].protein_ref == "P22222"
    assert report.accepted_entries[-1].peptide_sequence == "ZPEPTIDE"


def test_parse_target_panel_table_rejects_rows_without_primary_target() -> None:
    fixture = _format_fixture("target_panel.invalid.tsv")
    report = parse_target_panel_table(fixture)

    assert report.accepted_entries == ()
    assert len(report.rejected_rows) == 1
    assert report.rejected_rows[0].reason == "peptide targets require peptide_sequence"
