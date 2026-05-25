# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned design-matrix surfaces for quantification modeling."""

from __future__ import annotations

import csv
from io import StringIO
from itertools import combinations
import math
from pathlib import Path

import numpy as np

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    QuantDesignContrast,
    QuantDesignMatrixColumn,
    QuantDesignMatrixColumnEncoding,
    QuantDesignMatrixColumnKind,
    QuantDesignContrastEstimateEntry,
    QuantDesignMatrixReport,
    QuantDesignModelCoefficientEntry,
    QuantDesignModelFitReport,
    QuantDesignMatrixSampleRow,
    _matrix_value_index,
)
from bijux_proteomics.study.sample_run_identity import (
    SampleRunAnalysisPolicy,
    resolve_sample_run_analysis_entries,
)


def _resolve_design_value(entry: ExperimentalDesignEntry, field: str) -> str | None:
    direct_values = {
        "sample_id": entry.sample_id,
        "cohort": entry.cohort,
        "condition": entry.condition,
        "replicate": str(entry.replicate),
        "fraction": str(entry.fraction),
        "spectra_file": entry.spectra_file,
        "identifications_file": entry.identifications_file,
        "batch": entry.batch,
        "instrument": entry.instrument,
        "search_engine": entry.search_engine,
        "pair_id": entry.pair_id,
        "multiplex_group": entry.multiplex_group,
        "multiplex_channel": entry.multiplex_channel,
        "sample_role": entry.sample_role.value,
    }
    if field in direct_values:
        return direct_values[field]
    return entry.metadata.get(field)


def _require_populated_design_field(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    field: str,
) -> tuple[str, ...]:
    values = tuple(_resolve_design_value(entry, field) for entry in design_entries)
    if any(value in (None, "") for value in values):
        raise ValueError(f"design field {field!r} is missing for one or more samples")
    return tuple(str(value) for value in values if value not in (None, ""))


def _build_numeric_covariate_column(
    entries: tuple[ExperimentalDesignEntry, ...],
    field: str,
    *,
    kind: QuantDesignMatrixColumnKind = QuantDesignMatrixColumnKind.COVARIATE,
) -> tuple[QuantDesignMatrixColumn, tuple[float, ...]] | None:
    values = _require_populated_design_field(entries, field)
    try:
        numeric = tuple(float(value) for value in values)
    except ValueError:
        return None
    column_name = "timepoint" if kind is QuantDesignMatrixColumnKind.TIMEPOINT else f"covariate[{field}]"
    return (
        QuantDesignMatrixColumn(
            column_name=column_name,
            kind=kind,
            encoding=QuantDesignMatrixColumnEncoding.NUMERIC,
            source_field=field,
        ),
        numeric,
    )


def _build_categorical_columns(
    entries: tuple[ExperimentalDesignEntry, ...],
    *,
    field: str,
    kind: QuantDesignMatrixColumnKind,
) -> tuple[tuple[QuantDesignMatrixColumn, ...], tuple[tuple[float, ...], ...]]:
    values = _require_populated_design_field(entries, field)
    levels = tuple(sorted(set(values)))
    if len(levels) <= 1:
        return (), ()
    reference = levels[0]
    columns: list[QuantDesignMatrixColumn] = []
    data_columns: list[tuple[float, ...]] = []
    for level in levels[1:]:
        if kind is QuantDesignMatrixColumnKind.CONDITION:
            prefix = "condition"
        elif kind is QuantDesignMatrixColumnKind.TIMEPOINT:
            prefix = "timepoint"
        else:
            prefix = field
        columns.append(
            QuantDesignMatrixColumn(
                column_name=f"{prefix}[{level}]",
                kind=kind,
                encoding=QuantDesignMatrixColumnEncoding.CATEGORICAL_ONE_HOT,
                source_field=field,
                level=level,
                reference_level=reference,
            )
        )
        data_columns.append(
            tuple(1.0 if value == level else 0.0 for value in values)
        )
    return tuple(columns), tuple(data_columns)


