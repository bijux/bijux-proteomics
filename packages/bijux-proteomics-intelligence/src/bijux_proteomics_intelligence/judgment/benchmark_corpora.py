# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Flagship benchmark-backed decision corpora for intelligence judgment."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.reviews.benchmarks import (
    WorkflowBenchmarkReview,
    build_dda_benchmark_review,
    build_dia_benchmark_review,
    build_lfq_benchmark_review,
    build_multiplex_benchmark_review,
    build_ptm_benchmark_review,
    build_targeted_benchmark_review,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)

__all__ = [
    "BenchmarkDecisionCorpus",
    "BenchmarkDecisionCorpusKind",
    "BenchmarkDecisionOption",
    "BenchmarkDecisionScenario",
    "BenchmarkDisposition",
    "LabBurdenTier",
    "build_comparator_aware_decision_corpus",
    "build_do_not_recommend_benchmark_suite",
    "build_downgrade_chain_honesty_corpus",
    "build_lab_burden_aware_decision_corpus",
    "build_recommendation_quality_corpus",
    "build_rejection_quality_corpus",
    "list_flagship_benchmark_reviews",
]


class BenchmarkDisposition(StrEnum):
    """Recommendation conclusion for one benchmark-backed choice scenario."""

    RECOMMEND = "recommend"
    RECOMMEND_WITH_DOWNGRADE = "recommend_with_downgrade"
    DO_NOT_RECOMMEND = "do_not_recommend"


class BenchmarkDecisionCorpusKind(StrEnum):
    """Controlled benchmark corpus family for judgment quality."""

    RECOMMENDATION_QUALITY = "recommendation_quality"
    REJECTION_QUALITY = "rejection_quality"
    COMPARATOR_AWARE = "comparator_aware"
    LAB_BURDEN_AWARE = "lab_burden_aware"
    DOWNGRADE_CHAIN_HONESTY = "downgrade_chain_honesty"
    DO_NOT_RECOMMEND = "do_not_recommend"


