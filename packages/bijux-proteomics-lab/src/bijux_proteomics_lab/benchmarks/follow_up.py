# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Flagship benchmark follow-up packets for lab-facing assay decisions."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from functools import lru_cache

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_foundation.support.states import SupportState
from bijux_proteomics_intelligence.judgment.benchmark_corpora import (
    BenchmarkDisposition,
    list_flagship_benchmark_reviews,
)
from bijux_proteomics_intelligence.judgment.benchmark_packets import (
    BenchmarkRecommendationPacket,
    build_flagship_benchmark_recommendation_packet_family,
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
    "FlagshipAssayBurdenProfile",
    "FlagshipAssayBurdenReport",
    "FlagshipAssayBurdenReportEntry",
    "FlagshipLabFollowUpPacket",
    "FlagshipLabFollowUpPacketFamily",
    "FlagshipLabPacketPosture",
    "FlagshipLabReviewBoardArtifact",
    "FlagshipLabReviewBoardEntry",
    "FlagshipMinimumControlsTable",
    "FlagshipMinimumControlsTableEntry",
    "FlagshipNotWorthAssayEntry",
    "FlagshipNotWorthAssayReport",
    "build_flagship_assay_burden_report",
    "build_flagship_lab_follow_up_packet",
    "build_flagship_lab_follow_up_packet_family",
    "build_flagship_lab_review_board",
    "build_flagship_minimum_controls_table",
    "build_flagship_not_worth_assay_report",
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


class FlagshipAssayBurdenReportEntry(JsonModel):
    """One ranked burden row across flagship lab follow-up packets."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    posture: FlagshipLabPacketPosture
    burden_profile: FlagshipAssayBurdenProfile
    queue_posture: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class FlagshipAssayBurdenReport(JsonModel):
    """Aggregate assay burden surface for flagship lab follow-up work."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[FlagshipAssayBurdenReportEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipNotWorthAssayEntry(JsonModel):
    """One interesting-but-not-justified assay escalation entry."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    blocker_summary: tuple[str, ...] = Field(default_factory=tuple)
    burden_tradeoffs: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipNotWorthAssayReport(JsonModel):
    """Explicit refusal surface for assays that still are not worth running."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[FlagshipNotWorthAssayEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipMinimumControlsTableEntry(JsonModel):
    """Per-family control and design bar for honest decision-grade packets."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    minimum_controls: tuple[str, ...] = Field(default_factory=tuple)
    design_conditions: tuple[str, ...] = Field(default_factory=tuple)
    decision_grade_bar: tuple[str, ...] = Field(default_factory=tuple)
    currently_decision_grade_ready: bool
    current_blockers: tuple[str, ...] = Field(default_factory=tuple)


class FlagshipMinimumControlsTable(JsonModel):
    """Cross-family minimum-controls table for flagship lab packets."""

    model_config = ConfigDict(extra="forbid")

    table_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[FlagshipMinimumControlsTableEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class FlagshipLabReviewBoardEntry(JsonModel):
    """Ranked cross-family follow-up candidate for lab review-board decisions."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    scientific_credibility_score: float = Field(..., ge=0.0, le=1.0)
    operational_feasibility_score: float = Field(..., ge=0.0, le=1.0)
    overall_priority_score: float = Field(..., ge=0.0, le=1.0)
    recommendation_posture: str = Field(..., min_length=1)
    rationale: tuple[str, ...] = Field(default_factory=tuple)


class FlagshipLabReviewBoardArtifact(JsonModel):
    """Lab-facing ranked review board artifact across flagship benchmark packages."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[FlagshipLabReviewBoardEntry, ...] = Field(default_factory=tuple)
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
    KnowledgeWorkflowFamily.LFQ,
    KnowledgeWorkflowFamily.PTM,
    KnowledgeWorkflowFamily.TARGETED,
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
    KnowledgeWorkflowFamily.LFQ: _FollowUpBlueprint(
        suggested_assay_strategy=(
            "Run one LFQ replicate-expansion and batch-bridge follow-up only if the study design can honestly absorb more replicates and preserve predeclared contrasts."
        ),
        exploratory_boundary=(
            "Any LFQ repeat remains exploratory while missingness and normalization fragility are still dominating the contrast.",
            "Treat apparent effect recovery as provisional until replicate balance and bridge behavior stay stable across the full design.",
        ),
        decision_grade_boundary=(
            "Decision-grade LFQ follow-up requires at least one batch bridge, randomized acquisition order, and enough biological replication to keep the contrast from being single-sample theater.",
            "The lab packet should not upgrade LFQ if effect size stability still depends on imputation-sensitive rows.",
        ),
        extra_controls=("replicate_balance_audit",),
        design_conditions=(
            "Add enough biological replicates to make the target contrast interpretable rather than simply less noisy.",
            "Preserve randomized run order and a batch bridge so normalization drift is measurable rather than guessed.",
        ),
        expected_failure_modes=(
            "MNAR missingness makes the apparent rescue of a contrast look stronger than it is",
            "batch drift dominates the signal when bridge material is absent or underused",
        ),
        proceed_reasons=(
            "Only proceed when additional material can create a real replicate structure instead of a token rerun.",
            "The assay is useful only if the team is willing to keep the contrast and normalization plan fixed before the rerun.",
        ),
        stop_reasons=(
            "Do not spend the assay if only one extra sample can be added to a fragile contrast.",
            "Do not proceed when the run order and bridge design cannot be controlled tightly enough to learn anything new.",
        ),
        estimated_relative_cost=5.8,
        estimated_queue_days=18,
        confidence_gain_score=0.42,
        dependency_chain=(
            "additional biological replicates",
            "batch bridge material",
            "prespecified contrast and normalization plan",
        ),
        tradeoffs=(
            "LFQ follow-up can be moderately expensive while still failing to change belief if the replicate design remains weak.",
            "Confidence gain is capped because missingness and normalization pressure can survive a larger queue.",
        ),
        note=(
            "This packet keeps replicate and design realism visible so LFQ is not promoted by a cosmetic rerun."
        ),
    ),
    KnowledgeWorkflowFamily.PTM: _FollowUpBlueprint(
        suggested_assay_strategy=(
            "Run one PTM validation lane only if a site-targetable follow-up can preserve localized fragments, modified-versus-unmodified counterparts, and orthogonal confirmation."
        ),
        exploratory_boundary=(
            "PTM follow-up stays exploratory while site ambiguity, enrichment pressure, or motif storytelling remain unresolved.",
            "Treat any early phosphosite signal as advisory unless localization and counterpart evidence survive orthogonal review.",
        ),
        decision_grade_boundary=(
            "Decision-grade PTM follow-up requires site-localizing fragments, matched unmodified counterpart evidence, and a validation method that can separate neighboring ambiguous sites.",
            "Do not claim a decision-grade PTM packet if the lab cannot actually target the localized peptide with durable specificity.",
        ),
        extra_controls=("unmodified_counterpart_control",),
        design_conditions=(
            "Confirm that the localized peptide can be targeted without collapsing neighboring ambiguous sites into one assay.",
            "Plan the orthogonal confirmation method before the enrichment run so ambiguity handling is not postponed.",
        ),
        expected_failure_modes=(
            "site ambiguity survives the rerun and leaves the lab with a more expensive version of the same story",
            "enrichment or motif pressure creates a convincing signal without a targetable site-specific conclusion",
        ),
        proceed_reasons=(
            "Only proceed when the site is targetable enough for a real assay and the orthogonal confirmation path already exists.",
            "The effort is justified only if counterpart and localization evidence can both move, not just the modified signal alone.",
        ),
        stop_reasons=(
            "Do not proceed when site ambiguity is still the main story.",
            "Do not spend the assay if the orthogonal confirmation lane is unavailable or biologically non-specific.",
        ),
        estimated_relative_cost=8.3,
        estimated_queue_days=29,
        confidence_gain_score=0.34,
        dependency_chain=(
            "site-targetable localized peptide",
            "orthogonal site confirmation method",
            "modified and unmodified counterpart quantification plan",
        ),
        tradeoffs=(
            "PTM follow-up is expensive because ambiguity resolution and orthogonal confirmation are both first-class dependencies.",
            "Confidence gain stays low when the benchmark review is still thin and comparator-backed support is refused.",
        ),
        note=(
            "This packet stops PTM enthusiasm from outrunning targetability, localization, and orthogonal validation reality."
        ),
    ),
    KnowledgeWorkflowFamily.TARGETED: _FollowUpBlueprint(
        suggested_assay_strategy=(
            "Run one targeted transition panel only if heavy references, calibration standards, and interference review are already secured for the prioritized transitions."
        ),
        exploratory_boundary=(
            "A targeted follow-up remains exploratory while transition approval, heavy-light pairing, and interference handling still carry benchmark blockers.",
            "Treat a clean chromatogram as advisory until calibration and interference consequences are closed across the full panel.",
        ),
        decision_grade_boundary=(
            "Decision-grade targeted work requires approved transitions, heavy references, calibration standards, and interference scans that remain stable across replicates.",
            "Do not call the packet decision-grade when the transition panel is still optimized around a thin or refused discovery claim.",
        ),
        extra_controls=("interference_scout_injection",),
        design_conditions=(
            "Lock the transition list before acquisition so assay success is not redefined after the run.",
            "Include heavy-light pairing and calibration standards in the same queue used for the real sample interpretation.",
        ),
        expected_failure_modes=(
            "coeluting interference produces clean-looking transitions that still misstate the biology",
            "heavy-light mismatch or calibration drift turns the panel into an operationally neat but scientifically weak artifact",
        ),
        proceed_reasons=(
            "Proceed only when the transition panel, heavy references, and calibration materials already exist as governed dependencies.",
            "The assay is worth running only if interference handling can falsify the discovery story instead of merely decorating it.",
        ),
        stop_reasons=(
            "Do not proceed when heavy references or calibration standards are missing.",
            "Do not spend the assay when transition approval is still exploratory or interference handling is unresolved.",
        ),
        estimated_relative_cost=6.9,
        estimated_queue_days=21,
        confidence_gain_score=0.47,
        dependency_chain=(
            "approved transition panel",
            "heavy reference peptides",
            "calibration standards",
            "interference review injection",
        ),
        tradeoffs=(
            "Targeted follow-up can look operationally mature while still inheriting thin biological grounding from the discovery layer.",
            "Confidence gain depends on interference and calibration discipline, not on the presence of a neat panel alone.",
        ),
        note=(
            "This packet keeps transition, calibration, and interference consequences explicit before the lab spends effort on targeted follow-up."
        ),
    ),
    KnowledgeWorkflowFamily.MULTIPLEX: _FollowUpBlueprint(
        suggested_assay_strategy=(
            "Run one multiplex follow-up only if reference and bridge channels can be preserved and the carrier-load story remains quantitatively honest."
        ),
        exploratory_boundary=(
            "Multiplex follow-up stays exploratory while ratio compression, bridge behavior, and design imbalance still dominate the interpretation.",
        ),
        decision_grade_boundary=(
            "Decision-grade multiplex work requires stable reference or bridge channels, explicit carrier-load accounting, and a balanced label design that does not bury the claim in channel asymmetry.",
        ),
        extra_controls=("carrier_load_audit",),
        design_conditions=(
            "Keep reference and bridge channels inside the same label map used for the real samples.",
            "Declare carrier and channel-balance assumptions before the run begins.",
        ),
        expected_failure_modes=(
            "ratio compression survives the rerun and makes the quantitative story look cleaner than it is",
            "unbalanced channel design hides the fact that the signal is structurally fragile",
        ),
        proceed_reasons=(
            "Proceed only when the label map and carrier posture can be defended as part of the scientific design, not as a convenience.",
        ),
        stop_reasons=(
            "Do not proceed without defended bridge or reference channels.",
            "Do not queue the run when carrier assumptions remain opaque.",
        ),
        estimated_relative_cost=7.4,
        estimated_queue_days=25,
        confidence_gain_score=0.31,
        dependency_chain=(
            "reference or bridge channels",
            "declared carrier strategy",
            "balanced label map",
        ),
        tradeoffs=(
            "Multiplex follow-up can consume substantial queue and reagent budget while still remaining quantitatively fragile.",
            "Confidence gain is low because the benchmark review is still thin and comparator-backed support is refused.",
        ),
        note=(
            "This blueprint keeps multiplex review-board scoring honest even though no dedicated packet is promoted in this tranche."
        ),
    ),
}


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
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
            f"artifacts/lab/flagship-follow-up-packets/{workflow_family.value}.json"
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
            "This family turns the current flagship benchmark reviews into concrete DDA, DIA, LFQ, PTM, and targeted lab follow-up packets with visible burden and boundary conditions."
        ),
    )


def build_flagship_assay_burden_report() -> FlagshipAssayBurdenReport:
    """Build a ranked burden report across flagship lab follow-up packets."""

    entries: list[FlagshipAssayBurdenReportEntry] = []
    for packet in build_flagship_lab_follow_up_packet_family().packets:
        queue_posture = (
            "reserve_controlled_queue_slot"
            if packet.posture is FlagshipLabPacketPosture.EXPLORATORY_ONLY
            else "do_not_queue_until_blockers_close"
        )
        entries.append(
            FlagshipAssayBurdenReportEntry(
                workflow_family=packet.workflow_family,
                benchmark_id=packet.benchmark_id,
                posture=packet.posture,
                burden_profile=packet.burden_profile,
                queue_posture=queue_posture,
                note=(
                    "This row keeps cost, queue, dependency, and confidence tradeoffs visible at the same layer where the lab decides whether to allocate effort."
                ),
            )
        )
    ranked_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (
                -entry.burden_profile.estimated_relative_cost,
                -entry.burden_profile.estimated_queue_days,
            ),
        )
    )
    return FlagshipAssayBurdenReport(
        report_id="flagship-assay-burden-report",
        artifact_path="artifacts/lab/flagship-follow-up-packets/burden_report.json",
        entries=ranked_entries,
        note=(
            "This report ranks flagship follow-up work by visible assay burden instead of letting queue pressure hide inside packet prose."
        ),
    )


def build_flagship_not_worth_assay_report() -> FlagshipNotWorthAssayReport:
    """Build the explicit interesting-but-not-justified assay report."""

    entries = tuple(
        FlagshipNotWorthAssayEntry(
            workflow_family=packet.workflow_family,
            benchmark_id=packet.benchmark_id,
            blocker_summary=packet.stop_reasons[:3],
            burden_tradeoffs=packet.burden_profile.tradeoffs,
            note=(
                "The workflow remains scientifically interesting, but the current packet still says the assay is not worth spending until named blockers close."
            ),
        )
        for packet in build_flagship_lab_follow_up_packet_family().packets
        if packet.posture is FlagshipLabPacketPosture.NOT_WORTH_ASSAY
    )
    return FlagshipNotWorthAssayReport(
        report_id="flagship-not-worth-assay-report",
        artifact_path="artifacts/lab/flagship-follow-up-packets/not_worth_assay.json",
        entries=entries,
        note=(
            "This report makes refusal visible when a benchmark path is still too weak, ambiguous, or expensive to justify action."
        ),
    )


def _claim_support_score(review: WorkflowBenchmarkReview) -> float:
    if not review.claim_summaries:
        return 0.0
    total = 0.0
    for claim in review.claim_summaries:
        if claim.support_state is SupportState.SUPPORTED:
            total += 1.0
        elif claim.support_state is SupportState.ADVISORY:
            total += 0.5
        elif claim.support_state is SupportState.AMBIGUOUS:
            total += 0.25
    return total / len(review.claim_summaries)


def _comparator_score(review: WorkflowBenchmarkReview) -> float:
    if review.public_claim_support_state is ComparatorClaimSupportState.SUPPORTED:
        return 1.0
    if review.public_claim_support_state is ComparatorClaimSupportState.ADVISORY:
        return 0.55
    return 0.0


def _grounding_score(review: WorkflowBenchmarkReview) -> float:
    if review.reviewer_grounding_state is ReviewerGroundingState.DECISION_GRADE:
        return 1.0
    if review.reviewer_grounding_state is ReviewerGroundingState.REVIEW_GRADE:
        return 0.68
    return 0.18


def _burden_profile_for_family(
    workflow_family: KnowledgeWorkflowFamily,
) -> FlagshipAssayBurdenProfile:
    if workflow_family in _PACKET_FAMILIES:
        return build_flagship_lab_follow_up_packet(workflow_family).burden_profile
    blueprint = _FOLLOW_UP_BLUEPRINTS[workflow_family]
    return FlagshipAssayBurdenProfile(
        workflow_family=workflow_family,
        estimated_relative_cost=blueprint.estimated_relative_cost,
        estimated_queue_days=blueprint.estimated_queue_days,
        confidence_gain_score=blueprint.confidence_gain_score,
        dependency_chain=blueprint.dependency_chain,
        tradeoffs=blueprint.tradeoffs,
    )


def _operational_feasibility_score(burden_profile: FlagshipAssayBurdenProfile) -> float:
    cost_score = max(0.0, 1.0 - (burden_profile.estimated_relative_cost / 10.0))
    queue_score = max(0.0, 1.0 - (burden_profile.estimated_queue_days / 30.0))
    dependency_score = max(0.0, 1.0 - (len(burden_profile.dependency_chain) / 6.0))
    return min(
        1.0,
        (
            cost_score * 0.3
            + queue_score * 0.2
            + dependency_score * 0.2
            + burden_profile.confidence_gain_score * 0.3
        ),
    )


def build_flagship_minimum_controls_table() -> FlagshipMinimumControlsTable:
    """Build the per-family minimum-controls table for decision-grade lab packets."""

    entries: list[FlagshipMinimumControlsTableEntry] = []
    for workflow_family in KnowledgeWorkflowFamily:
        review = _reviews_by_family()[workflow_family]
        blueprint = _FOLLOW_UP_BLUEPRINTS[workflow_family]
        blockers: list[str] = list(review.improvement_targets[:2])
        if (
            review.public_claim_support_state
            is not ComparatorClaimSupportState.SUPPORTED
        ):
            blockers.append(
                "comparator-backed public claim support is not yet supported"
            )
        if review.reviewer_grounding_state is not ReviewerGroundingState.DECISION_GRADE:
            blockers.append("biological grounding is below decision-grade")
        entries.append(
            FlagshipMinimumControlsTableEntry(
                workflow_family=workflow_family,
                benchmark_id=review.benchmark_id,
                minimum_controls=_dedupe(
                    review.minimum_controls_required + blueprint.extra_controls
                ),
                design_conditions=blueprint.design_conditions,
                decision_grade_bar=_dedupe(
                    review.decision_grade_criteria + blueprint.decision_grade_boundary
                ),
                currently_decision_grade_ready=(
                    review.public_claim_support_state
                    is ComparatorClaimSupportState.SUPPORTED
                    and review.reviewer_grounding_state
                    is ReviewerGroundingState.DECISION_GRADE
                    and review.ready_for_release_review
                ),
                current_blockers=_dedupe(blockers),
            )
        )
    return FlagshipMinimumControlsTable(
        table_id="flagship-minimum-controls-table",
        artifact_path="artifacts/lab/flagship-follow-up-packets/minimum_controls.json",
        entries=tuple(entries),
        note=(
            "This table names the control and design conditions that must exist before a flagship lab packet can honestly be called decision-grade."
        ),
    )


def build_flagship_lab_review_board() -> FlagshipLabReviewBoardArtifact:
    """Build the ranked lab review-board artifact across flagship benchmark packages."""

    entries: list[FlagshipLabReviewBoardEntry] = []
    for workflow_family in KnowledgeWorkflowFamily:
        review = _reviews_by_family()[workflow_family]
        burden_profile = _burden_profile_for_family(workflow_family)
        scientific_credibility_score = min(
            1.0,
            (
                _claim_support_score(review) * 0.45
                + _comparator_score(review) * 0.25
                + _grounding_score(review) * 0.2
                + (0.1 if review.ready_for_release_review else 0.0)
            ),
        )
        operational_feasibility_score = _operational_feasibility_score(burden_profile)
        overall_priority_score = (
            scientific_credibility_score * 0.65 + operational_feasibility_score * 0.35
        )
        if review.public_claim_support_state is ComparatorClaimSupportState.REFUSED:
            overall_priority_score *= 0.82
        if (
            overall_priority_score >= 0.55
            and review.public_claim_support_state
            is not ComparatorClaimSupportState.REFUSED
        ):
            recommendation_posture = "advance_exploratory_slot"
        elif overall_priority_score >= 0.38:
            recommendation_posture = "hold_until_blockers_close"
        else:
            recommendation_posture = "refuse_queue"
        entries.append(
            FlagshipLabReviewBoardEntry(
                workflow_family=workflow_family,
                benchmark_id=review.benchmark_id,
                scientific_credibility_score=round(scientific_credibility_score, 4),
                operational_feasibility_score=round(operational_feasibility_score, 4),
                overall_priority_score=round(min(overall_priority_score, 1.0), 4),
                recommendation_posture=recommendation_posture,
                rationale=_dedupe(
                    [
                        review.reviewer_summary,
                        *review.comparator_failure_summaries[:1],
                        *burden_profile.tradeoffs[:1],
                    ]
                ),
            )
        )
    ranked_entries = tuple(
        sorted(entries, key=lambda entry: entry.overall_priority_score, reverse=True)
    )
    return FlagshipLabReviewBoardArtifact(
        artifact_id="flagship-lab-review-board",
        artifact_path="artifacts/lab/flagship-follow-up-packets/review_board.json",
        entries=ranked_entries,
        note=(
            "This artifact ranks flagship follow-up candidates by scientific credibility and operational feasibility together so lab queue decisions stop being driven by excitement alone."
        ),
    )
