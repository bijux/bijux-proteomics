# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned DIA spectral-library coverage surfaces."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.dia.protein_matrix import (
    DiaPeptideMatrixReport,
    DiaProteinMatrixReport,
    DiaProteinMatrixTargetKind,
    DiaSharedPeptidePolicy,
    build_diann_peptide_matrix_report,
    build_diann_protein_matrix_report,
)
from bijux_proteomics.io.formats import ExperimentalDesignEntry, parse_experimental_design_table
from bijux_proteomics.io.spectral_library import (
    SpectralLibraryImportReport,
    import_spectral_library,
)
from bijux_proteomics_foundation import JsonModel


class DiaLibraryCoverageSampleEntry(JsonModel):
    """One sample-scoped spectral-library coverage entry."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    detected_peptide_count: int = Field(..., ge=0)
    detected_protein_count: int = Field(..., ge=0)
    peptide_coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    protein_coverage_fraction: float = Field(..., ge=0.0, le=1.0)


class DiaLibraryCoverageConditionEntry(JsonModel):
    """One condition-scoped spectral-library coverage entry."""

    model_config = ConfigDict(extra="forbid")

    condition: str = Field(..., min_length=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    detected_peptide_count: int = Field(..., ge=0)
    detected_protein_count: int = Field(..., ge=0)
    peptide_coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    protein_coverage_fraction: float = Field(..., ge=0.0, le=1.0)


class DiaLibraryCoverageSummary(JsonModel):
    """Compact DIA spectral-library coverage summary."""

    model_config = ConfigDict(extra="forbid")

    library_peptide_count: int = Field(..., ge=0)
    detected_peptide_count: int = Field(..., ge=0)
    library_protein_count: int = Field(..., ge=0)
    detected_protein_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    condition_count: int = Field(..., ge=0)
    peptide_coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    protein_coverage_fraction: float = Field(..., ge=0.0, le=1.0)


class DiaLibraryCoverageReport(JsonModel):
    """Coverage of observed DIA peptide/protein evidence against one spectral library."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(default="DIA-NN", min_length=1)
    library_source_format: str = Field(..., min_length=1)
    sample_entries: tuple[DiaLibraryCoverageSampleEntry, ...] = Field(default_factory=tuple)
    condition_entries: tuple[DiaLibraryCoverageConditionEntry, ...] = Field(
        default_factory=tuple
    )
    summary: DiaLibraryCoverageSummary
    note: str = Field(..., min_length=1)


def build_dia_library_coverage_report(
    library_report: SpectralLibraryImportReport,
    peptide_matrix: DiaPeptideMatrixReport,
    protein_matrix: DiaProteinMatrixReport,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...] = (),
) -> DiaLibraryCoverageReport:
    """Compare DIA protein evidence against spectral-library peptide and protein scope."""

    library_peptides = {
        entry.canonical_peptide
        for entry in library_report.entries
        if entry.target_decoy_label.value != "decoy"
    }
    library_proteins = {
        protein_ref
        for entry in library_report.entries
        if entry.target_decoy_label.value != "decoy"
        for protein_ref in entry.protein_refs
    }
    detected_peptides = {
        row.canonical_peptide
        for row in peptide_matrix.rows
    }
    detected_proteins = {row.entity_id for row in protein_matrix.rows}
    sample_entries = _build_sample_entries(
        library_peptides=library_peptides,
        library_proteins=library_proteins,
        peptide_matrix=peptide_matrix,
        protein_matrix=protein_matrix,
    )
    condition_entries = _build_condition_entries(
        library_peptides=library_peptides,
        library_proteins=library_proteins,
        peptide_matrix=peptide_matrix,
        protein_matrix=protein_matrix,
        design_entries=design_entries,
    )
    return DiaLibraryCoverageReport(
        library_source_format=library_report.source_format.value,
        sample_entries=sample_entries,
        condition_entries=condition_entries,
        summary=DiaLibraryCoverageSummary(
            library_peptide_count=len(library_peptides),
            detected_peptide_count=len(detected_peptides & library_peptides),
            library_protein_count=len(library_proteins),
            detected_protein_count=len(detected_proteins & library_proteins),
            sample_count=len(sample_entries),
            condition_count=len(condition_entries),
            peptide_coverage_fraction=_fraction(
                len(detected_peptides & library_peptides),
                len(library_peptides),
            ),
            protein_coverage_fraction=_fraction(
                len(detected_proteins & library_proteins),
                len(library_proteins),
            ),
        ),
        note=(
            "library coverage compares observed DIA peptide and protein evidence against the measurable library scope instead of treating imported intensity as full proteome visibility"
        ),
    )


