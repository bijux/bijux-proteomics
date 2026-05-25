# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned heatmap-matrix preparation over governed quantification tables."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from enum import StrEnum
from io import StringIO
import math
from pathlib import Path

import numpy as np
from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import QuantMatrix as CanonicalQuantMatrix
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    QuantSampleMetadataEntry,
    _matrix_value_index,
    coerce_label_free_quant_table,
)
from bijux_proteomics_foundation import JsonModel


class HeatmapMissingValuePolicy(StrEnum):
    """Explicit missing-value handling for clustering-ready heatmap matrices."""

    DROP_ROWS = "drop_rows"
    FILL_ZERO = "fill_zero"
    FILL_ROW_MEDIAN = "fill_row_median"


class HeatmapPreparationPolicy(JsonModel):
    """Filter and transformation policy for one heatmap matrix."""

    model_config = ConfigDict(extra="forbid")

    entity_ids: tuple[str, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    min_observed_fraction: float = Field(default=0.5, ge=0.0, le=1.0)
    max_entity_count: int | None = Field(default=None, ge=1)
    z_score_rows: bool = True
    missing_value_policy: HeatmapMissingValuePolicy = (
        HeatmapMissingValuePolicy.FILL_ROW_MEDIAN
    )


class HeatmapPreparationSummary(JsonModel):
    """Compact summary over one prepared heatmap matrix."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    sample_count: int = Field(..., ge=0)
    input_entity_count: int = Field(..., ge=0)
    output_entity_count: int = Field(..., ge=0)
    filtered_entity_id_count: int = Field(..., ge=0)
    filtered_protein_ref_count: int = Field(..., ge=0)
    filtered_observed_fraction_count: int = Field(..., ge=0)
    filtered_missing_policy_count: int = Field(..., ge=0)
    truncated_entity_count: int = Field(..., ge=0)
    z_scored: bool
    missing_value_policy: HeatmapMissingValuePolicy


class HeatmapMatrixRow(JsonModel):
    """One prepared heatmap row over all selected samples."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    values: tuple[float, ...] = Field(default_factory=tuple)


class HeatmapRowMetadataEntry(JsonModel):
    """Stable metadata for one prepared heatmap row."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    member_peptides: tuple[str, ...] = Field(default_factory=tuple)
    observed_sample_count: int = Field(..., ge=0)
    missing_sample_count: int = Field(..., ge=0)
    filled_missing_sample_count: int = Field(..., ge=0)
    observed_fraction: float = Field(..., ge=0.0, le=1.0)
    missing_value_policy: HeatmapMissingValuePolicy
    mean_log2_abundance: float | None = None
    variance_log2_abundance: float | None = Field(default=None, ge=0.0)


class HeatmapColumnMetadataEntry(JsonModel):
    """Stable metadata for one prepared heatmap column."""

    model_config = ConfigDict(extra="forbid")

    column_index: int = Field(..., ge=0)
    sample_metadata: QuantSampleMetadataEntry
    missing_value_policy: HeatmapMissingValuePolicy
    normalization_factor: float


class HeatmapPreparationReport(JsonModel):
    """Prepared matrix and metadata for heatmaps and clustering."""

    model_config = ConfigDict(extra="forbid")

    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    summary: HeatmapPreparationSummary
    policy: HeatmapPreparationPolicy
    rows: tuple[HeatmapMatrixRow, ...] = Field(default_factory=tuple)
    row_metadata: tuple[HeatmapRowMetadataEntry, ...] = Field(default_factory=tuple)
    column_metadata: tuple[HeatmapColumnMetadataEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def build_heatmap_preparation_report(
    table: LabelFreeQuantTable | CanonicalQuantMatrix,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...] = (),
    policy: HeatmapPreparationPolicy | None = None,
) -> HeatmapPreparationReport:
    """Prepare one normalized sample-by-entity matrix for heatmaps and clustering."""

    table = coerce_label_free_quant_table(table)
    active_policy = policy or HeatmapPreparationPolicy()
    sample_ids = table.sample_ids
    value_lookup = _matrix_value_index(table)
    metadata_lookup = _sample_metadata_lookup(design_entries)
    entity_filter = set(active_policy.entity_ids)
    protein_filter = set(active_policy.protein_refs)

    filtered_entity_id_count = 0
    filtered_protein_ref_count = 0
    filtered_observed_fraction_count = 0
    filtered_missing_policy_count = 0
    truncated_entity_count = 0

    row_entries: list[tuple[HeatmapRowMetadataEntry, np.ndarray]] = []
    for entity_id in table.entity_ids:
        if entity_filter and entity_id not in entity_filter:
            filtered_entity_id_count += 1
            continue
        protein_refs = table.entity_protein_refs.get(entity_id, ())
        if protein_filter and not protein_filter.intersection(protein_refs):
            filtered_protein_ref_count += 1
            continue
        raw_values = np.array(
            [
                _log2_abundance(value_lookup[(entity_id, sample_id)].abundance)
                for sample_id in sample_ids
            ],
            dtype=float,
        )
        finite_mask = np.isfinite(raw_values)
        observed_sample_count = int(np.sum(finite_mask))
        observed_fraction = (
            observed_sample_count / len(sample_ids) if sample_ids else 0.0
        )
        if observed_fraction < active_policy.min_observed_fraction:
            filtered_observed_fraction_count += 1
            continue
        if (
            active_policy.missing_value_policy is HeatmapMissingValuePolicy.DROP_ROWS
            and not np.all(finite_mask)
        ):
            filtered_missing_policy_count += 1
            continue
        prepared_values = _apply_missing_value_policy(
            raw_values,
            policy=active_policy.missing_value_policy,
        )
        if active_policy.z_score_rows:
            prepared_values = _z_score_row(prepared_values)
        metadata = HeatmapRowMetadataEntry(
            entity_id=entity_id,
            protein_refs=protein_refs,
            member_peptides=table.entity_member_peptides.get(entity_id, ()),
            observed_sample_count=observed_sample_count,
            missing_sample_count=len(sample_ids) - observed_sample_count,
            filled_missing_sample_count=(
                len(sample_ids) - observed_sample_count
                if active_policy.missing_value_policy
                is not HeatmapMissingValuePolicy.DROP_ROWS
                else 0
            ),
            observed_fraction=observed_fraction,
            missing_value_policy=active_policy.missing_value_policy,
            mean_log2_abundance=(
                float(np.mean(raw_values[finite_mask])) if observed_sample_count else None
            ),
            variance_log2_abundance=(
                float(np.var(raw_values[finite_mask])) if observed_sample_count else None
            ),
        )
        row_entries.append((metadata, prepared_values))

    if active_policy.max_entity_count is not None and len(row_entries) > active_policy.max_entity_count:
        row_entries = sorted(
            row_entries,
            key=lambda item: (
                -(item[0].variance_log2_abundance or 0.0),
                item[0].entity_id,
            ),
        )[: active_policy.max_entity_count]
        truncated_entity_count = max(0, len(table.entity_ids) - filtered_entity_id_count - filtered_protein_ref_count - filtered_observed_fraction_count - filtered_missing_policy_count - len(row_entries))

    row_entries = sorted(row_entries, key=lambda item: item[0].entity_id)
    rows = tuple(
        HeatmapMatrixRow(
            entity_id=metadata.entity_id,
            values=tuple(float(value) for value in values),
        )
        for metadata, values in row_entries
    )
    row_metadata = tuple(metadata for metadata, _ in row_entries)
    column_metadata = tuple(
        HeatmapColumnMetadataEntry(
            column_index=index,
            sample_metadata=metadata_lookup.get(
                sample_id,
                QuantSampleMetadataEntry(sample_id=sample_id),
            ),
            missing_value_policy=active_policy.missing_value_policy,
            normalization_factor=table.normalization_factors.get(sample_id, 1.0),
        )
        for index, sample_id in enumerate(sample_ids)
    )
    return HeatmapPreparationReport(
        sample_ids=sample_ids,
        summary=HeatmapPreparationSummary(
            entity_level=table.entity_level,
            measure_kind=table.measure_kind,
            aggregation_method=table.aggregation_method,
            sample_count=len(sample_ids),
            input_entity_count=len(table.entity_ids),
            output_entity_count=len(rows),
            filtered_entity_id_count=filtered_entity_id_count,
            filtered_protein_ref_count=filtered_protein_ref_count,
            filtered_observed_fraction_count=filtered_observed_fraction_count,
            filtered_missing_policy_count=filtered_missing_policy_count,
            truncated_entity_count=truncated_entity_count,
            z_scored=active_policy.z_score_rows,
            missing_value_policy=active_policy.missing_value_policy,
        ),
        policy=active_policy,
        rows=rows,
        row_metadata=row_metadata,
        column_metadata=column_metadata,
        note=(
            "heatmap preparation preserves one normalized log2 matrix with explicit entity filtering, missing-value handling, and optional row z-scoring"
        ),
    )


def render_heatmap_matrix_tsv(report: HeatmapPreparationReport) -> str:
    """Render one prepared heatmap matrix as a wide TSV."""
    ordered_sample_ids = sort_strings(report.sample_ids)
    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("entity_id", *ordered_sample_ids))
    for row in sort_rows_by_fields(report.rows, "entity_id"):
        value_lookup = {
            sample_id: value for sample_id, value in zip(report.sample_ids, row.values, strict=True)
        }
        writer.writerow(
            (row.entity_id, *[f"{value_lookup[sample_id]:g}" for sample_id in ordered_sample_ids])
        )
    return handle.getvalue()


def render_heatmap_summary_tsv(report: HeatmapPreparationReport) -> str:
    """Render one compact heatmap preparation summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_level",
            "measure_kind",
            "aggregation_method",
            "sample_count",
            "input_entity_count",
            "output_entity_count",
            "filtered_entity_id_count",
            "filtered_protein_ref_count",
            "filtered_observed_fraction_count",
            "filtered_missing_policy_count",
            "truncated_entity_count",
            "z_scored",
            "missing_value_policy",
        )
    )
    writer.writerow(
        (
            report.summary.entity_level.value,
            report.summary.measure_kind.value,
            report.summary.aggregation_method.value,
            report.summary.sample_count,
            report.summary.input_entity_count,
            report.summary.output_entity_count,
            report.summary.filtered_entity_id_count,
            report.summary.filtered_protein_ref_count,
            report.summary.filtered_observed_fraction_count,
            report.summary.filtered_missing_policy_count,
            report.summary.truncated_entity_count,
            str(report.summary.z_scored).lower(),
            report.summary.missing_value_policy.value,
        )
    )
    return handle.getvalue()


