# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Outsider-auditable flagship workflow packets built from shipped evidence owners."""

from __future__ import annotations

from functools import lru_cache

from pydantic import ConfigDict, Field

from bijux_proteomics.benchmarks.flagship_acceptance import (
    AcceptanceReleaseLanguage,
    FlagshipAcceptanceSheet,
    build_flagship_acceptance_sheet,
)
from bijux_proteomics_foundation import JsonModel
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
    BenchmarkEvidenceTier,
    BenchmarkManifest,
    BenchmarkPackageArtifact,
    BenchmarkPackageArtifactKind,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparator_failures import (
    ComparatorClaimSupportState,
)
from bijux_proteomics_knowledge.references.workflows.reference_support import (
    get_benchmark_manifest_for_family,
)
from bijux_proteomics_knowledge.references.workflows.scientific_reading_packs import (
    WorkflowScientificReadingPack,
    build_workflow_scientific_reading_pack,
)
from bijux_proteomics_lab.benchmarks.follow_up import (
    FlagshipLabFollowUpPacket,
    FlagshipLabPacketPosture,
    build_flagship_lab_follow_up_packet_family,
)
from bijux_proteomics_lab.benchmarks.outcome_dossiers import (
    FlagshipAssayWorthLedgerEntry,
    FlagshipFollowUpOutcomeBasis,
    FlagshipFollowUpOutcomeDossier,
    build_flagship_assay_worth_ledger,
    build_flagship_follow_up_outcome_dossier_family,
)
from bijux_proteomics_runtime.workflows import (
    BenchmarkRunMode,
    BenchmarkRunSpec,
    BenchmarkRuntimeTruthRow,
    build_benchmark_run_specs,
    build_benchmark_runtime_truth_surface,
    build_runtime_flagship_proof_gate,
)

__all__ = [
    "FlagshipOutsiderArtifactLink",
    "FlagshipOutsiderReviewPacket",
    "FlagshipOutsiderReviewPacketFamily",
    "build_flagship_outsider_review_packet",
    "build_flagship_outsider_review_packet_family",
]


_WORKFLOW_FAMILIES: tuple[KnowledgeWorkflowFamily, ...] = (
    KnowledgeWorkflowFamily.DDA,
    KnowledgeWorkflowFamily.DIA,
    KnowledgeWorkflowFamily.LFQ,
    KnowledgeWorkflowFamily.PTM,
    KnowledgeWorkflowFamily.TARGETED,
)

_RUNTIME_TRUTH_BY_FAMILY: dict[KnowledgeWorkflowFamily, str] = {
    KnowledgeWorkflowFamily.DDA: "dda_import",
    KnowledgeWorkflowFamily.DIA: "dia_import",
    KnowledgeWorkflowFamily.LFQ: "quant_review",
    KnowledgeWorkflowFamily.PTM: "ptm_review",
    KnowledgeWorkflowFamily.TARGETED: "targeted_review",
}


class FlagshipOutsiderArtifactLink(JsonModel):
    """One concrete file path that an outsider can inspect directly."""

    model_config = ConfigDict(extra="forbid")

    link_id: str = Field(..., min_length=1)
    owner_package: str = Field(..., min_length=1)
    repo_relative_path: str = Field(..., min_length=1)
    why_open_this: str = Field(..., min_length=1)


