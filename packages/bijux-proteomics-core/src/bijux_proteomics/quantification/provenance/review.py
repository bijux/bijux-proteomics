# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Quantification and QC capability surfaces."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    DifferentialAbundanceTestType,
    ImputationMethod,
    ImputationReport,
    ImputationSensitivityReport,
    LabelBasedChannelRole,
    LabelBasedQuantPolicy,
    LabelFreeProvenanceBundle,
    LabelFreeQuantTable,
    MissingChannelPolicy,
    MissingnessConditionSummaryReport,
    MissingnessEntitySummaryReport,
    MissingnessIntensityDependenceReport,
    MissingValueSummaryReport,
    Ms1FeatureRecord,
    MultiConditionDifferentialAbundanceReport,
    MultiplexNormalizationPolicy,
    NormalizationComparisonReport,
    NormalizationMethod,
    PairedDifferentialPolicy,
    QuantDesignMatrixReport,
    QuantDesignModelFitReport,
    QuantEntityLevel,
    QuantRollupMethod,
    ReplicateAndBatchQcReport,
    TimeCourseDifferentialReport,
    TimeCourseTestingPolicy,
    apply_benjamini_hochberg,
    build_differential_abundance_report,
    build_imputation_report,
    build_imputation_sensitivity_report,
    build_label_based_quant_bundle,
    build_label_free_intensity_table,
    build_label_free_provenance_bundle,
    build_missingness_condition_summary_report,
    build_missingness_entity_summary_report,
    build_missingness_intensity_dependence_report,
    build_multi_condition_differential_abundance_report,
    build_multiplex_channel_balance_report,
    build_normalization_comparison_report,
    build_normalization_strategy_comparison_report,
    build_quant_artifact_bundle,
    build_quant_design_matrix_report,
    build_time_course_differential_report,
    fit_quant_design_matrix_model,
    impute_label_free_table,
    normalize_label_free_table,
    summarize_missing_values,
)
from bijux_proteomics.quantification.missingness.readiness import (
    QuantDecisionReadinessReport,
    build_quant_decision_readiness_report,
)
from bijux_proteomics.quantification.provenance.missingness_mechanism_profile import (
    MissingnessMechanismKind as MissingnessMechanismKind,
)
from bijux_proteomics.quantification.provenance.missingness_mechanism_profile import (
    MissingnessMechanismProfileReport as MissingnessMechanismProfileReport,
)
from bijux_proteomics.quantification.provenance.missingness_mechanism_profile import (
    build_missingness_mechanism_profile_report as build_missingness_mechanism_profile_report,
)
from bijux_proteomics.quantification.provenance.replicate_qc import (
    build_replicate_and_batch_qc_report,
)
from bijux_proteomics.quantification.statistics.multi_contrast_consistency import (
    MultiContrastConsistencyReport,
    build_multi_contrast_consistency_report,
)
from bijux_proteomics.study.replicate_structure import (
    count_effective_statistical_units_by_condition,
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


def build_lfq_feature_peptide_protein_provenance_report(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    top_n: int = 3,
) -> LfqFeaturePeptideProteinProvenanceReport:
    """Build LFQ provenance preserving feature, peptide, protein, and missingness context."""
    bundle = build_label_free_provenance_bundle(
        records,
        aggregation_method=aggregation_method,
        normalization_method=normalization_method,
        top_n=top_n,
    )
    peptide_table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    protein_table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    if normalization_method is not NormalizationMethod.NONE:
        peptide_table = normalize_label_free_table(
            peptide_table, method=normalization_method
        )
        protein_table = normalize_label_free_table(
            protein_table, method=normalization_method
        )

    peptide_missingness = summarize_missing_values(peptide_table)
    protein_missingness = summarize_missing_values(protein_table)
    return LfqFeaturePeptideProteinProvenanceReport(
        provenance_bundle=bundle,
        peptide_missingness=peptide_missingness,
        protein_missingness=protein_missingness,
        feature_entry_count=len(bundle.feature_entries),
        peptide_entry_count=len(bundle.peptide_entries),
        protein_entry_count=len(bundle.protein_entries),
        normalization_method=normalization_method,
        note=(
            "lfq provenance preserves feature-to-peptide-to-protein evidence while retaining missingness and normalization context"
        ),
    )


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


def build_label_based_quant_channel_ledger(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    policy: LabelBasedQuantPolicy,
    reagent_lot_by_channel: dict[tuple[str, str], str] | None = None,
) -> LabelBasedQuantChannelLedgerReport:
    """Build a channel-level ledger with role, missingness, and lot provenance."""
    lots = reagent_lot_by_channel or {}
    bundle = build_label_based_quant_bundle(
        table,
        design_entries=design_entries,
        policy=policy,
    )
    entries: list[LabelBasedQuantChannelLedgerEntry] = []
    for channel in bundle.channels:
        key = (channel.multiplex_group, channel.multiplex_channel)
        entries.append(
            LabelBasedQuantChannelLedgerEntry(
                multiplex_group=channel.multiplex_group,
                multiplex_channel=channel.multiplex_channel,
                normalization_group=channel.multiplex_group,
                channel_role=channel.channel_role,
                sample_id=channel.sample_id,
                condition=channel.condition,
                missing_channel=not channel.present_in_table,
                present_in_table=channel.present_in_table,
                reagent_lot=lots.get(key),
                note=channel.note,
            )
        )
    for missing in bundle.missing_channels:
        key = (missing.multiplex_group, missing.multiplex_channel)
        entries.append(
            LabelBasedQuantChannelLedgerEntry(
                multiplex_group=missing.multiplex_group,
                multiplex_channel=missing.multiplex_channel,
                normalization_group=missing.multiplex_group,
                channel_role=missing.expected_role,
                sample_id=None,
                condition=None,
                missing_channel=True,
                present_in_table=False,
                reagent_lot=lots.get(key),
                note=missing.message,
            )
        )
    deduped = {
        (entry.multiplex_group, entry.multiplex_channel, entry.sample_id): entry
        for entry in entries
    }
    ordered = tuple(
        sorted(
            deduped.values(),
            key=lambda entry: (
                entry.multiplex_group,
                entry.multiplex_channel,
                entry.sample_id or "",
            ),
        )
    )
    return LabelBasedQuantChannelLedgerReport(
        missing_channel_policy=policy.missing_channel_policy,
        entries=ordered,
        missing_channel_count=sum(1 for entry in ordered if entry.missing_channel),
    )


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


def build_multiplex_channel_balance_diagnostics_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    quant_policy: LabelBasedQuantPolicy,
    normalization_policy: MultiplexNormalizationPolicy | None = None,
) -> MultiplexChannelBalanceDiagnosticsReport:
    """Build multiplex balance diagnostics with role-aware and batch-aware caveats."""
    active_norm_policy = normalization_policy or MultiplexNormalizationPolicy()
    balance = build_multiplex_channel_balance_report(
        table,
        design_entries=design_entries,
        policy=active_norm_policy,
    )
    ledger = build_label_based_quant_channel_ledger(
        table,
        design_entries=design_entries,
        policy=quant_policy,
    )
    flagged = tuple(entry for entry in balance.entries if entry.flagged)
    carrier_effect = tuple(
        entry
        for entry in flagged
        if entry.channel_role
        in {LabelBasedChannelRole.CARRIER, LabelBasedChannelRole.REFERENCE}
    )
    batch_by_sample = {
        entry.sample_id: entry.batch
        for entry in design_entries
        if entry.sample_id and entry.batch
    }
    batch_caveat_count = sum(
        1 for entry in flagged if batch_by_sample.get(entry.sample_id) is not None
    )
    caveats: list[str] = []
    if flagged:
        caveats.append(
            "one or more multiplex channels exceed configured balance ratio thresholds"
        )
    if carrier_effect:
        caveats.append(
            "carrier/reference channels are among flagged channels and may distort ratio interpretation"
        )
    if ledger.missing_channel_count > 0:
        caveats.append(
            "missing multiplex channels were detected and should be reviewed alongside balance metrics"
        )
    if batch_caveat_count > 0:
        caveats.append(
            "some flagged channels map to batched samples; inspect potential batch-driven multiplex imbalance"
        )
    if not caveats:
        caveats.append("no multiplex balance caveats detected under the current policy")
    return MultiplexChannelBalanceDiagnosticsReport(
        policy=active_norm_policy,
        total_channel_count=len(balance.entries),
        flagged_imbalance_count=len(flagged),
        carrier_effect_channel_count=len(carrier_effect),
        missing_channel_count=ledger.missing_channel_count,
        batch_caveat_count=batch_caveat_count,
        caveats=tuple(caveats),
    )


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