def render_heatmap_row_metadata_tsv(report: HeatmapPreparationReport) -> str:
    """Render row-level heatmap metadata as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "protein_refs",
            "member_peptides",
            "observed_sample_count",
            "missing_sample_count",
            "filled_missing_sample_count",
            "observed_fraction",
            "missing_value_policy",
            "mean_log2_abundance",
            "variance_log2_abundance",
        )
    )
    for row in sort_rows_by_fields(report.row_metadata, "entity_id"):
        writer.writerow(
            (
                row.entity_id,
                ";".join(sort_strings(row.protein_refs)),
                ";".join(sort_strings(row.member_peptides)),
                row.observed_sample_count,
                row.missing_sample_count,
                row.filled_missing_sample_count,
                f"{row.observed_fraction:g}",
                row.missing_value_policy.value,
                "" if row.mean_log2_abundance is None else f"{row.mean_log2_abundance:g}",
                ""
                if row.variance_log2_abundance is None
                else f"{row.variance_log2_abundance:g}",
            )
        )
    return handle.getvalue()


def render_heatmap_column_metadata_tsv(report: HeatmapPreparationReport) -> str:
    """Render column-level heatmap metadata as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "column_index",
            "sample_id",
            "condition",
            "replicate",
            "fraction",
            "batch",
            "instrument",
            "search_engine",
            "missing_value_policy",
            "normalization_factor",
        )
    )
    for column in sorted(
        report.column_metadata,
        key=lambda entry: (entry.sample_metadata.sample_id, entry.column_index),
    ):
        writer.writerow(
            (
                column.column_index,
                column.sample_metadata.sample_id,
                column.sample_metadata.condition or "",
                "" if column.sample_metadata.replicate is None else column.sample_metadata.replicate,
                "" if column.sample_metadata.fraction is None else column.sample_metadata.fraction,
                column.sample_metadata.batch or "",
                column.sample_metadata.instrument or "",
                column.sample_metadata.search_engine or "",
                column.missing_value_policy.value,
                f"{column.normalization_factor:g}",
            )
        )
    return handle.getvalue()


