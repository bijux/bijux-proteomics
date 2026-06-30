# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Scientific benchmark surfaces for quantification credibility."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    LabelBasedQuantPolicy,
    LabelFreeQuantTable,
    MissingnessConditionSummaryReport,
    MissingnessEntitySummaryReport,
    MissingnessIntensityDependenceReport,
    MissingValueSummaryReport,
    Ms1FeatureRecord,
    MultiplexNormalizationPolicy,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_based_quant_bundle,
    build_label_free_intensity_table,
)
from bijux_proteomics.quantification.missingness import (
    build_missingness_condition_summary_report,
    build_missingness_entity_summary_report,
    build_missingness_intensity_dependence_report,
    summarize_missing_values,
)
from bijux_proteomics.quantification.normalization import (
    normalize_label_free_table,
)
from bijux_proteomics.quantification.missingness.readiness import (
    QuantDecisionReadinessReport,
    build_quant_decision_readiness_report,
)
from bijux_proteomics.quantification.provenance.review import (
    MissingnessMechanismKind,
    MissingnessMechanismProfileReport,
    MultiplexChannelBalanceDiagnosticsReport,
    QuantNormalizationPolicyKind,
    build_effect_size_first_differential_abundance_report,
    build_missingness_mechanism_profile_report,
    build_multiplex_channel_balance_diagnostics_report,
)
from bijux_proteomics_foundation import JsonModel


class QuantMissingnessRobustnessReport(JsonModel):
    """Review-grade report linking missingness realism to quant readiness."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    normalization_method: NormalizationMethod
    missing_value_summary: MissingValueSummaryReport
    missingness_entity_summary: MissingnessEntitySummaryReport
    missingness_condition_summary: MissingnessConditionSummaryReport
    missingness_intensity_dependence: MissingnessIntensityDependenceReport
    mechanism_profile: MissingnessMechanismProfileReport
    decision_readiness: QuantDecisionReadinessReport
    sparse_biology_candidate_count: int = Field(..., ge=0)
    technical_failure_count: int = Field(..., ge=0)
    robust_for_interpretation: bool
    note: str = Field(..., min_length=1)


class QuantNormalizationImpactEntry(JsonModel):
    """How one normalization policy changes the primary DA narrative."""

    model_config = ConfigDict(extra="forbid")

    policy: QuantNormalizationPolicyKind
    supported: bool
    top_entity_id: str | None = None
    top_entity_direction: str | None = None
    top_entity_effect_size: float | None = None
    note: str = Field(..., min_length=1)


class QuantNormalizationImpactBenchmarkReport(JsonModel):
    """Comparison report across normalization policies for one contrast."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    entries: tuple[QuantNormalizationImpactEntry, ...] = Field(default_factory=tuple)
    primary_narrative_changed: bool
    unsupported_policies: tuple[QuantNormalizationPolicyKind, ...] = Field(
        default_factory=tuple
    )