def _build_condition_contrasts(
    columns: tuple[QuantDesignMatrixColumn, ...],
    *,
    conditions: tuple[str, ...],
) -> tuple[QuantDesignContrast, ...]:
    reference = conditions[0]
    condition_columns = {
        column.level: column.column_name
        for column in columns
        if column.kind is QuantDesignMatrixColumnKind.CONDITION and column.level
    }
    contrasts: list[QuantDesignContrast] = []
    for condition_a, condition_b in combinations(conditions, 2):
        weights: dict[str, float] = {}
        if condition_a != reference:
            weights[condition_columns[condition_a]] = 1.0
        if condition_b != reference:
            weights[condition_columns[condition_b]] = (
                weights.get(condition_columns[condition_b], 0.0) - 1.0
            )
        if condition_a == reference and condition_b != reference:
            weights[condition_columns[condition_b]] = -1.0
        contrasts.append(
            QuantDesignContrast(
                contrast_name=f"{condition_a}_vs_{condition_b}",
                condition_a=condition_a,
                condition_b=condition_b,
                coefficient_weights=weights,
                coefficient_vector=tuple(
                    weights.get(column.column_name, 0.0) for column in columns
                ),
            )
        )
    return tuple(contrasts)


def _require_unique_sample_ids(
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> None:
    sample_ids = tuple(entry.sample_id for entry in design_entries)
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("design matrix requires unique sample_id values")


def _require_full_rank_design(
    columns: tuple[QuantDesignMatrixColumn, ...],
    column_values: tuple[tuple[float, ...], ...],
) -> None:
    design_matrix = np.column_stack(
        [np.array(values, dtype=float) for values in column_values]
    )
    if int(np.linalg.matrix_rank(design_matrix)) == len(columns):
        return

    retained: np.ndarray | None = None
    retained_rank = 0
    aliased_columns: list[str] = []
    for column, values in zip(columns, column_values, strict=False):
        candidate_column = np.array(values, dtype=float).reshape(-1, 1)
        candidate_matrix = (
            candidate_column
            if retained is None
            else np.column_stack((retained, candidate_column))
        )
        candidate_rank = int(np.linalg.matrix_rank(candidate_matrix))
        if candidate_rank <= retained_rank:
            aliased_columns.append(column.column_name)
            continue
        retained = candidate_matrix
        retained_rank = candidate_rank

    if not aliased_columns:
        aliased_columns = [column.column_name for column in columns]
    raise ValueError(
        "design matrix is confounded or rank-deficient; aliased columns: "
        + ", ".join(aliased_columns)
    )


def build_quant_design_matrix_report(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    batch_field: str | None = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
    timepoint_field: str | None = None,
    condition_field: str = "condition",
    sample_run_policy: SampleRunAnalysisPolicy = (
        SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS
    ),
) -> QuantDesignMatrixReport:
    """Build one explicit sample design matrix for quantification modeling."""
    if not design_entries:
        raise ValueError("design matrix requires at least one design entry")
    analysis_design_entries = resolve_sample_run_analysis_entries(
        design_entries,
        policy=sample_run_policy,
        required_consistency_fields=_required_consistency_fields(
            condition_field=condition_field,
            batch_field=batch_field,
            pairing_field=pairing_field,
            timepoint_field=timepoint_field,
            covariate_fields=covariate_fields,
        ),
    )
    _require_unique_sample_ids(analysis_design_entries)

    conditions = tuple(
        sorted(
            {
                value
                for value in _require_populated_design_field(
                    analysis_design_entries, condition_field
                )
            }
        )
    )
    if len(conditions) < 2:
        raise ValueError("design matrix requires at least two conditions")

    columns: list[QuantDesignMatrixColumn] = [
        QuantDesignMatrixColumn(
            column_name="intercept",
            kind=QuantDesignMatrixColumnKind.INTERCEPT,
            encoding=QuantDesignMatrixColumnEncoding.BINARY,
            source_field="intercept",
        )
    ]
    column_values: list[tuple[float, ...]] = [
        tuple(1.0 for _ in analysis_design_entries)
    ]

    condition_columns, condition_values = _build_categorical_columns(
        analysis_design_entries,
        field=condition_field,
        kind=QuantDesignMatrixColumnKind.CONDITION,
    )
    columns.extend(condition_columns)
    column_values.extend(condition_values)

    if batch_field:
        batch_columns, batch_values = _build_categorical_columns(
            analysis_design_entries,
            field=batch_field,
            kind=QuantDesignMatrixColumnKind.BATCH,
        )
        columns.extend(batch_columns)
        column_values.extend(batch_values)

    if pairing_field:
        pairing_columns, pairing_values = _build_categorical_columns(
            analysis_design_entries,
            field=pairing_field,
            kind=QuantDesignMatrixColumnKind.PAIRING,
        )
        columns.extend(pairing_columns)
        column_values.extend(pairing_values)

    if timepoint_field and timepoint_field not in {
        condition_field,
        batch_field,
        pairing_field,
    }:
        numeric_timepoint = _build_numeric_covariate_column(
            analysis_design_entries,
            timepoint_field,
            kind=QuantDesignMatrixColumnKind.TIMEPOINT,
        )
        if numeric_timepoint is not None:
            column, values = numeric_timepoint
            columns.append(column)
            column_values.append(values)
        else:
            timepoint_columns, timepoint_values = _build_categorical_columns(
                analysis_design_entries,
                field=timepoint_field,
                kind=QuantDesignMatrixColumnKind.TIMEPOINT,
            )
            columns.extend(timepoint_columns)
            column_values.extend(timepoint_values)

    for field in covariate_fields:
        if field in {condition_field, batch_field, pairing_field, timepoint_field}:
            continue
        numeric_covariate = _build_numeric_covariate_column(
            analysis_design_entries,
            field,
        )
        if numeric_covariate is not None:
            column, values = numeric_covariate
            columns.append(column)
            column_values.append(values)
            continue
        covariate_columns, covariate_values = _build_categorical_columns(
            analysis_design_entries,
            field=field,
            kind=QuantDesignMatrixColumnKind.COVARIATE,
        )
        columns.extend(covariate_columns)
        column_values.extend(covariate_values)

    rows: list[QuantDesignMatrixSampleRow] = []
    for row_index, entry in enumerate(analysis_design_entries):
        rows.append(
            QuantDesignMatrixSampleRow(
                sample_id=entry.sample_id,
                condition=entry.condition,
                batch=_resolve_design_value(entry, batch_field)
                if batch_field is not None
                else None,
                pair_id=_resolve_design_value(entry, pairing_field)
                if pairing_field is not None
                else entry.pair_id,
                metadata=entry.metadata,
                column_values=tuple(values[row_index] for values in column_values),
            )
        )

    _require_full_rank_design(tuple(columns), tuple(column_values))

    return QuantDesignMatrixReport(
        sample_count=len(rows),
        column_count=len(columns),
        condition_field=condition_field,
        batch_field=batch_field,
        pairing_field=pairing_field,
        timepoint_field=timepoint_field,
        covariate_fields=tuple(covariate_fields),
        columns=tuple(columns),
        rows=tuple(rows),
        contrasts=_build_condition_contrasts(
            tuple(columns),
            conditions=conditions,
        ),
        note=(
            "design matrix preserves intercept, condition contrasts, optional batch blocking, optional pairing blocks, optional timepoint structure, and declared sample covariates while honoring explicit biological-sample versus technical-run resolution policy"
        ),
    )


def _required_consistency_fields(
    *,
    condition_field: str,
    batch_field: str | None,
    pairing_field: str | None,
    timepoint_field: str | None,
    covariate_fields: tuple[str, ...],
) -> tuple[str, ...]:
    fields = [
        condition_field,
        batch_field,
        pairing_field,
        timepoint_field,
        *covariate_fields,
    ]
    return tuple(
        field
        for field in dict.fromkeys(field for field in fields if field not in (None, ""))
    )


def fit_quant_design_matrix_model(
    table: LabelFreeQuantTable,
    design_matrix: QuantDesignMatrixReport,
) -> QuantDesignModelFitReport:
    """Fit one lightweight least-squares model per quantified entity."""
    sample_ids = tuple(row.sample_id for row in design_matrix.rows)
    full_matrix = np.array(
        [row.column_values for row in design_matrix.rows],
        dtype=float,
    )
    lookup = _matrix_value_index(table)
    coefficient_entries: list[QuantDesignModelCoefficientEntry] = []
    contrast_estimates: list[QuantDesignContrastEstimateEntry] = []
    fitted_entity_count = 0
    skipped_entity_count = 0
    column_index = {
        column.column_name: index
        for index, column in enumerate(design_matrix.columns)
    }
    for entity_id in table.entity_ids:
        observed_rows: list[np.ndarray] = []
        observed_values: list[float] = []
        for row_index, sample_id in enumerate(sample_ids):
            cell = lookup.get((entity_id, sample_id))
            if cell is None or cell.abundance is None:
                continue
            observed_rows.append(full_matrix[row_index])
            observed_values.append(math.log2(cell.abundance + 1.0))
        if len(observed_values) < 2:
            skipped_entity_count += 1
            continue
        x_matrix = np.vstack(observed_rows)
        y_vector = np.array(observed_values, dtype=float)
        coefficients, _, _, _ = np.linalg.lstsq(x_matrix, y_vector, rcond=None)
        rank = int(np.linalg.matrix_rank(x_matrix))
        residual_df = max(len(observed_values) - rank, 0)
        fitted_entity_count += 1
        for column, estimate in zip(
            design_matrix.columns,
            coefficients,
            strict=False,
        ):
            coefficient_entries.append(
                QuantDesignModelCoefficientEntry(
                    entity_id=entity_id,
                    coefficient_name=column.column_name,
                    estimate=float(estimate),
                    observed_sample_count=len(observed_values),
                    design_rank=rank,
                    residual_degrees_of_freedom=residual_df,
                )
            )
        for contrast in design_matrix.contrasts:
            estimate = sum(
                coefficients[column_index[column_name]] * weight
                for column_name, weight in contrast.coefficient_weights.items()
            )
            contrast_estimates.append(
                QuantDesignContrastEstimateEntry(
                    entity_id=entity_id,
                    contrast_name=contrast.contrast_name,
                    condition_a=contrast.condition_a,
                    condition_b=contrast.condition_b,
                    estimate=float(estimate),
                )
            )
    return QuantDesignModelFitReport(
        entity_level=table.entity_level,
        normalization_method=table.normalization_method,
        imputation_method=table.imputation_method,
        design_matrix=design_matrix,
        fitted_entity_count=fitted_entity_count,
        skipped_entity_count=skipped_entity_count,
        coefficient_entries=tuple(coefficient_entries),
        contrast_estimates=tuple(contrast_estimates),
        note=(
            "design-model coefficients use one least-squares fit per entity over observed samples, so underdetermined designs remain descriptive rather than inferential"
        ),
    )


def render_quant_design_matrix_tsv(
    report: QuantDesignMatrixReport,
) -> str:
    """Render one design matrix as a stable TSV table."""
    metadata_fields = tuple(
        sorted({key for row in report.rows for key in row.metadata.keys()})
    )
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "sample_id",
            "condition",
            "batch",
            "pair_id",
            *metadata_fields,
            *[column.column_name for column in report.columns],
        ]
    )
    for row in report.rows:
        writer.writerow(
            [
                row.sample_id,
                row.condition,
                row.batch or "",
                row.pair_id or "",
                *[row.metadata.get(field, "") for field in metadata_fields],
                *[f"{value:.6g}" for value in row.column_values],
            ]
        )
    return buffer.getvalue()


