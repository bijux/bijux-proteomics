# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned differential-abundance analysis surfaces."""

from __future__ import annotations

import csv
from io import StringIO
from itertools import combinations
import math
from pathlib import Path

import numpy as np

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceContrast,
    DifferentialAbundanceAssumptionReport,
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
    DifferentialAbundanceTestType,
    DifferentialReplicatePolicy,
    LabelFreeQuantTable,
    MissingValueKind,
    MultiConditionDifferentialAbundanceReport,
    QuantAssessmentDisposition,
    QuantDesignContrast,
    QuantDesignMatrixReport,
    _condition_lookup,
    _effect_size_and_uncertainty,
    _matrix_value_index,
    _student_t_two_sided_p_value,
    _welch_t_test,
)
from bijux_proteomics.quantification.design_matrix import (
    build_quant_design_matrix_report,
)


def build_differential_abundance_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None = None,
    condition_b: str | None = None,
    test_type: DifferentialAbundanceTestType = DifferentialAbundanceTestType.WELCH_T_TEST,
    design_matrix: QuantDesignMatrixReport | None = None,
    contrast_name: str | None = None,
    replicate_policy: DifferentialReplicatePolicy | None = None,
) -> DifferentialAbundanceReport:
    """Run one owned two-condition differential abundance engine."""
    active_policy = replicate_policy or DifferentialReplicatePolicy()
    condition_by_sample = _condition_lookup(design_entries)
    conditions = tuple(
        sorted({condition for condition in condition_by_sample.values() if condition})
    )
    if condition_a is None or condition_b is None:
        if len(conditions) != 2:
            raise ValueError(
                "differential abundance requires exactly two conditions or explicit condition names"
            )
        condition_a, condition_b = conditions
    assert condition_a is not None
    assert condition_b is not None

    samples_a = _sample_ids_for_condition(condition_by_sample, condition_a)
    samples_b = _sample_ids_for_condition(condition_by_sample, condition_b)
    if not samples_a or not samples_b:
        raise ValueError("both conditions must map to at least one sample")
    if (
        len(samples_a) < active_policy.min_replicates_per_condition
        or len(samples_b) < active_policy.min_replicates_per_condition
    ) and active_policy.disposition is QuantAssessmentDisposition.ENFORCED:
        raise ValueError(
            "minimum replicate policy not satisfied for differential abundance"
        )

    active_design_matrix: QuantDesignMatrixReport | None = None
    active_contrast_name = contrast_name
    selected_contrast: QuantDesignContrast | None = None
    if test_type is DifferentialAbundanceTestType.LINEAR_MODEL_CONTRAST:
        active_design_matrix = design_matrix or build_quant_design_matrix_report(
            design_entries
        )
        selected_contrast = _resolve_design_contrast(
            active_design_matrix,
            condition_a=condition_a,
            condition_b=condition_b,
            contrast_name=contrast_name,
        )
        active_contrast_name = selected_contrast.contrast_name

    lookup = _matrix_value_index(table)
    entries: list[DifferentialAbundanceEntry] = []
    for entity_id in table.entity_ids:
        values_a, counts_a = _collect_condition_values(lookup, entity_id, samples_a)
        values_b, counts_b = _collect_condition_values(lookup, entity_id, samples_b)
        mean_a = float(np.mean(values_a)) if values_a.size else 0.0
        mean_b = float(np.mean(values_b)) if values_b.size else 0.0

        if test_type is DifferentialAbundanceTestType.LINEAR_MODEL_CONTRAST:
            assert active_design_matrix is not None
            assert selected_contrast is not None
            (
                log2_fold_change,
                p_value,
                standard_error,
                confidence_interval_low,
                confidence_interval_high,
                model_note,
            ) = _linear_model_contrast_statistics(
                table,
                entity_id,
                design_matrix=active_design_matrix,
                contrast=selected_contrast,
            )
            (
                _raw_standard_error,
                _raw_confidence_interval_low,
                _raw_confidence_interval_high,
                effect_size_cohens_d,
                effect_note,
            ) = _effect_size_and_uncertainty(values_a, values_b, log2_fold_change)
            uncertainty_note = _combine_notes(model_note, effect_note)
        else:
            log2_fold_change, p_value = _welch_t_test(values_a, values_b)
            (
                standard_error,
                confidence_interval_low,
                confidence_interval_high,
                effect_size_cohens_d,
                uncertainty_note,
            ) = _effect_size_and_uncertainty(values_a, values_b, log2_fold_change)

        entries.append(
            DifferentialAbundanceEntry(
                entity_id=entity_id,
                condition_a=condition_a,
                condition_b=condition_b,
                observations_a=int(values_a.size),
                observations_b=int(values_b.size),
                zero_values_a=counts_a[MissingValueKind.ZERO],
                zero_values_b=counts_b[MissingValueKind.ZERO],
                not_observed_values_a=counts_a[MissingValueKind.NOT_OBSERVED],
                not_observed_values_b=counts_b[MissingValueKind.NOT_OBSERVED],
                filtered_values_a=counts_a[MissingValueKind.FILTERED],
                filtered_values_b=counts_b[MissingValueKind.FILTERED],
                mean_log2_abundance_a=mean_a,
                mean_log2_abundance_b=mean_b,
                log2_fold_change=log2_fold_change,
                p_value=p_value,
                standard_error=standard_error,
                confidence_interval_low=confidence_interval_low,
                confidence_interval_high=confidence_interval_high,
                effect_size_cohens_d=effect_size_cohens_d,
                uncertainty_note=uncertainty_note,
            )
        )
    ordered_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.p_value,
                -abs(entry.log2_fold_change),
                entry.entity_id,
            ),
        )
    )
    report = DifferentialAbundanceReport(
        entity_level=table.entity_level,
        normalization_method=table.normalization_method,
        imputation_method=table.imputation_method,
        condition_a=condition_a,
        condition_b=condition_b,
        contrast_name=active_contrast_name,
        replicate_policy=active_policy,
        assumption_report=DifferentialAbundanceAssumptionReport(
            test_type=test_type,
            variance_assumption=(
                "unequal_variance"
                if test_type is DifferentialAbundanceTestType.WELCH_T_TEST
                else "design_matrix_residual_variance"
            ),
            multiple_testing_scope="uncorrected_report_wide_entities",
            replicate_policy=active_policy,
            contrast_name=active_contrast_name,
        ),
        entries=ordered_entries,
    )
    return apply_benjamini_hochberg(report)


