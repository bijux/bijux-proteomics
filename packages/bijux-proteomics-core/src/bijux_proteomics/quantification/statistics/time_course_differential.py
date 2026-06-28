# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned time-course differential-analysis surfaces."""

from __future__ import annotations

import csv
from io import StringIO
import math
from pathlib import Path
import re

import numpy as np

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts.design import (
    QuantDesignMatrixColumn,
    QuantDesignMatrixColumnEncoding,
    QuantDesignMatrixColumnKind,
)
from bijux_proteomics.quantification.contracts.differential import (
    TimeCourseDifferentialEntry,
    TimeCourseDifferentialReport,
    TimeCourseTestingPolicy,
    _student_t_two_sided_p_value,
)
from bijux_proteomics.quantification.contracts.matrix_building import _matrix_value_index
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable
from bijux_proteomics.quantification.matrix.design_matrix import (
    _build_categorical_columns,
    _build_numeric_covariate_column,
    _require_full_rank_design,
    _require_unique_sample_ids,
    _resolve_design_value,
)
from bijux_proteomics.quantification.statistics.differential_result_robustness import (
    annotate_time_course_differential_report_robustness,
)
from bijux_proteomics.study import (
    ExperimentDesignAnalysisFamily,
    require_feasible_experiment_design_for_analysis,
)
from bijux_proteomics.study.sample_run_identity import (
    SampleRunAnalysisPolicy,
    resolve_sample_run_analysis_entries,
)

_PREFIXED_NUMERIC_LABEL_RE = re.compile(
    r"^(?P<prefix>.*?)(?P<number>[+-]?\d+(?:\.\d+)?)$"
)