class EffectSizeStabilityBenchmarkReport(JsonModel):
    """Benchmark whether small perturbations reshuffle DA narratives."""

    model_config = ConfigDict(extra="forbid")

    baseline_top_entities: tuple[str, ...] = Field(default_factory=tuple)
    perturbed_top_entities: tuple[str, ...] = Field(default_factory=tuple)
    stable_top_rank: bool
    stable_top_set: bool
    overlap_fraction: float = Field(..., ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class MultiplexRatioExpectation(JsonModel):
    """Expected abundance ratio between two multiplex channels."""

    model_config = ConfigDict(extra="forbid")

    numerator_sample_id: str = Field(..., min_length=1)
    denominator_sample_id: str = Field(..., min_length=1)
    expected_ratio: float = Field(..., gt=0.0)


class MultiplexArtifactPressureEntry(JsonModel):
    """One expected multiplex ratio challenged by compression and interference."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    numerator_sample_id: str = Field(..., min_length=1)
    denominator_sample_id: str = Field(..., min_length=1)
    expected_ratio: float = Field(..., gt=0.0)
    observed_ratio: float = Field(..., gt=0.0)
    ratio_preservation_fraction: float = Field(..., ge=0.0, le=1.0)
    materially_compressed: bool
    numerator_channel_interference: float = Field(..., ge=0.0, le=1.0)
    denominator_channel_interference: float = Field(..., ge=0.0, le=1.0)
    numerator_reporter_bleed: float = Field(..., ge=0.0, le=1.0)
    denominator_reporter_bleed: float = Field(..., ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class MultiplexArtifactPressureBenchmarkReport(JsonModel):
    """Benchmark whether multiplex ratios survive realistic artifact pressure."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[MultiplexArtifactPressureEntry, ...] = Field(default_factory=tuple)
    materially_compressed_count: int = Field(..., ge=0)
    interference_flagged_channel_count: int = Field(..., ge=0)
    reporter_bleed_flagged_channel_count: int = Field(..., ge=0)
    ready_for_ratio_claims: bool
    note: str = Field(..., min_length=1)


class QuantTruthDirection(StrEnum):
    """Expected direction for a truth-package contrast."""

    UP_IN_CONDITION_A = "up_in_condition_a"
    UP_IN_CONDITION_B = "up_in_condition_b"
    NEUTRAL = "neutral"


class QuantTruthExpectationEntry(JsonModel):
    """One truth-package expectation for a controlled quantitative shift."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    expected_direction: QuantTruthDirection
    minimum_absolute_log2_fold_change: float = Field(default=0.0, ge=0.0)


class QuantTruthBenchmarkEntry(JsonModel):
    """Observed quant behavior for one expected truth-package entity."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    expected_direction: QuantTruthDirection
    observed_direction: QuantTruthDirection
    matched_direction: bool
    observed_log2_fold_change: float = 0.0
    observed_effect_size: float | None = None
    note: str = Field(..., min_length=1)


class QuantTruthPackageBenchmarkReport(JsonModel):
    """Truth-package benchmark over controlled quantitative expectations."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    entries: tuple[QuantTruthBenchmarkEntry, ...] = Field(default_factory=tuple)
    matched_expected_count: int = Field(..., ge=0)
    missed_expected_count: int = Field(..., ge=0)
    unexpected_leader_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class MultiplexStressBenchmarkReport(JsonModel):
    """Stress benchmark for multiplex reference dropout and carrier overload."""

    model_config = ConfigDict(extra="forbid")

    bundle_missing_channel_count: int = Field(..., ge=0)
    reference_dropout_count: int = Field(..., ge=0)
    carrier_overload_count: int = Field(..., ge=0)
    unbalanced_group_count: int = Field(..., ge=0)
    diagnostics: MultiplexChannelBalanceDiagnosticsReport
    ready_for_biological_rollup: bool
    note: str = Field(..., min_length=1)


def _quant_table(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    entity_level: QuantEntityLevel,
    aggregation_method: QuantRollupMethod,
    normalization_method: NormalizationMethod,
) -> LabelFreeQuantTable:
    table = build_label_free_intensity_table(
        records,
        entity_level=entity_level,
        aggregation_method=aggregation_method,
    )
    if normalization_method is NormalizationMethod.NONE:
        return table
    return normalize_label_free_table(table, method=normalization_method)


def _direction_from_log2_fold_change(value: float) -> QuantTruthDirection:
    if value > 0.0:
        return QuantTruthDirection.UP_IN_CONDITION_B
    if value < 0.0:
        return QuantTruthDirection.UP_IN_CONDITION_A
    return QuantTruthDirection.NEUTRAL


def build_quant_missingness_robustness_report(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    entity_level: QuantEntityLevel = QuantEntityLevel.PROTEIN,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
) -> QuantMissingnessRobustnessReport:
    """Link missingness structure to decision-grade quant interpretation."""

    table = _quant_table(
        records,
        entity_level=entity_level,
        aggregation_method=aggregation_method,
        normalization_method=normalization_method,
    )
    missingness = summarize_missing_values(table)
    entity_summary = build_missingness_entity_summary_report(table)
    condition_summary = build_missingness_condition_summary_report(
        table,
        design_entries=design_entries,
    )
    intensity_dependence = build_missingness_intensity_dependence_report(table)
    mechanism_profile = build_missingness_mechanism_profile_report(
        table,
        design_entries=design_entries,
    )
    readiness = build_quant_decision_readiness_report(
        table,
        design_entries=design_entries,
    )
    sparse_count = mechanism_profile.summary_counts.get(
        MissingnessMechanismKind.SPARSE_BIOLOGY_CANDIDATE,
        0,
    )
    technical_count = mechanism_profile.summary_counts.get(
        MissingnessMechanismKind.TECHNICAL_FAILURE,
        0,
    )
    robust = (
        readiness.readiness_state.value != "blocked"
        and (sparse_count + technical_count) >= 1
    )
    return QuantMissingnessRobustnessReport(
        entity_level=entity_level,
        normalization_method=normalization_method,
        missing_value_summary=missingness,
        missingness_entity_summary=entity_summary,
        missingness_condition_summary=condition_summary,
        missingness_intensity_dependence=intensity_dependence,
        mechanism_profile=mechanism_profile,
        decision_readiness=readiness,
        sparse_biology_candidate_count=sparse_count,
        technical_failure_count=technical_count,
        robust_for_interpretation=robust,
        note=(
            "missingness is classified into biologically sparse and technical-loss candidates before quant claims travel"
            if robust
            else "quant interpretation remains fragile because missingness realism or readiness is still unresolved"
        ),
    )


def build_quant_normalization_impact_benchmark_report(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    condition_a: str,
    condition_b: str,
    entity_level: QuantEntityLevel = QuantEntityLevel.PROTEIN,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
) -> QuantNormalizationImpactBenchmarkReport:
    """Show when normalization choice changes the primary DA narrative."""

    policies: tuple[
        tuple[QuantNormalizationPolicyKind, NormalizationMethod | None], ...
    ] = (
        (QuantNormalizationPolicyKind.NONE, NormalizationMethod.NONE),
        (QuantNormalizationPolicyKind.TOTAL, NormalizationMethod.TIC),
        (QuantNormalizationPolicyKind.MEDIAN, NormalizationMethod.MEDIAN),
        (QuantNormalizationPolicyKind.QUANTILE, NormalizationMethod.QUANTILE),
        (QuantNormalizationPolicyKind.VSN_LIKE, NormalizationMethod.VSN_LIKE),
    )
    entries: list[QuantNormalizationImpactEntry] = []
    supported_tops: list[tuple[str | None, str | None]] = []
    unsupported: list[QuantNormalizationPolicyKind] = []
    for policy, method in policies:
        if method is None:
            unsupported.append(policy)
            entries.append(
                QuantNormalizationImpactEntry(
                    policy=policy,
                    supported=False,
                    note="policy remains unsupported and cannot authorize a DA narrative",
                )
            )
            continue
        table = _quant_table(
            records,
            entity_level=entity_level,
            aggregation_method=aggregation_method,
            normalization_method=method,
        )
        report = build_effect_size_first_differential_abundance_report(
            table,
            design_entries=design_entries,
            condition_a=condition_a,
            condition_b=condition_b,
        )
        top = report.entries[0] if report.entries else None
        direction = (
            "up"
            if top is not None and top.log2_fold_change > 0
            else "down"
            if top is not None and top.log2_fold_change < 0
            else None
        )
        supported_tops.append((top.entity_id if top is not None else None, direction))
        entries.append(
            QuantNormalizationImpactEntry(
                policy=policy,
                supported=True,
                top_entity_id=top.entity_id if top is not None else None,
                top_entity_direction=direction,
                top_entity_effect_size=top.effect_size_cohens_d
                if top is not None
                else None,
                note="supported normalization policy produced a reviewable DA ranking",
            )
        )
    primary_narrative_changed = (
        len(set(supported_tops)) > 1 if supported_tops else False
    )
    return QuantNormalizationImpactBenchmarkReport(
        condition_a=condition_a,
        condition_b=condition_b,
        entries=tuple(entries),
        primary_narrative_changed=primary_narrative_changed,
        unsupported_policies=tuple(unsupported),
    )


def build_effect_size_stability_benchmark_report(
    baseline_records: tuple[Ms1FeatureRecord, ...],
    perturbed_records: tuple[Ms1FeatureRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    condition_a: str,
    condition_b: str,
    entity_level: QuantEntityLevel = QuantEntityLevel.PROTEIN,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    top_n: int = 3,
) -> EffectSizeStabilityBenchmarkReport:
    """Check whether small feature perturbations reshuffle DA narratives."""

    baseline_table = _quant_table(
        baseline_records,
        entity_level=entity_level,
        aggregation_method=aggregation_method,
        normalization_method=normalization_method,
    )
    perturbed_table = _quant_table(
        perturbed_records,
        entity_level=entity_level,
        aggregation_method=aggregation_method,
        normalization_method=normalization_method,
    )
    baseline = build_effect_size_first_differential_abundance_report(
        baseline_table,
        design_entries=design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    perturbed = build_effect_size_first_differential_abundance_report(
        perturbed_table,
        design_entries=design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    baseline_top = tuple(entry.entity_id for entry in baseline.entries[:top_n])
    perturbed_top = tuple(entry.entity_id for entry in perturbed.entries[:top_n])
    intersection = set(baseline_top) & set(perturbed_top)
    denominator = max(len(set(baseline_top) | set(perturbed_top)), 1)
    overlap_fraction = len(intersection) / denominator
    stable_rank = bool(baseline_top) and baseline_top[:1] == perturbed_top[:1]
    stable_set = set(baseline_top) == set(perturbed_top)
    return EffectSizeStabilityBenchmarkReport(
        baseline_top_entities=baseline_top,
        perturbed_top_entities=perturbed_top,
        stable_top_rank=stable_rank,
        stable_top_set=stable_set,
        overlap_fraction=overlap_fraction,
        note=(
            "small perturbations preserved the same top-ranked narrative"
            if stable_rank
            else "small perturbations reshuffled the leading differential-abundance narrative"
        ),
    )


def build_multiplex_artifact_pressure_benchmark_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    expected_ratios: tuple[MultiplexRatioExpectation, ...],
    interference_fraction_by_sample: dict[str, float] | None = None,
    reporter_bleed_fraction_by_sample: dict[str, float] | None = None,
    min_ratio_preservation_fraction: float = 0.75,
    material_artifact_fraction: float = 0.1,
) -> MultiplexArtifactPressureBenchmarkReport:
    """Benchmark whether multiplex ratios remain credible under artifact pressure."""

    design_lookup = {
        entry.sample_id: entry
        for entry in design_entries
        if entry.sample_id and entry.multiplex_group
    }
    total_abundance_by_sample = {
        sample_id: float(
            sum(
                value.abundance or 0.0
                for value in table.values
                if value.sample_id == sample_id and value.abundance is not None
            )
        )
        for sample_id in table.sample_ids
    }
    interference = interference_fraction_by_sample or {}
    reporter_bleed = reporter_bleed_fraction_by_sample or {}
    entries: list[MultiplexArtifactPressureEntry] = []
    for expectation in expected_ratios:
        numerator_design = design_lookup.get(expectation.numerator_sample_id)
        denominator_design = design_lookup.get(expectation.denominator_sample_id)
        if numerator_design is None or denominator_design is None:
            raise ValueError(
                "expected multiplex ratios require multiplex design metadata"
            )
        if numerator_design.multiplex_group != denominator_design.multiplex_group:
            raise ValueError(
                "expected multiplex ratios must compare channels inside one multiplex group"
            )
        numerator_total = total_abundance_by_sample.get(
            expectation.numerator_sample_id, 0.0
        )
        denominator_total = total_abundance_by_sample.get(
            expectation.denominator_sample_id,
            0.0,
        )
        if denominator_total <= 0.0:
            raise ValueError(
                "expected multiplex ratio denominator must have non-zero abundance"
            )
        observed_ratio = numerator_total / denominator_total
        ratio_preservation = min(
            observed_ratio / expectation.expected_ratio,
            expectation.expected_ratio / observed_ratio,
        )
        numerator_interference = interference.get(expectation.numerator_sample_id, 0.0)
        denominator_interference = interference.get(
            expectation.denominator_sample_id, 0.0
        )
        numerator_bleed = reporter_bleed.get(expectation.numerator_sample_id, 0.0)
        denominator_bleed = reporter_bleed.get(expectation.denominator_sample_id, 0.0)
        materially_compressed = ratio_preservation < min_ratio_preservation_fraction
        entries.append(
            MultiplexArtifactPressureEntry(
                multiplex_group=numerator_design.multiplex_group or "",
                numerator_sample_id=expectation.numerator_sample_id,
                denominator_sample_id=expectation.denominator_sample_id,
                expected_ratio=expectation.expected_ratio,
                observed_ratio=round(observed_ratio, 6),
                ratio_preservation_fraction=round(ratio_preservation, 6),
                materially_compressed=materially_compressed,
                numerator_channel_interference=numerator_interference,
                denominator_channel_interference=denominator_interference,
                numerator_reporter_bleed=numerator_bleed,
                denominator_reporter_bleed=denominator_bleed,
                note=(
                    "observed multiplex ratio stays close to the expected controlled ratio"
                    if not materially_compressed
                    else "observed multiplex ratio is compressed enough to weaken biological interpretation"
                ),
            )
        )
    interference_flagged = sum(
        1 for value in (*interference.values(),) if value >= material_artifact_fraction
    )
    bleed_flagged = sum(
        1
        for value in (*reporter_bleed.values(),)
        if value >= material_artifact_fraction
    )
    ready = (
        all(not entry.materially_compressed for entry in entries)
        and interference_flagged == 0
        and bleed_flagged == 0
    )
    return MultiplexArtifactPressureBenchmarkReport(
        entries=tuple(entries),
        materially_compressed_count=sum(
            1 for entry in entries if entry.materially_compressed
        ),
        interference_flagged_channel_count=interference_flagged,
        reporter_bleed_flagged_channel_count=bleed_flagged,
        ready_for_ratio_claims=ready,
        note=(
            "multiplex ratios survive controlled artifact pressure"
            if ready
            else "multiplex ratios remain vulnerable to compression, interference, or reporter bleed"
        ),
    )


def build_quant_truth_package_benchmark_report(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    expectations: tuple[QuantTruthExpectationEntry, ...],
    condition_a: str,
    condition_b: str,
    entity_level: QuantEntityLevel = QuantEntityLevel.PROTEIN,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
) -> QuantTruthPackageBenchmarkReport:
    """Benchmark controlled quantitative expectations against observed DA output."""

    table = _quant_table(
        records,
        entity_level=entity_level,
        aggregation_method=aggregation_method,
        normalization_method=normalization_method,
    )
    report = build_effect_size_first_differential_abundance_report(
        table,
        design_entries=design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    lookup = {entry.entity_id: entry for entry in report.entries}
    entries: list[QuantTruthBenchmarkEntry] = []
    for expectation in expectations:
        observed = lookup.get(expectation.entity_id)
        observed_log2_fold_change = (
            observed.log2_fold_change if observed is not None else 0.0
        )
        observed_direction = _direction_from_log2_fold_change(observed_log2_fold_change)
        matched = (
            observed_direction is expectation.expected_direction
            and abs(observed_log2_fold_change)
            >= expectation.minimum_absolute_log2_fold_change
        )
        entries.append(
            QuantTruthBenchmarkEntry(
                entity_id=expectation.entity_id,
                expected_direction=expectation.expected_direction,
                observed_direction=observed_direction,
                matched_direction=matched,
                observed_log2_fold_change=observed_log2_fold_change,
                observed_effect_size=(
                    observed.effect_size_cohens_d if observed is not None else None
                ),
                note=(
                    "controlled expectation was recovered by the observed contrast"
                    if matched
                    else "controlled expectation was missed or weakened in the observed contrast"
                ),
            )
        )
    expected_ids = {entry.entity_id for entry in expectations}
    unexpected_leaders = tuple(
        entry.entity_id
        for entry in report.entries[:3]
        if entry.entity_id not in expected_ids
    )
    matched_count = sum(1 for entry in entries if entry.matched_direction)
    return QuantTruthPackageBenchmarkReport(
        condition_a=condition_a,
        condition_b=condition_b,
        entries=tuple(entries),
        matched_expected_count=matched_count,
        missed_expected_count=len(entries) - matched_count,
        unexpected_leader_ids=unexpected_leaders,
        note=(
            "controlled shifts were recovered without unexpected leaders dominating the contrast"
            if matched_count == len(entries) and not unexpected_leaders
            else "controlled shifts still compete with unexpected or misdirected quantitative leaders"
        ),
    )


def build_multiplex_stress_benchmark_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    policy: LabelBasedQuantPolicy,
    normalization_policy: MultiplexNormalizationPolicy | None = None,
    overloaded_carrier_ratio_threshold: float = 2.0,
) -> MultiplexStressBenchmarkReport:
    """Stress multiplex support with missing references, carrier overload, and imbalance."""

    quant_bundle = build_label_based_quant_bundle(
        table,
        design_entries=design_entries,
        policy=policy,
    )
    diagnostics = build_multiplex_channel_balance_diagnostics_report(
        table,
        design_entries=design_entries,
        quant_policy=policy,
        normalization_policy=normalization_policy,
    )
    reference_dropout_count = sum(
        1
        for entry in quant_bundle.missing_channels
        if entry.expected_role.value == "reference"
    )
    carrier_overload_count = sum(
        1 for entry in diagnostics.caveats if "carrier/reference channels" in entry
    )
    sample_counts_by_group: dict[str, int] = {}
    for entry in design_entries:
        if entry.multiplex_group:
            sample_counts_by_group[entry.multiplex_group] = (
                sample_counts_by_group.get(entry.multiplex_group, 0) + 1
            )
    counts = tuple(sample_counts_by_group.values())
    smallest = min(counts) if counts else 0
    largest = max(counts) if counts else 0
    unbalanced_group_count = (
        1
        if smallest and (largest / smallest) >= overloaded_carrier_ratio_threshold
        else 0
    )
    ready = (
        reference_dropout_count == 0
        and diagnostics.flagged_imbalance_count == 0
        and diagnostics.missing_channel_count == 0
        and unbalanced_group_count == 0
    )
    return MultiplexStressBenchmarkReport(
        bundle_missing_channel_count=len(quant_bundle.missing_channels),
        reference_dropout_count=reference_dropout_count,
        carrier_overload_count=carrier_overload_count,
        unbalanced_group_count=unbalanced_group_count,
        diagnostics=diagnostics,
        ready_for_biological_rollup=ready,
        note=(
            "multiplex support survives missing-channel, carrier, and balance stress"
            if ready
            else "multiplex support remains bounded by missing references, carrier pressure, or unbalanced design"
        ),
    )