def apply_benjamini_hochberg(
    report: DifferentialAbundanceReport,
) -> DifferentialAbundanceReport:
    """Apply Benjamini-Hochberg correction to one differential report."""
    if (
        not report.entries
        or report.assumption_report.multiple_testing_scope
        == "benjamini_hochberg_report_wide_entities"
    ):
        return report
    adjusted: list[float] = [1.0] * len(report.entries)
    running = 1.0
    total = len(report.entries)
    for index in range(total - 1, -1, -1):
        rank = index + 1
        candidate = report.entries[index].p_value * total / rank
        running = min(running, candidate)
        adjusted[index] = min(max(running, 0.0), 1.0)
    entries = tuple(
        entry.model_copy(update={"adjusted_p_value": adjusted[index]})
        for index, entry in enumerate(report.entries)
    )
    return report.model_copy(
        update={
            "entries": entries,
            "assumption_report": report.assumption_report.model_copy(
                update={
                    "multiple_testing_scope": "benjamini_hochberg_report_wide_entities"
                }
            ),
        }
    )


def build_multi_condition_differential_abundance_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    contrasts: tuple[tuple[str, str], ...] | None = None,
    test_type: DifferentialAbundanceTestType = DifferentialAbundanceTestType.WELCH_T_TEST,
    design_matrix: QuantDesignMatrixReport | None = None,
    replicate_policy: DifferentialReplicatePolicy | None = None,
) -> MultiConditionDifferentialAbundanceReport:
    """Build pairwise differential reports across a study design."""
    active_policy = replicate_policy or DifferentialReplicatePolicy()
    condition_by_sample = _condition_lookup(design_entries)
    conditions = tuple(
        sorted({condition for condition in condition_by_sample.values() if condition})
    )
    if len(conditions) < 2:
        raise ValueError(
            "multi-condition differential abundance requires at least two conditions"
        )
    contrast_pairs = (
        tuple(combinations(conditions, 2)) if contrasts is None else contrasts
    )
    if not contrast_pairs:
        raise ValueError("multi-condition differential abundance requires contrasts")

    active_design_matrix: QuantDesignMatrixReport | None = None
    if test_type is DifferentialAbundanceTestType.LINEAR_MODEL_CONTRAST:
        active_design_matrix = design_matrix or build_quant_design_matrix_report(
            design_entries
        )

    known_conditions = set(conditions)
    contrast_entries: list[DifferentialAbundanceContrast] = []
    reports: list[DifferentialAbundanceReport] = []
    for condition_a, condition_b in contrast_pairs:
        if condition_a == condition_b:
            raise ValueError(
                f"differential abundance contrast {condition_a} vs {condition_b} is degenerate"
            )
        unknown = sorted({condition_a, condition_b} - known_conditions)
        if unknown:
            raise ValueError(
                "differential abundance contrast references unknown conditions: "
                + ", ".join(unknown)
            )
        contrast_name = None
        if active_design_matrix is not None:
            contrast_name = _resolve_design_contrast(
                active_design_matrix,
                condition_a=condition_a,
                condition_b=condition_b,
            ).contrast_name
        contrast_entries.append(
            DifferentialAbundanceContrast(
                condition_a=condition_a,
                condition_b=condition_b,
                contrast_name=contrast_name,
            )
        )
        reports.append(
            build_differential_abundance_report(
                table,
                design_entries,
                condition_a=condition_a,
                condition_b=condition_b,
                test_type=test_type,
                design_matrix=active_design_matrix,
                contrast_name=contrast_name,
                replicate_policy=active_policy,
            )
        )

    return MultiConditionDifferentialAbundanceReport(
        entity_level=table.entity_level,
        normalization_method=table.normalization_method,
        imputation_method=table.imputation_method,
        condition_count=len(conditions),
        replicate_policy=active_policy,
        contrasts=tuple(contrast_entries),
        reports=tuple(reports),
        note=(
            "pairwise differential abundance preserves one benjamini-hochberg-corrected report per selected condition contrast"
        ),
    )


