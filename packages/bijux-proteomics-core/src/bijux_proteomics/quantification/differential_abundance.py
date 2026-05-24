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
    BrokenPairDisposition,
    DifferentialAbundanceContrast,
    DifferentialAbundanceAssumptionReport,
    DifferentialBrokenPairEntry,
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
    DifferentialAbundanceTestType,
    DifferentialReplicatePolicy,
    LabelFreeQuantTable,
    MissingValueKind,
    MultiConditionDifferentialAbundanceReport,
    PairedDifferentialPolicy,
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
from bijux_proteomics.quantification.differential_result_robustness import (
    annotate_differential_abundance_report_robustness,
)
from bijux_proteomics.study.sample_run_identity import (
    SampleRunAnalysisPolicy,
    resolve_sample_run_analysis_entries,
)
from bijux_proteomics.study.replicate_structure import (
    count_effective_statistical_units_by_condition,
)
from bijux_proteomics.study.experiment_feasibility import (
    require_feasible_experiment_design_for_analysis,
)
from bijux_proteomics.study.design_classification import (
    ExperimentDesignAnalysisFamily,
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
    _require_table_sample_ids(
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
    assert condition_a is not None
    assert condition_b is not None

    active_paired_policy: PairedDifferentialPolicy | None = None
    chosen_analysis_family = ExperimentDesignAnalysisFamily.PAIRWISE_DIFFERENTIAL
    effective_pairing_field: str | None = None
    if test_type is DifferentialAbundanceTestType.PAIRED_T_TEST:
        active_paired_policy = paired_policy or PairedDifferentialPolicy()
        chosen_analysis_family = ExperimentDesignAnalysisFamily.PAIRED_DIFFERENTIAL
        effective_pairing_field = active_paired_policy.pair_id_field
    require_feasible_experiment_design_for_analysis(
        analysis_design_entries,
        chosen_analysis_family=chosen_analysis_family,
        condition_a=condition_a,
        condition_b=condition_b,
        pairing_field=effective_pairing_field,
        minimum_statistical_units_per_condition=(
            active_policy.min_replicates_per_condition
        ),
    )

    samples_a = _sample_ids_for_condition(condition_by_sample, condition_a)
    samples_b = _sample_ids_for_condition(condition_by_sample, condition_b)
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
            active_design_matrix = design_matrix or build_quant_design_matrix_report(
                analysis_design_entries,
                batch_field="",
                pairing_field=active_paired_policy.pair_id_field,
            )
        else:
            active_design_matrix = design_matrix or build_quant_design_matrix_report(
                analysis_design_entries
            )
        selected_contrast = _resolve_design_contrast(
            active_design_matrix,
            condition_a=condition_a,
            condition_b=condition_b,
            contrast_name=contrast_name,
        )
        active_contrast_name = selected_contrast.contrast_name
    complete_design_pairs: tuple[tuple[str, str, str], ...] = ()
    broken_pairs: tuple[DifferentialBrokenPairEntry, ...] = ()
    if test_type is DifferentialAbundanceTestType.PAIRED_T_TEST:
        assert active_design_matrix is not None
        assert active_paired_policy is not None
        complete_design_pairs, broken_pairs = _resolve_design_pairs(
            active_design_matrix,
            condition_a=condition_a,
            condition_b=condition_b,
            paired_policy=active_paired_policy,
        )
        if (
            active_paired_policy.broken_pair_disposition
            is BrokenPairDisposition.BLOCK
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
            contrast_name=active_contrast_name,
            paired_policy=active_paired_policy,
        ),
        entries=ordered_entries,
        broken_pairs=broken_pairs,
    )
    return annotate_differential_abundance_report_robustness(
        apply_benjamini_hochberg(report),
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
    _require_table_sample_ids(
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
                analysis_design_entries,
                condition_a=condition_a,
                condition_b=condition_b,
                test_type=test_type,
                design_matrix=active_design_matrix,
                contrast_name=contrast_name,
                replicate_policy=active_policy,
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


def _require_table_sample_ids(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    sample_run_policy: SampleRunAnalysisPolicy,
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
    if not missing_sample_ids:
        return
    raise ValueError(
        "quantification table sample ids do not cover the resolved analysis design "
        f"for sample/run policy {sample_run_policy.value!r}; missing sample ids: "
        + ", ".join(missing_sample_ids)
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
    path.write_text(render_differential_broken_pairs_tsv(report), encoding="utf-8")


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


def _resolve_design_pairs(
    design_matrix: QuantDesignMatrixReport,
    *,
    condition_a: str,
    condition_b: str,
    paired_policy: PairedDifferentialPolicy,
) -> tuple[tuple[tuple[str, str, str], ...], tuple[DifferentialBrokenPairEntry, ...]]:
    rows_by_pair_id: dict[str, dict[str, list[str]]] = {}
    broken_pairs: list[DifferentialBrokenPairEntry] = []
    for row in design_matrix.rows:
        if row.condition not in {condition_a, condition_b}:
            continue
        if row.pair_id in (None, ""):
            broken_pairs.append(
                DifferentialBrokenPairEntry(
                    condition_a=condition_a,
                    condition_b=condition_b,
                    pair_id=None,
                    sample_ids_a=(row.sample_id,) if row.condition == condition_a else (),
                    sample_ids_b=(row.sample_id,) if row.condition == condition_b else (),
                    reason_code="missing_pair_id",
                    detail=(
                        f"sample {row.sample_id} in condition {row.condition} is missing "
                        f"{paired_policy.pair_id_field}"
                    ),
                )
            )
            continue
        by_condition = rows_by_pair_id.setdefault(
            row.pair_id,
            {condition_a: [], condition_b: []},
        )
        by_condition[row.condition].append(row.sample_id)
    complete_pairs: list[tuple[str, str, str]] = []
    for pair_id, grouped in rows_by_pair_id.items():
        sample_ids_a = tuple(sorted(grouped[condition_a]))
        sample_ids_b = tuple(sorted(grouped[condition_b]))
        if len(sample_ids_a) != 1 or len(sample_ids_b) != 1:
            if not sample_ids_a or not sample_ids_b:
                reason_code = "unmatched_pair"
                detail = (
                    f"pair {pair_id} does not contain exactly one sample in each "
                    f"of {condition_a} and {condition_b}"
                )
            else:
                reason_code = "duplicated_pair_members"
                detail = (
                    f"pair {pair_id} contains duplicated samples within at least one condition"
                )
            broken_pairs.append(
                DifferentialBrokenPairEntry(
                    condition_a=condition_a,
                    condition_b=condition_b,
                    pair_id=pair_id,
                    sample_ids_a=sample_ids_a,
                    sample_ids_b=sample_ids_b,
                    reason_code=reason_code,
                    detail=detail,
                )
            )
            continue
        complete_pairs.append((pair_id, sample_ids_a[0], sample_ids_b[0]))
    return tuple(sorted(complete_pairs)), tuple(
        sorted(
            broken_pairs,
            key=lambda entry: (
                entry.pair_id or "",
                entry.reason_code,
                entry.sample_ids_a,
                entry.sample_ids_b,
            ),
        )
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


def _paired_t_test_statistics(
    lookup: dict[tuple[str, str], object],
    entity_id: str,
    *,
    complete_design_pairs: tuple[tuple[str, str, str], ...],
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
        paired_a.append(math.log2(cell_a.abundance + 1.0))
        paired_b.append(math.log2(cell_b.abundance + 1.0))
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
    differences = values_b - values_a
    complete_pair_count = int(differences.size)
    mean_a = float(np.mean(values_a))
    mean_b = float(np.mean(values_b))
    estimate = float(np.mean(differences))
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
            "paired test requires at least two complete observed pairs per entity",
        )
    sample_std = float(np.std(differences, ddof=1))
    if sample_std == 0.0 or not math.isfinite(sample_std):
        note = "within-pair differences collapsed to one value so paired uncertainty could not be estimated robustly"
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
            note,
        )
    standard_error = sample_std / math.sqrt(complete_pair_count)
    t_statistic = estimate / standard_error
    p_value = _student_t_two_sided_p_value(
        abs(t_statistic),
        float(complete_pair_count - 1),
    )
    interval_radius = 1.96 * standard_error
    effect_size = estimate / sample_std
    note = None
    if complete_pair_count < len(complete_design_pairs):
        note = (
            f"paired test used {complete_pair_count} complete observed pairs out of "
            f"{len(complete_design_pairs)} complete design pairs"
        )
    elif standard_error > 1.0:
        note = "within-pair uncertainty remains wide relative to the estimated effect"
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
                        if entry.robustness_score is None
                        else entry.robustness_score
                    ),
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
