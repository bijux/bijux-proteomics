# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned differential-abundance analysis surfaces."""

from __future__ import annotations

from collections.abc import Mapping
import csv
from io import StringIO
from itertools import combinations
import math
from pathlib import Path

import numpy as np

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts.design import (
    QuantDesignContrast,
    QuantDesignMatrixReport,
)
from bijux_proteomics.quantification.contracts.differential import (
    BrokenPairDisposition,
    DifferentialAbundanceAssumptionReport,
    DifferentialAbundanceContrast,
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
    DifferentialAbundanceTestType,
    DifferentialBrokenPairEntry,
    DifferentialReplicatePolicy,
    MultiConditionDifferentialAbundanceReport,
    PairedDifferentialPolicy,
    _effect_size_and_uncertainty,
    _student_t_two_sided_p_value,
    _welch_t_test,
)
from bijux_proteomics.quantification.contracts.input_models import (
    ImputationMethod,
    MissingValueKind,
    QuantAssessmentDisposition,
)
from bijux_proteomics.quantification.contracts.matrix_building import (
    _condition_lookup,
    _matrix_value_index,
)
from bijux_proteomics.quantification.contracts.matrix_models import (
    LabelFreeQuantTable,
    QuantValue,
)
from bijux_proteomics.quantification.contracts.study_qc import (
    SampleReliabilityWeightReport,
)
from bijux_proteomics.quantification.matrix import (
    build_dense_label_free_quant_table_view,
)
from bijux_proteomics.quantification.matrix.design_matrix import (
    build_quant_design_matrix_report,
)
from bijux_proteomics.quantification.statistics.differential_imputation_dependence import (
    annotate_differential_abundance_report_imputation_dependence,
    build_no_impute_reference_table,
)
from bijux_proteomics.quantification.statistics.differential_abundance.design_context import (
    require_differential_table_sample_ids,
    resolve_design_contrast,
    resolve_design_pairs,
    sample_ids_for_condition,
)
from bijux_proteomics.quantification.statistics.differential_abundance.observation_vectors import (
    collect_condition_values,
    collect_condition_values_vectorized,
)
from bijux_proteomics.quantification.statistics.differential_abundance.weighting import (
    combine_notes as _combine_notes,
    effective_weighted_sample_size as _effective_weighted_sample_size,
    sample_weight_lookup as _sample_weight_lookup,
    weighted_effect_size_and_uncertainty as _weighted_effect_size_and_uncertainty,
    weighted_observation_note as _weighted_observation_note,
    weighted_or_unweighted_mean as _weighted_or_unweighted_mean,
    weighted_sample_standard_deviation as _weighted_sample_standard_deviation,
    weighted_welch_statistics as _weighted_welch_statistics,
)
from bijux_proteomics.quantification.statistics.differential_result_robustness import (
    annotate_differential_abundance_report_robustness,
)
from bijux_proteomics.study.design_classification import (
    ExperimentDesignAnalysisFamily,
)
from bijux_proteomics.study.experiment_feasibility import (
    require_feasible_experiment_design_for_analysis,
)
from bijux_proteomics.study.replicate_structure import (
    count_effective_statistical_units_by_condition,
)
from bijux_proteomics.study.sample_run_identity import (
    SampleRunAnalysisPolicy,
    resolve_sample_run_analysis_entries,
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
    paired_policy: PairedDifferentialPolicy | None = None,
    replicate_policy: DifferentialReplicatePolicy | None = None,
    sample_weights_report: SampleReliabilityWeightReport | None = None,
    sample_run_policy: SampleRunAnalysisPolicy = (
        SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS
    ),
) -> DifferentialAbundanceReport:
    """Run one owned two-condition differential abundance engine."""
    active_policy = replicate_policy or DifferentialReplicatePolicy()
    analysis_design_entries = resolve_sample_run_analysis_entries(
        design_entries,
        policy=sample_run_policy,
    )
    require_differential_table_sample_ids(
        table,
        design_entries=analysis_design_entries,
        sample_run_policy=sample_run_policy,
    )
    condition_by_sample = _condition_lookup(analysis_design_entries)
    conditions = tuple(
        sorted({condition for condition in condition_by_sample.values() if condition})
    )
    if condition_a is None or condition_b is None:
        if len(conditions) != 2:
            raise ValueError(
                "differential abundance requires exactly two conditions or explicit condition names"
            )
        condition_a, condition_b = conditions
    if condition_a is None or condition_b is None:
        raise RuntimeError(
            "differential abundance requires resolved condition names after validation"
        )
    contrast_design_entries = tuple(
        entry
        for entry in analysis_design_entries
        if entry.condition in {condition_a, condition_b}
    )
    biological_contrast_design_entries = tuple(
        entry
        for entry in design_entries
        if entry.condition in {condition_a, condition_b}
    )

    active_paired_policy: PairedDifferentialPolicy | None = None
    chosen_analysis_family = ExperimentDesignAnalysisFamily.PAIRWISE_DIFFERENTIAL
    effective_pairing_field: str | None = None
    if test_type is DifferentialAbundanceTestType.PAIRED_T_TEST:
        active_paired_policy = paired_policy or PairedDifferentialPolicy()
        chosen_analysis_family = ExperimentDesignAnalysisFamily.PAIRED_DIFFERENTIAL
        effective_pairing_field = active_paired_policy.pair_id_field
    try:
        require_feasible_experiment_design_for_analysis(
            contrast_design_entries,
            chosen_analysis_family=chosen_analysis_family,
            condition_a=condition_a,
            condition_b=condition_b,
            pairing_field=effective_pairing_field,
            minimum_statistical_units_per_condition=(
                active_policy.min_replicates_per_condition
            ),
        )
    except ValueError as error:
        if (
            active_policy.disposition is QuantAssessmentDisposition.ENFORCED
            and "insufficient_group_size" in str(error)
        ):
            raise ValueError(
                "minimum replicate policy not satisfied for differential abundance"
            ) from error
        raise

    samples_a = sample_ids_for_condition(condition_by_sample, condition_a)
    samples_b = sample_ids_for_condition(condition_by_sample, condition_b)
    if not samples_a or not samples_b:
        raise ValueError("both conditions must map to at least one sample")
    effective_units_by_condition = count_effective_statistical_units_by_condition(
        biological_contrast_design_entries
    )
    if (
        effective_units_by_condition.get(condition_a, 0)
        < active_policy.min_replicates_per_condition
        or effective_units_by_condition.get(condition_b, 0)
        < active_policy.min_replicates_per_condition
    ) and active_policy.disposition is QuantAssessmentDisposition.ENFORCED:
        raise ValueError(
            "minimum replicate policy not satisfied for differential abundance"
        )

    active_design_matrix: QuantDesignMatrixReport | None = None
    active_contrast_name = contrast_name
    selected_contrast: QuantDesignContrast | None = None
    if test_type in (
        DifferentialAbundanceTestType.LINEAR_MODEL_CONTRAST,
        DifferentialAbundanceTestType.PAIRED_T_TEST,
    ):
        if test_type is DifferentialAbundanceTestType.PAIRED_T_TEST:
            if active_paired_policy is None:
                raise RuntimeError(
                    "paired differential abundance requires one paired policy"
                )
            active_design_matrix = design_matrix or build_quant_design_matrix_report(
                analysis_design_entries,
                batch_field="",
                pairing_field=active_paired_policy.pair_id_field,
            )
        else:
            active_design_matrix = design_matrix or build_quant_design_matrix_report(
                analysis_design_entries
            )
        selected_contrast = resolve_design_contrast(
            active_design_matrix,
            condition_a=condition_a,
            condition_b=condition_b,
            contrast_name=contrast_name,
        )
        active_contrast_name = selected_contrast.contrast_name
    complete_design_pairs: tuple[tuple[str, str, str], ...] = ()
    broken_pairs: tuple[DifferentialBrokenPairEntry, ...] = ()
    if test_type is DifferentialAbundanceTestType.PAIRED_T_TEST:
        if active_design_matrix is None or active_paired_policy is None:
            raise RuntimeError(
                "paired differential abundance requires a design matrix and paired policy"
            )
        complete_design_pairs, broken_pairs = resolve_design_pairs(
            active_design_matrix,
            condition_a=condition_a,
            condition_b=condition_b,
            paired_policy=active_paired_policy,
        )
        if (
            active_paired_policy.broken_pair_disposition is BrokenPairDisposition.BLOCK
            and broken_pairs
        ):
            raise ValueError(
                "paired differential testing blocked because the design contains unmatched or duplicated pairs"
            )
        if len(complete_design_pairs) < active_paired_policy.minimum_complete_pairs:
            raise ValueError(
                "paired differential testing requires at least "
                f"{active_paired_policy.minimum_complete_pairs} complete design pairs"
            )

    lookup = _matrix_value_index(table)
    dense_view = build_dense_label_free_quant_table_view(table)
    sample_indexes_a = np.array(
        [dense_view.sample_index[sample_id] for sample_id in samples_a],
        dtype=int,
    )
    sample_indexes_b = np.array(
        [dense_view.sample_index[sample_id] for sample_id in samples_b],
        dtype=int,
    )
    sample_weights = _sample_weight_lookup(sample_weights_report)
    sample_weight_vector = np.array(
        [
            1.0 if sample_weights is None else float(sample_weights.get(sample_id, 1.0))
            for sample_id in dense_view.sample_ids
        ],
        dtype=float,
    )
    entries: list[DifferentialAbundanceEntry] = []
    for entity_id in table.entity_ids:
        row_index = dense_view.entity_index[entity_id]
        values_a, weights_a, counts_a = collect_condition_values_vectorized(
            dense_view.log2_abundance_matrix[row_index],
            dense_view.missing_kind_codes[row_index],
            sample_indexes_a,
            sample_weight_vector=sample_weight_vector,
        )
        values_b, weights_b, counts_b = collect_condition_values_vectorized(
            dense_view.log2_abundance_matrix[row_index],
            dense_view.missing_kind_codes[row_index],
            sample_indexes_b,
            sample_weight_vector=sample_weight_vector,
        )
        mean_a = _weighted_or_unweighted_mean(values_a, weights_a)
        mean_b = _weighted_or_unweighted_mean(values_b, weights_b)

        if test_type is DifferentialAbundanceTestType.LINEAR_MODEL_CONTRAST:
            if active_design_matrix is None or selected_contrast is None:
                raise RuntimeError(
                    "linear-model contrasts require a design matrix and selected contrast"
                )
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
                sample_weights=sample_weights,
                exclusion_weight_threshold=(
                    sample_weights_report.exclusion_weight_threshold
                    if sample_weights_report is not None
                    else 0.0
                ),
            )
            (
                _raw_standard_error,
                _raw_confidence_interval_low,
                _raw_confidence_interval_high,
                effect_size_cohens_d,
                effect_note,
            ) = (
                _weighted_effect_size_and_uncertainty(
                    values_a,
                    weights_a,
                    values_b,
                    weights_b,
                    log2_fold_change,
                )
                if sample_weights_report is not None
                else _effect_size_and_uncertainty(values_a, values_b, log2_fold_change)
            )
            uncertainty_note = _combine_notes(
                model_note,
                effect_note,
                _weighted_observation_note(
                    weights_a,
                    weights_b,
                    exclusion_weight_threshold=(
                        sample_weights_report.exclusion_weight_threshold
                        if sample_weights_report is not None
                        else 0.0
                    ),
                ),
            )
            complete_pair_count = 0
        elif test_type is DifferentialAbundanceTestType.PAIRED_T_TEST:
            (
                mean_a,
                mean_b,
                log2_fold_change,
                p_value,
                standard_error,
                confidence_interval_low,
                confidence_interval_high,
                effect_size_cohens_d,
                complete_pair_count,
                uncertainty_note,
            ) = _paired_t_test_statistics(
                lookup,
                entity_id,
                complete_design_pairs=complete_design_pairs,
                sample_weights=sample_weights,
                exclusion_weight_threshold=(
                    sample_weights_report.exclusion_weight_threshold
                    if sample_weights_report is not None
                    else 0.0
                ),
            )
        else:
            if sample_weights_report is not None:
                (
                    log2_fold_change,
                    p_value,
                    standard_error,
                    confidence_interval_low,
                    confidence_interval_high,
                    effect_size_cohens_d,
                    uncertainty_note,
                ) = _weighted_welch_statistics(
                    values_a,
                    weights_a,
                    values_b,
                    weights_b,
                    exclusion_weight_threshold=(
                        sample_weights_report.exclusion_weight_threshold
                    ),
                    student_t_two_sided_p_value=_student_t_two_sided_p_value,
                )
            else:
                log2_fold_change, p_value = _welch_t_test(values_a, values_b)
                (
                    standard_error,
                    confidence_interval_low,
                    confidence_interval_high,
                    effect_size_cohens_d,
                    uncertainty_note,
                ) = _effect_size_and_uncertainty(values_a, values_b, log2_fold_change)
            complete_pair_count = 0

        entries.append(
            DifferentialAbundanceEntry(
                entity_id=entity_id,
                condition_a=condition_a,
                condition_b=condition_b,
                observations_a=int(values_a.size),
                observations_b=int(values_b.size),
                complete_pair_count=complete_pair_count,
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
                else (
                    "within_pair_difference"
                    if test_type is DifferentialAbundanceTestType.PAIRED_T_TEST
                    else "design_matrix_residual_variance"
                )
            ),
            multiple_testing_scope="uncorrected_report_wide_entities",
            replicate_policy=active_policy,
            sample_weighting=(
                "reliability_weighted"
                if sample_weights_report is not None
                else "unweighted"
            ),
            contrast_name=active_contrast_name,
            paired_policy=active_paired_policy,
        ),
        entries=ordered_entries,
        broken_pairs=broken_pairs,
    )
    corrected_report = apply_benjamini_hochberg(report)
    if table.imputation_method is not ImputationMethod.NONE:
        baseline_table = build_no_impute_reference_table(table)
        no_impute_report = build_differential_abundance_report(
            baseline_table,
            design_entries,
            condition_a=condition_a,
            condition_b=condition_b,
            test_type=test_type,
            design_matrix=active_design_matrix,
            contrast_name=active_contrast_name,
            paired_policy=active_paired_policy,
            replicate_policy=active_policy,
            sample_weights_report=sample_weights_report,
            sample_run_policy=sample_run_policy,
        )
        corrected_report = annotate_differential_abundance_report_imputation_dependence(
            corrected_report,
            no_impute_report=no_impute_report,
        )
    else:
        corrected_report = annotate_differential_abundance_report_imputation_dependence(
            corrected_report,
        )
    return annotate_differential_abundance_report_robustness(
        corrected_report,
        table,
        analysis_design_entries,
    )


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
    sample_weights_report: SampleReliabilityWeightReport | None = None,
    sample_run_policy: SampleRunAnalysisPolicy = (
        SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS
    ),
) -> MultiConditionDifferentialAbundanceReport:
    """Build pairwise differential reports across a study design."""
    active_policy = replicate_policy or DifferentialReplicatePolicy()
    analysis_design_entries = resolve_sample_run_analysis_entries(
        design_entries,
        policy=sample_run_policy,
    )
    require_differential_table_sample_ids(
        table,
        design_entries=analysis_design_entries,
        sample_run_policy=sample_run_policy,
    )
    condition_by_sample = _condition_lookup(analysis_design_entries)
    conditions = tuple(
        sorted({condition for condition in condition_by_sample.values() if condition})
    )
    if len(conditions) < 2:
        raise ValueError(
            "multi-condition differential abundance requires at least two conditions"
        )
    require_feasible_experiment_design_for_analysis(
        analysis_design_entries,
        chosen_analysis_family=(
            ExperimentDesignAnalysisFamily.MULTI_CONDITION_DIFFERENTIAL
        ),
        minimum_statistical_units_per_condition=(
            active_policy.min_replicates_per_condition
        ),
    )
    contrast_pairs = (
        tuple(combinations(conditions, 2)) if contrasts is None else contrasts
    )
    if not contrast_pairs:
        raise ValueError("multi-condition differential abundance requires contrasts")

    active_design_matrix: QuantDesignMatrixReport | None = None
    if test_type is DifferentialAbundanceTestType.LINEAR_MODEL_CONTRAST:
        active_design_matrix = design_matrix or build_quant_design_matrix_report(
            analysis_design_entries
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
            contrast_name = resolve_design_contrast(
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
                analysis_design_entries,
                condition_a=condition_a,
                condition_b=condition_b,
                test_type=test_type,
                design_matrix=active_design_matrix,
                contrast_name=contrast_name,
                replicate_policy=active_policy,
                sample_weights_report=sample_weights_report,
                sample_run_policy=sample_run_policy,
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


def render_differential_broken_pairs_tsv(
    report: DifferentialAbundanceReport,
) -> str:
    """Render one paired-design broken-pair ledger as a stable TSV table."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "condition_a",
            "condition_b",
            "pair_id",
            "sample_ids_a",
            "sample_ids_b",
            "reason_code",
            "detail",
        ]
    )
    for entry in report.broken_pairs:
        writer.writerow(
            [
                entry.condition_a,
                entry.condition_b,
                entry.pair_id or "",
                ";".join(entry.sample_ids_a),
                ";".join(entry.sample_ids_b),
                entry.reason_code,
                entry.detail,
            ]
        )
    return buffer.getvalue()


def export_differential_broken_pairs_tsv(
    report: DifferentialAbundanceReport,
    path: Path,
) -> None:
    """Write one paired-design broken-pair ledger to a stable TSV artifact."""
    write_output_table_tsv(path, render_differential_broken_pairs_tsv(report))


def export_differential_abundance_tsv(
    report: DifferentialAbundanceReport,
    path: Path,
) -> None:
    """Write one differential-abundance report to a stable TSV artifact."""
    write_output_table_tsv(path, render_differential_abundance_tsv(report))


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
    write_output_table_tsv(
        path, render_multi_condition_differential_abundance_tsv(report)
    )


_collect_condition_values = collect_condition_values
_collect_condition_values_vectorized = collect_condition_values_vectorized


def _linear_model_contrast_statistics(
    table: LabelFreeQuantTable,
    entity_id: str,
    *,
    design_matrix: QuantDesignMatrixReport,
    contrast: QuantDesignContrast,
    sample_weights: dict[str, float] | None = None,
    exclusion_weight_threshold: float = 0.0,
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
    observed_weights: list[float] = []
    for row_index, row in enumerate(design_matrix.rows):
        cell = lookup.get((entity_id, row.sample_id))
        if cell is None or cell.abundance is None:
            continue
        weight = (
            1.0
            if sample_weights is None
            else float(sample_weights.get(row.sample_id, 1.0))
        )
        if weight <= exclusion_weight_threshold:
            continue
        observed_rows.append(full_matrix[row_index])
        observed_values.append(math.log2(cell.abundance + 1.0))
        observed_weights.append(weight)
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
    weight_vector = np.array(observed_weights, dtype=float)
    sqrt_weight_vector = np.sqrt(weight_vector)
    weighted_x = x_matrix * sqrt_weight_vector[:, np.newaxis]
    weighted_y = y_vector * sqrt_weight_vector
    coefficients, _, _, _ = np.linalg.lstsq(weighted_x, weighted_y, rcond=None)
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
    rss = float(np.dot(weight_vector, residuals * residuals))
    sigma_squared = rss / float(residual_df)
    xtx_inverse = np.linalg.pinv(x_matrix.T @ np.diag(weight_vector) @ x_matrix)
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
    if sample_weights is not None:
        note = _combine_notes(
            note,
            _weighted_observation_note(
                weight_vector,
                np.array((), dtype=float),
                exclusion_weight_threshold=exclusion_weight_threshold,
            ),
        )
    return (
        estimate,
        p_value,
        standard_error,
        estimate - interval_radius,
        estimate + interval_radius,
        note,
    )


def _paired_t_test_statistics(
    lookup: Mapping[tuple[str, str], QuantValue],
    entity_id: str,
    *,
    complete_design_pairs: tuple[tuple[str, str, str], ...],
    sample_weights: dict[str, float] | None = None,
    exclusion_weight_threshold: float = 0.0,
) -> tuple[
    float,
    float,
    float,
    float,
    float | None,
    float | None,
    float | None,
    float | None,
    int,
    str | None,
]:
    paired_a: list[float] = []
    paired_b: list[float] = []
    pair_weights: list[float] = []
    for _, sample_id_a, sample_id_b in complete_design_pairs:
        cell_a = lookup.get((entity_id, sample_id_a))
        cell_b = lookup.get((entity_id, sample_id_b))
        if (
            cell_a is None
            or cell_b is None
            or cell_a.abundance is None
            or cell_b.abundance is None
        ):
            continue
        pair_weight = min(
            1.0
            if sample_weights is None
            else float(sample_weights.get(sample_id_a, 1.0)),
            1.0
            if sample_weights is None
            else float(sample_weights.get(sample_id_b, 1.0)),
        )
        if pair_weight <= exclusion_weight_threshold:
            continue
        paired_a.append(math.log2(cell_a.abundance + 1.0))
        paired_b.append(math.log2(cell_b.abundance + 1.0))
        pair_weights.append(pair_weight)
    if not paired_a:
        return (
            0.0,
            0.0,
            0.0,
            1.0,
            None,
            None,
            None,
            None,
            0,
            "paired test could not use any complete observed pairs for this entity",
        )
    values_a = np.array(paired_a, dtype=float)
    values_b = np.array(paired_b, dtype=float)
    weights = np.array(pair_weights, dtype=float)
    differences = values_b - values_a
    complete_pair_count = int(differences.size)
    mean_a = _weighted_or_unweighted_mean(values_a, weights)
    mean_b = _weighted_or_unweighted_mean(values_b, weights)
    estimate = _weighted_or_unweighted_mean(differences, weights)
    effective_pairs = _effective_weighted_sample_size(weights)
    if complete_pair_count < 2:
        return (
            mean_a,
            mean_b,
            estimate,
            1.0,
            None,
            None,
            None,
            None,
            complete_pair_count,
            "paired test requires at least two positive-weight complete observed pairs per entity",
        )
    sample_std = _weighted_sample_standard_deviation(differences, weights)
    if sample_std is None:
        return (
            mean_a,
            mean_b,
            estimate,
            1.0,
            None,
            None,
            None,
            None,
            complete_pair_count,
            "paired test could not estimate weighted within-pair variance robustly",
        )
    if sample_std == 0.0 or not math.isfinite(sample_std):
        collapsed_note = (
            "within-pair differences collapsed to one value so paired uncertainty "
            "could not be estimated robustly"
        )
        return (
            mean_a,
            mean_b,
            estimate,
            1.0 if estimate == 0.0 else 0.0,
            0.0,
            estimate,
            estimate,
            None,
            complete_pair_count,
            collapsed_note,
        )
    standard_error = sample_std / math.sqrt(effective_pairs)
    t_statistic = estimate / standard_error
    p_value = _student_t_two_sided_p_value(
        abs(t_statistic),
        float(max(effective_pairs - 1.0, 1.0)),
    )
    interval_radius = 1.96 * standard_error
    effect_size = estimate / sample_std
    note: str | None = None
    if complete_pair_count < len(complete_design_pairs):
        note = (
            f"paired test used {complete_pair_count} complete observed pairs out of "
            f"{len(complete_design_pairs)} complete design pairs"
        )
    elif standard_error > 1.0:
        note = "within-pair uncertainty remains wide relative to the estimated effect"
    if sample_weights is not None:
        note = _combine_notes(
            note,
            _weighted_observation_note(
                weights,
                np.array((), dtype=float),
                exclusion_weight_threshold=exclusion_weight_threshold,
            ),
        )
    return (
        mean_a,
        mean_b,
        estimate,
        p_value,
        standard_error,
        estimate - interval_radius,
        estimate + interval_radius,
        effect_size,
        complete_pair_count,
        note,
    )


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
            "complete_pair_count",
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
            "no_impute_adjusted_p_value",
            "no_impute_log2_fold_change",
            "imputed_adjusted_p_value",
            "imputed_log2_fold_change",
            "imputation_significance_change_reason",
            "imputation_dependent_hit",
            "robustness_score",
            "robustness_qc_status",
            "robustness_reason_codes",
            "robustness_note",
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
                    entry.complete_pair_count,
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
                    (
                        ""
                        if entry.no_impute_adjusted_p_value is None
                        else entry.no_impute_adjusted_p_value
                    ),
                    (
                        ""
                        if entry.no_impute_log2_fold_change is None
                        else entry.no_impute_log2_fold_change
                    ),
                    (
                        ""
                        if entry.imputed_adjusted_p_value is None
                        else entry.imputed_adjusted_p_value
                    ),
                    (
                        ""
                        if entry.imputed_log2_fold_change is None
                        else entry.imputed_log2_fold_change
                    ),
                    (
                        ""
                        if entry.imputation_significance_change_reason is None
                        else entry.imputation_significance_change_reason.value
                    ),
                    str(entry.imputation_dependent_hit).lower(),
                    ("" if entry.robustness_score is None else entry.robustness_score),
                    (
                        ""
                        if entry.robustness_qc_status is None
                        else entry.robustness_qc_status.value
                    ),
                    ";".join(reason.value for reason in entry.robustness_reason_codes),
                    entry.robustness_note or "",
                    entry.uncertainty_note or "",
                ]
            )
    return buffer.getvalue()


__all__ = [
    "apply_benjamini_hochberg",
    "build_differential_abundance_report",
    "build_multi_condition_differential_abundance_report",
    "export_differential_abundance_tsv",
    "export_differential_broken_pairs_tsv",
    "export_multi_condition_differential_abundance_tsv",
    "render_differential_abundance_tsv",
    "render_differential_broken_pairs_tsv",
    "render_multi_condition_differential_abundance_tsv",
]
