# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""External-review kits for outsider-auditable flagship workflow families."""

from __future__ import annotations

from functools import lru_cache

from pydantic import ConfigDict, Field

from bijux_proteomics.review.collaboration import (
    ExternalReviewerBundle,
    ExternalReviewerBundleInput,
    StandaloneVerifierInput,
    StandaloneVerifierReport,
    build_external_reviewer_bundle,
    run_standalone_bundle_verifier,
)
from bijux_proteomics_foundation import JsonModel, fingerprint_model
from bijux_proteomics_intelligence.reviews.independent_reruns import (
    WorkflowIndependentRerunDossier,
    build_workflow_independent_rerun_dossier_family,
)
from bijux_proteomics_intelligence.reviews.outsider_packets import (
    FlagshipOutsiderReviewPacket,
    build_flagship_outsider_review_packet_family,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)

__all__ = [
    "WorkflowExternalReviewKit",
    "WorkflowExternalReviewKitFamily",
    "build_workflow_external_review_kit",
    "build_workflow_external_review_kit_family",
]


_WORKFLOW_FAMILIES: tuple[KnowledgeWorkflowFamily, ...] = (
    KnowledgeWorkflowFamily.DDA,
    KnowledgeWorkflowFamily.DIA,
    KnowledgeWorkflowFamily.LFQ,
    KnowledgeWorkflowFamily.PTM,
    KnowledgeWorkflowFamily.TARGETED,
)


class WorkflowExternalReviewKit(JsonModel):
    """One outsider-usable review kit for a flagship workflow family."""

    model_config = ConfigDict(extra="forbid")

    kit_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    artifact_path: str = Field(..., min_length=1)
    reviewer_bundle: ExternalReviewerBundle
    standalone_verifier_report: StandaloneVerifierReport
    opening_sequence: tuple[str, ...] = Field(default_factory=tuple)
    shipped_artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    known_exclusions: tuple[str, ...] = Field(default_factory=tuple)
    ready_for_outsider_review: bool
    note: str = Field(..., min_length=1)


class WorkflowExternalReviewKitFamily(JsonModel):
    """Family of outsider-usable review kits for flagship workflows."""

    model_config = ConfigDict(extra="forbid")

    family_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    kits: tuple[WorkflowExternalReviewKit, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


@lru_cache(maxsize=1)
def _outsider_packets() -> dict[KnowledgeWorkflowFamily, FlagshipOutsiderReviewPacket]:
    family = build_flagship_outsider_review_packet_family()
    return {packet.workflow_family: packet for packet in family.packets}


@lru_cache(maxsize=1)
def _independent_rerun_dossiers() -> dict[
    KnowledgeWorkflowFamily, WorkflowIndependentRerunDossier
]:
    family = build_workflow_independent_rerun_dossier_family()
    return {dossier.workflow_family: dossier for dossier in family.dossiers}


def _artifact_paths(
    packet: FlagshipOutsiderReviewPacket,
    rerun_dossier: WorkflowIndependentRerunDossier,
) -> tuple[str, ...]:
    paths = list(rerun_dossier.public_opening_order)
    paths.extend(link.repo_relative_path for link in packet.primary_data_links[:3])
    paths.extend(link.repo_relative_path for link in packet.review_artifact_links[:4])
    return tuple(dict.fromkeys(paths))


def build_workflow_external_review_kit(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowExternalReviewKit:
    """Build one outsider-usable review kit for a flagship workflow family."""

    packet = _outsider_packets()[workflow_family]
    rerun_dossier = _independent_rerun_dossiers()[workflow_family]
    artifact_paths = _artifact_paths(packet, rerun_dossier)
    reviewer_bundle = build_external_reviewer_bundle(
        ExternalReviewerBundleInput(
            bundle_id=f"external_review_kit:{workflow_family.value}",
            schema_refs=(
                f"schema.{workflow_family.value}.outsider_review.v1",
                f"schema.{workflow_family.value}.independent_rerun.v1",
                "schema.external_review_kit.v1",
            ),
            evidence_pointer_ids=(
                packet.packet_id,
                packet.benchmark_id,
                packet.scientific_reading_pack_id,
                packet.recommendation_packet_id,
                packet.lab_packet_id,
                packet.lab_outcome_dossier_id,
                rerun_dossier.dossier_id,
            ),
            summary_lines=(
                rerun_dossier.independence_question,
                *packet.exact_claims[:2],
                *rerun_dossier.drift_questions[:1],
            ),
            hash_ledger_entries=(
                f"{packet.packet_id}={fingerprint_model(packet)}",
                f"{rerun_dossier.dossier_id}={fingerprint_model(rerun_dossier)}",
            ),
            reviewer_instructions=(
                "Open the flagship package, then the companion rerun package, then the outsider packet and limits before treating any workflow sentence as earned."
            ),
        )
    )
    verifier_report = run_standalone_bundle_verifier(
        StandaloneVerifierInput(
            bundle_id=reviewer_bundle.bundle_id,
            schema_refs=reviewer_bundle.schema_refs,
            artifact_paths=artifact_paths,
            hash_ledger_entries=reviewer_bundle.hash_ledger_entries,
        )
    )
    ready_for_outsider_review = (
        packet.complete_outsider_surface
        and rerun_dossier.scrutiny_ready
        and verifier_report.verified
        and not reviewer_bundle.completeness_notes
    )
    return WorkflowExternalReviewKit(
        kit_id=f"external_review_kit:{workflow_family.value}",
        workflow_family=workflow_family,
        artifact_path=(
            "artifacts/intelligence/external-review-kits/"
            f"{workflow_family.value}_external_review_kit.json"
        ),
        reviewer_bundle=reviewer_bundle,
        standalone_verifier_report=verifier_report,
        opening_sequence=artifact_paths[:5],
        shipped_artifact_paths=artifact_paths,
        known_exclusions=packet.missing_surface_reasons
        + rerun_dossier.remaining_limits,
        ready_for_outsider_review=ready_for_outsider_review,
        note=(
            "The external-review kit is not a promise of broad external reproducibility; it is a hostile-review bundle that lets one outsider challenge the current bounded claim with the same shipped files the maintainers rely on."
        ),
    )


def build_workflow_external_review_kit_family() -> WorkflowExternalReviewKitFamily:
    """Build outsider-usable review kits across flagship workflow families."""

    kits = tuple(
        build_workflow_external_review_kit(workflow_family)
        for workflow_family in _WORKFLOW_FAMILIES
    )
    return WorkflowExternalReviewKitFamily(
        family_id="flagship-external-review-kits",
        artifact_path=(
            "artifacts/intelligence/external-review-kits/"
            "flagship_external_review_kits.json"
        ),
        kits=kits,
        note=(
            "These kits are the shortest outsider path through the shipped benchmark, rerun, recommendation, and consequence surfaces for each flagship workflow family."
        ),
    )
