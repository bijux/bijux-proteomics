# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Review-facing quantification models and durable policy enums."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.quantification.contracts import (
    ImputationReport,
    ImputationSensitivityReport,
    LabelBasedChannelRole,
    LabelFreeProvenanceBundle,
    MissingChannelPolicy,
    MissingnessConditionSummaryReport,
    MissingnessEntitySummaryReport,
    MissingnessIntensityDependenceReport,
    MissingValueSummaryReport,
    MultiConditionDifferentialAbundanceReport,
    MultiplexNormalizationPolicy,
    NormalizationComparisonReport,
    NormalizationMethod,
    QuantDesignMatrixReport,
    QuantDesignModelFitReport,
    ReplicateAndBatchQcReport,
    TimeCourseDifferentialReport,
)
from bijux_proteomics.quantification.missingness.readiness import (
    QuantDecisionReadinessReport,
)
from bijux_proteomics.quantification.provenance.missingness_mechanism_profile import (
    MissingnessMechanismProfileReport,
)
from bijux_proteomics.quantification.statistics.multi_contrast_consistency import (
    MultiContrastConsistencyReport,
)
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.quantification.statistics.statistical_backend import (
        LimmaCompatibleQuantPackage,
        MsstatsCompatibleInputReport,
    )
else:
    LimmaCompatibleQuantPackage = object
    MsstatsCompatibleInputReport = object


class LfqFeaturePeptideProteinProvenanceReport(JsonModel):
    """Review-focused LFQ provenance with feature, peptide, and protein traceability."""

    model_config = ConfigDict(extra="forbid")

    provenance_bundle: LabelFreeProvenanceBundle
    peptide_missingness: MissingValueSummaryReport
    protein_missingness: MissingValueSummaryReport
    feature_entry_count: int = Field(..., ge=0)
    peptide_entry_count: int = Field(..., ge=0)
    protein_entry_count: int = Field(..., ge=0)
    normalization_method: NormalizationMethod
    note: str = Field(..., min_length=1)


class LabelBasedQuantChannelLedgerEntry(JsonModel):
    """Ledger row for one multiplex channel and its review-critical context."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    normalization_group: str = Field(..., min_length=1)
    channel_role: LabelBasedChannelRole
    sample_id: str | None = None
    condition: str | None = None
    missing_channel: bool
    present_in_table: bool
    reagent_lot: str | None = None
    note: str = Field(..., min_length=1)


class LabelBasedQuantChannelLedgerReport(JsonModel):
    """Channel ledger for multiplex quantification review and handoff."""

    model_config = ConfigDict(extra="forbid")

    missing_channel_policy: MissingChannelPolicy
    entries: tuple[LabelBasedQuantChannelLedgerEntry, ...] = Field(
        default_factory=tuple
    )
    missing_channel_count: int = Field(..., ge=0)


class MultiplexChannelBalanceDiagnosticsReport(JsonModel):
    """Expanded multiplex balance diagnostics with carrier and batch caveats."""

    model_config = ConfigDict(extra="forbid")

    policy: MultiplexNormalizationPolicy
    total_channel_count: int = Field(..., ge=0)
    flagged_imbalance_count: int = Field(..., ge=0)
    carrier_effect_channel_count: int = Field(..., ge=0)
    missing_channel_count: int = Field(..., ge=0)
    batch_caveat_count: int = Field(..., ge=0)
    caveats: tuple[str, ...] = Field(default_factory=tuple)


class QuantNormalizationPolicyKind(StrEnum):
    """Normalization policy families compared by the quant review matrix."""

    NONE = "none"
    TOTAL = "total"
    MEDIAN = "median"
    QUANTILE = "quantile"
    LOG2_MEDIAN_CENTERING = "log2_median_centering"
    VSN_LIKE = "vsn_like"
    REFERENCE_CHANNEL = "reference_channel"


class NormalizationPolicyComparisonEntry(JsonModel):
    """One normalization policy row with support status and balance metrics."""

    model_config = ConfigDict(extra="forbid")

    policy: QuantNormalizationPolicyKind
    supported: bool
    mapped_method: NormalizationMethod | None = None
    balance_score: float | None = Field(default=None, ge=0.0)
    note: str = Field(..., min_length=1)


class NormalizationPolicyComparisonMatrixReport(JsonModel):
    """Explicit comparison matrix across normalization policy families."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[NormalizationPolicyComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    recommended_supported_policy: QuantNormalizationPolicyKind | None = None


class ProteinRollupStrategyKind(StrEnum):
    """Protein rollup strategies compared by the quant analysis surface."""

    SUM = "sum"
    TOP_N = "top_n"
    MEDIAN_POLISH_LIKE = "median_polish_like"
    RAZOR_ONLY = "razor_only"
    SHARED_EXCLUDED = "shared_excluded"
    EVIDENCE_WEIGHTED = "evidence_weighted"


class ProteinRollupStrategyValue(JsonModel):
    """One strategy-specific abundance estimate for a protein/sample pair."""

    model_config = ConfigDict(extra="forbid")

    strategy: ProteinRollupStrategyKind
    abundance: float | None = Field(default=None, ge=0.0)