def export_heatmap_matrix_tsv(report: HeatmapPreparationReport, path: Path) -> None:
    """Write one prepared heatmap matrix to a stable TSV artifact."""

    write_output_table_tsv(path, render_heatmap_matrix_tsv(report))


def export_heatmap_summary_tsv(report: HeatmapPreparationReport, path: Path) -> None:
    """Write one compact heatmap summary to a stable TSV artifact."""

    write_output_table_tsv(path, render_heatmap_summary_tsv(report))


def export_heatmap_row_metadata_tsv(
    report: HeatmapPreparationReport, path: Path
) -> None:
    """Write row-level heatmap metadata to a stable TSV artifact."""

    write_output_table_tsv(path, render_heatmap_row_metadata_tsv(report))


def export_heatmap_column_metadata_tsv(
    report: HeatmapPreparationReport, path: Path
) -> None:
    """Write column-level heatmap metadata to a stable TSV artifact."""

    write_output_table_tsv(path, render_heatmap_column_metadata_tsv(report))


def _log2_abundance(value: float | None) -> float:
    if value is None:
        return float("nan")
    return math.log2(float(value) + 1.0)


def _apply_missing_value_policy(
    values: np.ndarray,
    *,
    policy: HeatmapMissingValuePolicy,
) -> np.ndarray:
    prepared = values.copy()
    missing = ~np.isfinite(prepared)
    if not np.any(missing):
        return prepared
    if policy is HeatmapMissingValuePolicy.FILL_ZERO:
        prepared[missing] = 0.0
        return prepared
    finite = prepared[np.isfinite(prepared)]
    fill_value = float(np.median(finite)) if finite.size else 0.0
    prepared[missing] = fill_value
    return prepared


