# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Interop surfaces for external statistical proteomics backends."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from io import StringIO
import math
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
    MissingValueKind,
    Ms1FeatureRecord,
    MultiConditionDifferentialAbundanceReport,
    QuantEntityLevel,
    QuantDesignMatrixReport,
    QuantMatrixExport,
    build_quant_design_matrix_report,
    build_quant_matrix_export,
)
from bijux_proteomics_foundation import JsonModel


class LimmaCompatibleSampleAnnotation(JsonModel):
    """One sample annotation row for limma-style workflows."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    batch: str | None = None
    pair_id: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class LimmaCompatibleQuantPackage(JsonModel):
    """R-compatible assay and design package for limma-style analysis."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(default="limma", min_length=1)
    entity_level: QuantEntityLevel
    matrix_export: QuantMatrixExport
    design_matrix_report: QuantDesignMatrixReport
    sample_annotations: tuple[LimmaCompatibleSampleAnnotation, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class MsstatsCompatibleInputRow(JsonModel):
    """One MSstats-compatible long-format row derived from observed evidence."""

    model_config = ConfigDict(extra="forbid")

    protein_name: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    precursor_charge: int | None = Field(default=None, ge=1)
    condition: str = Field(..., min_length=1)
    bio_replicate: str = Field(..., min_length=1)
    run: str = Field(..., min_length=1)
    intensity: float = Field(..., ge=0.0)
    fraction: int = Field(..., ge=1)
    isotope_label_type: str = Field(default="L", min_length=1)


class MsstatsCompatibleInputReport(JsonModel):
    """MSstats-compatible long-format export with skipped-row accountability."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(default="msstats", min_length=1)
    row_count: int = Field(..., ge=0)
    skipped_feature_count: int = Field(..., ge=0)
    rows: tuple[MsstatsCompatibleInputRow, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class ImportedStatisticalResultRow(JsonModel):
    """One normalized imported statistical-result row from an external backend."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(..., min_length=1)
    entity_id: str = Field(..., min_length=1)
    contrast_name: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    log2_fold_change: float
    p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)


