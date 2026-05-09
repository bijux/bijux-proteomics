# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Release-candidate synthesis built only from flagship public evidence surfaces."""

from __future__ import annotations

from functools import lru_cache

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.judgment.benchmark_corpora import (
    BenchmarkDisposition,
)
from bijux_proteomics_intelligence.reviews.benchmarks import ReviewerGroundingState
from bijux_proteomics_intelligence.reviews.outsider_packets import (
    FlagshipOutsiderReviewPacket,
    build_flagship_outsider_review_packet_family,
)
from bijux_proteomics_intelligence.reviews.workflow_authority import (
    WorkflowAuthorityKind,
    build_workflow_authority_matrix,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkEvidenceTier,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparator_failures import (
    ComparatorClaimSupportState,
)
from bijux_proteomics_knowledge.references.workflows.evidence_sufficiency import (
    WorkflowEvidenceTrustTier,
    build_workflow_evidence_sufficiency_rubric,
)
from bijux_proteomics_lab.benchmarks.follow_up import FlagshipLabPacketPosture
from bijux_proteomics_runtime.workflows.benchmark_runs import BenchmarkRunMode

__all__ = [
    "EliteReadinessScorecard",
    "EliteReadinessScorecardEntry",
    "FlagshipReleaseCandidateBundle",
    "FlagshipWorkflowDistrustPage",
    "FlagshipWorkflowTrustPage",
    "build_elite_readiness_scorecard",
    "build_flagship_release_candidate_bundle",
    "build_flagship_workflow_distrust_pages",
    "build_flagship_workflow_trust_pages",
]


class FlagshipWorkflowTrustPage(JsonModel):
    """One reviewer-facing trust page for a flagship workflow family."""

    model_config = ConfigDict(extra="forbid")

    page_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    doc_path: str = Field(..., min_length=1)
    trust_reasons: tuple[str, ...] = Field(default_factory=tuple)
    artifact_refs: tuple[str, ...] = Field(default_factory=tuple)
    exact_claims: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipWorkflowDistrustPage(JsonModel):
    """One reviewer-facing distrust page for a still-incomplete workflow family."""

    model_config = ConfigDict(extra="forbid")

    page_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    doc_path: str = Field(..., min_length=1)
    missing_reasons: tuple[str, ...] = Field(default_factory=tuple)
    closure_steps: tuple[str, ...] = Field(default_factory=tuple)
    blocked_claims: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipReleaseCandidateBundle(JsonModel):
    """One outsider-auditable release-candidate bundle across flagship families."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    strongest_workflow_family: KnowledgeWorkflowFamily
    outsider_packet_ids: tuple[str, ...] = Field(default_factory=tuple)
    outsider_auditable_workflow_families: tuple[KnowledgeWorkflowFamily, ...] = Field(
        default_factory=tuple
    )
    internal_support_workflow_families: tuple[KnowledgeWorkflowFamily, ...] = Field(
        default_factory=tuple
    )
    blocked_workflow_families: tuple[KnowledgeWorkflowFamily, ...] = Field(
        default_factory=tuple
    )
    benchmark_ids: tuple[str, ...] = Field(default_factory=tuple)
    runtime_package_ids: tuple[str, ...] = Field(default_factory=tuple)
    comparator_paths: tuple[str, ...] = Field(default_factory=tuple)
    scientific_reading_pack_ids: tuple[str, ...] = Field(default_factory=tuple)
    recommendation_packet_ids: tuple[str, ...] = Field(default_factory=tuple)
    lab_packet_ids: tuple[str, ...] = Field(default_factory=tuple)
    lab_outcome_dossier_ids: tuple[str, ...] = Field(default_factory=tuple)
    workflow_authority_matrix_path: str = Field(..., min_length=1)
    trust_page_paths: tuple[str, ...] = Field(default_factory=tuple)
    distrust_page_paths: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class EliteReadinessScorecardEntry(JsonModel):
    """Public-evidence-only readiness score for one flagship workflow family."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    public_package_score: float = Field(..., ge=0.0, le=1.0)
    runtime_execution_score: float = Field(..., ge=0.0, le=1.0)
    comparator_score: float = Field(..., ge=0.0, le=1.0)
    curated_knowledge_score: float = Field(..., ge=0.0, le=1.0)
    decision_posture_score: float = Field(..., ge=0.0, le=1.0)
    lab_consequence_score: float = Field(..., ge=0.0, le=1.0)
    outsider_auditable_surface: bool
    elite_language_allowed: bool
    overall_score: float = Field(..., ge=0.0, le=1.0)
    rationale: tuple[str, ...] = Field(default_factory=tuple)


class EliteReadinessScorecard(JsonModel):
    """Repository posture driven only by public benchmark substance."""

    model_config = ConfigDict(extra="forbid")

    scorecard_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[EliteReadinessScorecardEntry, ...] = Field(default_factory=tuple)
    repository_elite_language_allowed: bool
    repository_language_boundary: str = Field(..., min_length=1)
    scoring_basis: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


@lru_cache(maxsize=1)
def _outsider_packets() -> dict[KnowledgeWorkflowFamily, FlagshipOutsiderReviewPacket]:
    family = build_flagship_outsider_review_packet_family()
    return {packet.workflow_family: packet for packet in family.packets}


def _trust_page_path(workflow_family: KnowledgeWorkflowFamily) -> str:
    return (
        "docs/01-bijux-proteomics/foundation/"
        f"why-trust-{workflow_family.value}.md"
    )


def _distrust_page_path(workflow_family: KnowledgeWorkflowFamily) -> str:
    return (
        "docs/01-bijux-proteomics/foundation/"
        f"why-not-trust-{workflow_family.value}-yet.md"
    )


def build_flagship_workflow_trust_pages() -> tuple[FlagshipWorkflowTrustPage, ...]:
    """Build reviewer-facing trust pages across flagship workflow families."""

    pages: list[FlagshipWorkflowTrustPage] = []
    for workflow_family, packet in _outsider_packets().items():
        trust_reasons = [
            f"benchmark evidence tier is {packet.benchmark_evidence_tier.value}",
            f"public claim support is {packet.public_claim_support_state.value}",
            f"recommendation posture is {packet.recommendation_disposition.value}",
            f"lab posture is {packet.lab_posture.value}",
            f"outcome dossier basis is {packet.lab_outcome_basis.value}",
            (
                "shipped outcome revised the recommendation to "
                f"{packet.outcome_recommendation_disposition.value}"
            ),
        ]
        if packet.runtime_package_id is not None and packet.runtime_run_mode is not None:
            trust_reasons.append(
                f"runtime package {packet.runtime_package_id} is currently {packet.runtime_run_mode.value}"
            )
        pages.append(
            FlagshipWorkflowTrustPage(
                page_id=f"trust_page:{workflow_family.value}",
                workflow_family=workflow_family,
                doc_path=_trust_page_path(workflow_family),
                trust_reasons=tuple(trust_reasons),
                artifact_refs=tuple(
                    link.repo_relative_path
                    for link in packet.review_artifact_links[:6]
                ),
                exact_claims=packet.exact_claims,
                note=(
                    "The trust page should say exactly what this workflow family has earned from current shipped evidence, not what it might earn later."
                ),
            )
        )
    return tuple(pages)


def build_flagship_workflow_distrust_pages() -> tuple[FlagshipWorkflowDistrustPage, ...]:
    """Build reviewer-facing distrust pages for still-incomplete workflows."""

    return ()


def build_flagship_release_candidate_bundle() -> FlagshipReleaseCandidateBundle:
    """Build one outsider-auditable release-candidate bundle."""

    packets = tuple(_outsider_packets().values())
    matrix = build_workflow_authority_matrix()
    outsider_auditable = tuple(
        row.workflow_family
        for row in matrix.rows
        if next(
            cell
            for cell in row.cells
            if cell.authority_kind == WorkflowAuthorityKind.OUTSIDER_AUDITABLE
        ).earned
    )
    internal_support = tuple(
        row.workflow_family
        for row in matrix.rows
        if row.public_release_language == "internal_support_only"
    )
    trust_pages = build_flagship_workflow_trust_pages()
    distrust_pages = build_flagship_workflow_distrust_pages()
    strongest = next(
        packet.workflow_family for packet in packets if packet.complete_outsider_surface
    )
    return FlagshipReleaseCandidateBundle(
        bundle_id="flagship-release-candidate-bundle",
        artifact_path="artifacts/intelligence/release-candidates/flagship_bundle.json",
        strongest_workflow_family=strongest,
        outsider_packet_ids=tuple(packet.packet_id for packet in packets),
        outsider_auditable_workflow_families=outsider_auditable,
        internal_support_workflow_families=internal_support,
        blocked_workflow_families=(),
        benchmark_ids=tuple(packet.benchmark_id for packet in packets),
        runtime_package_ids=tuple(
            dict.fromkeys(
                packet.runtime_package_id
                for packet in packets
                if packet.runtime_package_id is not None
            )
        ),
        comparator_paths=tuple(
            dict.fromkeys(
                context
                for packet in packets
                for context in packet.comparator_context
                if "comparator_path:" in context
            )
        ),
        scientific_reading_pack_ids=tuple(
            packet.scientific_reading_pack_id for packet in packets
        ),
        recommendation_packet_ids=tuple(
            packet.recommendation_packet_id for packet in packets
        ),
        lab_packet_ids=tuple(packet.lab_packet_id for packet in packets),
        lab_outcome_dossier_ids=tuple(
            packet.lab_outcome_dossier_id for packet in packets
        ),
        workflow_authority_matrix_path=matrix.artifact_path,
        trust_page_paths=tuple(page.doc_path for page in trust_pages),
        distrust_page_paths=tuple(page.doc_path for page in distrust_pages),
        note=(
            "The release-candidate bundle collects the strongest shipped benchmark package, runtime lane, comparator pressure, knowledge dossier, recommendation packet, planned lab packet, and requested-versus-observed outcome dossier into one outsider-auditable review surface while naming multiplex separately as internal support only."
        ),
    )


def _score_public_package(packet: FlagshipOutsiderReviewPacket) -> float:
    if packet.benchmark_evidence_tier is BenchmarkEvidenceTier.EXTERNAL_REPRODUCTION_PACKAGE:
        return 1.0
    if packet.benchmark_package_id is not None:
        return 0.5
    return 0.0


def _score_runtime_execution(packet: FlagshipOutsiderReviewPacket) -> float:
    if packet.runtime_run_mode is BenchmarkRunMode.RAW_EXECUTABLE:
        return 1.0
    if packet.runtime_run_mode is BenchmarkRunMode.IMPORT_ONLY:
        return 0.75
    return 0.0


def _score_comparator(packet: FlagshipOutsiderReviewPacket) -> float:
    if packet.public_claim_support_state is ComparatorClaimSupportState.SUPPORTED:
        return 1.0
    if packet.public_claim_support_state is ComparatorClaimSupportState.ADVISORY:
        return 0.6
    return 0.0


def _score_knowledge(workflow_family: KnowledgeWorkflowFamily) -> float:
    tier = build_workflow_evidence_sufficiency_rubric(
        workflow_family
    ).current_authorized_tier
    if tier is WorkflowEvidenceTrustTier.DECISION_GRADE:
        return 1.0
    if tier is WorkflowEvidenceTrustTier.EXTERNALLY_CROSS_CHECKED:
        return 0.75
    if tier is WorkflowEvidenceTrustTier.BENCHMARK_BACKED:
        return 0.5
    return 0.25


def _score_decision(packet: FlagshipOutsiderReviewPacket) -> float:
    if packet.recommendation_disposition is BenchmarkDisposition.RECOMMEND:
        return 1.0
    if packet.recommendation_disposition is BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE:
        return 0.75
    return 0.0


def _score_lab(packet: FlagshipOutsiderReviewPacket) -> float:
    if packet.lab_posture is FlagshipLabPacketPosture.DECISION_GRADE_CANDIDATE:
        return 1.0
    if packet.lab_posture is FlagshipLabPacketPosture.EXPLORATORY_ONLY:
        return 0.5
    return 0.0


def build_elite_readiness_scorecard() -> EliteReadinessScorecard:
    """Build the public-evidence-only elite readiness scorecard."""

    entries: list[EliteReadinessScorecardEntry] = []
    for workflow_family, packet in _outsider_packets().items():
        public_package_score = _score_public_package(packet)
        runtime_execution_score = _score_runtime_execution(packet)
        comparator_score = _score_comparator(packet)
        curated_knowledge_score = _score_knowledge(workflow_family)
        decision_posture_score = _score_decision(packet)
        lab_consequence_score = _score_lab(packet)
        overall_score = (
            public_package_score
            + runtime_execution_score
            + comparator_score
            + curated_knowledge_score
            + decision_posture_score
            + lab_consequence_score
        ) / 6.0
        elite_language_allowed = (
            packet.complete_outsider_surface
            and packet.public_claim_support_state is ComparatorClaimSupportState.SUPPORTED
            and packet.reviewer_grounding_state is not ReviewerGroundingState.THIN
            and packet.recommendation_disposition is not BenchmarkDisposition.DO_NOT_RECOMMEND
            and packet.lab_posture is not FlagshipLabPacketPosture.NOT_WORTH_ASSAY
        )
        entries.append(
            EliteReadinessScorecardEntry(
                workflow_family=workflow_family,
                public_package_score=public_package_score,
                runtime_execution_score=runtime_execution_score,
                comparator_score=comparator_score,
                curated_knowledge_score=curated_knowledge_score,
                decision_posture_score=decision_posture_score,
                lab_consequence_score=lab_consequence_score,
                outsider_auditable_surface=packet.complete_outsider_surface,
                elite_language_allowed=elite_language_allowed,
                overall_score=overall_score,
                rationale=(
                    f"public_package_score={public_package_score}",
                    f"runtime_execution_score={runtime_execution_score}",
                    f"comparator_score={comparator_score}",
                    f"curated_knowledge_score={curated_knowledge_score}",
                    f"decision_posture_score={decision_posture_score}",
                    f"lab_consequence_score={lab_consequence_score}",
                ),
            )
        )
    return EliteReadinessScorecard(
        scorecard_id="elite-readiness-scorecard",
        artifact_path="artifacts/intelligence/release-candidates/elite_readiness_scorecard.json",
        entries=tuple(entries),
        repository_elite_language_allowed=False,
        repository_language_boundary=(
            "Multiple workflow families are now outsider-auditable in a bounded sense, but repository-wide elite language remains blocked until more than one family survives the same standard with stronger supported comparator, grounding, and lab-consequence authority."
        ),
        scoring_basis=(
            "public benchmark package substance",
            "real runtime execution or explicit runtime block state",
            "external comparator confrontation",
            "curated knowledge sufficiency",
            "benchmark-backed recommendation posture",
            "lab-facing consequence packets",
        ),
        note=(
            "The scorecard forbids file-count, doc-count, or governance-volume scoring and only measures shipped public-evidence substance."
        ),
    )
