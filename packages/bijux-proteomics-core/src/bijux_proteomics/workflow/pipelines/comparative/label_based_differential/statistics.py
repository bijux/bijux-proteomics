# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Design fitting and differential statistics for labeled workflows."""

from __future__ import annotations

from itertools import combinations
import math

import numpy as np

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts.design import (
    QuantDesignContrastEstimateEntry,
    QuantDesignMatrixReport,
    QuantDesignModelCoefficientEntry,
    QuantDesignModelFitReport,
)
from bijux_proteomics.quantification.contracts.differential import (
    DifferentialAbundanceAssumptionReport,
    DifferentialAbundanceContrast,
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
    DifferentialAbundanceTestType,
    DifferentialReplicatePolicy,
    MultiConditionDifferentialAbundanceReport,
    _effect_size_and_uncertainty,
    _welch_t_test,
)
from bijux_proteomics.quantification.contracts.input_models import (
    ImputationMethod,
    NormalizationMethod,
    QuantAssessmentDisposition,
    QuantEntityLevel,
)
from bijux_proteomics.quantification.contracts.matrix_building import _condition_lookup
from bijux_proteomics.quantification.differential_abundance import (
    apply_benjamini_hochberg,
)
from bijux_proteomics.study import count_effective_statistical_units_by_condition
from bijux_proteomics.workflow.pipelines.comparative.label_based_differential.models import (
    LabelBasedDifferentialInputReport,
    LabelBasedDifferentialVolcanoPlot,
    LabelBasedDifferentialVolcanoPoint,
    LabelBasedMeasurementKind,
)


def fit_label_based_design_matrix_model(
    report: LabelBasedDifferentialInputReport,
    design_matrix: QuantDesignMatrixReport,
) -> QuantDesignModelFitReport:
    """Fit one least-squares design model per labeled protein entity."""

    sample_ids = tuple(row.sample_id for row in design_matrix.rows)
    full_matrix = np.array(
        [row.column_values for row in design_matrix.rows], dtype=float
    )
    column_index = {
        column.column_name: index for index, column in enumerate(design_matrix.columns)
    }
    row_lookup = {row.entity_id: row for row in report.rows}
    coefficient_entries: list[QuantDesignModelCoefficientEntry] = []
    contrast_estimates: list[QuantDesignContrastEstimateEntry] = []
    fitted_entity_count = 0
    skipped_entity_count = 0
    for entity_id in sorted(row_lookup):
        row = row_lookup[entity_id]
        value_lookup = {value.sample_id: value for value in row.values}
        observed_rows: list[np.ndarray] = []
        observed_values: list[float] = []
        for row_index, sample_id in enumerate(sample_ids):
            value = value_lookup.get(sample_id)
            if value is None or value.abundance is None:
                continue
            transformed = _transformed_value(
                value.abundance,
                measurement_kind=report.measurement_kind,
            )
            if transformed is None:
                continue
            observed_rows.append(full_matrix[row_index])
            observed_values.append(transformed)
        if len(observed_values) < 2:
            skipped_entity_count += 1
            continue
        x_matrix = np.vstack(observed_rows)
        y_vector = np.array(observed_values, dtype=float)
        coefficients, _, _, _ = np.linalg.lstsq(x_matrix, y_vector, rcond=None)
        rank = int(np.linalg.matrix_rank(x_matrix))
        residual_df = max(len(observed_values) - rank, 0)
        fitted_entity_count += 1
        for column, estimate in zip(design_matrix.columns, coefficients, strict=False):
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
        entity_level=QuantEntityLevel.PROTEIN,
        normalization_method=NormalizationMethod.NONE,
        imputation_method=ImputationMethod.NONE,
        design_matrix=design_matrix,
        fitted_entity_count=fitted_entity_count,
        skipped_entity_count=skipped_entity_count,
        coefficient_entries=tuple(coefficient_entries),
        contrast_estimates=tuple(contrast_estimates),
        note=(
            "design-model coefficients use one least-squares fit per labeled protein entity over transformed observed samples"
        ),
    )


