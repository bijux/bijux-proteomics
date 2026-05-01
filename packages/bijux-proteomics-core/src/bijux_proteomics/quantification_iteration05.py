# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Iteration-05 quantification and QC capability surfaces."""

from __future__ import annotations

from pydantic import ConfigDict, Field
from enum import StrEnum

from bijux_proteomics.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    LabelBasedChannelRole,
    LabelBasedQuantPolicy,
    LabelFreeProvenanceBundle,
    LabelFreeQuantTable,
    MultiplexNormalizationPolicy,
    MissingChannelPolicy,
    MissingValueSummaryReport,
    Ms1FeatureRecord,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    build_label_free_provenance_bundle,
    build_label_based_quant_bundle,
    build_multiplex_channel_balance_report,
    build_normalization_strategy_comparison_report,
    build_differential_abundance_report,
    normalize_label_free_table,
    summarize_missing_values,
)
from bijux_proteomics_foundation import JsonModel


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
        peptide_table = normalize_label_free_table(peptide_table, method=normalization_method)
        protein_table = normalize_label_free_table(protein_table, method=normalization_method)

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
    entries: tuple[LabelBasedQuantChannelLedgerEntry, ...] = Field(default_factory=tuple)
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
        if entry.channel_role in {LabelBasedChannelRole.CARRIER, LabelBasedChannelRole.REFERENCE}
    )
    batch_by_sample = {
        entry.sample_id: entry.batch
        for entry in design_entries
        if entry.sample_id and entry.batch
    }
    batch_caveat_count = sum(
        1
        for entry in flagged
        if batch_by_sample.get(entry.sample_id) is not None
    )
    caveats: list[str] = []
    if flagged:
        caveats.append("one or more multiplex channels exceed configured balance ratio thresholds")
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
    """Normalization policy families tracked by the iteration-05 comparison matrix."""

    NONE = "none"
    TOTAL = "total"
    MEDIAN = "median"
    QUANTILE = "quantile"
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

    entries: tuple[NormalizationPolicyComparisonEntry, ...] = Field(default_factory=tuple)
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
            policy=QuantNormalizationPolicyKind.VSN_LIKE,
            supported=False,
            mapped_method=None,
            balance_score=None,
            note="vsn-like normalization is not currently supported and remains an explicit gap",
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
    """Protein rollup strategies compared for iteration-05 quant analysis."""

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
    strategy_values: tuple[ProteinRollupStrategyValue, ...] = Field(default_factory=tuple)
    max_strategy_difference: float = Field(..., ge=0.0)


class ProteinRollupStrategyComparisonReport(JsonModel):
    """Comparison report over multiple protein rollup strategies."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ProteinRollupStrategyComparisonEntry, ...] = Field(default_factory=tuple)


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
            {
                protein_ref
                for record in records
                for protein_ref in record.protein_refs
            }
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
            finite = [value.abundance for value in values if value.abundance is not None]
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
    by_condition: dict[str, set[str]] = {}
    for entry in design_entries:
        by_condition.setdefault(entry.condition, set()).add(entry.sample_id)
    condition_replicates = {
        condition: len(sample_ids) for condition, sample_ids in by_condition.items()
    }
    issues: list[DifferentialAbundanceDesignIssue] = []
    known_conditions = set(by_condition)
    for left, right in contrasts:
        if left == right:
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="degenerate_contrast",
                    message=f"contrast {left} vs {right} is degenerate",
                    severity="error",
                )
            )
        missing = [condition for condition in (left, right) if condition not in known_conditions]
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
    da = build_differential_abundance_report(
        table,
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
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
                -(abs(item.effect_size_cohens_d) if item.effect_size_cohens_d is not None else abs(item.log2_fold_change)),
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
        global_caveats.append("effect-size ranking includes complete statistical annotations")
    return EffectSizeFirstDaReport(
        condition_a=condition_a,
        condition_b=condition_b,
        entries=ranked,
        global_caveats=tuple(global_caveats),
    )