def build_normalization_policy_comparison_matrix_report(
    table: LabelFreeQuantTable,
) -> NormalizationPolicyComparisonMatrixReport:
    """Compare normalization policies and preserve unsupported states explicitly."""
    strategy = build_normalization_strategy_comparison_report(
        table,
        methods=(
            NormalizationMethod.NONE,
            NormalizationMethod.TIC,
            NormalizationMethod.MEDIAN,
            NormalizationMethod.QUANTILE,
            NormalizationMethod.LOG2_MEDIAN_CENTERING,
            NormalizationMethod.VSN_LIKE,
        ),
    )
    score_by_method = {entry.method: entry.balance_score for entry in strategy.entries}
    entries = (
        NormalizationPolicyComparisonEntry(
            policy=QuantNormalizationPolicyKind.NONE,
            supported=True,
            mapped_method=NormalizationMethod.NONE,
            balance_score=score_by_method.get(NormalizationMethod.NONE),
            note="no-normalization policy is directly supported",
        ),
        NormalizationPolicyComparisonEntry(
            policy=QuantNormalizationPolicyKind.TOTAL,
            supported=True,
            mapped_method=NormalizationMethod.TIC,
            balance_score=score_by_method.get(NormalizationMethod.TIC),
            note="total-intensity normalization is mapped to TIC support",
        ),
        NormalizationPolicyComparisonEntry(
            policy=QuantNormalizationPolicyKind.MEDIAN,
            supported=True,
            mapped_method=NormalizationMethod.MEDIAN,
            balance_score=score_by_method.get(NormalizationMethod.MEDIAN),
            note="median normalization is supported natively",
        ),
        NormalizationPolicyComparisonEntry(
            policy=QuantNormalizationPolicyKind.QUANTILE,
            supported=True,
            mapped_method=NormalizationMethod.QUANTILE,
            balance_score=score_by_method.get(NormalizationMethod.QUANTILE),
            note="quantile normalization is supported natively",
        ),
        NormalizationPolicyComparisonEntry(
            policy=QuantNormalizationPolicyKind.LOG2_MEDIAN_CENTERING,
            supported=True,
            mapped_method=NormalizationMethod.LOG2_MEDIAN_CENTERING,
            balance_score=score_by_method.get(
                NormalizationMethod.LOG2_MEDIAN_CENTERING
            ),
            note="log2 median-centering is supported with explicit nonpositive-value handling before log transform",
        ),
        NormalizationPolicyComparisonEntry(
            policy=QuantNormalizationPolicyKind.VSN_LIKE,
            supported=True,
            mapped_method=NormalizationMethod.VSN_LIKE,
            balance_score=score_by_method.get(NormalizationMethod.VSN_LIKE),
            note="vsn-like normalization is supported through log-scale median centering",
        ),
        NormalizationPolicyComparisonEntry(
            policy=QuantNormalizationPolicyKind.REFERENCE_CHANNEL,
            supported=False,
            mapped_method=None,
            balance_score=None,
            note="reference-channel normalization requires dedicated channel-aware transforms and is not currently supported",
        ),
    )
    recommended_supported = next(
        (
            entry.policy
            for entry in entries
            if entry.supported and entry.mapped_method is strategy.recommended_method
        ),
        None,
    )
    return NormalizationPolicyComparisonMatrixReport(
        entries=entries,
        recommended_supported_policy=recommended_supported,
    )


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