def build_label_based_differential_report(
    report: LabelBasedDifferentialInputReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str,
    condition_b: str,
    replicate_policy: DifferentialReplicatePolicy | None,
) -> DifferentialAbundanceReport:
    """Build one pairwise labeled differential report for an explicit contrast."""

    active_policy = replicate_policy or DifferentialReplicatePolicy()
    condition_by_sample = _condition_lookup(design_entries)
    samples_a = tuple(
        sample_id
        for sample_id, condition in condition_by_sample.items()
        if condition == condition_a
    )
    samples_b = tuple(
        sample_id
        for sample_id, condition in condition_by_sample.items()
        if condition == condition_b
    )
    if not samples_a or not samples_b:
        raise ValueError("both conditions must map to at least one sample")
    effective_units_by_condition = count_effective_statistical_units_by_condition(
        design_entries
    )
    if (
        effective_units_by_condition.get(condition_a, 0)
        < active_policy.min_replicates_per_condition
        or effective_units_by_condition.get(condition_b, 0)
        < active_policy.min_replicates_per_condition
    ) and active_policy.disposition is QuantAssessmentDisposition.ENFORCED:
        raise ValueError(
            "minimum replicate policy not satisfied for labeled differential analysis"
        )
    entries: list[DifferentialAbundanceEntry] = []
    for row in report.rows:
        value_lookup = {value.sample_id: value for value in row.values}
        values_a = np.array(
            [
                transformed
                for sample_id in samples_a
                if (value := value_lookup.get(sample_id)) is not None
                and value.abundance is not None
                and (
                    transformed := _transformed_value(
                        value.abundance,
                        measurement_kind=report.measurement_kind,
                    )
                )
                is not None
            ],
            dtype=float,
        )
        values_b = np.array(
            [
                transformed
                for sample_id in samples_b
                if (value := value_lookup.get(sample_id)) is not None
                and value.abundance is not None
                and (
                    transformed := _transformed_value(
                        value.abundance,
                        measurement_kind=report.measurement_kind,
                    )
                )
                is not None
            ],
            dtype=float,
        )
        mean_a = float(np.mean(values_a)) if values_a.size else 0.0
        mean_b = float(np.mean(values_b)) if values_b.size else 0.0
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
                entity_id=row.entity_id,
                condition_a=condition_a,
                condition_b=condition_b,
                observations_a=int(values_a.size),
                observations_b=int(values_b.size),
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
    entries = sorted(
        entries,
        key=lambda entry: (
            entry.p_value,
            -abs(entry.log2_fold_change),
            entry.entity_id,
        ),
    )
    return DifferentialAbundanceReport(
        entity_level=QuantEntityLevel.PROTEIN,
        normalization_method=NormalizationMethod.NONE,
        imputation_method=ImputationMethod.NONE,
        condition_a=condition_a,
        condition_b=condition_b,
        replicate_policy=active_policy,
        assumption_report=DifferentialAbundanceAssumptionReport(
            test_type=DifferentialAbundanceTestType.WELCH_T_TEST,
            variance_assumption="unequal_variance",
            multiple_testing_scope="uncorrected_report_wide_entities",
            replicate_policy=active_policy,
        ),
        entries=tuple(entries),
    )


def build_multi_condition_label_based_differential_report(
    report: LabelBasedDifferentialInputReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    contrasts: tuple[tuple[str, str], ...] | None = None,
    replicate_policy: DifferentialReplicatePolicy | None,
) -> MultiConditionDifferentialAbundanceReport:
    """Build pairwise labeled reports across every selected condition contrast."""

    active_policy = replicate_policy or DifferentialReplicatePolicy()
    selected_contrasts = contrasts or tuple(
        combinations(list_label_based_conditions(design_entries), 2)
    )
    differential_reports: list[DifferentialAbundanceReport] = []
    contrast_entries: list[DifferentialAbundanceContrast] = []
    for condition_a, condition_b in selected_contrasts:
        contrast_entries.append(
            DifferentialAbundanceContrast(
                condition_a=condition_a,
                condition_b=condition_b,
            )
        )
        differential_reports.append(
            apply_benjamini_hochberg(
                build_label_based_differential_report(
                    report,
                    design_entries,
                    condition_a=condition_a,
                    condition_b=condition_b,
                    replicate_policy=active_policy,
                )
            )
        )
    return MultiConditionDifferentialAbundanceReport(
        entity_level=QuantEntityLevel.PROTEIN,
        normalization_method=NormalizationMethod.NONE,
        imputation_method=ImputationMethod.NONE,
        condition_count=len(list_label_based_conditions(design_entries)),
        replicate_policy=active_policy,
        contrasts=tuple(contrast_entries),
        reports=tuple(differential_reports),
        note=(
            "pairwise labeled differential analysis preserves one benjamini-hochberg-corrected report per selected condition contrast"
        ),
    )


