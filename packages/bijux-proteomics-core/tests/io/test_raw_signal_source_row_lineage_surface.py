# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.raw_signal_evidence_cards import (
    extract_mzml_raw_signal_evidence_cards,
    render_raw_signal_evidence_card_tsv,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_raw_signal_evidence_cards_emit_explicit_derived_no_source_reason() -> None:
    report = extract_mzml_raw_signal_evidence_cards(
        (
            _format_fixture("raw_signal_card_reference.mzml"),
            _format_fixture("raw_signal_card_shifted.mzml"),
        ),
        _format_fixture("raw_signal_card_targets.tsv"),
        selected_precursor_ids=("prec_peptide",),
    )

    assert report.cards
    card = report.cards[0]
    assert card.source_row_refs == ()
    assert card.derived_no_source_reason == (
        "raw-signal evidence cards summarize mzML trace windows, spectra, and peak models rather than row-numbered tabular inputs"
    )
    assert "derived_no_source_reason" in render_raw_signal_evidence_card_tsv(report)
