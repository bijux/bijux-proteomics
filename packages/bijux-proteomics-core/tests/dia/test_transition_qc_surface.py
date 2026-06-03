# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.dia import (
    build_transition_qc_report,
    build_transition_qc_report_from_table,
)
from bijux_proteomics.io import parse_transition_table
from bijux_proteomics.io.transition_table import TransitionTableEntry


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_build_transition_qc_report_links_transitions_to_precursors() -> None:
    report = build_transition_qc_report_from_table(
        _format_fixture("transition_quant.tsv")
    )

    assert report.summary.precursor_count == 2
    assert report.summary.transition_count == 4
    assert report.summary.sample_count == 3
    assert report.summary.observed_cell_count == 7
    assert report.summary.missing_cell_count == 5
    assert report.summary.weak_transition_count == 1
    assert report.entries[0].precursor_id == "prec_a"
    assert report.entries[0].precursor_charge == 2
    assert report.entries[0].transition_id == "tr_y7_a"
    assert report.entries[0].fragment_label == "y7"
    assert report.entries[0].median_retention_time_minutes == 12.45
    assert report.entries[-1].precursor_id == "prec_b"
    assert report.entries[-1].precursor_charge == 3
    assert report.entries[-1].transition_id == "tr_y6_b"


def test_build_transition_qc_report_summarizes_transition_intensities() -> None:
    report = build_transition_qc_report_from_table(
        _format_fixture("transition_quant.tsv")
    )

    first_entry = report.entries[0]
    assert first_entry.detected_sample_count == 2
    assert first_entry.total_intensity == 230000.0
    assert first_entry.mean_intensity == 115000.0
    assert first_entry.median_intensity == 115000.0
    assert round(first_entry.median_relative_share, 6) == 0.837185
    assert first_entry.min_q_value == 0.002
    assert first_entry.values[0].sample_id == "s1"
    assert first_entry.values[0].intensity == 120000.0
    assert first_entry.values[0].retention_time_minutes == 12.5
    assert first_entry.values[0].precursor_total_intensity == 160000.0
    assert first_entry.values[0].relative_share == 0.75
    assert first_entry.values[2].detected is False


def test_build_transition_qc_report_flags_weak_transitions() -> None:
    report = build_transition_qc_report_from_table(
        _format_fixture("transition_quant.tsv")
    )

    assert len(report.weak_transitions) == 1
    assert report.weak_transitions[0].transition_id == "tr_y6_b"
    assert round(report.weak_transitions[0].detection_fraction, 6) == 0.333333
    assert round(report.weak_transitions[0].median_relative_share, 6) == 0.078947
    assert report.weak_transitions[0].weak_reasons == (
        "low sample detection fraction",
        "low median precursor-relative share",
    )
    weak_entry = next(
        entry for entry in report.entries if entry.transition_id == "tr_y6_b"
    )
    assert weak_entry.weak is True


def test_build_transition_qc_report_keeps_same_transition_id_separate_by_precursor() -> (
    None
):
    parse_report = parse_transition_table(_format_fixture("transition_quant.tsv"))
    extra_entry = TransitionTableEntry(
        transition_id="tr_y7_a",
        precursor_id="prec_c",
        precursor_charge=4,
        sample_id="s1",
        intensity=45000.0,
        peptide_sequence="ALTPEP",
        protein_ref="P777",
        fragment_label="y7",
        retention_time_minutes=22.1,
        fragment_mz=801.2,
    )

    split_report = build_transition_qc_report(
        parse_report.accepted_entries + (extra_entry,)
    )

    split_entries = [
        entry for entry in split_report.entries if entry.transition_id == "tr_y7_a"
    ]

    assert len(split_entries) == 2
    assert split_entries[0].precursor_id == "prec_a"
    assert split_entries[1].precursor_id == "prec_c"
    assert split_entries[1].precursor_charge == 4
    assert split_entries[1].detected_sample_count == 1
    assert split_entries[1].values[0].retention_time_minutes == 22.1
