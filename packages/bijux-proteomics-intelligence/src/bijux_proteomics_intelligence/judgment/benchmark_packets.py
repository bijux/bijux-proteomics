# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Full recommendation packets for flagship benchmark-backed workflow paths."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_foundation.support.states import SupportState
from bijux_proteomics_intelligence.judgment.benchmark_corpora import (
    BenchmarkDecisionCorpusKind,
    BenchmarkDecisionOption,
    BenchmarkDecisionScenario,
    BenchmarkDisposition,
    LabBurdenTier,
    list_flagship_benchmark_reviews,
)
from bijux_proteomics_intelligence.judgment.benchmark_policies import (
    BenchmarkDecisionPolicy,
    build_flagship_benchmark_decision_policy,
    evaluate_benchmark_decision_scenario,
)
from bijux_proteomics_intelligence.reviews.benchmarks import (
    ReviewerGroundingState,
    WorkflowBenchmarkReview,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparator_failures import (
    ComparatorClaimSupportState,
)

__all__ = [
    "BenchmarkRecommendationPacket",
    "BenchmarkRecommendationPacketFamily",
    "FlagshipBenchmarkEvidenceState",
    "build_flagship_benchmark_recommendation_packet_family",
]


class FlagshipBenchmarkEvidenceState(JsonModel):
    """Packet-friendly summary of benchmark evidence and review posture."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    public_claim_support_state: ComparatorClaimSupportState
    reviewer_grounding_state: ReviewerGroundingState
    ready_for_release_review: bool
    supported_claim_count: int = Field(..., ge=0)
    advisory_claim_count: int = Field(..., ge=0)
    refused_claim_count: int = Field(..., ge=0)


class BenchmarkRecommendationPacket(JsonModel):
    """Full outsider-readable recommendation packet for one flagship benchmark path."""

    model_config = ConfigDict(extra="forbid")

    packet_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    benchmark_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    benchmark_package_id: str | None = None
    disposition: BenchmarkDisposition
    downgrade_chain: tuple[str, ...] = Field(default_factory=tuple)
    blocker_set: tuple[str, ...] = Field(default_factory=tuple)
    evidence_state: FlagshipBenchmarkEvidenceState
    comparator_pressure: tuple[str, ...] = Field(default_factory=tuple)
    operational_implications: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class BenchmarkRecommendationPacketFamily(JsonModel):
    """Packet family covering every flagship benchmark workflow path."""

    model_config = ConfigDict(extra="forbid")

    family_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    packets: tuple[BenchmarkRecommendationPacket, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def _build_evidence_state(
    review: WorkflowBenchmarkReview,
) -> FlagshipBenchmarkEvidenceState:
    supported = sum(
        1
        for claim in review.claim_summaries
        if claim.support_state is SupportState.SUPPORTED
    )
    advisory = sum(
        1
        for claim in review.claim_summaries
        if claim.support_state is SupportState.ADVISORY
    )
    refused = sum(
        1
        for claim in review.claim_summaries
        if claim.support_state is SupportState.REFUSED
    )
    return FlagshipBenchmarkEvidenceState(
        benchmark_id=review.benchmark_id,
        workflow_family=review.workflow_family,
        public_claim_support_state=review.public_claim_support_state,
        reviewer_grounding_state=review.reviewer_grounding_state,
        ready_for_release_review=review.ready_for_release_review,
        supported_claim_count=supported,
        advisory_claim_count=advisory,
        refused_claim_count=refused,
    )


def build_flagship_benchmark_recommendation_packet_family(
    *,
    policy: BenchmarkDecisionPolicy | None = None,
) -> BenchmarkRecommendationPacketFamily:
    """Build full recommendation packets for every flagship benchmark workflow path."""

    active_policy = policy or build_flagship_benchmark_decision_policy()
    packets: list[BenchmarkRecommendationPacket] = []
    default_burdens = {
        KnowledgeWorkflowFamily.DDA: (LabBurdenTier.MEDIUM, 12),
        KnowledgeWorkflowFamily.DIA: (LabBurdenTier.MEDIUM, 17),
        KnowledgeWorkflowFamily.LFQ: (LabBurdenTier.MEDIUM, 18),
        KnowledgeWorkflowFamily.MULTIPLEX: (LabBurdenTier.HIGH, 22),
        KnowledgeWorkflowFamily.PTM: (LabBurdenTier.HIGH, 30),
        KnowledgeWorkflowFamily.TARGETED: (LabBurdenTier.HIGH, 28),
    }
    for review in list_flagship_benchmark_reviews():
        burden, turnaround = default_burdens[review.workflow_family]
        scenario = BenchmarkDecisionScenario(
            scenario_id=f"packet:{review.workflow_family.value}",
            corpus_kind=BenchmarkDecisionCorpusKind.RECOMMENDATION_QUALITY,
            summary=f"Solo recommendation packet for {review.workflow_family.value} benchmark review.",
            decision_quality_claim=(
                "A full recommendation packet must show conclusion, downgrade chain, blockers, evidence state, comparator pressure, and operational implications together."
            ),
            naive_failure_mode="solo packet still needs full benchmark-backed judgment rather than promotional summary",
            options=(
                BenchmarkDecisionOption(
                    option_id=f"{review.workflow_family.value}_packet_option",
                    review=review,
                    surface_attractiveness=0.72,
                    lab_burden=burden,
                    turnaround_days=turnaround,
                    burden_note="Packet burden is derived from the flagship workflow family follow-up profile.",
                ),
            ),
            expected_selected_option_id=None,
            expected_disposition=BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE,
        )
        outcome = evaluate_benchmark_decision_scenario(scenario, active_policy)
        packets.append(
            BenchmarkRecommendationPacket(
                packet_id=f"flagship_packet:{review.workflow_family.value}",
                artifact_path=(
                    "artifacts/intelligence/recommendation-packets/"
                    f"{review.workflow_family.value}.json"
                ),
                benchmark_id=review.benchmark_id,
                workflow_family=review.workflow_family,
                benchmark_package_id=review.benchmark_package_id,
                disposition=outcome.disposition,
                downgrade_chain=outcome.downgrade_chain,
                blocker_set=outcome.blocker_set,
                evidence_state=_build_evidence_state(review),
                comparator_pressure=review.comparator_failure_summaries,
                operational_implications=(
                    f"lab_burden={burden.value}",
                    f"turnaround_days={turnaround}",
                    *review.minimum_controls_required,
                ),
                note=(
                    "This packet keeps benchmark evidence posture, comparator pressure, and operational implications together for outsider inspection."
                ),
            )
        )
    return BenchmarkRecommendationPacketFamily(
        family_id="flagship-benchmark-recommendation-packets",
        artifact_path="artifacts/intelligence/recommendation-packets/flagship_packet_family.json",
        packets=tuple(packets),
        note=(
            "This family publishes one full recommendation packet per flagship workflow benchmark path."
        ),
    )