def build_time_course_differential_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    policy: TimeCourseTestingPolicy | None = None,
    sample_run_policy: SampleRunAnalysisPolicy = (
        SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS
    ),
) -> TimeCourseDifferentialReport:
    """Build one ordered time-course differential report over a quant table."""
    if not design_entries:
        raise ValueError("time-course testing requires design entries")
    active_policy = policy or TimeCourseTestingPolicy()
    analysis_design_entries = resolve_sample_run_analysis_entries(
        design_entries,
        policy=sample_run_policy,
        required_consistency_fields=_required_consistency_fields(active_policy),
    )
    _require_unique_sample_ids(analysis_design_entries)
    _require_table_sample_ids(table, design_entries=analysis_design_entries)
    require_feasible_experiment_design_for_analysis(
        analysis_design_entries,
        chosen_analysis_family=ExperimentDesignAnalysisFamily.TIME_COURSE_DIFFERENTIAL,
        batch_field=active_policy.batch_field,
        pairing_field=active_policy.pairing_field,
        timepoint_field=active_policy.timepoint_field,
        ordered_timepoints=active_policy.ordered_timepoints,
    )
    timepoint_by_sample, timepoint_positions, ordered_timepoints, order_note = (
        _resolve_timepoint_positions(
            analysis_design_entries,
            timepoint_field=active_policy.timepoint_field,
            ordered_timepoints=active_policy.ordered_timepoints,
        )
    )
    if len(ordered_timepoints) < 2:
        raise ValueError("time-course testing requires at least two ordered timepoints")
    conditions = tuple(
        sorted(
            {
                str(_resolve_design_value(entry, "condition"))
                for entry in analysis_design_entries
                if _resolve_design_value(entry, "condition") not in (None, "")
            }
        )
    )
    if not conditions:
        raise ValueError("time-course testing requires at least one condition")
    reference_condition = conditions[0]

    effective_pairing_field = active_policy.pairing_field
    if effective_pairing_field is None and all(
        entry.pair_id not in (None, "") for entry in analysis_design_entries
    ):
        effective_pairing_field = "pair_id"

    design_columns, design_values, condition_columns = _build_time_course_design(
        analysis_design_entries,
        timepoint_by_sample=timepoint_by_sample,
        timepoint_field=active_policy.timepoint_field,
        batch_field=active_policy.batch_field,
        pairing_field=effective_pairing_field,
        covariate_fields=active_policy.covariate_fields,
    )
    _require_full_rank_design(design_columns, design_values)

    row_index_by_sample = {
        entry.sample_id: row_index
        for row_index, entry in enumerate(analysis_design_entries)
    }
    condition_column_by_level = {
        column.level: column
        for column in condition_columns
        if column.level not in (None, "")
    }
    interaction_column_names = {
        level: f"{condition_column_by_level[level].column_name}:timepoint"
        for level in condition_column_by_level
    }
    column_index = {
        column.column_name: index for index, column in enumerate(design_columns)
    }
    time_column_index = column_index["timepoint"]

    lookup = _matrix_value_index(table)
    entries: list[TimeCourseDifferentialEntry] = []
    for entity_id in table.entity_ids:
        observed_rows: list[np.ndarray] = []
        observed_values: list[float] = []
        observed_count_by_condition = dict.fromkeys(conditions, 0)
        observed_timepoints_by_condition: dict[str, set[str]] = {
            condition: set() for condition in conditions
        }
        for entry in analysis_design_entries:
            cell = lookup.get((entity_id, entry.sample_id))
            if cell is None or cell.abundance is None:
                continue
            row_index = row_index_by_sample[entry.sample_id]
            observed_rows.append(
                np.array(
                    design_values_by_row(design_values, row_index),
                    dtype=float,
                )
            )
            observed_values.append(math.log2(cell.abundance + 1.0))
            observed_count_by_condition[entry.condition] += 1
            observed_timepoints_by_condition[entry.condition].add(
                _resolve_design_value(entry, active_policy.timepoint_field) or ""
            )
        fit = _fit_time_course_model(observed_rows, observed_values)
        for condition in conditions:
            slope_vector = np.zeros(len(design_columns), dtype=float)
            slope_vector[time_column_index] = 1.0
            if condition != reference_condition:
                slope_vector[column_index[interaction_column_names[condition]]] = 1.0
            (
                slope_estimate,
                slope_p_value,
                slope_standard_error,
                slope_confidence_interval_low,
                slope_confidence_interval_high,
                slope_note,
            ) = _contrast_statistics(
                fit,
                slope_vector,
                unavailable_note=(
                    "time-course slope could not be estimated robustly for this entity"
                ),
            )
            interaction_effect = None
            interaction_p_value = None
            interaction_note = None
            if condition != reference_condition:
                interaction_vector = np.zeros(len(design_columns), dtype=float)
                interaction_vector[
                    column_index[interaction_column_names[condition]]
                ] = 1.0
                (
                    interaction_effect,
                    interaction_p_value,
                    _interaction_standard_error,
                    _interaction_confidence_interval_low,
                    _interaction_confidence_interval_high,
                    interaction_note,
                ) = _contrast_statistics(
                    fit,
                    interaction_vector,
                    unavailable_note=(
                        "time-course interaction could not be estimated robustly for this entity"
                    ),
                )
            notes: list[str] = []
            for note in (
                slope_note,
                interaction_note,
                _condition_support_note(
                    condition=condition,
                    observed_sample_count=observed_count_by_condition[condition],
                    observed_timepoint_count=len(
                        observed_timepoints_by_condition[condition]
                    ),
                ),
            ):
                if note is not None and note != "":
                    notes.append(note)
            entries.append(
                TimeCourseDifferentialEntry(
                    entity_id=entity_id,
                    condition=condition,
                    reference_condition=reference_condition,
                    observed_sample_count=observed_count_by_condition[condition],
                    observed_timepoint_count=len(
                        observed_timepoints_by_condition[condition]
                    ),
                    slope_per_timepoint=slope_estimate,
                    slope_standard_error=slope_standard_error,
                    slope_confidence_interval_low=slope_confidence_interval_low,
                    slope_confidence_interval_high=slope_confidence_interval_high,
                    time_effect_p_value=slope_p_value,
                    interaction_effect=interaction_effect,
                    interaction_p_value=interaction_p_value,
                    note="; ".join(dict.fromkeys(notes)) or None,
                )
            )
    ordered_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.entity_id,
                entry.condition,
            ),
        )
    )
    report = TimeCourseDifferentialReport(
        entity_level=table.entity_level,
        normalization_method=table.normalization_method,
        imputation_method=table.imputation_method,
        reference_condition=reference_condition,
        condition_count=len(conditions),
        ordered_timepoints=ordered_timepoints,
        timepoint_positions=timepoint_positions,
        policy=active_policy.model_copy(
            update={
                "ordered_timepoints": ordered_timepoints,
                "pairing_field": effective_pairing_field,
            }
        ),
        entries=ordered_entries,
        note=(
            "time-course differential analysis preserves ordered timepoints, per-condition slopes, and condition-by-time interaction testing"
            f"; {order_note}"
        ),
    )
    return annotate_time_course_differential_report_robustness(
        _apply_time_course_multiple_testing(report),
        table,
        analysis_design_entries,
    )