def _rollup_value_for_strategy(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    protein_ref: str,
    sample_id: str,
    strategy: ProteinRollupStrategyKind,
    top_n: int,
) -> float | None:
    bucket = [
        record
        for record in records
        if record.sample_id == sample_id
        and record.intensity is not None
        and protein_ref in record.protein_refs
    ]
    if not bucket:
        return None
    intensities = [float(record.intensity or 0.0) for record in bucket]
    if strategy is ProteinRollupStrategyKind.SUM:
        return float(sum(intensities))
    if strategy is ProteinRollupStrategyKind.TOP_N:
        return float(sum(sorted(intensities, reverse=True)[:top_n]))
    if strategy is ProteinRollupStrategyKind.MEDIAN_POLISH_LIKE:
        ordered = sorted(intensities)
        middle = len(ordered) // 2
        if len(ordered) % 2:
            return float(ordered[middle])
        return float((ordered[middle - 1] + ordered[middle]) / 2.0)
    if strategy is ProteinRollupStrategyKind.RAZOR_ONLY:
        unique = [
            float(record.intensity or 0.0)
            for record in bucket
            if len(record.protein_refs) == 1
        ]
        return float(sum(unique)) if unique else None
    if strategy is ProteinRollupStrategyKind.SHARED_EXCLUDED:
        non_shared = [
            float(record.intensity or 0.0)
            for record in bucket
            if len(record.protein_refs) == 1
        ]
        return float(sum(non_shared)) if non_shared else 0.0
    weighted = [
        float(record.intensity or 0.0) / max(1, len(record.protein_refs))
        for record in bucket
    ]
    return float(sum(weighted))


