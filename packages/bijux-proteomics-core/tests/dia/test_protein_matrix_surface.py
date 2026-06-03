# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.dia import (
    DiaPeptideRollupMethod,
    DiaProteinMatrixTargetKind,
    DiaProteinRollupMethod,
    DiaSharedPeptidePolicy,
    build_dia_peptide_matrix_report,
    build_dia_protein_matrix_report,
    build_diann_precursor_matrix_report,
    build_spectronaut_protein_matrix_report,
)


def _bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "diann"
    )


def test_build_dia_peptide_matrix_report_rolls_precursors_to_peptides() -> None:
    precursor_matrix = build_diann_precursor_matrix_report(
        _bundle_root() / "diann_report.tsv"
    )

    report = build_dia_peptide_matrix_report(
        precursor_matrix,
        rollup_method=DiaPeptideRollupMethod.MAX,
    )

    assert report.source_name == "DIA-NN"
    assert report.rollup_method is DiaPeptideRollupMethod.MAX
    assert report.sample_ids == ("sample_A", "sample_B")
    assert report.summary.peptide_row_count == 2
    assert report.summary.sample_count == 2
    assert report.summary.observed_cell_count == 3
    assert report.summary.missing_cell_count == 1
    assert "peptide-level DIA review" in report.note

    first_row = report.rows[0]
    assert first_row.peptide_key == "ACDM[Oxidation]K|PG002"
    assert first_row.modified_peptide == "ACDM[Oxidation]K"
    assert first_row.values[0].abundance == 890000.0
    assert first_row.values[0].q_value == 0.0048
    assert first_row.values[1].detected is False

    second_row = report.rows[1]
    assert second_row.peptide_key == "PESTIDE|PG001"
    assert second_row.values[0].abundance == 1250000.0
    assert second_row.values[1].abundance == 1300000.0


def test_build_dia_peptide_matrix_report_supports_sum_rollup() -> None:
    precursor_matrix = build_diann_precursor_matrix_report(
        _bundle_root() / "diann_report.tsv"
    )

    report = build_dia_peptide_matrix_report(
        precursor_matrix,
        rollup_method=DiaPeptideRollupMethod.SUM,
    )

    assert report.summary.peptide_row_count == 2
    assert report.rows[1].values[0].abundance == 1250000.0


def test_build_dia_peptide_matrix_report_lists_excluded_precursors() -> None:
    precursor_matrix = build_diann_precursor_matrix_report(
        _bundle_root() / "diann_report.tsv",
        max_q_value=0.003,
    )

    report = build_dia_peptide_matrix_report(precursor_matrix)

    excluded_entry = next(
        entry for entry in report.rollup_evidence_entries if entry.included is False
    )
    assert excluded_entry.rollup_stage.value == "precursor_to_peptide"
    assert excluded_entry.target_entity_level.value == "peptide"
    assert excluded_entry.target_entity_id == "ACDM[Oxidation]K|PG002"
    assert excluded_entry.source_precursor_key == "ACDM[Oxidation]K|z3|PG002"
    assert excluded_entry.exclusion_reason is not None
    assert excluded_entry.exclusion_reason.value == "q_value_threshold"


def test_build_dia_protein_matrix_report_rolls_peptides_to_protein_groups() -> None:
    precursor_matrix = build_diann_precursor_matrix_report(
        _bundle_root() / "diann_report.tsv"
    )
    peptide_matrix = build_dia_peptide_matrix_report(precursor_matrix)

    report = build_dia_protein_matrix_report(
        peptide_matrix,
        target_kind=DiaProteinMatrixTargetKind.PROTEIN_GROUP,
        shared_peptide_policy=DiaSharedPeptidePolicy.INCLUDE,
        rollup_method=DiaProteinRollupMethod.SUM,
    )

    assert report.target_kind is DiaProteinMatrixTargetKind.PROTEIN_GROUP
    assert report.shared_peptide_policy is DiaSharedPeptidePolicy.INCLUDE
    assert report.summary.protein_row_count == 2
    assert report.summary.sample_count == 2
    assert report.summary.observed_cell_count == 3
    assert report.summary.missing_cell_count == 1
    assert "shared-peptide participation explicit" in report.note

    first_row = report.rows[0]
    assert first_row.entity_id == "PG001"
    assert first_row.peptide_count == 1
    assert first_row.shared_peptide_count == 1
    assert first_row.values[0].abundance == 1250000.0
    assert first_row.values[1].abundance == 1300000.0
    assert report.summary.rollup_evidence_entry_count >= 3


def test_build_dia_protein_matrix_report_can_exclude_shared_peptides() -> None:
    precursor_matrix = build_diann_precursor_matrix_report(
        _bundle_root() / "diann_report.tsv"
    )
    peptide_matrix = build_dia_peptide_matrix_report(precursor_matrix)

    report = build_dia_protein_matrix_report(
        peptide_matrix,
        target_kind=DiaProteinMatrixTargetKind.PROTEIN,
        shared_peptide_policy=DiaSharedPeptidePolicy.EXCLUDE,
        rollup_method=DiaProteinRollupMethod.MAX,
    )

    assert report.summary.protein_row_count == 1
    assert report.summary.excluded_shared_peptide_count == 1
    assert report.rows[0].entity_id == "P22222"
    assert report.rows[0].values[0].abundance == 890000.0
    assert report.rows[0].values[1].detected is False
    excluded_shared_entry = next(
        entry
        for entry in report.rollup_evidence_entries
        if entry.exclusion_reason is not None
        and entry.exclusion_reason.value == "shared_peptide_policy"
    )
    assert excluded_shared_entry.target_entity_level.value == "protein"
    assert excluded_shared_entry.target_entity_id == "P11111"


def test_build_spectronaut_protein_matrix_report_preserves_source_name() -> None:
    root = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "spectronaut"
    )

    report = build_spectronaut_protein_matrix_report(
        root / "spectronaut_report.tsv",
        config_path=root / "spectronaut_settings.txt",
    )

    assert report.source_name == "Spectronaut"
    assert report.summary.protein_row_count == 2
    assert report.rollup_evidence_entries[0].target_entity_level.value in {
        "peptide",
        "protein_group",
    }
