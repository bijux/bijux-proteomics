# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable workflow handoff contracts across the proteomics package spine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class WorkflowOwnerPackage(StrEnum):
    """Canonical package owners participating in the reviewable workflow spine."""

    RUNTIME = "bijux-proteomics-runtime"
    CORE = "bijux-proteomics-core"
    KNOWLEDGE = "bijux-proteomics-knowledge"
    INTELLIGENCE = "bijux-proteomics-intelligence"
    LAB = "bijux-proteomics-lab"


@dataclass(frozen=True)
class WorkflowStageHandoffContract:
    """One explicit, reviewable handoff between workflow stages."""

    stage_id: str
    owner_package: WorkflowOwnerPackage
    produced_surface_ref: str
    review_packet_surface_ref: str
    upstream_stage_ids: tuple[str, ...]
    downstream_stage_ids: tuple[str, ...]
    required_artifact_kinds: tuple[str, ...]
    notes: tuple[str, ...] = ()


def build_canonical_workflow_handoff_contracts() -> tuple[WorkflowStageHandoffContract, ...]:
    """Return the governed stage-to-stage handoff graph for the flagship workflow."""

    return (
        WorkflowStageHandoffContract(
            stage_id="runtime-workflow-manifest",
            owner_package=WorkflowOwnerPackage.RUNTIME,
            produced_surface_ref=(
                "bijux_proteomics_runtime.workflows.plans.build_proteomics_workflow_manifest"
            ),
            review_packet_surface_ref=(
                "bijux_proteomics_runtime.workflows.plans.build_workflow_manifest_explanation_report"
            ),
            upstream_stage_ids=(),
            downstream_stage_ids=("core-identification-review",),
            required_artifact_kinds=("workflow-manifest", "workflow-manifest-report"),
            notes=(
                "The workflow manifest is the only allowed root of the reviewable workflow graph.",
                "Downstream stages may not invent hidden inputs outside the manifest and its declared assets.",
            ),
        ),
        WorkflowStageHandoffContract(
            stage_id="core-identification-review",
            owner_package=WorkflowOwnerPackage.CORE,
            produced_surface_ref=(
                "bijux_proteomics.identification.contracts.build_review_ready_evidence_bundle"
            ),
            review_packet_surface_ref=(
                "bijux_proteomics.identification.contracts.build_review_ready_evidence_bundle"
            ),
            upstream_stage_ids=("runtime-workflow-manifest",),
            downstream_stage_ids=(
                "core-quantification-review",
                "core-ptm-review",
                "knowledge-evidence-review",
            ),
            required_artifact_kinds=(
                "review-ready-evidence-bundle",
                "psm-summary",
                "protein-summary",
                "combined-evidence-report",
            ),
            notes=(
                "Identification review is the shared evidence base for quantification, PTM review, and knowledge synthesis.",
                "Any downstream protein, peptide, or site claim must remain traceable to this bundle.",
            ),
        ),
        WorkflowStageHandoffContract(
            stage_id="core-quantification-review",
            owner_package=WorkflowOwnerPackage.CORE,
            produced_surface_ref=(
                "bijux_proteomics.quantification.review.build_quant_review_bundle"
            ),
            review_packet_surface_ref=(
                "bijux_proteomics.quantification.review.build_quant_review_bundle"
            ),
            upstream_stage_ids=("core-identification-review",),
            downstream_stage_ids=("knowledge-evidence-review", "intelligence-decision-review"),
            required_artifact_kinds=(
                "quant-review-bundle",
                "normalization-matrix",
                "missingness-profile",
                "decision-readiness-report",
            ),
            notes=(
                "Quantification may only promote proteins already supported by identification review.",
            ),
        ),
        WorkflowStageHandoffContract(
            stage_id="core-ptm-review",
            owner_package=WorkflowOwnerPackage.CORE,
            produced_surface_ref=(
                "bijux_proteomics.ptm.review.build_ptm_lab_validation_packet"
            ),
            review_packet_surface_ref=(
                "bijux_proteomics.ptm.review.build_ptm_lab_validation_packet"
            ),
            upstream_stage_ids=("core-identification-review",),
            downstream_stage_ids=("knowledge-evidence-review", "lab-review-packet"),
            required_artifact_kinds=(
                "ptm-lab-validation-packet",
                "ptm-occupancy-counterpart-report",
            ),
            notes=(
                "PTM review must carry ambiguity and control needs explicitly before any lab recommendation survives the boundary.",
            ),
        ),
        WorkflowStageHandoffContract(
            stage_id="knowledge-evidence-review",
            owner_package=WorkflowOwnerPackage.KNOWLEDGE,
            produced_surface_ref=(
                "bijux_proteomics_knowledge.reviews.decision_briefs.build_knowledge_decision_brief"
            ),
            review_packet_surface_ref=(
                "bijux_proteomics_knowledge.reviews.decision_briefs.build_knowledge_decision_brief"
            ),
            upstream_stage_ids=(
                "core-identification-review",
                "core-quantification-review",
                "core-ptm-review",
            ),
            downstream_stage_ids=("intelligence-decision-review",),
            required_artifact_kinds=(
                "knowledge-review-packet",
                "evidence-state-index",
                "critical-claim-provenance",
            ),
            notes=(
                "Knowledge review owns the benchmark-versus-literature boundary before decision ranking.",
            ),
        ),
        WorkflowStageHandoffContract(
            stage_id="intelligence-decision-review",
            owner_package=WorkflowOwnerPackage.INTELLIGENCE,
            produced_surface_ref=(
                "bijux_proteomics_intelligence.reviews.packets.build_intelligence_review_packet"
            ),
            review_packet_surface_ref=(
                "bijux_proteomics_intelligence.reviews.packets.build_intelligence_review_packet"
            ),
            upstream_stage_ids=("knowledge-evidence-review", "core-quantification-review"),
            downstream_stage_ids=("lab-review-packet",),
            required_artifact_kinds=(
                "intelligence-review-packet",
                "consensus-summary",
                "portfolio-summary",
            ),
            notes=(
                "Intelligence may downgrade or refuse advancement, but it may not bypass knowledge grounding.",
            ),
        ),
        WorkflowStageHandoffContract(
            stage_id="lab-review-packet",
            owner_package=WorkflowOwnerPackage.LAB,
            produced_surface_ref=(
                "bijux_proteomics_lab.planning.assays.build_lab_review_packet_bundle"
            ),
            review_packet_surface_ref=(
                "bijux_proteomics_lab.planning.assays.build_lab_review_packet_bundle"
            ),
            upstream_stage_ids=("core-ptm-review", "intelligence-decision-review"),
            downstream_stage_ids=("lab-operational-follow-up",),
            required_artifact_kinds=(
                "lab-review-packet-bundle",
                "assay-rationale-map",
                "unresolved-risk-ledger",
            ),
            notes=(
                "Lab review must preserve assay rationale, unresolved risk, and blocking control needs as first-class fields.",
            ),
        ),
        WorkflowStageHandoffContract(
            stage_id="lab-operational-follow-up",
            owner_package=WorkflowOwnerPackage.LAB,
            produced_surface_ref=(
                "bijux_proteomics_lab.reconciliation.follow_up.build_operational_follow_up_path"
            ),
            review_packet_surface_ref=(
                "bijux_proteomics_lab.reconciliation.follow_up.build_operational_follow_up_path"
            ),
            upstream_stage_ids=("lab-review-packet",),
            downstream_stage_ids=(),
            required_artifact_kinds=(
                "operational-follow-up-path",
                "next-cycle-packet",
                "operator-action-ledger",
            ),
            notes=(
                "Observed outcomes must close the loop with explicit next-cycle actions rather than narrative-only reconciliation.",
            ),
        ),
    )