def build_protein_rollup_strategy_comparison_report(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    top_n: int = 3,
) -> ProteinRollupStrategyComparisonReport:
    """Compare protein rollup outcomes across six explicit strategy families."""
    proteins = tuple(
        sorted(
            {protein_ref for record in records for protein_ref in record.protein_refs}
        )
    )
    samples = tuple(sorted({record.sample_id for record in records}))
    strategies = (
        ProteinRollupStrategyKind.SUM,
        ProteinRollupStrategyKind.TOP_N,
        ProteinRollupStrategyKind.MEDIAN_POLISH_LIKE,
        ProteinRollupStrategyKind.RAZOR_ONLY,
        ProteinRollupStrategyKind.SHARED_EXCLUDED,
        ProteinRollupStrategyKind.EVIDENCE_WEIGHTED,
    )
    entries: list[ProteinRollupStrategyComparisonEntry] = []
    for protein_ref in proteins:
        for sample_id in samples:
            values = tuple(
                ProteinRollupStrategyValue(
                    strategy=strategy,
                    abundance=_rollup_value_for_strategy(
                        records,
                        protein_ref=protein_ref,
                        sample_id=sample_id,
                        strategy=strategy,
                        top_n=top_n,
                    ),
                )
                for strategy in strategies
            )
            finite = [
                value.abundance for value in values if value.abundance is not None
            ]
            entries.append(
                ProteinRollupStrategyComparisonEntry(
                    protein_ref=protein_ref,
                    sample_id=sample_id,
                    strategy_values=values,
                    max_strategy_difference=(
                        max(finite) - min(finite) if finite else 0.0
                    ),
                )
            )
    return ProteinRollupStrategyComparisonReport(entries=tuple(entries))


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


def validate_differential_abundance_design_context(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    contrasts: tuple[tuple[str, str], ...],
    covariates: tuple[str, ...] = (),
    blocking_field: str | None = "batch",
    min_replicates_per_condition: int = 2,
    multiple_testing_scope: str = "global_per_analysis",
) -> DifferentialAbundanceDesignValidationReport:
    """Validate DA design assumptions before running statistical comparisons."""
    condition_replicates = count_effective_statistical_units_by_condition(
        design_entries
    )
    issues: list[DifferentialAbundanceDesignIssue] = []
    known_conditions = set(condition_replicates)
    for left, right in contrasts:
        if left == right:
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="degenerate_contrast",
                    message=f"contrast {left} vs {right} is degenerate",
                    severity="error",
                )
            )
        missing = [
            condition
            for condition in (left, right)
            if condition not in known_conditions
        ]
        if missing:
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="unknown_contrast_condition",
                    message=f"contrast references unknown conditions: {', '.join(missing)}",
                    severity="error",
                )
            )
    for condition, replicate_count in sorted(condition_replicates.items()):
        if replicate_count < min_replicates_per_condition:
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="insufficient_replicates",
                    message=(
                        f"condition {condition} has {replicate_count} replicates; "
                        f"minimum is {min_replicates_per_condition}"
                    ),
                    severity="error",
                )
            )
    covariate_lookup = {
        "batch": lambda entry: entry.batch,
        "instrument": lambda entry: entry.instrument,
        "fraction": lambda entry: entry.fraction,
        "replicate": lambda entry: entry.replicate,
    }
    for covariate in covariates:
        resolver = covariate_lookup.get(covariate)
        if resolver is None:
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="unknown_covariate",
                    message=f"covariate {covariate!r} is not recognized",
                    severity="warning",
                )
            )
            continue
        values = [resolver(entry) for entry in design_entries]
        if all(value in (None, "", 0) for value in values):
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="empty_covariate",
                    message=f"covariate {covariate!r} has no populated values",
                    severity="warning",
                )
            )
    if blocking_field:
        resolver = covariate_lookup.get(blocking_field)
        if resolver is None:
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="unknown_blocking_field",
                    message=f"blocking field {blocking_field!r} is not recognized",
                    severity="warning",
                )
            )
        else:
            if all(resolver(entry) in (None, "", 0) for entry in design_entries):
                issues.append(
                    DifferentialAbundanceDesignIssue(
                        code="missing_blocking_values",
                        message=f"blocking field {blocking_field!r} has no populated values",
                        severity="warning",
                    )
                )
    if multiple_testing_scope not in {
        "global_per_analysis",
        "per_contrast",
        "hierarchical",
    }:
        issues.append(
            DifferentialAbundanceDesignIssue(
                code="unsupported_multiple_testing_scope",
                message=(
                    "multiple-testing scope must be one of "
                    "'global_per_analysis', 'per_contrast', or 'hierarchical'"
                ),
                severity="error",
            )
        )
    return DifferentialAbundanceDesignValidationReport(
        valid=not any(issue.severity == "error" for issue in issues),
        condition_replicates=condition_replicates,
        issues=tuple(issues),
    )


