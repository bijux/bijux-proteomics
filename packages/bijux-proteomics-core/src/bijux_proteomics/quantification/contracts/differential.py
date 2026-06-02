# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Label-free quantification and differential abundance contracts."""

from __future__ import annotations

from enum import StrEnum
import math
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
)
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.study.sample_run_identity import SampleRunAnalysisPolicy


from .input_models import (
    ImputationMethod,
    NormalizationMethod,
    QuantAssessmentDisposition,
    QuantEntityLevel,
)
from .design import QuantDesignMatrixReport
from .matrix_models import LabelFreeQuantTable
from .study_qc import SampleReliabilityWeightReport

class DifferentialImputationSignificanceChangeReason(StrEnum):
    """How one differential result changes between no-impute and imputed analysis."""

    NOT_IMPUTED = "not_imputed"
    STABLE_SIGNIFICANT = "stable_significant"
    STABLE_NON_SIGNIFICANT = "stable_non_significant"
    SIGNIFICANT_ONLY_AFTER_IMPUTATION = "significant_only_after_imputation"
    SIGNIFICANCE_LOST_AFTER_IMPUTATION = "significance_lost_after_imputation"

class DifferentialReplicatePolicy(JsonModel):
    """Minimum replicate policy for differential abundance comparisons."""

    model_config = ConfigDict(extra="forbid")

    min_replicates_per_condition: int = Field(default=2, ge=1)
    disposition: QuantAssessmentDisposition = QuantAssessmentDisposition.ENFORCED

class DifferentialAbundanceTestType(StrEnum):
    """Supported inferential engines for differential abundance results."""

    WELCH_T_TEST = "welch_t_test"
    LINEAR_MODEL_CONTRAST = "linear_model_contrast"
    PAIRED_T_TEST = "paired_t_test"

class BrokenPairDisposition(StrEnum):
    """Policies for broken design pairs during paired differential testing."""

    EXCLUDE = "exclude"
    BLOCK = "block"

class PairedDifferentialPolicy(JsonModel):
    """Pair completeness policy for paired differential abundance testing."""

    model_config = ConfigDict(extra="forbid")

    pair_id_field: str = Field(default="pair_id", min_length=1)
    minimum_complete_pairs: int = Field(default=2, ge=1)
    broken_pair_disposition: BrokenPairDisposition = BrokenPairDisposition.EXCLUDE

class DifferentialBrokenPairEntry(JsonModel):
    """One design pair excluded or blocked during paired testing."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    pair_id: str | None = None
    sample_ids_a: tuple[str, ...] = Field(default_factory=tuple)
    sample_ids_b: tuple[str, ...] = Field(default_factory=tuple)
    reason_code: str = Field(..., min_length=1)
    detail: str = Field(..., min_length=1)

class DifferentialAbundanceAssumptionReport(JsonModel):
    """Test and correction assumptions carried by a differential abundance report."""

    model_config = ConfigDict(extra="forbid")

    test_type: DifferentialAbundanceTestType
    variance_assumption: str = Field(..., min_length=1)
    multiple_testing_scope: str = Field(..., min_length=1)
    replicate_policy: DifferentialReplicatePolicy
    sample_weighting: str = Field(default="unweighted", min_length=1)
    contrast_name: str | None = None
    paired_policy: PairedDifferentialPolicy | None = None

class DifferentialResultRobustnessQcStatus(StrEnum):
    """Stable QC severity carried onto differential-result rows."""

    PASSED = "pass"
    CAUTION = "caution"
    FAIL = "fail"

class DifferentialResultRobustnessReasonCode(StrEnum):
    """Stable downgrade reasons for one differential-result robustness score."""

    LOW_EFFECT_SIZE = "low_effect_size"
    ELEVATED_FDR = "elevated_fdr"
    HIGH_MISSINGNESS = "high_missingness"
    IMPUTATION_HEAVY = "imputation_heavy"
    IMPUTATION_DEPENDENT_SIGNIFICANCE = "imputation_dependent_significance"
    LOW_PEPTIDE_SUPPORT = "low_peptide_support"
    REPLICATE_INCONSISTENCY = "replicate_inconsistency"
    CAUTION_QC = "caution_qc"
    FAILED_QC = "failed_qc"

class DifferentialAbundanceEntry(JsonModel):
    """One entity-level two-condition differential abundance result."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    observations_a: int = Field(..., ge=0)
    observations_b: int = Field(..., ge=0)
    complete_pair_count: int = Field(default=0, ge=0)
    zero_values_a: int = Field(default=0, ge=0)
    zero_values_b: int = Field(default=0, ge=0)
    not_observed_values_a: int = Field(default=0, ge=0)
    not_observed_values_b: int = Field(default=0, ge=0)
    filtered_values_a: int = Field(default=0, ge=0)
    filtered_values_b: int = Field(default=0, ge=0)
    mean_log2_abundance_a: float
    mean_log2_abundance_b: float
    log2_fold_change: float
    p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    standard_error: float | None = Field(default=None, ge=0.0)
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    effect_size_cohens_d: float | None = None
    no_impute_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    no_impute_log2_fold_change: float | None = None
    imputed_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    imputed_log2_fold_change: float | None = None
    imputation_significance_change_reason: (
        DifferentialImputationSignificanceChangeReason | None
    ) = None
    imputation_dependent_hit: bool = False
    robustness_score: float | None = Field(default=None, ge=0.0, le=1.0)
    robustness_qc_status: DifferentialResultRobustnessQcStatus | None = None
    robustness_reason_codes: tuple[DifferentialResultRobustnessReasonCode, ...] = (
        Field(default_factory=tuple)
    )
    robustness_note: str | None = None
    uncertainty_note: str | None = None