def render_differential_abundance_tsv(
    report: DifferentialAbundanceReport,
) -> str:
    """Render one differential-abundance report as a stable TSV table."""
    return _render_differential_rows((report,))


def export_differential_abundance_tsv(
    report: DifferentialAbundanceReport,
    path: Path,
) -> None:
    """Write one differential-abundance report to a stable TSV artifact."""
    path.write_text(render_differential_abundance_tsv(report), encoding="utf-8")


def render_multi_condition_differential_abundance_tsv(
    report: MultiConditionDifferentialAbundanceReport,
) -> str:
    """Render a multi-condition DA collection as one flattened TSV table."""
    return _render_differential_rows(report.reports)


def export_multi_condition_differential_abundance_tsv(
    report: MultiConditionDifferentialAbundanceReport,
    path: Path,
) -> None:
    """Write a multi-condition DA collection to one flattened TSV artifact."""
    path.write_text(
        render_multi_condition_differential_abundance_tsv(report),
        encoding="utf-8",
    )


def _sample_ids_for_condition(
    condition_by_sample: dict[str, str],
    condition: str,
) -> tuple[str, ...]:
    return tuple(
        sample_id
        for sample_id, sample_condition in condition_by_sample.items()
        if sample_condition == condition
    )


def _collect_condition_values(
    lookup: dict[tuple[str, str], object],
    entity_id: str,
    sample_ids: tuple[str, ...],
) -> tuple[np.ndarray, dict[MissingValueKind, int]]:
    values: list[float] = []
    counts = {
        MissingValueKind.ZERO: 0,
        MissingValueKind.NOT_OBSERVED: 0,
        MissingValueKind.FILTERED: 0,
    }
    for sample_id in sample_ids:
        cell = lookup.get((entity_id, sample_id))
        if cell is None:
            counts[MissingValueKind.NOT_OBSERVED] += 1
            continue
        if cell.missing_value_kind is MissingValueKind.ZERO:
            counts[MissingValueKind.ZERO] += 1
        elif cell.missing_value_kind is MissingValueKind.NOT_OBSERVED:
            counts[MissingValueKind.NOT_OBSERVED] += 1
        elif cell.missing_value_kind is MissingValueKind.FILTERED:
            counts[MissingValueKind.FILTERED] += 1
        if cell.abundance is not None:
            values.append(math.log2(cell.abundance + 1.0))
    return np.array(values, dtype=float), counts


def _resolve_design_contrast(
    design_matrix: QuantDesignMatrixReport,
    *,
    condition_a: str,
    condition_b: str,
    contrast_name: str | None = None,
) -> QuantDesignContrast:
    if contrast_name is not None:
        for contrast in design_matrix.contrasts:
            if contrast.contrast_name == contrast_name:
                if (
                    contrast.condition_a != condition_a
                    or contrast.condition_b != condition_b
                ):
                    raise ValueError(
                        "design contrast does not match the requested differential conditions"
                    )
                return contrast
        raise ValueError(f"unknown design contrast {contrast_name!r}")
    for contrast in design_matrix.contrasts:
        if (
            contrast.condition_a == condition_a
            and contrast.condition_b == condition_b
        ):
            return contrast
    raise ValueError(
        "design matrix does not preserve the requested condition contrast"
    )