class LabBurdenTier(StrEnum):
    """Operational burden that must remain visible in recommendation quality."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BenchmarkDecisionOption(JsonModel):
    """One benchmark-backed path that intelligence may recommend or refuse."""

    model_config = ConfigDict(extra="forbid")

    option_id: str = Field(..., min_length=1)
    review: WorkflowBenchmarkReview
    surface_attractiveness: float = Field(..., ge=0.0, le=1.0)
    lab_burden: LabBurdenTier
    turnaround_days: int = Field(..., ge=1)
    burden_note: str = Field(..., min_length=1)


class BenchmarkDecisionScenario(JsonModel):
    """One controlled decision scenario over flagship benchmark-backed paths."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    corpus_kind: BenchmarkDecisionCorpusKind
    summary: str = Field(..., min_length=1)
    decision_quality_claim: str = Field(..., min_length=1)
    naive_failure_mode: str = Field(..., min_length=1)
    options: tuple[BenchmarkDecisionOption, ...] = Field(default_factory=tuple)
    expected_selected_option_id: str | None = None
    expected_disposition: BenchmarkDisposition
    required_downgrade_reasons: tuple[str, ...] = Field(default_factory=tuple)
    required_blockers: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkDecisionCorpus(JsonModel):
    """One governed corpus for benchmark-backed recommendation quality."""

    model_config = ConfigDict(extra="forbid")

    corpus_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    corpus_kind: BenchmarkDecisionCorpusKind
    scenarios: tuple[BenchmarkDecisionScenario, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


@lru_cache(maxsize=1)
def list_flagship_benchmark_reviews() -> tuple[WorkflowBenchmarkReview, ...]:
    """Return the flagship benchmark review surfaces used by decision corpora."""

    return (
        build_dda_benchmark_review(),
        build_dia_benchmark_review(),
        build_lfq_benchmark_review(),
        build_multiplex_benchmark_review(),
        build_ptm_benchmark_review(),
        build_targeted_benchmark_review(),
    )


def _review_by_family(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowBenchmarkReview:
    return next(
        review
        for review in list_flagship_benchmark_reviews()
        if review.workflow_family is workflow_family
    )


def _solo_option(
    workflow_family: KnowledgeWorkflowFamily,
    *,
    option_id: str,
    surface_attractiveness: float,
    lab_burden: LabBurdenTier,
    turnaround_days: int,
    burden_note: str,
) -> BenchmarkDecisionOption:
    return BenchmarkDecisionOption(
        option_id=option_id,
        review=_review_by_family(workflow_family),
        surface_attractiveness=surface_attractiveness,
        lab_burden=lab_burden,
        turnaround_days=turnaround_days,
        burden_note=burden_note,
    )


def build_recommendation_quality_corpus() -> BenchmarkDecisionCorpus:
    """Build benchmark scenarios where safer and more reproducible paths should win."""

    return BenchmarkDecisionCorpus(
        corpus_id="flagship-recommendation-quality-corpus",
        artifact_path="artifacts/intelligence/benchmark-decisions/recommendation_quality.json",
        corpus_kind=BenchmarkDecisionCorpusKind.RECOMMENDATION_QUALITY,
        scenarios=(
            BenchmarkDecisionScenario(
                scenario_id="safer-reviewable-path-over-flashy-thin-ptm",
                corpus_kind=BenchmarkDecisionCorpusKind.RECOMMENDATION_QUALITY,
                summary=(
                    "A DDA path with bounded comparator caveats should beat a flashier PTM path "
                    "whose public claim posture is still refused."
                ),
                decision_quality_claim=(
                    "The right recommendation should prefer the safer and more reproducible flagship path, "
                    "not simply the most visually attractive evidence surface."
                ),
                naive_failure_mode=(
                    "surface appeal overweights PTM novelty and hides that comparator-backed claim support is still refused"
                ),
                options=(
                    _solo_option(
                        KnowledgeWorkflowFamily.DDA,
                        option_id="dda_reviewable_path",
                        surface_attractiveness=0.72,
                        lab_burden=LabBurdenTier.MEDIUM,
                        turnaround_days=12,
                        burden_note="DDA follow-up needs standard controls but does not demand specialized validation lanes.",
                    ),
                    _solo_option(
                        KnowledgeWorkflowFamily.PTM,
                        option_id="ptm_flashy_path",
                        surface_attractiveness=0.94,
                        lab_burden=LabBurdenTier.HIGH,
                        turnaround_days=26,
                        burden_note="PTM follow-up carries localization, enrichment, and validation burden before it becomes decision-worthy.",
                    ),
                ),
                expected_selected_option_id="dda_reviewable_path",
                expected_disposition=BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE,
                required_downgrade_reasons=(
                    "external comparator claim support is still advisory",
                ),
            ),
        ),
        note=(
            "This corpus proves the intelligence layer should prefer flagship benchmark paths that are safer and more reproducible, "
            "not merely more attractive on the surface."
        ),
    )


def build_rejection_quality_corpus() -> BenchmarkDecisionCorpus:
    """Build benchmark scenarios where refusal or hard downgrade is the correct call."""

    return BenchmarkDecisionCorpus(
        corpus_id="flagship-rejection-quality-corpus",
        artifact_path="artifacts/intelligence/benchmark-decisions/rejection_quality.json",
        corpus_kind=BenchmarkDecisionCorpusKind.REJECTION_QUALITY,
        scenarios=(
            BenchmarkDecisionScenario(
                scenario_id="refuse-thin-targeted-and-ptm-promotion",
                corpus_kind=BenchmarkDecisionCorpusKind.REJECTION_QUALITY,
                summary=(
                    "PTM and targeted paths can look operationally exciting while still lacking enough grounded and burden-justified trust to justify promotion."
                ),
                decision_quality_claim=(
                    "The right decision is refusal when attractive benchmark surfaces remain thin, contradictory, or operationally unjustified."
                ),
                naive_failure_mode=(
                    "promotion by assay excitement ignores thin grounding and high follow-up burden"
                ),
                options=(
                    _solo_option(
                        KnowledgeWorkflowFamily.PTM,
                        option_id="ptm_promotion_attempt",
                        surface_attractiveness=0.91,
                        lab_burden=LabBurdenTier.HIGH,
                        turnaround_days=30,
                        burden_note="PTM validation demands enrichment, ambiguity control, and site-specific follow-up before promotion is defensible.",
                    ),
                    _solo_option(
                        KnowledgeWorkflowFamily.TARGETED,
                        option_id="targeted_promotion_attempt",
                        surface_attractiveness=0.87,
                        lab_burden=LabBurdenTier.HIGH,
                        turnaround_days=28,
                        burden_note="Targeted follow-up depends on heavy references, calibration standards, and interference review that are still only advisory in the benchmark review.",
                    ),
                ),
                expected_selected_option_id=None,
                expected_disposition=BenchmarkDisposition.DO_NOT_RECOMMEND,
                required_blockers=(
                    "biological grounding remains thin",
                    "operational burden remains too high for a justified recommendation",
                ),
            ),
        ),
        note=(
            "This corpus proves the intelligence layer can refuse attractive but underpowered flagship benchmark paths."
        ),
    )


def build_comparator_aware_decision_corpus() -> BenchmarkDecisionCorpus:
    """Build benchmark scenarios where external comparator posture must change the decision."""

    return BenchmarkDecisionCorpus(
        corpus_id="flagship-comparator-aware-decision-corpus",
        artifact_path="artifacts/intelligence/benchmark-decisions/comparator_aware.json",
        corpus_kind=BenchmarkDecisionCorpusKind.COMPARATOR_AWARE,
        scenarios=(
            BenchmarkDecisionScenario(
                scenario_id="comparator-mismatch-blocks-lfq-promotion",
                corpus_kind=BenchmarkDecisionCorpusKind.COMPARATOR_AWARE,
                summary=(
                    "Bounded comparator posture on the LFQ path should still materially change the recommendation and keep the safer DIA path ahead."
                ),
                decision_quality_claim=(
                    "External tool mismatches must change recommendation output, not merely decorate it."
                ),
                naive_failure_mode=(
                    "surface-heavy ranking promotes LFQ repeatability without treating advisory comparator posture as decision-changing evidence"
                ),
                options=(
                    _solo_option(
                        KnowledgeWorkflowFamily.DIA,
                        option_id="dia_library_path",
                        surface_attractiveness=0.7,
                        lab_burden=LabBurdenTier.MEDIUM,
                        turnaround_days=15,
                        burden_note="DIA follow-up still needs library and vendor scrutiny, but the review stays above thin-grounding posture.",
                    ),
                    _solo_option(
                        KnowledgeWorkflowFamily.LFQ,
                        option_id="lfq_repeatability_path",
                        surface_attractiveness=0.84,
                        lab_burden=LabBurdenTier.MEDIUM,
                        turnaround_days=16,
                        burden_note="LFQ follow-up looks inexpensive, but comparator-backed trust remains advisory and generalization stays bounded in the benchmark review.",
                    ),
                ),
                expected_selected_option_id="dia_library_path",
                expected_disposition=BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE,
                required_downgrade_reasons=(
                    "vendor and library comparison gaps remain open",
                ),
            ),
        ),
        note=(
            "This corpus forces comparator posture to alter the recommendation instead of staying as decorative review prose."
        ),
    )


def build_lab_burden_aware_decision_corpus() -> BenchmarkDecisionCorpus:
    """Build benchmark scenarios where cost, burden, and turnaround must change the decision."""

    return BenchmarkDecisionCorpus(
        corpus_id="flagship-lab-burden-aware-decision-corpus",
        artifact_path="artifacts/intelligence/benchmark-decisions/lab_burden_aware.json",
        corpus_kind=BenchmarkDecisionCorpusKind.LAB_BURDEN_AWARE,
        scenarios=(
            BenchmarkDecisionScenario(
                scenario_id="lab-burden-favors-dda-over-targeted",
                corpus_kind=BenchmarkDecisionCorpusKind.LAB_BURDEN_AWARE,
                summary=(
                    "A targeted path with high assay burden should not outrank a more reviewable DDA path when the scientific basis is weaker."
                ),
                decision_quality_claim=(
                    "Replicate cost, assay burden, and turnaround should materially change the correct recommendation."
                ),
                naive_failure_mode=(
                    "targeted assay excitement hides heavy-reference, calibration, and interference burden"
                ),
                options=(
                    _solo_option(
                        KnowledgeWorkflowFamily.DDA,
                        option_id="dda_follow_up_path",
                        surface_attractiveness=0.71,
                        lab_burden=LabBurdenTier.MEDIUM,
                        turnaround_days=12,
                        burden_note="DDA follow-up stays within ordinary reviewable benchmark controls.",
                    ),
                    _solo_option(
                        KnowledgeWorkflowFamily.TARGETED,
                        option_id="targeted_high_burden_path",
                        surface_attractiveness=0.89,
                        lab_burden=LabBurdenTier.HIGH,
                        turnaround_days=29,
                        burden_note="Targeted follow-up carries heavy-reference, calibration, and interference obligations before a lab should spend effort.",
                    ),
                ),
                expected_selected_option_id="dda_follow_up_path",
                expected_disposition=BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE,
                required_downgrade_reasons=(
                    "external comparator claim support is still advisory",
                ),
            ),
            BenchmarkDecisionScenario(
                scenario_id="borderline-dia-burden-still-confuses-current-policy",
                corpus_kind=BenchmarkDecisionCorpusKind.LAB_BURDEN_AWARE,
                summary=(
                    "A borderline DIA-versus-targeted choice still exposes that the current flagship policy does not weight assay burden harshly enough."
                ),
                decision_quality_claim=(
                    "Current intelligence should admit when it still chooses badly on borderline burden-heavy flagship benchmark choices."
                ),
                naive_failure_mode=(
                    "surface strength and moderate review posture still outweigh the operational cost that should keep the recommendation on hold"
                ),
                options=(
                    _solo_option(
                        KnowledgeWorkflowFamily.DIA,
                        option_id="dia_borderline_path",
                        surface_attractiveness=0.82,
                        lab_burden=LabBurdenTier.HIGH,
                        turnaround_days=24,
                        burden_note="DIA follow-up here still drags library, vendor, and control burden into a borderline package.",
                    ),
                    _solo_option(
                        KnowledgeWorkflowFamily.TARGETED,
                        option_id="targeted_borderline_path",
                        surface_attractiveness=0.8,
                        lab_burden=LabBurdenTier.HIGH,
                        turnaround_days=27,
                        burden_note="Targeted follow-up remains expensive and comparator-thin even when it looks focused.",
                    ),
                ),
                expected_selected_option_id=None,
                expected_disposition=BenchmarkDisposition.DO_NOT_RECOMMEND,
                required_blockers=(
                    "operational burden remains too high for a justified recommendation",
                ),
            ),
        ),
        note=(
            "This corpus keeps lab burden visible and also records one current failure case instead of pretending the policy is already perfect."
        ),
    )


def build_downgrade_chain_honesty_corpus() -> BenchmarkDecisionCorpus:
    """Build benchmark scenarios where recommendation strength must keep uncertainty visible."""

    return BenchmarkDecisionCorpus(
        corpus_id="flagship-downgrade-chain-honesty-corpus",
        artifact_path="artifacts/intelligence/benchmark-decisions/downgrade_chain_honesty.json",
        corpus_kind=BenchmarkDecisionCorpusKind.DOWNGRADE_CHAIN_HONESTY,
        scenarios=(
            BenchmarkDecisionScenario(
                scenario_id="dia-recommendation-must-keep-its-caveats-visible",
                corpus_kind=BenchmarkDecisionCorpusKind.DOWNGRADE_CHAIN_HONESTY,
                summary=(
                    "A recommendable DIA path still has to show the weaker evidence it overcame."
                ),
                decision_quality_claim=(
                    "Strong recommendations must keep downgrade chains visible instead of flattening uncertainty away."
                ),
                naive_failure_mode=(
                    "promotion language drops comparator and vendor caveats once the path remains nominally ready for review"
                ),
                options=(
                    _solo_option(
                        KnowledgeWorkflowFamily.DIA,
                        option_id="dia_caveat_visible_path",
                        surface_attractiveness=0.77,
                        lab_burden=LabBurdenTier.MEDIUM,
                        turnaround_days=17,
                        burden_note="DIA follow-up remains plausible, but comparator and vendor gaps still matter.",
                    ),
                ),
                expected_selected_option_id="dia_caveat_visible_path",
                expected_disposition=BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE,
                required_downgrade_reasons=(
                    "vendor and library comparison gaps remain open",
                    "claim support is not yet strong enough for an unqualified recommendation",
                ),
            ),
        ),
        note=(
            "This corpus proves the downgrade chain remains attached to the recommendation instead of being scrubbed from the final packet."
        ),
    )


def build_do_not_recommend_benchmark_suite() -> BenchmarkDecisionCorpus:
    """Build benchmark scenarios that must resolve to no recommendation at all."""

    return BenchmarkDecisionCorpus(
        corpus_id="flagship-do-not-recommend-suite",
        artifact_path="artifacts/intelligence/benchmark-decisions/do_not_recommend.json",
        corpus_kind=BenchmarkDecisionCorpusKind.DO_NOT_RECOMMEND,
        scenarios=(
            BenchmarkDecisionScenario(
                scenario_id="multiplex-stays-on-hold-with-internal-support-only-authority",
                corpus_kind=BenchmarkDecisionCorpusKind.DO_NOT_RECOMMEND,
                summary=(
                    "Multiplex should still resolve to no action while it remains an internal-support family without outsider review or lab consequence authority."
                ),
                decision_quality_claim=(
                    "The intelligence layer must choose no action when a workflow family is still explicitly narrowed to internal support only."
                ),
                naive_failure_mode=(
                    "supportive internal signals are mistaken for decision-worthy trust even though the workflow family remains internal-support only"
                ),
                options=(
                    _solo_option(
                        KnowledgeWorkflowFamily.MULTIPLEX,
                        option_id="multiplex_hold_path",
                        surface_attractiveness=0.85,
                        lab_burden=LabBurdenTier.HIGH,
                        turnaround_days=22,
                        burden_note="Multiplex follow-up adds reference-channel and interference burden on top of refused comparator trust.",
                    ),
                ),
                expected_selected_option_id=None,
                expected_disposition=BenchmarkDisposition.DO_NOT_RECOMMEND,
                required_blockers=(
                    "public comparator-backed claim support is refused",
                    "biological grounding remains thin",
                    "operational burden remains too high for a justified recommendation",
                ),
            ),
            BenchmarkDecisionScenario(
                scenario_id="ptm-and-targeted-remain-unjustified-for-lab-spend",
                corpus_kind=BenchmarkDecisionCorpusKind.DO_NOT_RECOMMEND,
                summary=(
                    "PTM and targeted still do not justify lab spend when both remain exploratory and burden-heavy."
                ),
                decision_quality_claim=(
                    "Weak comparator trust plus high operational burden should force a do-not-recommend outcome."
                ),
                naive_failure_mode=(
                    "specialized assay excitement hides thin grounding and expensive follow-up requirements"
                ),
                options=(
                    _solo_option(
                        KnowledgeWorkflowFamily.PTM,
                        option_id="ptm_hold_path",
                        surface_attractiveness=0.9,
                        lab_burden=LabBurdenTier.HIGH,
                        turnaround_days=30,
                        burden_note="PTM follow-up remains expensive and ambiguity-heavy.",
                    ),
                    _solo_option(
                        KnowledgeWorkflowFamily.TARGETED,
                        option_id="targeted_hold_path",
                        surface_attractiveness=0.86,
                        lab_burden=LabBurdenTier.HIGH,
                        turnaround_days=28,
                        burden_note="Targeted follow-up remains calibration-heavy and comparator-thin.",
                    ),
                ),
                expected_selected_option_id=None,
                expected_disposition=BenchmarkDisposition.DO_NOT_RECOMMEND,
                required_blockers=(
                    "operational burden remains too high for a justified recommendation",
                ),
            ),
        ),
        note=(
            "This suite explicitly proves that the intelligence layer can recommend no action when flagship benchmark evidence is still too weak."
        ),
    )