def build_label_based_differential_volcano_plot(
    report: DifferentialAbundanceReport,
    *,
    protein_refs_by_entity: dict[str, tuple[str, ...]],
    adjusted_p_value_threshold: float = 0.1,
    absolute_log2_fold_change_threshold: float = 1.0,
) -> LabelBasedDifferentialVolcanoPlot:
    """Build one volcano payload over a BH-corrected labeled differential report."""

    points: list[LabelBasedDifferentialVolcanoPoint] = []
    for entry in report.entries:
        adjusted_p_value = entry.adjusted_p_value or entry.p_value
        highlighted = (
            adjusted_p_value <= adjusted_p_value_threshold
            and abs(entry.log2_fold_change) >= absolute_log2_fold_change_threshold
        )
        points.append(
            LabelBasedDifferentialVolcanoPoint(
                entity_id=entry.entity_id,
                protein_refs=protein_refs_by_entity.get(entry.entity_id, ()),
                log2_fold_change=entry.log2_fold_change,
                raw_p_value=entry.p_value,
                adjusted_p_value=adjusted_p_value,
                negative_log10_adjusted_p_value=_negative_log10(adjusted_p_value),
                highlighted=highlighted,
            )
        )
    return LabelBasedDifferentialVolcanoPlot(
        condition_a=report.condition_a,
        condition_b=report.condition_b,
        significant_point_count=sum(1 for point in points if point.highlighted),
        points=tuple(
            sorted(
                points,
                key=lambda point: (
                    -point.negative_log10_adjusted_p_value,
                    -abs(point.log2_fold_change),
                    point.entity_id,
                ),
            )
        ),
        note=(
            "volcano plot preserves fold change and adjusted significance for one explicit labeled contrast"
        ),
    )


def list_label_based_conditions(
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[str, ...]:
    """Return the ordered distinct condition names used by the labeled design."""

    return tuple(
        sorted(
            {
                condition
                for condition in _condition_lookup(design_entries).values()
                if condition
            }
        )
    )


def filter_label_based_design_entries(
    report: LabelBasedDifferentialInputReport,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[ExperimentalDesignEntry, ...]:
    """Keep only experiment-design entries present in the labeled matrix."""

    sample_id_set = set(report.sample_ids)
    filtered = tuple(
        entry for entry in design_entries if entry.sample_id in sample_id_set
    )
    if not filtered:
        raise ValueError(
            "labeled differential analysis requires design entries for the analysis sample ids"
        )
    return filtered


def resolve_label_based_contrast(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None,
    condition_b: str | None,
) -> tuple[str, str] | None:
    """Resolve the explicit or implicit pairwise contrast for labeled analysis."""

    conditions = list_label_based_conditions(design_entries)
    if condition_a is None and condition_b is None:
        if len(conditions) == 2:
            return conditions[0], conditions[1]
        return None
    if condition_a is None or condition_b is None:
        raise ValueError("both condition names must be provided together")
    if condition_a == condition_b:
        raise ValueError("condition contrast must compare two distinct conditions")
    known_conditions = set(conditions)
    unknown = sorted({condition_a, condition_b} - known_conditions)
    if unknown:
        raise ValueError(
            "labeled differential contrast references unknown conditions: "
            + ", ".join(unknown)
        )
    return condition_a, condition_b


_analysis_design_entries = filter_label_based_design_entries
_build_differential_report = build_label_based_differential_report
_build_multi_condition_differential_report = (
    build_multi_condition_label_based_differential_report
)
_condition_names = list_label_based_conditions
_fit_design_matrix_model = fit_label_based_design_matrix_model
_resolve_selected_contrast = resolve_label_based_contrast


def _transformed_value(
    abundance: float,
    *,
    measurement_kind: LabelBasedMeasurementKind,
) -> float | None:
    if abundance < 0.0:
        return None
    if measurement_kind is LabelBasedMeasurementKind.INTENSITY:
        return float(math.log2(abundance + 1.0))
    if abundance <= 0.0:
        return None
    return float(math.log2(abundance))


def _negative_log10(value: float) -> float:
    clipped = max(value, 1e-300)
    return float(-math.log10(clipped))


__all__ = [
    "build_label_based_differential_report",
    "build_label_based_differential_volcano_plot",
    "build_multi_condition_label_based_differential_report",
    "filter_label_based_design_entries",
    "fit_label_based_design_matrix_model",
    "list_label_based_conditions",
    "resolve_label_based_contrast",
]