def build_diann_library_coverage_report(
    result_tsv_path: Path,
    library_path: Path,
    *,
    design_path: Path | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = None,
    shared_peptide_policy: DiaSharedPeptidePolicy = DiaSharedPeptidePolicy.INCLUDE,
) -> DiaLibraryCoverageReport:
    """Build DIA spectral-library coverage directly from DIA-NN evidence and one library."""

    library_report = import_spectral_library(library_path)
    peptide_matrix = build_diann_peptide_matrix_report(
        result_tsv_path,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
    )
    protein_matrix = build_diann_protein_matrix_report(
        result_tsv_path,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
        target_kind=DiaProteinMatrixTargetKind.PROTEIN,
        shared_peptide_policy=shared_peptide_policy,
    )
    design_entries = ()
    if design_path is not None:
        design_entries = parse_experimental_design_table(design_path).accepted_entries
    return build_dia_library_coverage_report(
        library_report,
        peptide_matrix,
        protein_matrix,
        design_entries=design_entries,
    )


def _build_sample_entries(
    *,
    library_peptides: set[str],
    library_proteins: set[str],
    peptide_matrix: DiaPeptideMatrixReport,
    protein_matrix: DiaProteinMatrixReport,
) -> tuple[DiaLibraryCoverageSampleEntry, ...]:
    entries: list[DiaLibraryCoverageSampleEntry] = []
    for sample_id in protein_matrix.sample_ids:
        detected_peptides = {
            row.canonical_peptide
            for row in peptide_matrix.rows
            for value in row.values
            if value.sample_id == sample_id and value.detected
        }
        detected_proteins = {
            row.entity_id
            for row in protein_matrix.rows
            for value in row.values
            if value.sample_id == sample_id and value.detected
        }
        entries.append(
            DiaLibraryCoverageSampleEntry(
                sample_id=sample_id,
                detected_peptide_count=len(detected_peptides & library_peptides),
                detected_protein_count=len(detected_proteins & library_proteins),
                peptide_coverage_fraction=_fraction(
                    len(detected_peptides & library_peptides),
                    len(library_peptides),
                ),
                protein_coverage_fraction=_fraction(
                    len(detected_proteins & library_proteins),
                    len(library_proteins),
                ),
            )
        )
    return tuple(entries)


def _build_condition_entries(
    *,
    library_peptides: set[str],
    library_proteins: set[str],
    peptide_matrix: DiaPeptideMatrixReport,
    protein_matrix: DiaProteinMatrixReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[DiaLibraryCoverageConditionEntry, ...]:
    sample_ids_by_condition: dict[str, list[str]] = {}
    for entry in design_entries:
        if entry.sample_id in protein_matrix.sample_ids:
            sample_ids_by_condition.setdefault(entry.condition, []).append(entry.sample_id)
    entries: list[DiaLibraryCoverageConditionEntry] = []
    for condition, sample_ids in sorted(sample_ids_by_condition.items()):
        detected_peptides = {
            row.canonical_peptide
            for row in peptide_matrix.rows
            for value in row.values
            if value.sample_id in sample_ids and value.detected
        }
        detected_proteins = {
            row.entity_id
            for row in protein_matrix.rows
            for value in row.values
            if value.sample_id in sample_ids and value.detected
        }
        entries.append(
            DiaLibraryCoverageConditionEntry(
                condition=condition,
                sample_ids=tuple(sorted(sample_ids)),
                detected_peptide_count=len(detected_peptides & library_peptides),
                detected_protein_count=len(detected_proteins & library_proteins),
                peptide_coverage_fraction=_fraction(
                    len(detected_peptides & library_peptides),
                    len(library_peptides),
                ),
                protein_coverage_fraction=_fraction(
                    len(detected_proteins & library_proteins),
                    len(library_proteins),
                ),
            )
        )
    return tuple(entries)


def _fraction(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return min(1.0, max(0.0, numerator / denominator))
