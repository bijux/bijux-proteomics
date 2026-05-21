# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned design-matrix surfaces for quantification modeling."""

from __future__ import annotations

from itertools import combinations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    QuantDesignContrast,
    QuantDesignMatrixColumn,
    QuantDesignMatrixColumnEncoding,
    QuantDesignMatrixColumnKind,
    QuantDesignMatrixReport,
    QuantDesignMatrixSampleRow,
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
) -> tuple[QuantDesignMatrixColumn, tuple[float, ...]] | None:
    values = _require_populated_design_field(entries, field)
    try:
        numeric = tuple(float(value) for value in values)
    except ValueError:
        return None
    return (
        QuantDesignMatrixColumn(
            column_name=f"covariate[{field}]",
            kind=QuantDesignMatrixColumnKind.COVARIATE,
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
        prefix = "condition" if kind is QuantDesignMatrixColumnKind.CONDITION else field
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
    condition_field: str,
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
            )
        )
    return tuple(contrasts)


def build_quant_design_matrix_report(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    batch_field: str | None = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
    condition_field: str = "condition",
) -> QuantDesignMatrixReport:
    """Build one explicit sample design matrix for quantification modeling."""
    if not design_entries:
        raise ValueError("design matrix requires at least one design entry")

    conditions = tuple(
        sorted(
            {
                value
                for value in _require_populated_design_field(
                    design_entries, condition_field
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
    column_values: list[tuple[float, ...]] = [tuple(1.0 for _ in design_entries)]

    condition_columns, condition_values = _build_categorical_columns(
        design_entries,
        field=condition_field,
        kind=QuantDesignMatrixColumnKind.CONDITION,
    )
    columns.extend(condition_columns)
    column_values.extend(condition_values)

    if batch_field:
        batch_columns, batch_values = _build_categorical_columns(
            design_entries,
            field=batch_field,
            kind=QuantDesignMatrixColumnKind.BATCH,
        )
        columns.extend(batch_columns)
        column_values.extend(batch_values)

    if pairing_field:
        pairing_columns, pairing_values = _build_categorical_columns(
            design_entries,
            field=pairing_field,
            kind=QuantDesignMatrixColumnKind.PAIRING,
        )
        columns.extend(pairing_columns)
        column_values.extend(pairing_values)

    for field in covariate_fields:
        if field in {condition_field, batch_field, pairing_field}:
            continue
        numeric_covariate = _build_numeric_covariate_column(design_entries, field)
        if numeric_covariate is not None:
            column, values = numeric_covariate
            columns.append(column)
            column_values.append(values)
            continue
        covariate_columns, covariate_values = _build_categorical_columns(
            design_entries,
            field=field,
            kind=QuantDesignMatrixColumnKind.COVARIATE,
        )
        columns.extend(covariate_columns)
        column_values.extend(covariate_values)

    rows: list[QuantDesignMatrixSampleRow] = []
    for row_index, entry in enumerate(design_entries):
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

    return QuantDesignMatrixReport(
        sample_count=len(rows),
        column_count=len(columns),
        condition_field=condition_field,
        batch_field=batch_field,
        pairing_field=pairing_field,
        covariate_fields=tuple(covariate_fields),
        columns=tuple(columns),
        rows=tuple(rows),
        contrasts=_build_condition_contrasts(
            tuple(columns),
            conditions=conditions,
            condition_field=condition_field,
        ),
        note=(
            "design matrix preserves intercept, condition contrasts, optional batch blocking, optional pairing blocks, and declared sample covariates"
        ),
    )
