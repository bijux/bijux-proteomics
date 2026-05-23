# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics.io import parse_experimental_design_table
from bijux_proteomics.targeted import (
    build_skyline_result_import_report,
    build_targeted_carryover_report,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_build_targeted_carryover_report_keeps_ordered_run_candidates_visible() -> None:
    import_report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_carryover_results.tsv")
    )
    design_entries = parse_experimental_design_table(
        _format_fixture("skyline_targeted_carryover.design.tsv")
    ).accepted_entries

    report = build_targeted_carryover_report(import_report, design_entries)

    assert report.source_name == "Skyline"
    assert report.summary.run_count == 4
    assert report.summary.precursor_count == 2
    assert report.summary.candidate_entry_count == 2
    assert report.summary.affected_run_count == 2
    assert report.summary.source_run_count == 1

    immediate_candidate = report.candidates[0]
    assert immediate_candidate.source_run_id == "source_high.raw"
    assert immediate_candidate.source_sample_id == "source_high"
    assert immediate_candidate.source_run_order == 1
    assert immediate_candidate.affected_run_id == "blank_after_source.raw"
    assert immediate_candidate.affected_sample_id == "blank_after_source"
    assert immediate_candidate.affected_run_order == 2
    assert immediate_candidate.order_gap == 1
    assert immediate_candidate.precursor_id == "CARRYPEP/2"
    assert immediate_candidate.peptide_sequence == "CARRYPEP"
    assert immediate_candidate.protein_ref == "P100"
    assert immediate_candidate.source_total_intensity == 200000.0
    assert immediate_candidate.affected_total_intensity == 4000.0
    assert immediate_candidate.repeated_signal_fraction == 0.02
    assert immediate_candidate.carryover_score == 0.9333
    assert immediate_candidate.concern_codes == (
        "high_intensity_previous_run",
        "low_level_repeated_signal",
        "immediate_run_order_followup",
    )

    delayed_candidate = report.candidates[1]
    assert delayed_candidate.affected_run_id == "target_sample.raw"
    assert delayed_candidate.affected_run_order == 3
    assert delayed_candidate.order_gap == 2
    assert delayed_candidate.affected_total_intensity == 2000.0
    assert delayed_candidate.repeated_signal_fraction == 0.01
    assert delayed_candidate.carryover_score == 0.8


def test_build_targeted_carryover_report_requires_run_order() -> None:
    import_report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_carryover_results.tsv")
    )
    unordered_design_entries = parse_experimental_design_table(
        _format_fixture("skyline_targeted_qc.design.tsv")
    ).accepted_entries

    with pytest.raises(ValueError, match="run_order is required for carryover analysis"):
        build_targeted_carryover_report(import_report, unordered_design_entries)
