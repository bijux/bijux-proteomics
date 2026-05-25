# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned DIA spectral-library coverage surfaces."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from io import StringIO
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


class DiaLibraryCoveragePeptideEntry(JsonModel):
    """One library peptide with explicit DIA detection burden."""

    model_config = ConfigDict(extra="forbid")

    canonical_peptide: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    detected_overall: bool
    detected_sample_count: int = Field(..., ge=0)
    detected_condition_count: int = Field(..., ge=0)


class DiaLibraryCoverageProteinEntry(JsonModel):
    """One library protein with explicit DIA detection burden."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    detected_overall: bool
    detected_sample_count: int = Field(..., ge=0)
    detected_condition_count: int = Field(..., ge=0)


class DiaObservedOutsideLibraryPeptideEntry(JsonModel):
    """One observed DIA peptide that is absent from the imported library."""

    model_config = ConfigDict(extra="forbid")

    canonical_peptide: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    condition_ids: tuple[str, ...] = Field(default_factory=tuple)
    detected_sample_count: int = Field(..., ge=0)
    detected_condition_count: int = Field(..., ge=0)


class DiaObservedOutsideLibraryProteinEntry(JsonModel):
    """One observed DIA protein that is absent from the imported library."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    condition_ids: tuple[str, ...] = Field(default_factory=tuple)
    detected_sample_count: int = Field(..., ge=0)
    detected_condition_count: int = Field(..., ge=0)


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
    observed_outside_library_peptide_count: int = Field(..., ge=0)
    library_protein_count: int = Field(..., ge=0)
    detected_protein_count: int = Field(..., ge=0)
    observed_outside_library_protein_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    condition_count: int = Field(..., ge=0)
    peptide_coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    protein_coverage_fraction: float = Field(..., ge=0.0, le=1.0)


class DiaLibraryCoverageReport(JsonModel):
    """Coverage of observed DIA peptide/protein evidence against one spectral library."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(default="DIA-NN", min_length=1)
    library_source_format: str = Field(..., min_length=1)
    peptide_entries: tuple[DiaLibraryCoveragePeptideEntry, ...] = Field(
        default_factory=tuple
    )
    protein_entries: tuple[DiaLibraryCoverageProteinEntry, ...] = Field(
        default_factory=tuple
    )
    observed_outside_library_peptide_entries: tuple[
        DiaObservedOutsideLibraryPeptideEntry, ...
    ] = Field(default_factory=tuple)
    observed_outside_library_protein_entries: tuple[
        DiaObservedOutsideLibraryProteinEntry, ...
    ] = Field(default_factory=tuple)
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
    library_peptide_protein_refs = _build_library_peptide_protein_refs(library_report)
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
    peptide_entries = _build_peptide_entries(
        library_peptide_protein_refs=library_peptide_protein_refs,
        peptide_matrix=peptide_matrix,
        design_entries=design_entries,
    )
    protein_entries = _build_protein_entries(
        library_proteins=library_proteins,
        protein_matrix=protein_matrix,
        design_entries=design_entries,
    )
    observed_outside_library_peptide_entries = (
        _build_observed_outside_library_peptide_entries(
            library_peptides=library_peptides,
            peptide_matrix=peptide_matrix,
            design_entries=design_entries,
        )
    )
    observed_outside_library_protein_entries = (
        _build_observed_outside_library_protein_entries(
            library_proteins=library_proteins,
            protein_matrix=protein_matrix,
            design_entries=design_entries,
        )
    )
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
        peptide_entries=peptide_entries,
        protein_entries=protein_entries,
        observed_outside_library_peptide_entries=observed_outside_library_peptide_entries,
        observed_outside_library_protein_entries=observed_outside_library_protein_entries,
        sample_entries=sample_entries,
        condition_entries=condition_entries,
        summary=DiaLibraryCoverageSummary(
            library_peptide_count=len(library_peptides),
            detected_peptide_count=len(detected_peptides & library_peptides),
            observed_outside_library_peptide_count=len(
                observed_outside_library_peptide_entries
            ),
            library_protein_count=len(library_proteins),
            detected_protein_count=len(detected_proteins & library_proteins),
            observed_outside_library_protein_count=len(
                observed_outside_library_protein_entries
            ),
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
            "library coverage compares observed DIA peptide and protein evidence against the measurable library scope while preserving observed evidence that is absent from the imported library as separate ledgers"
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


def render_dia_library_coverage_summary_tsv(report: DiaLibraryCoverageReport) -> str:
    """Render a compact summary for one DIA spectral-library coverage report."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "source_name",
            "library_source_format",
            "library_peptide_count",
            "detected_peptide_count",
            "observed_outside_library_peptide_count",
            "library_protein_count",
            "detected_protein_count",
            "observed_outside_library_protein_count",
            "sample_count",
            "condition_count",
            "peptide_coverage_fraction",
            "protein_coverage_fraction",
            "note",
        ]
    )
    writer.writerow(
        [
            report.source_name,
            report.library_source_format,
            report.summary.library_peptide_count,
            report.summary.detected_peptide_count,
            report.summary.observed_outside_library_peptide_count,
            report.summary.library_protein_count,
            report.summary.detected_protein_count,
            report.summary.observed_outside_library_protein_count,
            report.summary.sample_count,
            report.summary.condition_count,
            report.summary.peptide_coverage_fraction,
            report.summary.protein_coverage_fraction,
            report.note,
        ]
    )
    return buffer.getvalue()


