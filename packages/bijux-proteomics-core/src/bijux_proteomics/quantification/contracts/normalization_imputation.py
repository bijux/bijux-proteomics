# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Label-free quantification and differential abundance contracts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    pass


from .input_models import (
    ImputationMethod,
    MissingValueKind,
    NormalizationMethod,
    QuantEntityLevel,
)
from .matrix_models import LabelFreeQuantTable

class NormalizationStrategySummaryEntry(JsonModel):
    """One normalization method summarized across sample-balance metrics."""

    model_config = ConfigDict(extra="forbid")

    method: NormalizationMethod
    total_abundance_cv: float = Field(..., ge=0.0)
    median_abundance_cv: float = Field(..., ge=0.0)
    interquartile_range_cv: float = Field(..., ge=0.0)
    balance_score: float = Field(..., ge=0.0)

class NormalizationStrategyComparisonReport(JsonModel):
    """Explicit comparison of normalization methods on one quant table."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    entries: tuple[NormalizationStrategySummaryEntry, ...] = Field(
        default_factory=tuple
    )
    recommended_method: NormalizationMethod

class NormalizationSampleSnapshot(JsonModel):
    """Per-sample totals, medians, and spread for a quant table snapshot."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    total_abundance: float = Field(..., ge=0.0)
    median_abundance: float = Field(..., ge=0.0)
    interquartile_range: float = Field(..., ge=0.0)

class NormalizationDistributionSnapshot(JsonModel):
    """Per-sample distribution summary before or after normalization."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    observed_count: int = Field(..., ge=0)
    zero_count: int = Field(..., ge=0)
    negative_count: int = Field(..., ge=0)
    min_abundance: float | None = Field(default=None, ge=0.0)
    lower_quartile_abundance: float | None = Field(default=None, ge=0.0)
    median_abundance: float | None = Field(default=None, ge=0.0)
    upper_quartile_abundance: float | None = Field(default=None, ge=0.0)
    max_abundance: float | None = Field(default=None, ge=0.0)

class NormalizationLogTransformPreparation(JsonModel):
    """Explicit per-sample handling of nonpositive values before log transform."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    zero_count: int = Field(..., ge=0)
    negative_count: int = Field(..., ge=0)
    positive_count: int = Field(..., ge=0)
    handling_strategy: str = Field(..., min_length=1)
    pseudocount: float | None = Field(default=None, gt=0.0)

class NormalizationComparisonReport(JsonModel):
    """Before/after report for one normalization operation."""

    model_config = ConfigDict(extra="forbid")

    method: NormalizationMethod
    normalization_factors: dict[str, float] = Field(default_factory=dict)
    before: tuple[NormalizationSampleSnapshot, ...] = Field(default_factory=tuple)
    after: tuple[NormalizationSampleSnapshot, ...] = Field(default_factory=tuple)
    before_distributions: tuple[NormalizationDistributionSnapshot, ...] = Field(
        default_factory=tuple
    )
    after_distributions: tuple[NormalizationDistributionSnapshot, ...] = Field(
        default_factory=tuple
    )
    log_transform_preparation: tuple[NormalizationLogTransformPreparation, ...] = (
        Field(default_factory=tuple)
    )

class ImputationEntry(JsonModel):
    """One imputed abundance with explicit source missingness context."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    original_missing_value_kind: MissingValueKind
    imputed_abundance: float = Field(..., ge=0.0)
    neighbor_entity_ids: tuple[str, ...] = Field(default_factory=tuple)
    donor_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    reference_group: str | None = None
    strategy: str = Field(..., min_length=1)

class ImputationReport(JsonModel):
    """Explicit ledger of values introduced by one imputation method."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    method: ImputationMethod
    entries: tuple[ImputationEntry, ...] = Field(default_factory=tuple)
    imputed_value_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)