def build_multiple_testing_scope_benchmark_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    condition_a: str,
    condition_b: str,
    scopes: tuple[str, ...] = (
        "global_per_analysis",
        "per_contrast",
        "hierarchical",
    ),
) -> MultipleTestingScopeBenchmarkReport:
    """Benchmark which multiple-testing scopes are actually supported today."""
    entries: list[MultipleTestingScopeBenchmarkEntry] = []
    da_report = build_differential_abundance_report(
        table,
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    bh_report = apply_benjamini_hochberg(da_report)
    adjusted_values = [
        entry.adjusted_p_value
        for entry in bh_report.entries
        if entry.adjusted_p_value is not None
    ]
    monotonic = all(
        left <= right
        for left, right in zip(adjusted_values, adjusted_values[1:], strict=False)
    )
    for scope in scopes:
        validation = validate_differential_abundance_design_context(
            design_entries,
            contrasts=((condition_a, condition_b),),
            multiple_testing_scope=scope,
        )
        if scope == "hierarchical":
            entries.append(
                MultipleTestingScopeBenchmarkEntry(
                    scope=scope,
                    status=MultipleTestingScopeBenchmarkStatus.REFUSED,
                    adjusted_p_values_complete=False,
                    adjusted_p_values_monotonic=False,
                    evidence_count=len(bh_report.entries),
                    note="hierarchical multiple-testing support is still refused because no hierarchical correction engine is implemented",
                )
            )
            continue
        entries.append(
            MultipleTestingScopeBenchmarkEntry(
                scope=scope,
                status=(
                    MultipleTestingScopeBenchmarkStatus.SUPPORTED
                    if validation.valid
                    else MultipleTestingScopeBenchmarkStatus.REFUSED
                ),
                adjusted_p_values_complete=all(
                    entry.adjusted_p_value is not None for entry in bh_report.entries
                ),
                adjusted_p_values_monotonic=monotonic,
                evidence_count=len(bh_report.entries),
                note=(
                    "benjamini-hochberg-corrected report remains complete and monotonic under the current one-contrast benchmark surface"
                    if validation.valid
                    else "design validation failed before a supported multiple-testing benchmark could be claimed"
                ),
            )
        )
    note = "multiple-testing benchmark distinguishes supported report-wide correction from explicitly refused hierarchical scope"
    return MultipleTestingScopeBenchmarkReport(entries=tuple(entries), note=note)


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


def build_effect_size_first_differential_abundance_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    condition_a: str,
    condition_b: str,
) -> EffectSizeFirstDaReport:
    """Build a DA report ranked by effect size with statistical and QC caveats retained."""
    paired_policy = (
        PairedDifferentialPolicy()
        if all(entry.pair_id not in (None, "") for entry in design_entries)
        else None
    )
    da = build_differential_abundance_report(
        table,
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
        test_type=(
            DifferentialAbundanceTestType.PAIRED_T_TEST
            if paired_policy is not None
            else DifferentialAbundanceTestType.WELCH_T_TEST
        ),
        paired_policy=paired_policy,
    )
    entries: list[EffectSizeFirstDaEntry] = []
    for entry in da.entries:
        caveats: list[str] = []
        if entry.observations_a == 0 or entry.observations_b == 0:
            caveats.append("one condition has no observed replicates for this entity")
        if entry.adjusted_p_value is None:
            caveats.append("adjusted p-value is unavailable")
        if entry.uncertainty_note:
            caveats.append(entry.uncertainty_note)
        if entry.effect_size_cohens_d is None:
            caveats.append("effect size could not be estimated robustly")
        entries.append(
            EffectSizeFirstDaEntry(
                entity_id=entry.entity_id,
                log2_fold_change=entry.log2_fold_change,
                effect_size_cohens_d=entry.effect_size_cohens_d,
                standard_error=entry.standard_error,
                confidence_interval_low=entry.confidence_interval_low,
                confidence_interval_high=entry.confidence_interval_high,
                p_value=entry.p_value,
                adjusted_p_value=entry.adjusted_p_value,
                observations_a=entry.observations_a,
                observations_b=entry.observations_b,
                uncertainty_note=entry.uncertainty_note,
                caveats=tuple(caveats),
            )
        )
    ranked = tuple(
        sorted(
            entries,
            key=lambda item: (
                -(
                    abs(item.effect_size_cohens_d)
                    if item.effect_size_cohens_d is not None
                    else abs(item.log2_fold_change)
                ),
                item.adjusted_p_value if item.adjusted_p_value is not None else 1.0,
                item.entity_id,
            ),
        )
    )
    global_caveats: list[str] = []
    if any(entry.adjusted_p_value is None for entry in ranked):
        global_caveats.append("some entities are missing adjusted p-values")
    if any(entry.observations_a < 2 or entry.observations_b < 2 for entry in ranked):
        global_caveats.append("one or more entities have low replicate support")
    if not global_caveats:
        global_caveats.append(
            "effect-size ranking includes complete statistical annotations"
        )
    return EffectSizeFirstDaReport(
        condition_a=condition_a,
        condition_b=condition_b,
        entries=ranked,
        global_caveats=tuple(global_caveats),
    )


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