def render_dia_library_coverage_sample_tsv(report: DiaLibraryCoverageReport) -> str:
    """Render sample-scoped library coverage entries."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "sample_id",
            "detected_peptide_count",
            "detected_protein_count",
            "peptide_coverage_fraction",
            "protein_coverage_fraction",
        ]
    )
    for entry in report.sample_entries:
        writer.writerow(
            [
                entry.sample_id,
                entry.detected_peptide_count,
                entry.detected_protein_count,
                entry.peptide_coverage_fraction,
                entry.protein_coverage_fraction,
            ]
        )
    return buffer.getvalue()


def render_dia_library_coverage_condition_tsv(report: DiaLibraryCoverageReport) -> str:
    """Render condition-scoped library coverage entries."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "condition",
            "sample_ids",
            "detected_peptide_count",
            "detected_protein_count",
            "peptide_coverage_fraction",
            "protein_coverage_fraction",
        ]
    )
    for entry in report.condition_entries:
        writer.writerow(
            [
                entry.condition,
                ";".join(entry.sample_ids),
                entry.detected_peptide_count,
                entry.detected_protein_count,
                entry.peptide_coverage_fraction,
                entry.protein_coverage_fraction,
            ]
        )
    return buffer.getvalue()


def render_dia_library_coverage_peptide_tsv(report: DiaLibraryCoverageReport) -> str:
    """Render library peptide coverage identities."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "canonical_peptide",
            "protein_refs",
            "detected_overall",
            "detected_sample_count",
            "detected_condition_count",
        ]
    )
    for entry in report.peptide_entries:
        writer.writerow(
            [
                entry.canonical_peptide,
                ";".join(entry.protein_refs),
                str(entry.detected_overall).lower(),
                entry.detected_sample_count,
                entry.detected_condition_count,
            ]
        )
    return buffer.getvalue()


def render_dia_library_coverage_protein_tsv(report: DiaLibraryCoverageReport) -> str:
    """Render library protein coverage identities."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "protein_ref",
            "detected_overall",
            "detected_sample_count",
            "detected_condition_count",
        ]
    )
    for entry in report.protein_entries:
        writer.writerow(
            [
                entry.protein_ref,
                str(entry.detected_overall).lower(),
                entry.detected_sample_count,
                entry.detected_condition_count,
            ]
        )
    return buffer.getvalue()


