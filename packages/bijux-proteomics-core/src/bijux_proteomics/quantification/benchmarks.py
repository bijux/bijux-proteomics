# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Scientific benchmark surfaces for quantification credibility."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    LabelFreeQuantTable,
    MissingValueSummaryReport,
    Ms1FeatureRecord,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    normalize_label_free_table,
    summarize_missing_values,
)
from bijux_proteomics.quantification.readiness import (
    QuantDecisionReadinessReport,
    build_quant_decision_readiness_report,
)
from bijux_proteomics.quantification.review import (
    MissingnessMechanismKind,
    MissingnessMechanismProfileReport,
    QuantNormalizationPolicyKind,
    build_effect_size_first_differential_abundance_report,
    build_missingness_mechanism_profile_report,
)
from bijux_proteomics_foundation import JsonModel


class QuantMissingnessRobustnessReport(JsonModel):
    """Review-grade report linking missingness realism to quant readiness."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    normalization_method: NormalizationMethod
    missing_value_summary: MissingValueSummaryReport
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

    policies: tuple[tuple[QuantNormalizationPolicyKind, NormalizationMethod | None], ...] = (
        (QuantNormalizationPolicyKind.NONE, NormalizationMethod.NONE),
        (QuantNormalizationPolicyKind.MEDIAN, NormalizationMethod.MEDIAN),
        (QuantNormalizationPolicyKind.QUANTILE, NormalizationMethod.QUANTILE),
        (QuantNormalizationPolicyKind.VSN_LIKE, None),
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
                top_entity_effect_size=top.effect_size_cohens_d if top is not None else None,
                note="supported normalization policy produced a reviewable DA ranking",
            )
        )
    primary_narrative_changed = len(set(supported_tops)) > 1 if supported_tops else False
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