class FlagshipOutsiderReviewPacket(JsonModel):
    """One outsider-auditable packet for a flagship workflow family."""

    model_config = ConfigDict(extra="forbid")

    packet_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    benchmark_title: str = Field(..., min_length=1)
    benchmark_package_id: str | None = None
    benchmark_evidence_tier: BenchmarkEvidenceTier
    runtime_package_id: str | None = None
    runtime_run_mode: BenchmarkRunMode | None = None
    scientific_reading_pack_id: str = Field(..., min_length=1)
    recommendation_packet_id: str = Field(..., min_length=1)
    lab_packet_id: str = Field(..., min_length=1)
    lab_outcome_dossier_id: str = Field(..., min_length=1)
    lab_outcome_basis: FlagshipFollowUpOutcomeBasis
    public_claim_support_state: ComparatorClaimSupportState
    reviewer_grounding_state: ReviewerGroundingState
    recommendation_disposition: BenchmarkDisposition
    outcome_recommendation_disposition: BenchmarkDisposition
    lab_posture: FlagshipLabPacketPosture
    assay_worth_it: bool
    exact_claims: tuple[str, ...] = Field(default_factory=tuple)
    primary_data_links: tuple[FlagshipOutsiderArtifactLink, ...] = Field(
        default_factory=tuple
    )
    review_artifact_links: tuple[FlagshipOutsiderArtifactLink, ...] = Field(
        default_factory=tuple
    )
    comparator_context: tuple[str, ...] = Field(default_factory=tuple)
    literature_context: tuple[str, ...] = Field(default_factory=tuple)
    inspection_sequence: tuple[str, ...] = Field(default_factory=tuple)
    known_limits: tuple[str, ...] = Field(default_factory=tuple)
    validating_tests: tuple[str, ...] = Field(default_factory=tuple)
    complete_outsider_surface: bool
    missing_surface_reasons: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipOutsiderReviewPacketFamily(JsonModel):
    """Family of outsider packets across flagship workflow families."""

    model_config = ConfigDict(extra="forbid")

    family_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    packets: tuple[FlagshipOutsiderReviewPacket, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


@lru_cache(maxsize=1)
def _reviews_by_family() -> dict[KnowledgeWorkflowFamily, WorkflowBenchmarkReview]:
    return {
        review.workflow_family: review for review in list_flagship_benchmark_reviews()
    }


@lru_cache(maxsize=1)
def _reading_packs_by_family() -> dict[
    KnowledgeWorkflowFamily, WorkflowScientificReadingPack
]:
    return {
        workflow_family: build_workflow_scientific_reading_pack(workflow_family)
        for workflow_family in _WORKFLOW_FAMILIES
    }


@lru_cache(maxsize=1)
def _recommendation_packets_by_family() -> dict[
    KnowledgeWorkflowFamily, BenchmarkRecommendationPacket
]:
    family = build_flagship_benchmark_recommendation_packet_family()
    return {packet.workflow_family: packet for packet in family.packets}


@lru_cache(maxsize=1)
def _lab_packets_by_family() -> dict[
    KnowledgeWorkflowFamily, FlagshipLabFollowUpPacket
]:
    family = build_flagship_lab_follow_up_packet_family()
    return {packet.workflow_family: packet for packet in family.packets}


@lru_cache(maxsize=1)
def _lab_outcome_dossiers_by_family() -> dict[
    KnowledgeWorkflowFamily, FlagshipFollowUpOutcomeDossier
]:
    family = build_flagship_follow_up_outcome_dossier_family()
    return {dossier.workflow_family: dossier for dossier in family.dossiers}


@lru_cache(maxsize=1)
def _worth_ledger_entries_by_family() -> dict[
    KnowledgeWorkflowFamily, FlagshipAssayWorthLedgerEntry
]:
    ledger = build_flagship_assay_worth_ledger()
    return {entry.workflow_family: entry for entry in ledger.entries}


@lru_cache(maxsize=1)
def _runtime_truth_rows() -> dict[str, BenchmarkRuntimeTruthRow]:
    return {row.workflow_family: row for row in build_benchmark_runtime_truth_surface()}


@lru_cache(maxsize=1)
def _runtime_specs_by_package_id() -> dict[str, BenchmarkRunSpec]:
    return {spec.package_id: spec for spec in build_benchmark_run_specs()}


def _owner_package_from_path(repo_relative_path: str) -> str:
    if "/packages/" not in f"/{repo_relative_path}":
        return "bijux-proteomics-docs"
    return repo_relative_path.split("/")[1]


def _link_from_artifact(
    *,
    workflow_family: KnowledgeWorkflowFamily,
    artifact: BenchmarkPackageArtifact,
) -> FlagshipOutsiderArtifactLink:
    return FlagshipOutsiderArtifactLink(
        link_id=f"{workflow_family.value}:{artifact.artifact_id}",
        owner_package=_owner_package_from_path(artifact.repo_relative_path),
        repo_relative_path=artifact.repo_relative_path,
        why_open_this=artifact.note,
    )


def _is_primary_data_artifact(artifact: BenchmarkPackageArtifact) -> bool:
    return artifact.artifact_kind in {
        BenchmarkPackageArtifactKind.RAW_SPECTRA,
        BenchmarkPackageArtifactKind.EXTERNAL_PIPELINE_EXPORT,
        BenchmarkPackageArtifactKind.FEATURE_TABLE,
        BenchmarkPackageArtifactKind.RESULTS_TABLE,
        BenchmarkPackageArtifactKind.TARGETED_QC_TABLE,
        BenchmarkPackageArtifactKind.DESIGN_TABLE,
    }


def _benchmark_links(
    workflow_family: KnowledgeWorkflowFamily,
    manifest: BenchmarkManifest,
) -> tuple[
    tuple[FlagshipOutsiderArtifactLink, ...],
    tuple[FlagshipOutsiderArtifactLink, ...],
]:
    package = manifest.benchmark_package
    if package is None:
        return (), ()
    data_links = tuple(
        _link_from_artifact(workflow_family=workflow_family, artifact=artifact)
        for artifact in package.package_artifacts
        if _is_primary_data_artifact(artifact)
    )
    review_links = tuple(
        _link_from_artifact(workflow_family=workflow_family, artifact=artifact)
        for artifact in package.package_artifacts
    )
    return data_links, review_links


def _runtime_links(
    workflow_family: KnowledgeWorkflowFamily,
    runtime_package_id: str | None,
) -> tuple[FlagshipOutsiderArtifactLink, ...]:
    if runtime_package_id is None:
        return ()
    spec = _runtime_specs_by_package_id().get(runtime_package_id)
    if spec is None:
        return ()
    links = [
        FlagshipOutsiderArtifactLink(
            link_id=f"{workflow_family.value}:{runtime_package_id}:primary_input",
            owner_package=_owner_package_from_path(spec.primary_input_path),
            repo_relative_path=spec.primary_input_path,
            why_open_this="The primary runtime input shows what the current flagship run actually consumes.",
        )
    ]
    links.extend(
        FlagshipOutsiderArtifactLink(
            link_id=f"{workflow_family.value}:{runtime_package_id}:companion:{index}",
            owner_package=_owner_package_from_path(path),
            repo_relative_path=path,
            why_open_this="Companion runtime inputs keep engine settings or adjacent evidence visible beside the primary lane.",
        )
        for index, path in enumerate(spec.companion_input_paths, start=1)
    )
    links.extend(
        FlagshipOutsiderArtifactLink(
            link_id=f"{workflow_family.value}:{runtime_package_id}:public:{index}",
            owner_package=_owner_package_from_path(path),
            repo_relative_path=path,
            why_open_this="These tracked files are the public package anchors the runtime lane claims to represent.",
        )
        for index, path in enumerate(spec.public_package_paths, start=1)
    )
    return tuple(links)


def _runtime_truth_row(
    workflow_family: KnowledgeWorkflowFamily,
) -> BenchmarkRuntimeTruthRow | None:
    runtime_key = _RUNTIME_TRUTH_BY_FAMILY.get(workflow_family)
    if runtime_key is None:
        return None
    return _runtime_truth_rows().get(runtime_key)


def _dedupe_links(
    links: tuple[FlagshipOutsiderArtifactLink, ...],
) -> tuple[FlagshipOutsiderArtifactLink, ...]:
    ordered: dict[str, FlagshipOutsiderArtifactLink] = {}
    for link in links:
        ordered.setdefault(link.repo_relative_path, link)
    return tuple(ordered.values())


def _complete_outsider_surface(
    *,
    workflow_family: KnowledgeWorkflowFamily,
    acceptance_sheet: FlagshipAcceptanceSheet,
    manifest: BenchmarkManifest,
    runtime_truth: BenchmarkRuntimeTruthRow | None,
    recommendation: BenchmarkRecommendationPacket,
    lab_packet: FlagshipLabFollowUpPacket,
    outcome_dossier: FlagshipFollowUpOutcomeDossier | None,
    worth_entry: FlagshipAssayWorthLedgerEntry | None,
) -> bool:
    runtime_gate_issues = _runtime_gate_issues(workflow_family)
    return (
        manifest.benchmark_package is not None
        and manifest.evidence_tier
        is BenchmarkEvidenceTier.EXTERNAL_REPRODUCTION_PACKAGE
        and runtime_truth is not None
        and runtime_truth.run_mode is not BenchmarkRunMode.BLOCKED
        and not runtime_gate_issues
        and acceptance_sheet.earned_release_language
        is AcceptanceReleaseLanguage.OUTSIDER_AUDITABLE_BOUNDED
        and not acceptance_sheet.claim_ahead_of_evidence
        and recommendation.disposition is not BenchmarkDisposition.DO_NOT_RECOMMEND
        and lab_packet.posture is not FlagshipLabPacketPosture.NOT_WORTH_ASSAY
        and outcome_dossier is not None
        and worth_entry is not None
    )


def _missing_surface_reasons(
    *,
    workflow_family: KnowledgeWorkflowFamily,
    acceptance_sheet: FlagshipAcceptanceSheet,
    manifest: BenchmarkManifest,
    review: WorkflowBenchmarkReview,
    reading_pack: WorkflowScientificReadingPack,
    runtime_truth: BenchmarkRuntimeTruthRow | None,
    recommendation: BenchmarkRecommendationPacket,
    lab_packet: FlagshipLabFollowUpPacket,
    outcome_dossier: FlagshipFollowUpOutcomeDossier | None,
    worth_entry: FlagshipAssayWorthLedgerEntry | None,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if manifest.benchmark_package is None:
        reasons.append(
            "no benchmark package is registered for this workflow family yet"
        )
    elif (
        manifest.evidence_tier
        is not BenchmarkEvidenceTier.EXTERNAL_REPRODUCTION_PACKAGE
    ):
        reasons.append(
            f"benchmark evidence tier is {manifest.evidence_tier.value}, so the family still lacks a flagship outsider-readable public package"
        )
    if acceptance_sheet.claim_ahead_of_evidence:
        reasons.append(
            "the current flagship acceptance sheet says release language is ahead of the benchmark evidence"
        )
        reasons.extend(
            f"acceptance failed for {criterion.dimension}: observed {criterion.observed_value} but required {criterion.required_relation.value} {criterion.required_value}"
            for criterion in acceptance_sheet.criteria
            if not criterion.passed
        )
    if runtime_truth is None:
        reasons.append(
            "no flagship runtime truth row is published for this workflow family yet"
        )
    elif runtime_truth.run_mode is BenchmarkRunMode.BLOCKED:
        reasons.extend(runtime_truth.blocker_notes)
    reasons.extend(_runtime_gate_issues(workflow_family))
    if review.public_claim_support_state is ComparatorClaimSupportState.REFUSED:
        reasons.append("public comparator-backed claim support is still refused")
    if recommendation.disposition is BenchmarkDisposition.DO_NOT_RECOMMEND:
        reasons.extend(
            recommendation.blocker_set
            or ("the current benchmark recommendation posture is refusal",)
        )
    if lab_packet.posture is FlagshipLabPacketPosture.NOT_WORTH_ASSAY:
        reasons.extend(lab_packet.stop_reasons)
    if outcome_dossier is None:
        reasons.append(
            "no shipped requested-versus-observed lab outcome dossier exists for this workflow family yet"
        )
    if worth_entry is None:
        reasons.append(
            "no shipped assay-worth-it ledger row exists for this workflow family yet"
        )
    for gap_group in (
        reading_pack.deficit_report.public_data_gaps,
        reading_pack.deficit_report.comparator_gaps,
        reading_pack.deficit_report.runtime_proof_gaps,
    ):
        reasons.extend(item.summary for item in gap_group)
    return tuple(dict.fromkeys(reasons))


def build_flagship_outsider_review_packet(
    workflow_family: KnowledgeWorkflowFamily,
) -> FlagshipOutsiderReviewPacket:
    """Build one outsider-auditable packet for a flagship workflow family."""

    review = _reviews_by_family()[workflow_family]
    acceptance_sheet = build_flagship_acceptance_sheet(workflow_family)
    manifest = get_benchmark_manifest_for_family(workflow_family)
    reading_pack = _reading_packs_by_family()[workflow_family]
    recommendation = _recommendation_packets_by_family()[workflow_family]
    lab_packet = _lab_packets_by_family()[workflow_family]
    outcome_dossier = _lab_outcome_dossiers_by_family().get(workflow_family)
    worth_entry = _worth_ledger_entries_by_family().get(workflow_family)
    runtime_truth = _runtime_truth_row(workflow_family)
    runtime_package_id = runtime_truth.package_id if runtime_truth is not None else None
    benchmark_data_links, benchmark_review_links = _benchmark_links(
        workflow_family, manifest
    )
    runtime_links = _runtime_links(workflow_family, runtime_package_id)
    extra_review_links: tuple[FlagshipOutsiderArtifactLink, ...] = ()
    if outcome_dossier is not None:
        extra_review_links += (
            FlagshipOutsiderArtifactLink(
                link_id=f"{workflow_family.value}:lab-outcome-dossier",
                owner_package="bijux-proteomics-lab",
                repo_relative_path=outcome_dossier.artifact_path,
                why_open_this="The requested-versus-observed dossier shows what the flagship follow-up loop actually delivered.",
            ),
        )
    if worth_entry is not None:
        extra_review_links += (
            FlagshipOutsiderArtifactLink(
                link_id=f"{workflow_family.value}:assay-worth-ledger",
                owner_package="bijux-proteomics-lab",
                repo_relative_path=build_flagship_assay_worth_ledger().artifact_path,
                why_open_this="The assay-worth ledger scores whether the shipped follow-up loop repaid cost, time, and decision pressure.",
            ),
        )
    review_links = _dedupe_links(
        (*benchmark_review_links, *runtime_links, *extra_review_links)
    )
    complete_surface = _complete_outsider_surface(
        workflow_family=workflow_family,
        acceptance_sheet=acceptance_sheet,
        manifest=manifest,
        runtime_truth=runtime_truth,
        recommendation=recommendation,
        lab_packet=lab_packet,
        outcome_dossier=outcome_dossier,
        worth_entry=worth_entry,
    )
    known_limits = tuple(
        dict.fromkeys(
            (
                *review.scientific_limits,
                *review.reviewer_grounding_limits,
                *review.comparison_notes,
                *recommendation.downgrade_chain,
                *recommendation.blocker_set,
                *lab_packet.stop_reasons,
            )
        )
    )
    runtime_validating_tests: tuple[str, ...] = ()
    if runtime_links and runtime_package_id is not None:
        runtime_spec = _runtime_specs_by_package_id().get(runtime_package_id)
        if runtime_spec is not None:
            runtime_validating_tests = runtime_spec.validating_test_paths
    validating_tests = tuple(
        dict.fromkeys(
            (
                *runtime_validating_tests,
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
                "packages/bijux-proteomics-intelligence/tests/judgment/test_benchmark_recommendation_packet_surface.py",
                "packages/bijux-proteomics-lab/tests/benchmarks/test_benchmark_flagship_follow_up_surface.py",
                "packages/bijux-proteomics-lab/tests/benchmarks/test_outcome_dossiers_surface.py",
            )
        )
    )
    return FlagshipOutsiderReviewPacket(
        packet_id=f"outsider_review:{workflow_family.value}",
        workflow_family=workflow_family,
        benchmark_id=review.benchmark_id,
        benchmark_title=review.title,
        benchmark_package_id=review.benchmark_package_id,
        benchmark_evidence_tier=manifest.evidence_tier,
        runtime_package_id=runtime_package_id,
        runtime_run_mode=runtime_truth.run_mode if runtime_truth is not None else None,
        scientific_reading_pack_id=reading_pack.pack_id,
        recommendation_packet_id=recommendation.packet_id,
        lab_packet_id=lab_packet.packet_id,
        lab_outcome_dossier_id=(
            outcome_dossier.dossier_id
            if outcome_dossier is not None
            else f"missing_lab_outcome:{workflow_family.value}"
        ),
        lab_outcome_basis=(
            outcome_dossier.outcome_basis
            if outcome_dossier is not None
            else FlagshipFollowUpOutcomeBasis.BENCHMARK_SIMULATED
        ),
        public_claim_support_state=review.public_claim_support_state,
        reviewer_grounding_state=review.reviewer_grounding_state,
        recommendation_disposition=recommendation.disposition,
        outcome_recommendation_disposition=(
            outcome_dossier.revised_recommendation_disposition
            if outcome_dossier is not None
            else recommendation.disposition
        ),
        lab_posture=lab_packet.posture,
        assay_worth_it=worth_entry.worth_it if worth_entry is not None else False,
        exact_claims=review.supported_repo_claims,
        primary_data_links=_dedupe_links((*benchmark_data_links, *runtime_links)),
        review_artifact_links=review_links,
        comparator_context=tuple(
            dict.fromkeys(
                (
                    *review.comparator_failure_summaries,
                    *review.improvement_targets,
                    *manifest.comparison_notes,
                )
            )
        ),
        literature_context=reading_pack.citation_digest,
        inspection_sequence=(
            f"open {manifest.benchmark_id} first to see the benchmark scope and supported claims",
            "inspect the primary data links before trusting any summary prose",
            f"read {reading_pack.pack_id} to see literature and contradiction context",
            f"check {recommendation.packet_id} for recommendation posture and downgrade chain",
            f"check {lab_packet.packet_id} for the planned assay boundary",
            f"finish with {outcome_dossier.dossier_id if outcome_dossier is not None else 'the missing lab outcome dossier'} to see whether the evidence was actually worth operational follow-up",
        ),
        known_limits=known_limits,
        validating_tests=validating_tests,
        complete_outsider_surface=complete_surface,
        missing_surface_reasons=_missing_surface_reasons(
            workflow_family=workflow_family,
            acceptance_sheet=acceptance_sheet,
            manifest=manifest,
            review=review,
            reading_pack=reading_pack,
            runtime_truth=runtime_truth,
            recommendation=recommendation,
            lab_packet=lab_packet,
            outcome_dossier=outcome_dossier,
            worth_entry=worth_entry,
        ),
        note=(
            "The outsider packet exists to let a skeptical reviewer inspect the current flagship workflow posture from tracked files, runtime evidence, scientific reading, recommendation logic, planned assay boundaries, and shipped requested-versus-observed lab consequence without maintainer narration."
        ),
    )


def _runtime_gate_issues(workflow_family: KnowledgeWorkflowFamily) -> tuple[str, ...]:
    runtime_family = _RUNTIME_TRUTH_BY_FAMILY.get(workflow_family)
    if runtime_family is None:
        return ()
    gate = build_runtime_flagship_proof_gate()
    return tuple(
        issue.detail for issue in gate.issues if issue.workflow_family == runtime_family
    )


def build_flagship_outsider_review_packet_family() -> (
    FlagshipOutsiderReviewPacketFamily
):
    """Build outsider-auditable packets across flagship workflow families."""

    return FlagshipOutsiderReviewPacketFamily(
        family_id="flagship-outsider-review-packets",
        artifact_path="artifacts/intelligence/outsider-review/flagship_packet_family.json",
        packets=tuple(
            build_flagship_outsider_review_packet(workflow_family)
            for workflow_family in _WORKFLOW_FAMILIES
        ),
        note=(
            "These packets replace maintainer-narrated capability claims with direct cross-package audit packets for each flagship workflow family."
        ),
    )