def render_dia_library_coverage_observed_outside_peptide_tsv(
    report: DiaLibraryCoverageReport,
) -> str:
    """Render observed DIA peptides that are absent from the imported library."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "canonical_peptide",
            "protein_refs",
            "sample_ids",
            "condition_ids",
            "detected_sample_count",
            "detected_condition_count",
        ]
    )
    for entry in report.observed_outside_library_peptide_entries:
        writer.writerow(
            [
                entry.canonical_peptide,
                ";".join(entry.protein_refs),
                ";".join(entry.sample_ids),
                ";".join(entry.condition_ids),
                entry.detected_sample_count,
                entry.detected_condition_count,
            ]
        )
    return buffer.getvalue()


def render_dia_library_coverage_observed_outside_protein_tsv(
    report: DiaLibraryCoverageReport,
) -> str:
    """Render observed DIA proteins that are absent from the imported library."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "protein_ref",
            "sample_ids",
            "condition_ids",
            "detected_sample_count",
            "detected_condition_count",
        ]
    )
    for entry in report.observed_outside_library_protein_entries:
        writer.writerow(
            [
                entry.protein_ref,
                ";".join(entry.sample_ids),
                ";".join(entry.condition_ids),
                entry.detected_sample_count,
                entry.detected_condition_count,
            ]
        )
    return buffer.getvalue()


def export_dia_library_coverage_summary_tsv(
    report: DiaLibraryCoverageReport,
    path: Path,
) -> None:
    write_output_table_tsv(path, render_dia_library_coverage_summary_tsv(report))


def export_dia_library_coverage_sample_tsv(
    report: DiaLibraryCoverageReport,
    path: Path,
) -> None:
    write_output_table_tsv(path, render_dia_library_coverage_sample_tsv(report))


def export_dia_library_coverage_condition_tsv(
    report: DiaLibraryCoverageReport,
    path: Path,
) -> None:
    write_output_table_tsv(path, render_dia_library_coverage_condition_tsv(report))


def export_dia_library_coverage_peptide_tsv(
    report: DiaLibraryCoverageReport,
    path: Path,
) -> None:
    write_output_table_tsv(path, render_dia_library_coverage_peptide_tsv(report))


def export_dia_library_coverage_protein_tsv(
    report: DiaLibraryCoverageReport,
    path: Path,
) -> None:
    write_output_table_tsv(path, render_dia_library_coverage_protein_tsv(report))


def export_dia_library_coverage_observed_outside_peptide_tsv(
    report: DiaLibraryCoverageReport,
    path: Path,
) -> None:
    write_output_table_tsv(path, render_dia_library_coverage_observed_outside_peptide_tsv(report))


def export_dia_library_coverage_observed_outside_protein_tsv(
    report: DiaLibraryCoverageReport,
    path: Path,
) -> None:
    write_output_table_tsv(path, render_dia_library_coverage_observed_outside_protein_tsv(report))


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


def _build_library_peptide_protein_refs(
    library_report: SpectralLibraryImportReport,
) -> dict[str, tuple[str, ...]]:
    peptide_protein_refs: dict[str, set[str]] = {}
    for entry in library_report.entries:
        if entry.target_decoy_label.value == "decoy":
            continue
        peptide_protein_refs.setdefault(entry.canonical_peptide, set()).update(
            entry.protein_refs
        )
    return {
        canonical_peptide: tuple(sorted(protein_refs))
        for canonical_peptide, protein_refs in sorted(peptide_protein_refs.items())
    }


