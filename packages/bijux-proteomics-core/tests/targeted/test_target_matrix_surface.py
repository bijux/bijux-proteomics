# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.targeted import (
    build_skyline_targeted_matrix_report,
    build_transition_table_targeted_matrix_report,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_build_skyline_targeted_matrix_report_rolls_up_precursor_targets() -> None:
    report = build_skyline_targeted_matrix_report(_format_fixture("skyline_targeted_results.tsv"))

    assert report.source_name == "Skyline"
    assert report.summary.target_count == 2
    assert report.summary.sample_count == 2
    assert report.summary.observed_cell_count == 3
    assert report.summary.missing_cell_count == 1
    assert report.rows[0].target_id == "ACDMPEP/3"
    assert report.rows[0].detected_sample_count == 1
    assert report.rows[1].target_id == "PEPTIDEK/2"
    assert report.rows[1].total_intensity == 281000.0


def test_build_transition_table_targeted_matrix_report_rolls_up_transition_table_targets() -> None:
    report = build_transition_table_targeted_matrix_report(
        _format_fixture("targeted_transition_results.tsv")
    )

    assert report.source_name == "transition table"
    assert report.summary.target_count == 2
    assert report.summary.sample_count == 2
    assert report.rows[0].target_id == "prec_a"
    assert report.rows[0].values[0].intensity == 160000.0
    assert report.rows[1].target_id == "prec_b"
    assert report.rows[1].values[1].detected is False