class DifferentialAbundanceReport(JsonModel):
    """Stable two-condition differential abundance report."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    normalization_method: NormalizationMethod
    imputation_method: ImputationMethod = ImputationMethod.NONE
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    contrast_name: str | None = None
    replicate_policy: DifferentialReplicatePolicy = Field(
        default_factory=DifferentialReplicatePolicy
    )
    assumption_report: DifferentialAbundanceAssumptionReport
    entries: tuple[DifferentialAbundanceEntry, ...] = Field(default_factory=tuple)
    broken_pairs: tuple[DifferentialBrokenPairEntry, ...] = Field(default_factory=tuple)

class DifferentialAbundanceContrast(JsonModel):
    """One named condition contrast preserved inside a DA collection."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    contrast_name: str | None = None

class MultiConditionDifferentialAbundanceReport(JsonModel):
    """Pairwise differential-abundance collection over a multi-condition study."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    normalization_method: NormalizationMethod
    imputation_method: ImputationMethod = ImputationMethod.NONE
    condition_count: int = Field(..., ge=2)
    replicate_policy: DifferentialReplicatePolicy = Field(
        default_factory=DifferentialReplicatePolicy
    )
    contrasts: tuple[DifferentialAbundanceContrast, ...] = Field(default_factory=tuple)
    reports: tuple[DifferentialAbundanceReport, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)

class TimeCourseTestingPolicy(JsonModel):
    """Ordered-timepoint policy for one time-course differential analysis."""

    model_config = ConfigDict(extra="forbid")

    timepoint_field: str = Field(default="timepoint", min_length=1)
    ordered_timepoints: tuple[str, ...] = Field(default_factory=tuple)
    batch_field: str | None = None
    pairing_field: str | None = None
    covariate_fields: tuple[str, ...] = Field(default_factory=tuple)

class TimeCourseDifferentialEntry(JsonModel):
    """One entity-level time-course effect row for one condition."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    reference_condition: str = Field(..., min_length=1)
    observed_sample_count: int = Field(..., ge=0)
    observed_timepoint_count: int = Field(..., ge=0)
    slope_per_timepoint: float
    slope_standard_error: float | None = Field(default=None, ge=0.0)
    slope_confidence_interval_low: float | None = None
    slope_confidence_interval_high: float | None = None
    time_effect_p_value: float = Field(..., ge=0.0, le=1.0)
    time_effect_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    interaction_effect: float | None = None
    interaction_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    interaction_adjusted_p_value: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    no_impute_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    no_impute_log2_fold_change: float | None = None
    imputed_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    imputed_log2_fold_change: float | None = None
    imputation_significance_change_reason: (
        DifferentialImputationSignificanceChangeReason | None
    ) = None
    imputation_dependent_hit: bool = False
    robustness_score: float | None = Field(default=None, ge=0.0, le=1.0)
    robustness_qc_status: DifferentialResultRobustnessQcStatus | None = None
    robustness_reason_codes: tuple[DifferentialResultRobustnessReasonCode, ...] = (
        Field(default_factory=tuple)
    )
    robustness_note: str | None = None
    note: str | None = None