def _build_peptide_entries(
    *,
    library_peptide_protein_refs: dict[str, tuple[str, ...]],
    peptide_matrix: DiaPeptideMatrixReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[DiaLibraryCoveragePeptideEntry, ...]:
    row_by_peptide = {
        row.canonical_peptide: row for row in peptide_matrix.rows
    }
    entries: list[DiaLibraryCoveragePeptideEntry] = []
    for canonical_peptide, protein_refs in sorted(library_peptide_protein_refs.items()):
        matching_row = row_by_peptide.get(canonical_peptide)
        detected_samples = (
            {value.sample_id for value in matching_row.values if value.detected}
            if matching_row is not None
            else set()
        )
        entries.append(
            DiaLibraryCoveragePeptideEntry(
                canonical_peptide=canonical_peptide,
                protein_refs=protein_refs,
                detected_overall=matching_row is not None,
                detected_sample_count=len(detected_samples),
                detected_condition_count=len(
                    _condition_ids_for_sample_ids(
                        detected_samples,
                        design_entries=design_entries,
                    )
                ),
            )
        )
    return tuple(entries)


def _build_observed_outside_library_peptide_entries(
    *,
    library_peptides: set[str],
    peptide_matrix: DiaPeptideMatrixReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[DiaObservedOutsideLibraryPeptideEntry, ...]:
    entries: list[DiaObservedOutsideLibraryPeptideEntry] = []
    for row in sorted(peptide_matrix.rows, key=lambda entry: entry.canonical_peptide):
        if row.canonical_peptide in library_peptides:
            continue
        detected_samples = tuple(
            sorted({value.sample_id for value in row.values if value.detected})
        )
        if not detected_samples:
            continue
        condition_ids = tuple(
            sorted(
                _condition_ids_for_sample_ids(
                    set(detected_samples),
                    design_entries=design_entries,
                )
            )
        )
        entries.append(
            DiaObservedOutsideLibraryPeptideEntry(
                canonical_peptide=row.canonical_peptide,
                protein_refs=row.protein_refs,
                sample_ids=detected_samples,
                condition_ids=condition_ids,
                detected_sample_count=len(detected_samples),
                detected_condition_count=len(condition_ids),
            )
        )
    return tuple(entries)


def _build_protein_entries(
    *,
    library_proteins: set[str],
    protein_matrix: DiaProteinMatrixReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[DiaLibraryCoverageProteinEntry, ...]:
    row_by_protein = {row.entity_id: row for row in protein_matrix.rows}
    entries: list[DiaLibraryCoverageProteinEntry] = []
    for protein_ref in sorted(library_proteins):
        matching_row = row_by_protein.get(protein_ref)
        detected_samples = (
            {value.sample_id for value in matching_row.values if value.detected}
            if matching_row is not None
            else set()
        )
        entries.append(
            DiaLibraryCoverageProteinEntry(
                protein_ref=protein_ref,
                detected_overall=matching_row is not None,
                detected_sample_count=len(detected_samples),
                detected_condition_count=len(
                    _condition_ids_for_sample_ids(
                        detected_samples,
                        design_entries=design_entries,
                    )
                ),
            )
        )
    return tuple(entries)


def _build_observed_outside_library_protein_entries(
    *,
    library_proteins: set[str],
    protein_matrix: DiaProteinMatrixReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[DiaObservedOutsideLibraryProteinEntry, ...]:
    entries: list[DiaObservedOutsideLibraryProteinEntry] = []
    for row in sorted(protein_matrix.rows, key=lambda entry: entry.entity_id):
        if row.entity_id in library_proteins:
            continue
        detected_samples = tuple(
            sorted({value.sample_id for value in row.values if value.detected})
        )
        if not detected_samples:
            continue
        condition_ids = tuple(
            sorted(
                _condition_ids_for_sample_ids(
                    set(detected_samples),
                    design_entries=design_entries,
                )
            )
        )
        entries.append(
            DiaObservedOutsideLibraryProteinEntry(
                protein_ref=row.entity_id,
                sample_ids=detected_samples,
                condition_ids=condition_ids,
                detected_sample_count=len(detected_samples),
                detected_condition_count=len(condition_ids),
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


def _condition_ids_for_sample_ids(
    sample_ids: set[str],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> set[str]:
    return {
        entry.condition
        for entry in design_entries
        if entry.sample_id in sample_ids
    }