def _required_consistency_fields(
    policy: TimeCourseTestingPolicy,
) -> tuple[str, ...]:
    fields = [
        policy.batch_field,
        policy.pairing_field,
        policy.timepoint_field,
        *policy.covariate_fields,
    ]
    ordered_fields: list[str] = []
    for field in fields:
        if field is None or field == "" or field in ordered_fields:
            continue
        ordered_fields.append(field)
    return tuple(ordered_fields)


def _require_table_sample_ids(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> None:
    missing_sample_ids = tuple(
        sorted(
            {
                entry.sample_id
                for entry in design_entries
                if entry.sample_id not in table.sample_ids
            }
        )
    )
    if missing_sample_ids:
        raise ValueError(
            "quantification table sample ids do not cover the resolved time-course "
            "analysis design; missing sample ids: " + ", ".join(missing_sample_ids)
        )


def render_time_course_differential_tsv(
    report: TimeCourseDifferentialReport,
) -> str:
    """Render one time-course differential report as a stable TSV table."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "entity_id",
            "condition",
            "reference_condition",
            "observed_sample_count",
            "observed_timepoint_count",
            "slope_per_timepoint",
            "slope_standard_error",
            "slope_confidence_interval_low",
            "slope_confidence_interval_high",
            "time_effect_p_value",
            "time_effect_adjusted_p_value",
            "interaction_effect",
            "interaction_p_value",
            "interaction_adjusted_p_value",
            "robustness_score",
            "robustness_qc_status",
            "robustness_reason_codes",
            "robustness_note",
            "note",
        ]
    )
    for entry in report.entries:
        writer.writerow(
            [
                entry.entity_id,
                entry.condition,
                entry.reference_condition,
                entry.observed_sample_count,
                entry.observed_timepoint_count,
                entry.slope_per_timepoint,
                ""
                if entry.slope_standard_error is None
                else entry.slope_standard_error,
                (
                    ""
                    if entry.slope_confidence_interval_low is None
                    else entry.slope_confidence_interval_low
                ),
                (
                    ""
                    if entry.slope_confidence_interval_high is None
                    else entry.slope_confidence_interval_high
                ),
                entry.time_effect_p_value,
                (
                    ""
                    if entry.time_effect_adjusted_p_value is None
                    else entry.time_effect_adjusted_p_value
                ),
                "" if entry.interaction_effect is None else entry.interaction_effect,
                "" if entry.interaction_p_value is None else entry.interaction_p_value,
                (
                    ""
                    if entry.interaction_adjusted_p_value is None
                    else entry.interaction_adjusted_p_value
                ),
                ("" if entry.robustness_score is None else entry.robustness_score),
                (
                    ""
                    if entry.robustness_qc_status is None
                    else entry.robustness_qc_status.value
                ),
                ";".join(reason.value for reason in entry.robustness_reason_codes),
                entry.robustness_note or "",
                entry.note or "",
            ]
        )
    return buffer.getvalue()


def export_time_course_differential_tsv(
    report: TimeCourseDifferentialReport,
    path: Path,
) -> None:
    """Write one time-course differential report to a stable TSV artifact."""
    write_output_table_tsv(path, render_time_course_differential_tsv(report))


def _build_time_course_design(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    timepoint_by_sample: dict[str, float],
    timepoint_field: str,
    batch_field: str | None,
    pairing_field: str | None,
    covariate_fields: tuple[str, ...],
) -> tuple[
    tuple[QuantDesignMatrixColumn, ...],
    tuple[tuple[float, ...], ...],
    tuple[QuantDesignMatrixColumn, ...],
]:
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
        field="condition",
        kind=QuantDesignMatrixColumnKind.CONDITION,
    )
    columns.extend(condition_columns)
    column_values.extend(condition_values)
    columns.append(
        QuantDesignMatrixColumn(
            column_name="timepoint",
            kind=QuantDesignMatrixColumnKind.TIMEPOINT,
            encoding=QuantDesignMatrixColumnEncoding.NUMERIC,
            source_field=timepoint_field,
        )
    )
    column_values.append(
        tuple(timepoint_by_sample[entry.sample_id] for entry in design_entries)
    )
    interaction_columns: list[QuantDesignMatrixColumn] = []
    interaction_values: list[tuple[float, ...]] = []
    for condition_column, condition_value in zip(
        condition_columns,
        condition_values,
        strict=False,
    ):
        interaction_columns.append(
            QuantDesignMatrixColumn(
                column_name=f"{condition_column.column_name}:timepoint",
                kind=QuantDesignMatrixColumnKind.INTERACTION,
                encoding=QuantDesignMatrixColumnEncoding.NUMERIC,
                source_field=timepoint_field,
                level=condition_column.level,
                reference_level=condition_column.reference_level,
            )
        )
        interaction_values.append(
            tuple(
                indicator * timepoint_by_sample[entry.sample_id]
                for indicator, entry in zip(
                    condition_value,
                    design_entries,
                    strict=False,
                )
            )
        )
    columns.extend(interaction_columns)
    column_values.extend(interaction_values)
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
        if field in {"condition", batch_field, pairing_field, timepoint_field}:
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
    return tuple(columns), tuple(column_values), condition_columns


def _resolve_timepoint_positions(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    timepoint_field: str,
    ordered_timepoints: tuple[str, ...],
) -> tuple[dict[str, float], dict[str, float], tuple[str, ...], str]:
    raw_timepoints = {
        entry.sample_id: _resolve_design_value(entry, timepoint_field)
        for entry in design_entries
    }
    if any(value in (None, "") for value in raw_timepoints.values()):
        raise ValueError(
            f"time-course testing requires populated {timepoint_field!r} metadata for every sample"
        )
    labels = tuple(str(raw_timepoints[entry.sample_id]) for entry in design_entries)
    unique_labels = tuple(dict.fromkeys(labels))
    if ordered_timepoints:
        declared_order = tuple(ordered_timepoints)
        if len(declared_order) != len(set(declared_order)):
            raise ValueError("timepoint order contains duplicate labels")
        if set(declared_order) != set(unique_labels):
            raise ValueError(
                "timepoint order must contain exactly the timepoint labels present in the design"
            )
        positions = {label: float(index) for index, label in enumerate(declared_order)}
        return (
            {
                sample_id: positions[str(label)]
                for sample_id, label in raw_timepoints.items()
            },
            positions,
            declared_order,
            "timepoint order was supplied explicitly",
        )
    inferred_positions = _infer_numeric_timepoint_positions(unique_labels)
    if inferred_positions is None:
        raise ValueError("unordered timepoint labels require an explicit order file")
    ordered = tuple(
        sorted(unique_labels, key=lambda label: (inferred_positions[label], label))
    )
    return (
        {
            sample_id: inferred_positions[str(label)]
            for sample_id, label in raw_timepoints.items()
        },
        inferred_positions,
        ordered,
        "timepoint order was inferred from numeric labels",
    )


def _infer_numeric_timepoint_positions(
    labels: tuple[str, ...],
) -> dict[str, float] | None:
    direct_numeric: dict[str, float] = {}
    try:
        for label in labels:
            direct_numeric[label] = float(label)
    except ValueError:
        direct_numeric = {}
    if direct_numeric:
        return direct_numeric
    parsed = []
    for label in labels:
        match = _PREFIXED_NUMERIC_LABEL_RE.match(label)
        if match is None:
            return None
        parsed.append((label, match.group("prefix"), float(match.group("number"))))
    prefixes = {prefix for _, prefix, _ in parsed}
    if len(prefixes) != 1:
        return None
    return {label: number for label, _prefix, number in parsed}


def design_values_by_row(
    column_values: tuple[tuple[float, ...], ...],
    row_index: int,
) -> tuple[float, ...]:
    return tuple(values[row_index] for values in column_values)


def _fit_time_course_model(
    observed_rows: list[np.ndarray],
    observed_values: list[float],
) -> tuple[np.ndarray, np.ndarray | None, float, str | None]:
    if len(observed_values) < 2:
        return (
            np.array([], dtype=float),
            None,
            0.0,
            "time-course model requires at least two observed samples for this entity",
        )
    x_matrix = np.vstack(observed_rows)
    y_vector = np.array(observed_values, dtype=float)
    coefficients, _, _, _ = np.linalg.lstsq(x_matrix, y_vector, rcond=None)
    fitted = x_matrix @ coefficients
    residuals = y_vector - fitted
    rank = int(np.linalg.matrix_rank(x_matrix))
    residual_df = float(len(observed_values) - rank)
    if residual_df <= 0:
        return (
            coefficients,
            None,
            residual_df,
            "time-course model requires positive residual degrees of freedom",
        )
    rss = float(np.dot(residuals, residuals))
    sigma_squared = rss / residual_df
    covariance = sigma_squared * np.linalg.pinv(x_matrix.T @ x_matrix)
    return coefficients, covariance, residual_df, None


def _contrast_statistics(
    fit: tuple[np.ndarray, np.ndarray | None, float, str | None],
    contrast_vector: np.ndarray,
    *,
    unavailable_note: str,
) -> tuple[float, float, float | None, float | None, float | None, str | None]:
    coefficients, covariance, residual_df, fit_note = fit
    if coefficients.size == 0:
        return 0.0, 1.0, None, None, None, fit_note or unavailable_note
    estimate = float(np.dot(contrast_vector, coefficients))
    if covariance is None or residual_df <= 0:
        return estimate, 1.0, None, None, None, fit_note or unavailable_note
    variance = float(contrast_vector @ covariance @ contrast_vector)
    if variance <= 0.0 or not math.isfinite(variance):
        return estimate, 1.0, None, None, None, fit_note or unavailable_note
    standard_error = math.sqrt(variance)
    if standard_error == 0.0 or not math.isfinite(standard_error):
        return estimate, 1.0, None, None, None, fit_note or unavailable_note
    t_statistic = estimate / standard_error
    p_value = _student_t_two_sided_p_value(abs(t_statistic), residual_df)
    interval_radius = 1.96 * standard_error
    return (
        estimate,
        p_value,
        standard_error,
        estimate - interval_radius,
        estimate + interval_radius,
        fit_note,
    )


def _condition_support_note(
    *,
    condition: str,
    observed_sample_count: int,
    observed_timepoint_count: int,
) -> str | None:
    if observed_sample_count == 0:
        return f"condition {condition} has no observed samples for this entity"
    if observed_timepoint_count < 2:
        return f"condition {condition} has fewer than two observed timepoints for this entity"
    return None


def _apply_time_course_multiple_testing(
    report: TimeCourseDifferentialReport,
) -> TimeCourseDifferentialReport:
    time_adjusted = _benjamini_hochberg(
        tuple(entry.time_effect_p_value for entry in report.entries)
    )
    interaction_indices = [
        index
        for index, entry in enumerate(report.entries)
        if entry.interaction_p_value is not None
    ]
    interaction_adjusted_values = _benjamini_hochberg(
        tuple(
            report.entries[index].interaction_p_value or 1.0
            for index in interaction_indices
        )
    )
    interaction_adjusted_by_index = {
        entry_index: interaction_adjusted_values[position]
        for position, entry_index in enumerate(interaction_indices)
    }
    entries = tuple(
        entry.model_copy(
            update={
                "time_effect_adjusted_p_value": time_adjusted[index],
                "interaction_adjusted_p_value": interaction_adjusted_by_index.get(
                    index
                ),
            }
        )
        for index, entry in enumerate(report.entries)
    )
    return report.model_copy(update={"entries": entries})


def _benjamini_hochberg(p_values: tuple[float, ...]) -> tuple[float, ...]:
    if not p_values:
        return ()
    adjusted: list[float] = [1.0] * len(p_values)
    running = 1.0
    total = len(p_values)
    ordered = sorted(enumerate(p_values), key=lambda item: item[1])
    for reverse_rank, (index, p_value) in enumerate(reversed(ordered), start=1):
        rank = total - reverse_rank + 1
        candidate = p_value * total / rank
        running = min(running, candidate)
        adjusted[index] = min(max(running, 0.0), 1.0)
    return tuple(adjusted)