class ImputationSensitivityEntry(JsonModel):
    """Downstream DA summary for one imputation policy."""

    model_config = ConfigDict(extra="forbid")

    method: ImputationMethod
    supported: bool
    imputed_value_count: int = Field(..., ge=0)
    significant_entity_count: int = Field(default=0, ge=0)
    top_entity_id: str | None = None
    top_entity_direction: str | None = None
    top_entity_effect_size: float | None = None
    note: str = Field(..., min_length=1)

class ImputationSensitivityOverlapEntry(JsonModel):
    """Pairwise overlap of significant hits across imputation methods."""

    model_config = ConfigDict(extra="forbid")

    method_a: ImputationMethod
    method_b: ImputationMethod
    significant_entity_count_a: int = Field(..., ge=0)
    significant_entity_count_b: int = Field(..., ge=0)
    overlapping_significant_entity_count: int = Field(..., ge=0)
    method_a_only_count: int = Field(..., ge=0)
    method_b_only_count: int = Field(..., ge=0)
    jaccard_index: float = Field(..., ge=0.0, le=1.0)

class ImputationSensitivityChangedSignificanceEntry(JsonModel):
    """One entity whose significance changes between two imputation methods."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    reference_method: ImputationMethod
    compared_method: ImputationMethod
    reference_significant: bool
    compared_significant: bool
    reference_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    compared_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    reference_log2_fold_change: float | None = None
    compared_log2_fold_change: float | None = None
    note: str = Field(..., min_length=1)

class ImputationDependentHitEntry(JsonModel):
    """One entity that becomes significant only after imputation."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    baseline_method: ImputationMethod
    imputation_methods: tuple[ImputationMethod, ...] = Field(default_factory=tuple)
    baseline_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    best_imputation_method: ImputationMethod
    best_imputation_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    best_imputation_log2_fold_change: float | None = None
    note: str = Field(..., min_length=1)

class ImputationSensitivityReport(JsonModel):
    """Comparison of downstream DA behavior across imputation methods."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    baseline_method: ImputationMethod = ImputationMethod.NONE
    significance_threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    entries: tuple[ImputationSensitivityEntry, ...] = Field(default_factory=tuple)
    overlap_entries: tuple[ImputationSensitivityOverlapEntry, ...] = Field(
        default_factory=tuple
    )
    changed_significance_entries: tuple[
        ImputationSensitivityChangedSignificanceEntry, ...
    ] = Field(default_factory=tuple)
    imputation_dependent_hits: tuple[ImputationDependentHitEntry, ...] = Field(
        default_factory=tuple
    )
    primary_narrative_changed: bool

def build_normalization_comparison_report(
    before: LabelFreeQuantTable,
    after: LabelFreeQuantTable,
) -> NormalizationComparisonReport:
    """Build a before/after normalization summary over sample totals and spread."""
    from bijux_proteomics.quantification.normalization import (
        build_normalization_comparison_report as _implementation,
    )

    return _implementation(before, after)

def build_normalization_strategy_comparison_report(
    table: LabelFreeQuantTable,
    *,
    methods: tuple[NormalizationMethod, ...] = (
        NormalizationMethod.NONE,
        NormalizationMethod.TIC,
        NormalizationMethod.MEDIAN,
        NormalizationMethod.QUANTILE,
        NormalizationMethod.VSN_LIKE,
    ),
) -> NormalizationStrategyComparisonReport:
    """Compare normalization methods using stable sample-balance summary metrics."""
    from bijux_proteomics.quantification.normalization import (
        build_normalization_strategy_comparison_report as _implementation,
    )

    return _implementation(table, methods=methods)

def normalize_label_free_table(
    table: LabelFreeQuantTable,
    *,
    method: NormalizationMethod = NormalizationMethod.MEDIAN,
) -> LabelFreeQuantTable:
    """Normalize a label-free intensity table with one stable baseline method."""
    from bijux_proteomics.quantification.normalization import (
        normalize_label_free_table as _implementation,
    )

    return _implementation(table, method=method)
