# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.dia import (
    DiaPrecursorQValueFilterTiming,
    build_diann_precursor_matrix_report,
    build_spectronaut_precursor_matrix_report,
)


def _bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "diann"
    )


def test_build_diann_precursor_matrix_report_groups_precursors_across_samples() -> None:
    report = build_diann_precursor_matrix_report(_bundle_root() / "diann_report.tsv")

    assert report.source_name == "DIA-NN"
    assert (
        report.summary.q_value_filter_timing
        is DiaPrecursorQValueFilterTiming.BEFORE_MATRIX_CONSTRUCTION
    )
    assert report.sample_ids == ("sample_A", "sample_B")
    assert report.run_names == ("raw_A", "raw_B")
    assert report.summary.precursor_row_count == 2
    assert report.summary.sample_count == 2
    assert report.summary.target_row_count == 2
    assert report.summary.decoy_row_count == 0
    assert report.summary.excluded_decoy_count == 1
    assert report.summary.observed_cell_count == 3
    assert report.summary.missing_cell_count == 1
    assert "run-scoped" in report.note

    first_row = report.rows[0]
    assert first_row.precursor_key == "ACDM[Oxidation]K|z3|PG002"
    assert first_row.modified_peptide == "ACDM[Oxidation]K"
    assert first_row.source_precursor_ids == ("raw_A_ACDMK_3",)
    first_value = first_row.values[0]
    second_value = first_row.values[1]
    assert first_value.sample_id == "sample_A"
    assert first_value.run_names == ("raw_A",)
    assert first_value.abundance == 890000.0
    assert first_value.q_value == 0.0048
    assert second_value.sample_id == "sample_B"
    assert second_value.detected is False

    second_row = report.rows[1]
    assert second_row.precursor_key == "PESTIDE|z2|PG001"
    assert second_row.source_precursor_ids == ("raw_A_PESTIDE_2", "raw_B_PESTIDE_2")
    assert second_row.values[0].abundance == 1250000.0
    assert second_row.values[1].abundance == 1300000.0
    assert report.metadata_entries[0].source_observation_count >= 1


def test_build_diann_precursor_matrix_report_can_retain_decoys_and_filter_q_value() -> (
    None
):
    report = build_diann_precursor_matrix_report(
        _bundle_root() / "diann_report.tsv",
        include_decoys=True,
        max_q_value=0.01,
    )

    assert report.summary.precursor_row_count == 2
    assert report.summary.decoy_row_count == 0
    assert report.summary.excluded_decoy_count == 0
    assert report.summary.excluded_q_value_count == 1


def test_build_diann_precursor_matrix_report_can_filter_after_matrix_construction() -> (
    None
):
    report = build_diann_precursor_matrix_report(
        _bundle_root() / "diann_report.tsv",
        include_decoys=True,
        max_q_value=0.01,
        q_value_filter_timing=DiaPrecursorQValueFilterTiming.AFTER_MATRIX_CONSTRUCTION,
    )

    assert report.summary.precursor_row_count == 3
    assert report.summary.decoy_row_count == 1
    assert report.summary.excluded_q_value_count == 1
    assert (
        report.summary.q_value_filter_timing
        is DiaPrecursorQValueFilterTiming.AFTER_MATRIX_CONSTRUCTION
    )
    decoy_row = next(
        row for row in report.rows if row.target_decoy_label.value == "decoy"
    )
    assert all(value.detected is False for value in decoy_row.values)
    decoy_metadata = next(
        entry
        for entry in report.metadata_entries
        if entry.target_decoy_label.value == "decoy"
    )
    assert decoy_metadata.excluded_q_value_observation_count == 1
    assert decoy_metadata.detected_sample_count == 0


def test_build_spectronaut_precursor_matrix_report_groups_supported_precursors() -> (
    None
):
    root = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "spectronaut"
    )
    report = build_spectronaut_precursor_matrix_report(
        root / "spectronaut_report.tsv",
        config_path=root / "spectronaut_settings.txt",
    )

    assert report.source_name == "Spectronaut"
    assert report.sample_ids == ("sample_A", "sample_B")
    assert report.summary.precursor_row_count == 2
    assert report.summary.excluded_decoy_count == 1
    precursor_row = next(
        row for row in report.rows if row.modified_peptide == "PES[Phospho]TIDE"
    )
    assert precursor_row.precursor_key == "PES[Phospho]TIDE|z2|PG001"
    assert precursor_row.values[0].abundance == 1420000.0