class ProteinRollupStrategyComparisonEntry(JsonModel):
    """Comparison row for protein/sample abundance across rollup strategies."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    strategy_values: tuple[ProteinRollupStrategyValue, ...] = Field(
        default_factory=tuple
    )
    max_strategy_difference: float = Field(..., ge=0.0)


class ProteinRollupStrategyComparisonReport(JsonModel):
    """Comparison report over multiple protein rollup strategies."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ProteinRollupStrategyComparisonEntry, ...] = Field(
        default_factory=tuple
    )


class DifferentialAbundanceDesignIssue(JsonModel):
    """One design-validation issue for differential abundance configuration."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    severity: str = Field(..., pattern="^(error|warning)$")


class DifferentialAbundanceDesignValidationReport(JsonModel):
    """Validation report over contrasts, covariates, blocking, and replicate support."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    condition_replicates: dict[str, int] = Field(default_factory=dict)
    issues: tuple[DifferentialAbundanceDesignIssue, ...] = Field(default_factory=tuple)


class MultipleTestingScopeBenchmarkStatus(StrEnum):
    """Support posture for one multiple-testing scope benchmark."""

    REFUSED = "refused"
    SUPPORTED = "supported"


class MultipleTestingScopeBenchmarkEntry(JsonModel):
    """Strict benchmark result for one multiple-testing scope."""

    model_config = ConfigDict(extra="forbid")

    scope: str = Field(..., min_length=1)
    status: MultipleTestingScopeBenchmarkStatus
    adjusted_p_values_complete: bool
    adjusted_p_values_monotonic: bool
    evidence_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class MultipleTestingScopeBenchmarkReport(JsonModel):
    """Benchmark report over supported and refused multiple-testing scopes."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[MultipleTestingScopeBenchmarkEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class EffectSizeFirstDaEntry(JsonModel):
    """Differential abundance entry ranked primarily by effect size magnitude."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    log2_fold_change: float
    effect_size_cohens_d: float | None = None
    standard_error: float | None = Field(default=None, ge=0.0)
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    observations_a: int = Field(..., ge=0)
    observations_b: int = Field(..., ge=0)
    uncertainty_note: str | None = None
    caveats: tuple[str, ...] = Field(default_factory=tuple)


class EffectSizeFirstDaReport(JsonModel):
    """Effect-size-first differential abundance report with integrated caveats."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    entries: tuple[EffectSizeFirstDaEntry, ...] = Field(default_factory=tuple)
    global_caveats: tuple[str, ...] = Field(default_factory=tuple)


class QuantReviewBundle(JsonModel):
    """Integrated quant review bundle with evidence and caveat context."""

    model_config = ConfigDict(extra="forbid")

    artifact_bundle_hash: str = Field(..., min_length=64, max_length=64)
    lfq_provenance: LfqFeaturePeptideProteinProvenanceReport
    normalization_comparison: NormalizationComparisonReport
    imputation_report: ImputationReport
    imputation_sensitivity: ImputationSensitivityReport | None = None
    normalization_matrix: NormalizationPolicyComparisonMatrixReport
    rollup_strategy_comparison: ProteinRollupStrategyComparisonReport
    limma_compatible_package: LimmaCompatibleQuantPackage
    msstats_compatible_input_report: MsstatsCompatibleInputReport
    design_matrix_report: QuantDesignMatrixReport
    design_model_fit_report: QuantDesignModelFitReport
    effect_size_da_report: EffectSizeFirstDaReport | None = None
    differential_abundance_multi_condition_report: (
        MultiConditionDifferentialAbundanceReport | None
    ) = None
    multi_contrast_consistency_report: MultiContrastConsistencyReport | None = None
    time_course_differential_report: TimeCourseDifferentialReport | None = None
    missingness_profile: MissingnessMechanismProfileReport
    missingness_entity_summary: MissingnessEntitySummaryReport
    missingness_condition_summary: MissingnessConditionSummaryReport
    missingness_intensity_dependence: MissingnessIntensityDependenceReport
    qc_report: ReplicateAndBatchQcReport
    decision_readiness: QuantDecisionReadinessReport
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    caveats: tuple[str, ...] = Field(default_factory=tuple)


__all__ = [
    "DifferentialAbundanceDesignIssue",
    "DifferentialAbundanceDesignValidationReport",
    "EffectSizeFirstDaEntry",
    "EffectSizeFirstDaReport",
    "LabelBasedQuantChannelLedgerEntry",
    "LabelBasedQuantChannelLedgerReport",
    "LfqFeaturePeptideProteinProvenanceReport",
    "MultipleTestingScopeBenchmarkEntry",
    "MultipleTestingScopeBenchmarkReport",
    "MultipleTestingScopeBenchmarkStatus",
    "MultiplexChannelBalanceDiagnosticsReport",
    "NormalizationPolicyComparisonEntry",
    "NormalizationPolicyComparisonMatrixReport",
    "ProteinRollupStrategyComparisonEntry",
    "ProteinRollupStrategyComparisonReport",
    "ProteinRollupStrategyKind",
    "ProteinRollupStrategyValue",
    "QuantNormalizationPolicyKind",
    "QuantReviewBundle",
]