class TimeCourseDifferentialReport(JsonModel):
    """Time-course differential report over ordered study timepoints."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    normalization_method: NormalizationMethod
    imputation_method: ImputationMethod = ImputationMethod.NONE
    reference_condition: str = Field(..., min_length=1)
    condition_count: int = Field(..., ge=1)
    ordered_timepoints: tuple[str, ...] = Field(default_factory=tuple)
    timepoint_positions: dict[str, float] = Field(default_factory=dict)
    policy: TimeCourseTestingPolicy
    entries: tuple[TimeCourseDifferentialEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)

def _betacf(a: float, b: float, x: float) -> float:
    max_iter = 200
    eps = 3.0e-7
    fpmin = 1.0e-30
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for step in range(1, max_iter + 1):
        step_twice = 2 * step
        aa = step * (b - step) * x / ((qam + step_twice) * (a + step_twice))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(a + step) * (qab + step) * x / ((a + step_twice) * (qap + step_twice))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h

def _regularized_beta(x: float, a: float, b: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    log_beta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(log_beta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b

def _student_t_two_sided_p_value(
    t_statistic: float, degrees_of_freedom: float
) -> float:
    if (
        not math.isfinite(t_statistic)
        or not math.isfinite(degrees_of_freedom)
        or degrees_of_freedom <= 0
    ):
        return 1.0
    x = degrees_of_freedom / (degrees_of_freedom + t_statistic * t_statistic)
    return min(max(_regularized_beta(x, degrees_of_freedom / 2.0, 0.5), 0.0), 1.0)

def _welch_t_test(values_a: np.ndarray, values_b: np.ndarray) -> tuple[float, float]:
    if values_a.size < 2 or values_b.size < 2:
        return 0.0, 1.0
    mean_a = float(np.mean(values_a))
    mean_b = float(np.mean(values_b))
    var_a = float(np.var(values_a, ddof=1))
    var_b = float(np.var(values_b, ddof=1))
    if var_a == 0.0 and var_b == 0.0:
        return mean_b - mean_a, 1.0
    denominator = math.sqrt((var_a / values_a.size) + (var_b / values_b.size))
    if denominator == 0.0:
        return mean_b - mean_a, 1.0
    t_statistic = (mean_b - mean_a) / denominator
    numerator = (var_a / values_a.size + var_b / values_b.size) ** 2
    denominator_df = ((var_a / values_a.size) ** 2) / (values_a.size - 1) + (
        (var_b / values_b.size) ** 2
    ) / (values_b.size - 1)
    if denominator_df == 0.0:
        return mean_b - mean_a, 1.0
    degrees_of_freedom = numerator / denominator_df
    return mean_b - mean_a, _student_t_two_sided_p_value(
        abs(t_statistic), degrees_of_freedom
    )

def _effect_size_and_uncertainty(
    values_a: np.ndarray,
    values_b: np.ndarray,
    log2_fold_change: float,
) -> tuple[float | None, float | None, float | None, float | None, str | None]:
    if values_a.size < 2 or values_b.size < 2:
        return (
            None,
            None,
            None,
            None,
            "confidence intervals and effect sizes require at least two observations per condition",
        )
    variance_a = float(np.var(values_a, ddof=1))
    variance_b = float(np.var(values_b, ddof=1))
    standard_error = math.sqrt(
        variance_a / float(values_a.size) + variance_b / float(values_b.size)
    )
    interval_radius = 1.96 * standard_error
    pooled_variance_numerator = (values_a.size - 1) * variance_a + (
        values_b.size - 1
    ) * variance_b
    pooled_variance_denominator = values_a.size + values_b.size - 2
    pooled_sd = math.sqrt(pooled_variance_numerator / pooled_variance_denominator)
    cohens_d = (log2_fold_change / pooled_sd) if pooled_sd > 0 else None
    note = None
    if standard_error > 1.0:
        note = "uncertainty remains wide relative to the estimated fold change"
    return (
        standard_error,
        log2_fold_change - interval_radius,
        log2_fold_change + interval_radius,
        cohens_d,
        note,
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
    sample_run_policy: "SampleRunAnalysisPolicy" = None,
) -> DifferentialAbundanceReport:
    """Run one owned two-condition differential abundance engine."""
    from bijux_proteomics.quantification.differential_abundance import (
        build_differential_abundance_report as _implementation,
    )
    from bijux_proteomics.study.sample_run_identity import SampleRunAnalysisPolicy

    resolved_sample_run_policy = (
        sample_run_policy or SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS
    )

    return _implementation(
        table,
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
        test_type=test_type,
        design_matrix=design_matrix,
        contrast_name=contrast_name,
        paired_policy=paired_policy,
        replicate_policy=replicate_policy,
        sample_weights_report=sample_weights_report,
        sample_run_policy=resolved_sample_run_policy,
    )

def apply_benjamini_hochberg(
    report: DifferentialAbundanceReport,
) -> DifferentialAbundanceReport:
    """Apply Benjamini-Hochberg correction to one differential report."""
    from bijux_proteomics.quantification.differential_abundance import (
        apply_benjamini_hochberg as _implementation,
    )

    return _implementation(report)

def render_differential_abundance_tsv(
    report: DifferentialAbundanceReport,
) -> str:
    """Render one differential-abundance report as a stable TSV table."""
    from bijux_proteomics.quantification.differential_abundance import (
        render_differential_abundance_tsv as _implementation,
    )

    return _implementation(report)

def render_differential_broken_pairs_tsv(
    report: DifferentialAbundanceReport,
) -> str:
    """Render one broken-pair ledger for paired differential testing."""
    from bijux_proteomics.quantification.differential_abundance import (
        render_differential_broken_pairs_tsv as _implementation,
    )

    return _implementation(report)

def export_differential_broken_pairs_tsv(
    report: DifferentialAbundanceReport,
    path: Path,
) -> None:
    """Write one broken-pair ledger to a stable TSV artifact."""
    from bijux_proteomics.quantification.differential_abundance import (
        export_differential_broken_pairs_tsv as _implementation,
    )

    _implementation(report, path)

def export_differential_abundance_tsv(
    report: DifferentialAbundanceReport,
    path: Path,
) -> None:
    """Write one differential-abundance report to a stable TSV artifact."""
    from bijux_proteomics.quantification.differential_abundance import (
        export_differential_abundance_tsv as _implementation,
    )

    _implementation(report, path)

def render_multi_condition_differential_abundance_tsv(
    report: MultiConditionDifferentialAbundanceReport,
) -> str:
    """Render a multi-condition DA collection as one flattened TSV table."""
    from bijux_proteomics.quantification.differential_abundance import (
        render_multi_condition_differential_abundance_tsv as _implementation,
    )

    return _implementation(report)

def export_multi_condition_differential_abundance_tsv(
    report: MultiConditionDifferentialAbundanceReport,
    path: Path,
) -> None:
    """Write a multi-condition DA collection to one flattened TSV artifact."""
    from bijux_proteomics.quantification.differential_abundance import (
        export_multi_condition_differential_abundance_tsv as _implementation,
    )

    _implementation(report, path)

def build_time_course_differential_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    policy: TimeCourseTestingPolicy | None = None,
    sample_run_policy: "SampleRunAnalysisPolicy" = None,
) -> TimeCourseDifferentialReport:
    """Build one ordered time-course differential report over a quant table."""
    from bijux_proteomics.quantification.time_course_differential import (
        build_time_course_differential_report as _implementation,
    )
    from bijux_proteomics.study.sample_run_identity import SampleRunAnalysisPolicy

    resolved_sample_run_policy = (
        sample_run_policy or SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS
    )
    return _implementation(
        table,
        design_entries,
        policy=policy,
        sample_run_policy=resolved_sample_run_policy,
    )

def render_time_course_differential_tsv(
    report: TimeCourseDifferentialReport,
) -> str:
    """Render one time-course differential report as a stable TSV table."""
    from bijux_proteomics.quantification.time_course_differential import (
        render_time_course_differential_tsv as _implementation,
    )

    return _implementation(report)

def export_time_course_differential_tsv(
    report: TimeCourseDifferentialReport,
    path: Path,
) -> None:
    """Write one time-course differential report to a stable TSV artifact."""
    from bijux_proteomics.quantification.time_course_differential import (
        export_time_course_differential_tsv as _implementation,
    )

    _implementation(report, path)
