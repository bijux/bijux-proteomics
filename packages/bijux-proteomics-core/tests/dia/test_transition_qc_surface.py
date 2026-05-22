# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.dia import build_transition_qc_report_from_table


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_build_transition_qc_report_links_transitions_to_precursors() -> None:
    report = build_transition_qc_report_from_table(_format_fixture("transition_quant.tsv"))

    assert report.summary.precursor_count == 2
    assert report.summary.transition_count == 4
    assert report.summary.sample_count == 3
    assert report.summary.observed_cell_count == 7
    assert report.summary.missing_cell_count == 5
    assert report.entries[0].precursor_id == "prec_a"
    assert report.entries[0].transition_id == "tr_y7_a"
    assert report.entries[0].fragment_label == "y7"
    assert report.entries[-1].precursor_id == "prec_b"
    assert report.entries[-1].transition_id == "tr_y6_b"


def test_build_transition_qc_report_summarizes_transition_intensities() -> None:
    report = build_transition_qc_report_from_table(_format_fixture("transition_quant.tsv"))

    first_entry = report.entries[0]
    assert first_entry.detected_sample_count == 2
    assert first_entry.total_intensity == 230000.0
    assert first_entry.mean_intensity == 115000.0
    assert first_entry.median_intensity == 115000.0
    assert first_entry.min_q_value == 0.002
    assert first_entry.values[0].sample_id == "s1"
    assert first_entry.values[0].intensity == 120000.0
    assert first_entry.values[2].detected is False
