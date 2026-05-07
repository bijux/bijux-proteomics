# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Flagship quantification pressure corpora tied to public LFQ benchmark packages."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.quantification.benchmarks import (
    EffectSizeStabilityBenchmarkReport,
    QuantMissingnessRobustnessReport,
    QuantNormalizationImpactBenchmarkReport,
)
from bijux_proteomics_foundation import JsonModel


class QuantificationPressureCorpusReport(JsonModel):
    """Study-scale quant pressure corpus that gathers the hardest LFQ credibility risks."""

    model_config = ConfigDict(extra="forbid")

    corpus_id: str = Field(..., min_length=1)
    benchmark_package_id: str = Field(..., min_length=1)
    supporting_identity_paths: tuple[str, ...] = Field(default_factory=tuple)
    missingness_robustness: QuantMissingnessRobustnessReport
    normalization_impact: QuantNormalizationImpactBenchmarkReport
    effect_size_stability: EffectSizeStabilityBenchmarkReport
    missingness_blocks_broad_claims: bool
    normalization_changes_primary_narrative: bool
    unstable_effect_size_narrative: bool
    ready_for_broad_quant_claim: bool
    note: str = Field(..., min_length=1)


def build_quantification_pressure_corpus_report(
    *,
    benchmark_package_id: str,
    supporting_identity_paths: tuple[str, ...],
    missingness_robustness: QuantMissingnessRobustnessReport,
    normalization_impact: QuantNormalizationImpactBenchmarkReport,
    effect_size_stability: EffectSizeStabilityBenchmarkReport,
) -> QuantificationPressureCorpusReport:
    """Build the flagship LFQ pressure corpus from study-scale evidence."""

    missingness_blocks = not missingness_robustness.robust_for_interpretation
    normalization_changes = normalization_impact.primary_narrative_changed
    unstable_effect_size = not (
        effect_size_stability.stable_top_rank and effect_size_stability.stable_top_set
    )
    ready = not (
        missingness_blocks or normalization_changes or unstable_effect_size
    )
    return QuantificationPressureCorpusReport(
        corpus_id="flagship_quant_pressure:lfq",
        benchmark_package_id=benchmark_package_id,
        supporting_identity_paths=tuple(sorted(supporting_identity_paths)),
        missingness_robustness=missingness_robustness,
        normalization_impact=normalization_impact,
        effect_size_stability=effect_size_stability,
        missingness_blocks_broad_claims=missingness_blocks,
        normalization_changes_primary_narrative=normalization_changes,
        unstable_effect_size_narrative=unstable_effect_size,
        ready_for_broad_quant_claim=ready,
        note=(
            "The flagship LFQ pressure corpus keeps study-scale missingness, normalization drift, and effect-size fragility together before quant claims travel as broad biology."
        ),
    )


__all__ = [
    "QuantificationPressureCorpusReport",
    "build_quantification_pressure_corpus_report",
]