class StatisticalResultImportReport(JsonModel):
    """Normalized imported result-table report from one external backend."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(..., min_length=1)
    row_count: int = Field(..., ge=0)
    rows: tuple[ImportedStatisticalResultRow, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class StatisticalBackendValidationReport(JsonModel):
    """Validation summary comparing imported backend results to native evidence."""

    model_config = ConfigDict(extra="forbid")

    backend: str = Field(..., min_length=1)
    imported_row_count: int = Field(..., ge=0)
    matched_row_count: int = Field(..., ge=0)
    directionally_concordant_count: int = Field(..., ge=0)
    mean_absolute_log2_fold_change_delta: float | None = Field(default=None, ge=0.0)
    note: str = Field(..., min_length=1)


def _design_annotations(
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[LimmaCompatibleSampleAnnotation, ...]:
    return tuple(
        LimmaCompatibleSampleAnnotation(
            sample_id=entry.sample_id,
            condition=entry.condition,
            batch=entry.batch,
            pair_id=entry.pair_id,
            metadata=entry.metadata,
        )
        for entry in design_entries
    )


def build_limma_compatible_quant_package(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    batch_field: str | None = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
    timepoint_field: str | None = None,
) -> LimmaCompatibleQuantPackage:
    """Build an R-compatible limma-style assay, design, and contrast package."""
    effective_pairing_field = pairing_field
    if effective_pairing_field is None and all(
        entry.pair_id not in (None, "") for entry in design_entries
    ):
        effective_pairing_field = "pair_id"
    effective_timepoint_field = timepoint_field
    if effective_timepoint_field is None and all(
        entry.metadata.get("timepoint") not in (None, "") for entry in design_entries
    ):
        effective_timepoint_field = "timepoint"
    design_matrix = build_quant_design_matrix_report(
        design_entries,
        batch_field=batch_field,
        covariate_fields=covariate_fields,
        pairing_field=effective_pairing_field,
        timepoint_field=effective_timepoint_field,
    )
    return LimmaCompatibleQuantPackage(
        entity_level=table.entity_level,
        matrix_export=build_quant_matrix_export(table, design_entries=design_entries),
        design_matrix_report=design_matrix,
        sample_annotations=_design_annotations(design_entries),
        note=(
            "limma package preserves a log-scale assay matrix, sample annotations, one owned design matrix, and named condition contrasts"
        ),
    )


def render_limma_assay_matrix_tsv(package: LimmaCompatibleQuantPackage) -> str:
    """Render a limma-style assay matrix with entities as rows and samples as columns."""
    sample_ids = tuple(
        dict.fromkeys(
            row.sample_metadata.sample_id for row in package.matrix_export.rows
        )
    )
    entity_ids = tuple(dict.fromkeys(row.entity_id for row in package.matrix_export.rows))
    grouped: dict[str, dict[str, float | None]] = {
        entity_id: {sample_id: None for sample_id in sample_ids}
        for entity_id in entity_ids
    }
    for row in package.matrix_export.rows:
        grouped[row.entity_id][row.sample_metadata.sample_id] = (
            None if row.abundance is None else math.log2(row.abundance + 1.0)
        )
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(["entity_id", *sample_ids])
    for entity_id in entity_ids:
        writer.writerow(
            [
                entity_id,
                *[
                    ""
                    if grouped[entity_id][sample_id] is None
                    else f"{grouped[entity_id][sample_id]:.6g}"
                    for sample_id in sample_ids
                ],
            ]
        )
    return buffer.getvalue()


def render_limma_sample_annotations_tsv(package: LimmaCompatibleQuantPackage) -> str:
    """Render limma sample annotations with preserved extra metadata fields."""
    metadata_fields = tuple(
        sorted(
            {
                key
                for annotation in package.sample_annotations
                for key in annotation.metadata.keys()
            }
        )
    )
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(["sample_id", "condition", "batch", "pair_id", *metadata_fields])
    for annotation in package.sample_annotations:
        writer.writerow(
            [
                annotation.sample_id,
                annotation.condition,
                annotation.batch or "",
                annotation.pair_id or "",
                *[annotation.metadata.get(field, "") for field in metadata_fields],
            ]
        )
    return buffer.getvalue()


def render_limma_design_matrix_tsv(package: LimmaCompatibleQuantPackage) -> str:
    """Render the owned design matrix for limma-style external modeling."""
    from bijux_proteomics.quantification.matrix.design_matrix import (
        render_quant_design_matrix_tsv,
    )

    return render_quant_design_matrix_tsv(package.design_matrix_report)


def render_limma_contrast_matrix_tsv(package: LimmaCompatibleQuantPackage) -> str:
    """Render limma-style contrast weights over design-matrix coefficient columns."""
    columns = tuple(
        column.column_name for column in package.design_matrix_report.columns[1:]
    )
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "coefficient_name",
            *[contrast.contrast_name for contrast in package.design_matrix_report.contrasts],
        ]
    )
    for column_name in columns:
        writer.writerow(
            [
                column_name,
                *[
                    f"{contrast.coefficient_weights.get(column_name, 0.0):.6g}"
                    for contrast in package.design_matrix_report.contrasts
                ],
            ]
        )
    return buffer.getvalue()


def export_limma_assay_matrix_tsv(
    package: LimmaCompatibleQuantPackage, path: Path
) -> None:
    write_output_table_tsv(path, render_limma_assay_matrix_tsv(package))


def export_limma_sample_annotations_tsv(
    package: LimmaCompatibleQuantPackage, path: Path
) -> None:
    write_output_table_tsv(path, render_limma_sample_annotations_tsv(package))


def export_limma_design_matrix_tsv(
    package: LimmaCompatibleQuantPackage, path: Path
) -> None:
    write_output_table_tsv(path, render_limma_design_matrix_tsv(package))


def export_limma_contrast_matrix_tsv(
    package: LimmaCompatibleQuantPackage, path: Path
) -> None:
    write_output_table_tsv(path, render_limma_contrast_matrix_tsv(package))


def build_msstats_compatible_input_report(
    records: tuple[Ms1FeatureRecord, ...],
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> MsstatsCompatibleInputReport:
    """Build one MSstats-compatible long-format export where evidence allows."""
    design_lookup = {entry.sample_id: entry for entry in design_entries}
    rows: list[MsstatsCompatibleInputRow] = []
    skipped = 0
    for record in records:
        if record.missing_value_kind is not MissingValueKind.OBSERVED:
            skipped += 1
            continue
        design_entry = design_lookup.get(record.sample_id)
        if (
            design_entry is None
            or not record.protein_refs
            or record.intensity is None
        ):
            skipped += 1
            continue
        rows.append(
            MsstatsCompatibleInputRow(
                protein_name=";".join(record.protein_refs),
                peptide_sequence=record.canonical_peptide,
                precursor_charge=record.charge,
                condition=design_entry.condition,
                bio_replicate=design_entry.sample_id,
                run=Path(design_entry.spectra_file).stem or design_entry.sample_id,
                intensity=float(record.intensity),
                fraction=design_entry.fraction,
            )
        )
    return MsstatsCompatibleInputReport(
        row_count=len(rows),
        skipped_feature_count=skipped,
        rows=tuple(rows),
        note=(
            "msstats-compatible export preserves observed peptide evidence with sample condition, biological replicate identity, run, fraction, and precursor charge when the feature table provides it"
        ),
    )


def render_msstats_compatible_input_tsv(report: MsstatsCompatibleInputReport) -> str:
    """Render one MSstats-compatible long-format table."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "ProteinName",
            "PeptideSequence",
            "PrecursorCharge",
            "Condition",
            "BioReplicate",
            "Run",
            "Intensity",
            "Fraction",
            "IsotopeLabelType",
        ]
    )
    for row in report.rows:
        writer.writerow(
            [
                row.protein_name,
                row.peptide_sequence,
                "" if row.precursor_charge is None else row.precursor_charge,
                row.condition,
                row.bio_replicate,
                row.run,
                f"{row.intensity:.6g}",
                row.fraction,
                row.isotope_label_type,
            ]
        )
    return buffer.getvalue()