def _linear_model_contrast_statistics(
    table: LabelFreeQuantTable,
    entity_id: str,
    *,
    design_matrix: QuantDesignMatrixReport,
    contrast: QuantDesignContrast,
) -> tuple[float, float, float | None, float | None, float | None, str | None]:
    if not contrast.coefficient_vector:
        return (
            0.0,
            1.0,
            None,
            None,
            None,
            "linear-model contrast requires an explicit coefficient vector",
        )
    full_matrix = np.array(
        [row.column_values for row in design_matrix.rows],
        dtype=float,
    )
    contrast_vector = -np.array(contrast.coefficient_vector, dtype=float)
    lookup = _matrix_value_index(table)
    observed_rows: list[np.ndarray] = []
    observed_values: list[float] = []
    for row_index, row in enumerate(design_matrix.rows):
        cell = lookup.get((entity_id, row.sample_id))
        if cell is None or cell.abundance is None:
            continue
        observed_rows.append(full_matrix[row_index])
        observed_values.append(math.log2(cell.abundance + 1.0))
    if len(observed_values) < 2:
        return (
            0.0,
            1.0,
            None,
            None,
            None,
            "linear-model contrast requires at least two observed samples",
        )
    x_matrix = np.vstack(observed_rows)
    y_vector = np.array(observed_values, dtype=float)
    coefficients, _, _, _ = np.linalg.lstsq(x_matrix, y_vector, rcond=None)
    fitted = x_matrix @ coefficients
    residuals = y_vector - fitted
    rank = int(np.linalg.matrix_rank(x_matrix))
    residual_df = len(observed_values) - rank
    estimate = float(np.dot(contrast_vector, coefficients))
    if residual_df <= 0:
        return (
            estimate,
            1.0,
            None,
            None,
            None,
            "linear-model contrast requires positive residual degrees of freedom",
        )
    rss = float(np.dot(residuals, residuals))
    sigma_squared = rss / float(residual_df)
    xtx_inverse = np.linalg.pinv(x_matrix.T @ x_matrix)
    contrast_variance = float(
        sigma_squared * (contrast_vector @ xtx_inverse @ contrast_vector)
    )
    if contrast_variance <= 0.0 or not math.isfinite(contrast_variance):
        return (
            estimate,
            1.0,
            None,
            None,
            None,
            "linear-model contrast variance could not be estimated robustly",
        )
    standard_error = math.sqrt(contrast_variance)
    if standard_error == 0.0 or not math.isfinite(standard_error):
        return (
            estimate,
            1.0,
            None,
            None,
            None,
            "linear-model contrast standard error collapsed to zero",
        )
    t_statistic = estimate / standard_error
    p_value = _student_t_two_sided_p_value(abs(t_statistic), float(residual_df))
    interval_radius = 1.96 * standard_error
    note = None
    if standard_error > 1.0:
        note = "uncertainty remains wide relative to the modeled contrast estimate"
    return (
        estimate,
        p_value,
        standard_error,
        estimate - interval_radius,
        estimate + interval_radius,
        note,
    )


def _combine_notes(*notes: str | None) -> str | None:
    ordered_notes = tuple(
        dict.fromkeys(note for note in notes if note not in (None, ""))
    )
    if not ordered_notes:
        return None
    return "; ".join(ordered_notes)


def _render_differential_rows(
    reports: tuple[DifferentialAbundanceReport, ...],
) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "entity_id",
            "condition_a",
            "condition_b",
            "contrast_name",
            "observations_a",
            "observations_b",
            "zero_values_a",
            "zero_values_b",
            "not_observed_values_a",
            "not_observed_values_b",
            "filtered_values_a",
            "filtered_values_b",
            "mean_log2_abundance_a",
            "mean_log2_abundance_b",
            "log2_fold_change",
            "p_value",
            "adjusted_p_value",
            "standard_error",
            "confidence_interval_low",
            "confidence_interval_high",
            "effect_size_cohens_d",
            "uncertainty_note",
        ]
    )
    for report in reports:
        for entry in report.entries:
            writer.writerow(
                [
                    entry.entity_id,
                    entry.condition_a,
                    entry.condition_b,
                    report.contrast_name or "",
                    entry.observations_a,
                    entry.observations_b,
                    entry.zero_values_a,
                    entry.zero_values_b,
                    entry.not_observed_values_a,
                    entry.not_observed_values_b,
                    entry.filtered_values_a,
                    entry.filtered_values_b,
                    entry.mean_log2_abundance_a,
                    entry.mean_log2_abundance_b,
                    entry.log2_fold_change,
                    entry.p_value,
                    "" if entry.adjusted_p_value is None else entry.adjusted_p_value,
                    "" if entry.standard_error is None else entry.standard_error,
                    (
                        ""
                        if entry.confidence_interval_low is None
                        else entry.confidence_interval_low
                    ),
                    (
                        ""
                        if entry.confidence_interval_high is None
                        else entry.confidence_interval_high
                    ),
                    (
                        ""
                        if entry.effect_size_cohens_d is None
                        else entry.effect_size_cohens_d
                    ),
                    entry.uncertainty_note or "",
                ]
            )
    return buffer.getvalue()