def export_quant_design_matrix_tsv(
    report: QuantDesignMatrixReport,
    path: Path,
) -> None:
    """Write one design matrix to a stable TSV artifact."""
    path.write_text(render_quant_design_matrix_tsv(report), encoding="utf-8")


def render_quant_design_model_coefficients_tsv(
    report: QuantDesignModelFitReport,
) -> str:
    """Render per-entity design-model coefficients as a stable TSV table."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "entity_id",
            "coefficient_name",
            "estimate",
            "observed_sample_count",
            "design_rank",
            "residual_degrees_of_freedom",
        ]
    )
    for entry in report.coefficient_entries:
        writer.writerow(
            [
                entry.entity_id,
                entry.coefficient_name,
                f"{entry.estimate:.6g}",
                entry.observed_sample_count,
                entry.design_rank,
                entry.residual_degrees_of_freedom,
            ]
        )
    return buffer.getvalue()


def export_quant_design_model_coefficients_tsv(
    report: QuantDesignModelFitReport,
    path: Path,
) -> None:
    """Write design-model coefficients to a stable TSV artifact."""
    path.write_text(render_quant_design_model_coefficients_tsv(report), encoding="utf-8")


def render_quant_design_contrast_estimates_tsv(
    report: QuantDesignModelFitReport,
) -> str:
    """Render per-entity condition-contrast estimates as a stable TSV table."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "entity_id",
            "contrast_name",
            "condition_a",
            "condition_b",
            "estimate",
        ]
    )
    for entry in report.contrast_estimates:
        writer.writerow(
            [
                entry.entity_id,
                entry.contrast_name,
                entry.condition_a,
                entry.condition_b,
                f"{entry.estimate:.6g}",
            ]
        )
    return buffer.getvalue()


def export_quant_design_contrast_estimates_tsv(
    report: QuantDesignModelFitReport,
    path: Path,
) -> None:
    """Write condition-contrast estimates to a stable TSV artifact."""
    path.write_text(render_quant_design_contrast_estimates_tsv(report), encoding="utf-8")