def export_msstats_compatible_input_tsv(
    report: MsstatsCompatibleInputReport, path: Path
) -> None:
    write_output_table_tsv(path, render_msstats_compatible_input_tsv(report))


def _read_delimited_rows(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return []
    delimiter = "\t" if "\t" in lines[0] else ","
    return list(csv.DictReader(lines, delimiter=delimiter))


def parse_limma_result_table(
    path: Path,
    *,
    condition_a: str,
    condition_b: str,
    contrast_name: str | None = None,
) -> StatisticalResultImportReport:
    """Parse one limma-like result table into the normalized result contract."""
    normalized_rows: list[ImportedStatisticalResultRow] = []
    chosen_contrast = contrast_name or f"{condition_a}_vs_{condition_b}"
    for row in _read_delimited_rows(path):
        entity_id = (
            row.get("entity_id")
            or row.get("Protein")
            or row.get("protein")
            or row.get("protein_id")
            or ""
        ).strip()
        if not entity_id:
            continue
        normalized_rows.append(
            ImportedStatisticalResultRow(
                backend="limma",
                entity_id=entity_id,
                contrast_name=(row.get("contrast_name") or chosen_contrast).strip(),
                condition_a=condition_a,
                condition_b=condition_b,
                log2_fold_change=float(row.get("logFC") or row.get("log2FC") or "0"),
                p_value=(
                    None if row.get("P.Value") in (None, "") else float(row.get("P.Value") or "0")
                ),
                adjusted_p_value=(
                    None if row.get("adj.P.Val") in (None, "") else float(row.get("adj.P.Val") or "0")
                ),
            )
        )
    return StatisticalResultImportReport(
        backend="limma",
        row_count=len(normalized_rows),
        rows=tuple(normalized_rows),
        note="limma-like result table was normalized to the owned backend result contract",
    )


def parse_msstats_result_table(
    path: Path,
    *,
    condition_a: str,
    condition_b: str,
    contrast_name: str | None = None,
) -> StatisticalResultImportReport:
    """Parse one MSstats-like result table into the normalized result contract."""
    normalized_rows: list[ImportedStatisticalResultRow] = []
    chosen_contrast = contrast_name or f"{condition_a}_vs_{condition_b}"
    for row in _read_delimited_rows(path):
        entity_id = (row.get("Protein") or row.get("ProteinName") or "").strip()
        if not entity_id:
            continue
        normalized_rows.append(
            ImportedStatisticalResultRow(
                backend="msstats",
                entity_id=entity_id,
                contrast_name=(row.get("Label") or chosen_contrast).strip(),
                condition_a=condition_a,
                condition_b=condition_b,
                log2_fold_change=float(
                    row.get("log2FC")
                    or row.get("logFC")
                    or row.get("log2FoldChange")
                    or "0"
                ),
                p_value=(
                    None
                    if row.get("pvalue") in (None, "")
                    else float(row.get("pvalue") or "0")
                ),
                adjusted_p_value=(
                    None
                    if row.get("adj.pvalue") in (None, "")
                    else float(row.get("adj.pvalue") or "0")
                ),
            )
        )
    return StatisticalResultImportReport(
        backend="msstats",
        row_count=len(normalized_rows),
        rows=tuple(normalized_rows),
        note="msstats-like result table was normalized to the owned backend result contract",
    )


def _reference_lookup(
    report: DifferentialAbundanceReport | MultiConditionDifferentialAbundanceReport,
) -> dict[tuple[str, str], float]:
    if isinstance(report, DifferentialAbundanceReport):
        return {
            (entry.entity_id, f"{report.condition_a}_vs_{report.condition_b}"): entry.log2_fold_change
            for entry in report.entries
        }
    lookup: dict[tuple[str, str], float] = {}
    for subreport in report.reports:
        contrast_name = f"{subreport.condition_a}_vs_{subreport.condition_b}"
        for entry in subreport.entries:
            lookup[(entry.entity_id, contrast_name)] = entry.log2_fold_change
    return lookup


def build_statistical_backend_validation_report(
    imported: StatisticalResultImportReport,
    reference: DifferentialAbundanceReport | MultiConditionDifferentialAbundanceReport,
) -> StatisticalBackendValidationReport:
    """Validate imported backend results against the owned differential surface."""
    lookup = _reference_lookup(reference)
    matched = 0
    concordant = 0
    deltas: list[float] = []
    for row in imported.rows:
        reference_value = lookup.get((row.entity_id, row.contrast_name))
        if reference_value is None:
            continue
        matched += 1
        if (reference_value == 0 and row.log2_fold_change == 0) or (
            reference_value > 0 and row.log2_fold_change > 0
        ) or (reference_value < 0 and row.log2_fold_change < 0):
            concordant += 1
        deltas.append(abs(reference_value - row.log2_fold_change))
    return StatisticalBackendValidationReport(
        backend=imported.backend,
        imported_row_count=imported.row_count,
        matched_row_count=matched,
        directionally_concordant_count=concordant,
        mean_absolute_log2_fold_change_delta=(
            None if not deltas else sum(deltas) / len(deltas)
        ),
        note=(
            "backend validation compares imported fold-change direction and magnitude against the owned differential abundance surface for matching entity and contrast keys"
        ),
    )