def build_quant_review_bundle(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    imputation_method: ImputationMethod = ImputationMethod.NONE,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
) -> QuantReviewBundle:
    """Build a full quant review bundle from feature-level quant records."""
    observed_sample_ids = {record.sample_id for record in records}
    measured_design_entries = tuple(
        entry for entry in design_entries if entry.sample_id in observed_sample_ids
    )
    covariate_fields = tuple(
        sorted(
            {
                field
                for entry in measured_design_entries
                for field, value in entry.metadata.items()
                if field != "timepoint" and value not in ("", None)
            }
        )
    )
    timepoint_field = (
        "timepoint"
        if all(
            entry.metadata.get("timepoint") not in ("", None)
            for entry in measured_design_entries
        )
        else None
    )
    pairing_field = (
        "pair_id"
        if all(entry.pair_id not in (None, "") for entry in measured_design_entries)
        else None
    )
    peptide_table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=aggregation_method,
    )
    normalized_table = (
        normalize_label_free_table(peptide_table, method=normalization_method)
        if normalization_method is not NormalizationMethod.NONE
        else peptide_table
    )
    normalization_comparison = build_normalization_comparison_report(
        peptide_table,
        normalized_table,
    )
    conditions = tuple(sorted({entry.condition for entry in measured_design_entries}))
    imputed_table = impute_label_free_table(
        normalized_table,
        method=imputation_method,
    )
    imputation_report = build_imputation_report(
        normalized_table,
        imputed_table,
    )
    missingness_entity_summary = build_missingness_entity_summary_report(imputed_table)
    missingness_condition_summary = build_missingness_condition_summary_report(
        imputed_table,
        design_entries=measured_design_entries,
    )
    missingness_intensity_dependence = build_missingness_intensity_dependence_report(
        imputed_table
    )
    missingness = build_missingness_mechanism_profile_report(
        imputed_table,
        design_entries=measured_design_entries,
    )
    imputation_sensitivity = (
        build_imputation_sensitivity_report(
            normalized_table,
            measured_design_entries,
            condition_a=conditions[0],
            condition_b=conditions[1],
        )
        if len(conditions) >= 2
        else None
    )
    design_matrix_report = build_quant_design_matrix_report(
        measured_design_entries,
        batch_field="batch",
        covariate_fields=covariate_fields,
        pairing_field=pairing_field,
        timepoint_field=timepoint_field,
    )
    differential_report = None
    if len(conditions) == 2:
        try:
            differential_report = build_differential_abundance_report(
                imputed_table,
                measured_design_entries,
                condition_a=conditions[0],
                condition_b=conditions[1],
                test_type=(
                    DifferentialAbundanceTestType.PAIRED_T_TEST
                    if pairing_field is not None
                    else DifferentialAbundanceTestType.WELCH_T_TEST
                ),
                paired_policy=(
                    PairedDifferentialPolicy(pair_id_field=pairing_field)
                    if pairing_field is not None
                    else None
                ),
            )
        except ValueError as error:
            if not (
                timepoint_field is not None
                and "different_analysis_family_required" in str(error)
            ):
                raise
    time_course_differential_report = (
        build_time_course_differential_report(
            imputed_table,
            measured_design_entries,
            policy=TimeCourseTestingPolicy(
                timepoint_field=timepoint_field,
                batch_field="batch",
                pairing_field=pairing_field,
                covariate_fields=covariate_fields,
            ),
        )
        if timepoint_field is not None
        else None
    )
    multi_condition_differential_report = None
    if len(conditions) > 2:
        try:
            multi_condition_differential_report = (
                build_multi_condition_differential_abundance_report(
                    imputed_table,
                    measured_design_entries,
                    test_type=DifferentialAbundanceTestType.LINEAR_MODEL_CONTRAST,
                    design_matrix=design_matrix_report,
                )
            )
        except ValueError as error:
            if "insufficient_group_size" not in str(error):
                raise
    multi_contrast_consistency_report = (
        build_multi_contrast_consistency_report(
            multi_condition_differential_report,
            entity_protein_refs=imputed_table.entity_protein_refs,
        )
        if multi_condition_differential_report is not None
        else None
    )
    from bijux_proteomics.quantification.statistics.statistical_backend import (
        build_limma_compatible_quant_package,
        build_msstats_compatible_input_report,
    )

    limma_package = build_limma_compatible_quant_package(
        imputed_table,
        measured_design_entries,
        batch_field="batch",
        covariate_fields=covariate_fields,
        pairing_field=pairing_field,
        timepoint_field=timepoint_field,
    )
    msstats_input_report = build_msstats_compatible_input_report(
        records,
        measured_design_entries,
    )
    design_model_fit_report = fit_quant_design_matrix_model(
        imputed_table,
        design_matrix_report,
    )
    qc_report = build_replicate_and_batch_qc_report(
        imputed_table,
        design_entries=measured_design_entries,
    )
    artifact_bundle = build_quant_artifact_bundle(
        imputed_table,
        design_entries=measured_design_entries,
        imputation_report=imputation_report,
        imputation_sensitivity_report=imputation_sensitivity,
        missingness_entity_summary=missingness_entity_summary,
        missingness_condition_summary=missingness_condition_summary,
        missingness_intensity_dependence=missingness_intensity_dependence,
        replicate_qc_report=qc_report,
        normalization_comparison_report=normalization_comparison,
        normalization_strategy_report=build_normalization_strategy_comparison_report(
            peptide_table
        ),
        limma_compatible_package=limma_package,
        msstats_compatible_input_report=msstats_input_report,
        design_matrix_report=design_matrix_report,
        design_model_fit_report=design_model_fit_report,
        differential_abundance_report=differential_report,
        differential_abundance_multi_condition_report=(
            multi_condition_differential_report
        ),
        time_course_differential_report=time_course_differential_report,
    )
    lfq_provenance = build_lfq_feature_peptide_protein_provenance_report(
        records,
        aggregation_method=aggregation_method,
        normalization_method=normalization_method,
    )
    normalization_matrix = build_normalization_policy_comparison_matrix_report(
        peptide_table
    )
    rollup_strategy = build_protein_rollup_strategy_comparison_report(records)
    decision_readiness = build_quant_decision_readiness_report(
        imputed_table,
        design_entries=design_entries,
    )
    da_report = None
    if len(conditions) == 2:
        try:
            da_report = build_effect_size_first_differential_abundance_report(
                imputed_table,
                design_entries=design_entries,
                condition_a=conditions[0],
                condition_b=conditions[1],
            )
        except ValueError as error:
            if not (
                timepoint_field is not None
                and "different_analysis_family_required" in str(error)
            ):
                raise
    caveats: list[str] = []
    if da_report is None and multi_condition_differential_report is None:
        caveats.append(
            "differential abundance report is unavailable because fewer than two conditions were provided"
        )
    if multi_condition_differential_report is not None:
        caveats.append(
            "multi-condition study emitted pairwise differential contrasts plus a cross-contrast consistency review instead of one primary effect-size ranking"
        )
    if (
        multi_contrast_consistency_report is not None
        and multi_contrast_consistency_report.summary.direction_conflict_count > 0
    ):
        caveats.append(
            "multi-condition contrast review found contradictory directionality across significant contrasts"
        )
    if qc_report.outlier_samples:
        caveats.append(
            "qc outlier samples were detected and should be reviewed before publication decisions"
        )
    if decision_readiness.readiness_state.value != "decision_grade":
        caveats.append(decision_readiness.note)
    evidence_pointers = (
        "quant_artifact_bundle.matrix_export",
        "quant_artifact_bundle.normalization_comparison_report",
        "quant_artifact_bundle.imputation_report",
        "quant_artifact_bundle.imputation_sensitivity_report",
        "quant_artifact_bundle.limma_compatible_package",
        "quant_artifact_bundle.msstats_compatible_input_report",
        "quant_artifact_bundle.replicate_qc_report.replicate_correlation_report.entries",
        "quant_artifact_bundle.replicate_qc_report.replicate_cv_report.entries",
        "quant_artifact_bundle.replicate_qc_report.outlier_samples",
        "quant_artifact_bundle.design_matrix_report",
        "quant_artifact_bundle.design_model_fit_report",
        "quant_artifact_bundle.differential_abundance_report",
        "quant_artifact_bundle.differential_abundance_multi_condition_report",
        "quant_artifact_bundle.time_course_differential_report",
        "quant_review_bundle.multi_contrast_consistency_report.entities",
        "lfq_provenance.feature_entries",
        "quant_review_bundle.normalization_comparison",
        "quant_review_bundle.imputation_report",
        "rollup_strategy_comparison.entries",
        "missingness_profile.entries",
        "missingness_entity_summary.entries",
        "missingness_condition_summary.entries",
        "missingness_intensity_dependence.plot_points",
        "qc_report.replicate_correlation_report.entries",
        "qc_report.replicate_cv_report.entries",
        "qc_report.sample_pca_report.entries",
        "qc_report.condition_clustering_report",
        "qc_report.outlier_samples",
        "quant_decision_readiness",
    )
    return QuantReviewBundle(
        artifact_bundle_hash=artifact_bundle.document_schema.content_hash or "",
        lfq_provenance=lfq_provenance,
        normalization_comparison=normalization_comparison,
        imputation_report=imputation_report,
        imputation_sensitivity=imputation_sensitivity,
        normalization_matrix=normalization_matrix,
        rollup_strategy_comparison=rollup_strategy,
        limma_compatible_package=limma_package,
        msstats_compatible_input_report=msstats_input_report,
        design_matrix_report=design_matrix_report,
        design_model_fit_report=design_model_fit_report,
        effect_size_da_report=da_report,
        differential_abundance_multi_condition_report=(
            multi_condition_differential_report
        ),
        multi_contrast_consistency_report=multi_contrast_consistency_report,
        time_course_differential_report=time_course_differential_report,
        missingness_profile=missingness,
        missingness_entity_summary=missingness_entity_summary,
        missingness_condition_summary=missingness_condition_summary,
        missingness_intensity_dependence=missingness_intensity_dependence,
        qc_report=qc_report,
        decision_readiness=decision_readiness,
        evidence_pointers=evidence_pointers,
        caveats=tuple(caveats),
    )
