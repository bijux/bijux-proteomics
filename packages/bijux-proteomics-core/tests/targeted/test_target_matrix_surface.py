# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.targeted import (
    TargetedResultImportReport,
    TargetedResultImportSummary,
    TargetedResultObservation,
    TargetedResultSourceKind,
    build_skyline_targeted_matrix_report,
    build_targeted_matrix_report,
    build_transition_table_targeted_matrix_report,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_build_skyline_targeted_matrix_report_rolls_up_precursor_targets() -> None:
    report = build_skyline_targeted_matrix_report(
        _format_fixture("skyline_targeted_results.tsv")
    )

    assert report.source_name == "Skyline"
    assert report.summary.target_count == 2
    assert report.summary.sample_count == 2
    assert report.summary.observed_cell_count == 3
    assert report.summary.missing_cell_count == 1
    assert report.summary.zero_passing_cell_count == 0
    assert report.summary.retained_transition_count == 4
    assert report.summary.excluded_transition_count == 2
    assert report.summary.quality_flag_count == 2
    assert report.rows[0].target_id == "ACDMPEP/3"
    assert report.rows[0].detected_sample_count == 1
    assert report.rows[0].retained_transition_ids == ("y5",)
    assert report.rows[0].excluded_transition_ids == ("y6",)
    assert report.rows[0].median_retention_time_minutes == 18.1
    assert report.rows[0].quality_flag_count == 1
    assert report.rows[1].target_id == "PEPTIDEK/2"
    assert report.rows[1].total_intensity == 273000.0
    assert report.rows[1].values[1].retained_transition_ids == ("y7",)
    assert report.rows[1].values[1].excluded_transition_ids == ("y8",)
    assert report.rows[1].values[1].intensity == 115000.0
    assert report.rows[1].flagged_sample_count == 1
    assert report.excluded_transitions[0].transition_id == "y6"
    assert report.excluded_transitions[-1].transition_id == "y8"
    missing_entry = next(
        entry
        for entry in report.missingness
        if entry.target_id == "ACDMPEP/3" and entry.sample_id == "sample_B"
    )
    assert missing_entry.missing_reason == "no_observation"


def test_build_transition_table_targeted_matrix_report_rolls_up_transition_table_targets() -> (
    None
):
    report = build_transition_table_targeted_matrix_report(
        _format_fixture("targeted_transition_results.tsv")
    )

    assert report.source_name == "transition table"
    assert report.summary.target_count == 2
    assert report.summary.sample_count == 2
    assert report.summary.retained_transition_count == 4
    assert report.summary.excluded_transition_count == 2
    assert report.summary.quality_flag_count == 2
    assert report.rows[0].target_id == "prec_a"
    assert report.rows[0].values[0].intensity == 160000.0
    assert report.rows[0].values[1].intensity == 110000.0
    assert report.rows[0].values[1].quality_flags == ("interference",)
    assert report.rows[1].target_id == "prec_b"
    assert report.rows[1].values[1].detected is False
    assert report.rows[1].values[1].missing_reason == "no_observation"


def test_build_targeted_matrix_report_marks_zero_passing_transition_cells_missing() -> (
    None
):
    import_report = TargetedResultImportReport(
        source_kind=TargetedResultSourceKind.SKYLINE_EXPORT,
        source_name="Skyline",
        observations=(
            TargetedResultObservation(
                source_kind=TargetedResultSourceKind.SKYLINE_EXPORT,
                transition_id="y7",
                precursor_id="PEPTIDEK/2",
                precursor_charge=2,
                peptide_sequence="PEPTIDEK",
                sample_id="sample_A",
                intensity=120000.0,
                retention_time_minutes=12.5,
                quality_flag="pass",
                protein_ref="P001",
                provenance=ImportedEvidenceProvenance.from_single_row(
                    source_engine="skyline",
                    source_file="synthetic.tsv",
                    source_row_number=2,
                    original_identifiers={
                        "transition_id": "y7",
                        "precursor_id": "PEPTIDEK/2",
                        "sample_id": "sample_A",
                    },
                ),
            ),
            TargetedResultObservation(
                source_kind=TargetedResultSourceKind.SKYLINE_EXPORT,
                transition_id="y7",
                precursor_id="PEPTIDEK/2",
                precursor_charge=2,
                peptide_sequence="PEPTIDEK",
                sample_id="sample_B",
                intensity=115000.0,
                retention_time_minutes=12.4,
                quality_flag="interference",
                protein_ref="P001",
                provenance=ImportedEvidenceProvenance.from_single_row(
                    source_engine="skyline",
                    source_file="synthetic.tsv",
                    source_row_number=3,
                    original_identifiers={
                        "transition_id": "y7",
                        "precursor_id": "PEPTIDEK/2",
                        "sample_id": "sample_B",
                    },
                ),
            ),
            TargetedResultObservation(
                source_kind=TargetedResultSourceKind.SKYLINE_EXPORT,
                transition_id="y8",
                precursor_id="PEPTIDEK/2",
                precursor_charge=2,
                peptide_sequence="PEPTIDEK",
                sample_id="sample_B",
                intensity=8000.0,
                retention_time_minutes=12.7,
                quality_flag="low_signal",
                protein_ref="P001",
                provenance=ImportedEvidenceProvenance.from_single_row(
                    source_engine="skyline",
                    source_file="synthetic.tsv",
                    source_row_number=4,
                    original_identifiers={
                        "transition_id": "y8",
                        "precursor_id": "PEPTIDEK/2",
                        "sample_id": "sample_B",
                    },
                ),
            ),
        ),
        summary=TargetedResultImportSummary(
            observation_count=3,
            precursor_count=1,
            transition_count=2,
            sample_count=2,
            retention_time_count=3,
            quality_flag_count=2,
        ),
        note="synthetic import report",
    )

    matrix_report = build_targeted_matrix_report(import_report)

    assert matrix_report.summary.observed_cell_count == 1
    assert matrix_report.summary.missing_cell_count == 1
    assert matrix_report.summary.zero_passing_cell_count == 1
    assert matrix_report.rows[0].total_intensity == 120000.0
    assert matrix_report.rows[0].values[1].detected is False
    assert matrix_report.rows[0].values[1].intensity is None
    assert matrix_report.rows[0].values[1].missing_reason == "no_passing_transitions"
    assert matrix_report.rows[0].values[1].excluded_transition_count == 2
    assert matrix_report.missingness[1].missing is True
    assert matrix_report.missingness[1].missing_reason == "no_passing_transitions"
