# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io import parse_transition_table


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_parse_transition_table_accepts_transition_observations() -> None:
    report = parse_transition_table(_format_fixture("transition_quant.tsv"))

    assert report.rejected_rows == ()
    assert len(report.accepted_entries) == 7
    assert report.accepted_entries[0].transition_id == "tr_y7_a"
    assert report.accepted_entries[0].precursor_id == "prec_a"
    assert report.accepted_entries[0].sample_id == "s1"
    assert report.accepted_entries[0].peptide_sequence == "PEPTIDEK"
    assert report.accepted_entries[0].fragment_label == "y7"
    assert report.accepted_entries[0].metadata["platform"] == "prm"
    assert report.accepted_entries[-1].sample_id == "s3"


def test_parse_transition_table_rejects_rows_without_precursor_id() -> None:
    report = parse_transition_table(_format_fixture("transition_quant.invalid.tsv"))

    assert report.accepted_entries == ()
    assert len(report.rejected_rows) == 1
    assert report.rejected_rows[0].reason == "transition row requires precursor_id"
