# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Flagship benchmark follow-up packets for lab-facing assay decisions."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.judgment.benchmark_corpora import (
    list_flagship_benchmark_reviews,
)
from bijux_proteomics_intelligence.judgment.benchmark_packets import (
    BenchmarkRecommendationPacket,
    build_flagship_benchmark_recommendation_packet_family,
)
from bijux_proteomics_intelligence.judgment.benchmark_policies import (
    BenchmarkDisposition,
)
from bijux_proteomics_intelligence.reviews.benchmarks import WorkflowBenchmarkReview
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)

__all__ = [
    "FlagshipAssayBurdenProfile",
    "FlagshipLabFollowUpPacket",
    "FlagshipLabFollowUpPacketFamily",
    "FlagshipLabPacketPosture",
    "build_flagship_lab_follow_up_packet",
    "build_flagship_lab_follow_up_packet_family",
]


class FlagshipLabPacketPosture(StrEnum):
    """Operational follow-up posture that the lab should carry forward."""

    EXPLORATORY_ONLY = "exploratory_only"
    DECISION_GRADE_CANDIDATE = "decision_grade_candidate"
    NOT_WORTH_ASSAY = "not_worth_assay"


class FlagshipAssayBurdenProfile(JsonModel):
    """Visible assay tradeoffs attached to one flagship follow-up packet."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    estimated_relative_cost: float = Field(..., ge=0.0)
    estimated_queue_days: int = Field(..., ge=0)
    confidence_gain_score: float = Field(..., ge=0.0, le=1.0)
    dependency_chain: tuple[str, ...] = Field(default_factory=tuple)
    tradeoffs: tuple[str, ...] = Field(default_factory=tuple)


class FlagshipLabFollowUpPacket(JsonModel):
    """Concrete lab-facing packet for one flagship benchmark workflow family."""

    model_config = ConfigDict(extra="forbid")

    packet_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    benchmark_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    benchmark_package_id: str | None = None
    disposition: BenchmarkDisposition
    posture: FlagshipLabPacketPosture
    suggested_assay_strategy: str = Field(..., min_length=1)
    exploratory_boundary: tuple[str, ...] = Field(default_factory=tuple)
    decision_grade_boundary: tuple[str, ...] = Field(default_factory=tuple)
    required_controls: tuple[str, ...] = Field(default_factory=tuple)
    design_conditions: tuple[str, ...] = Field(default_factory=tuple)
    expected_failure_modes: tuple[str, ...] = Field(default_factory=tuple)
    proceed_reasons: tuple[str, ...] = Field(default_factory=tuple)
    stop_reasons: tuple[str, ...] = Field(default_factory=tuple)
    comparator_pressure: tuple[str, ...] = Field(default_factory=tuple)
    burden_profile: FlagshipAssayBurdenProfile
    note: str = Field(..., min_length=1)


class FlagshipLabFollowUpPacketFamily(JsonModel):
    """Packet family for flagship benchmark-backed lab follow-up planning."""

    model_config = ConfigDict(extra="forbid")

    family_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    packets: tuple[FlagshipLabFollowUpPacket, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class _FollowUpBlueprint(JsonModel):
    """Durable per-family operational blueprint for lab packet construction."""

    model_config = ConfigDict(extra="forbid")

    suggested_assay_strategy: str = Field(..., min_length=1)
    exploratory_boundary: tuple[str, ...] = Field(default_factory=tuple)
    decision_grade_boundary: tuple[str, ...] = Field(default_factory=tuple)
    extra_controls: tuple[str, ...] = Field(default_factory=tuple)
    design_conditions: tuple[str, ...] = Field(default_factory=tuple)
    expected_failure_modes: tuple[str, ...] = Field(default_factory=tuple)
    proceed_reasons: tuple[str, ...] = Field(default_factory=tuple)
    stop_reasons: tuple[str, ...] = Field(default_factory=tuple)
    estimated_relative_cost: float = Field(..., ge=0.0)
    estimated_queue_days: int = Field(..., ge=0)
    confidence_gain_score: float = Field(..., ge=0.0, le=1.0)
    dependency_chain: tuple[str, ...] = Field(default_factory=tuple)
    tradeoffs: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


_PACKET_FAMILIES: tuple[KnowledgeWorkflowFamily, ...] = (
    KnowledgeWorkflowFamily.DDA,
    KnowledgeWorkflowFamily.DIA,
)

_FOLLOW_UP_BLUEPRINTS: dict[KnowledgeWorkflowFamily, _FollowUpBlueprint] = {
    KnowledgeWorkflowFamily.DDA: _FollowUpBlueprint(
        suggested_assay_strategy=(
            "Run one reviewable DDA confirmation lane with fresh digest material, pooled reference, and contaminant surveillance before broad biology is promoted."
        ),
        exploratory_boundary=(
            "Treat peptide and protein-level direction as exploratory while comparator-backed claim support remains advisory.",
            "Use the run to pressure calibration drift and protein-inference stability rather than to declare biological closure.",
        ),
        decision_grade_boundary=(
            "Promotion requires stable target-decoy behavior after the follow-up digest and no new contaminant-driven protein inference collapse.",
            "A decision-grade handoff also needs the pooled reference and blank controls to stay interpretable across the full run order.",
        ),
        extra_controls=("digest_reproducibility_reference", "carryover_blank"),
        design_conditions=(
            "Repeat the digest on the same biological material so disagreement is attributable to workflow pressure rather than sample drift.",
            "Keep the pooled reference at the start and end of the queue to expose run-order calibration movement.",
        ),
        expected_failure_modes=(
            "shared-peptide pressure changes protein-level conclusions even when peptide counts look stable",
            "contaminant promotion inflates confidence when blank carryover is not inspected",
        ),
        proceed_reasons=(
            "DDA still has review-grade grounding and advisory comparator support, so a bounded confirmation run can genuinely reduce uncertainty.",
            "The follow-up is cheaper than PTM or targeted escalation and directly tests the flagship identification backbone.",
        ),
        stop_reasons=(
            "Do not treat a single repeat as decision-grade if calibration drift reappears.",
            "Do not proceed if digest reproducibility control material is unavailable.",
        ),
        estimated_relative_cost=3.5,
        estimated_queue_days=11,
        confidence_gain_score=0.64,
        dependency_chain=(
            "fresh digest material",
            "pooled reference aliquot",
            "contaminant-aware search adapter normalization",
        ),
        tradeoffs=(
            "The assay is comparatively affordable, but its value collapses if contaminant and target-decoy checks are skipped.",
            "Confidence gain comes from reproducing identification semantics, not from discovering new biology.",
        ),
        note=(
            "This packet turns the DDA flagship review into one bounded confirmation lane instead of a vague rerun suggestion."
        ),
    ),
    KnowledgeWorkflowFamily.DIA: _FollowUpBlueprint(
        suggested_assay_strategy=(
            "Run one DIA follow-up that keeps library reference and pooled reference material in the queue, then separate exploratory extraction from any decision-worthy claim."
        ),
        exploratory_boundary=(
            "Exploratory DIA follow-up may confirm that extraction behavior is internally stable without proving that the library and vendor assumptions are closed.",
            "Treat biological interpretation as provisional until library-conditioned behavior and absent-expected-peptide pressure stay controlled.",
        ),
        decision_grade_boundary=(
            "A decision-grade follow-up needs stable library-reference behavior, no new missing expected peptide failures, and a clean distinction between import success and biological support.",
            "Queue pressure is acceptable only if the same controls can be repeated across the bridge and reference runs.",
        ),
        extra_controls=("bridge_sample",),
        design_conditions=(
            "Keep the same library reference and pooled reference in the run so library-conditioned extraction can be compared against the benchmark baseline.",
            "Reserve one bridge sample to tell apart instrument drift from library incompleteness.",
        ),
        expected_failure_modes=(
            "library incompleteness hides true peptide absence behind extraction failure",
            "ion-mobility or vendor-conditioned assumptions make the output look richer than the evidence posture warrants",
        ),
        proceed_reasons=(
            "DIA has review-grade grounding and can still teach the lab whether extraction stability survives a realistic follow-up queue.",
            "The packet makes the exploratory-versus-decision boundary explicit instead of letting the lab over-read a stable import surface.",
        ),
        stop_reasons=(
            "Do not use the run for a decision-grade claim if the library reference is missing.",
            "Do not interpret successful extraction as biological closure when expected peptides still disappear without explanation.",
        ),
        estimated_relative_cost=4.4,
        estimated_queue_days=15,
        confidence_gain_score=0.58,
        dependency_chain=(
            "library reference material",
            "pooled reference aliquot",
            "bridge sample for run-order drift",
        ),
        tradeoffs=(
            "The assay can reduce uncertainty, but only if the library-conditioned surface is kept honest in the run design itself.",
            "Operational burden is moderate because the queue must preserve a reference-rich structure rather than a single sample injection.",
        ),
        note=(
            "This packet makes DIA follow-up operationally real by distinguishing extraction success from decision-worthy evidence."
        ),
    ),
}


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


@lru_cache(maxsize=1)
def _reviews_by_family() -> dict[KnowledgeWorkflowFamily, WorkflowBenchmarkReview]:
    return {
        review.workflow_family: review for review in list_flagship_benchmark_reviews()
    }


@lru_cache(maxsize=1)
def _recommendation_packets_by_family() -> dict[
    KnowledgeWorkflowFamily, BenchmarkRecommendationPacket
]:
    family = build_flagship_benchmark_recommendation_packet_family()
    return {packet.workflow_family: packet for packet in family.packets}


def _posture_for_packet(
    packet: BenchmarkRecommendationPacket,
) -> FlagshipLabPacketPosture:
    if packet.disposition is BenchmarkDisposition.RECOMMEND:
        return FlagshipLabPacketPosture.DECISION_GRADE_CANDIDATE
    if packet.disposition is BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE:
        return FlagshipLabPacketPosture.EXPLORATORY_ONLY
    return FlagshipLabPacketPosture.NOT_WORTH_ASSAY


def build_flagship_lab_follow_up_packet(
    workflow_family: KnowledgeWorkflowFamily,
) -> FlagshipLabFollowUpPacket:
    """Build one concrete lab packet for a flagship benchmark workflow family."""

    if workflow_family not in _PACKET_FAMILIES:
        raise ValueError(
            f"unsupported flagship lab packet family: {workflow_family.value}"
        )

    review = _reviews_by_family()[workflow_family]
    recommendation_packet = _recommendation_packets_by_family()[workflow_family]
    blueprint = _FOLLOW_UP_BLUEPRINTS[workflow_family]
    required_controls = _dedupe(
        review.minimum_controls_required + blueprint.extra_controls
    )
    stop_reasons = _dedupe(
        recommendation_packet.blocker_set
        + review.comparator_failure_summaries
        + blueprint.stop_reasons
    )

    return FlagshipLabFollowUpPacket(
        packet_id=f"flagship_lab_packet:{workflow_family.value}",
        artifact_path=(
            "artifacts/lab/flagship-follow-up-packets/"
            f"{workflow_family.value}.json"
        ),
        benchmark_id=review.benchmark_id,
        workflow_family=workflow_family,
        benchmark_package_id=review.benchmark_package_id,
        disposition=recommendation_packet.disposition,
        posture=_posture_for_packet(recommendation_packet),
        suggested_assay_strategy=blueprint.suggested_assay_strategy,
        exploratory_boundary=_dedupe(
            recommendation_packet.downgrade_chain + blueprint.exploratory_boundary
        ),
        decision_grade_boundary=_dedupe(
            review.decision_grade_criteria + blueprint.decision_grade_boundary
        ),
        required_controls=required_controls,
        design_conditions=blueprint.design_conditions,
        expected_failure_modes=blueprint.expected_failure_modes,
        proceed_reasons=blueprint.proceed_reasons,
        stop_reasons=stop_reasons,
        comparator_pressure=review.comparator_failure_summaries,
        burden_profile=FlagshipAssayBurdenProfile(
            workflow_family=workflow_family,
            estimated_relative_cost=blueprint.estimated_relative_cost,
            estimated_queue_days=blueprint.estimated_queue_days,
            confidence_gain_score=blueprint.confidence_gain_score,
            dependency_chain=blueprint.dependency_chain,
            tradeoffs=blueprint.tradeoffs,
        ),
        note=blueprint.note,
    )


def build_flagship_lab_follow_up_packet_family() -> FlagshipLabFollowUpPacketFamily:
    """Build the current family of flagship benchmark-backed lab packets."""

    return FlagshipLabFollowUpPacketFamily(
        family_id="flagship-lab-follow-up-packets",
        artifact_path="artifacts/lab/flagship-follow-up-packets/family.json",
        packets=tuple(
            build_flagship_lab_follow_up_packet(workflow_family)
            for workflow_family in _PACKET_FAMILIES
        ),
        note=(
            "This family turns the current flagship benchmark reviews into concrete DDA and DIA lab follow-up packets with visible burden and boundary conditions."
        ),
    )