def _z_score_row(values: np.ndarray) -> np.ndarray:
    mean = float(np.mean(values))
    std = float(np.std(values))
    if std == 0.0:
        return np.zeros_like(values, dtype=float)
    return (values - mean) / std


def _sample_metadata_lookup(
    entries: tuple[ExperimentalDesignEntry, ...],
) -> dict[str, QuantSampleMetadataEntry]:
    return {
        entry.sample_id: QuantSampleMetadataEntry(
            sample_id=entry.sample_id,
            condition=entry.condition,
            replicate=entry.replicate,
            fraction=entry.fraction,
            batch=entry.batch,
            instrument=entry.instrument,
            search_engine=entry.search_engine,
        )
        for entry in entries
    }


__all__ = [
    "HeatmapColumnMetadataEntry",
    "HeatmapMatrixRow",
    "HeatmapMissingValuePolicy",
    "HeatmapPreparationPolicy",
    "HeatmapPreparationReport",
    "HeatmapPreparationSummary",
    "HeatmapRowMetadataEntry",
    "build_heatmap_preparation_report",
    "export_heatmap_column_metadata_tsv",
    "export_heatmap_matrix_tsv",
    "export_heatmap_row_metadata_tsv",
    "export_heatmap_summary_tsv",
    "render_heatmap_column_metadata_tsv",
    "render_heatmap_matrix_tsv",
    "render_heatmap_row_metadata_tsv",
    "render_heatmap_summary_tsv",
]
