# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Packet-boundary contracts for reviewable workflow stage outputs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class WorkflowPacketSerializationMode(StrEnum):
    """How a workflow stage packet must survive a package boundary."""

    MODEL_DUMP = "model_dump"


@dataclass(frozen=True)
class WorkflowStagePacketBoundaryContract:
    """Serialization contract for one review packet that crosses package boundaries."""

    stage_id: str
    packet_surface_ref: str
    serialization_mode: WorkflowPacketSerializationMode
    required_top_level_keys: tuple[str, ...]
    consumer_stage_ids: tuple[str, ...]
    notes: tuple[str, ...] = ()


def build_workflow_stage_packet_boundary_contracts() -> tuple[WorkflowStagePacketBoundaryContract, ...]:
    """Return packet-boundary contracts for the flagship reviewable workflow."""

    return (
        WorkflowStagePacketBoundaryContract(
            stage_id="runtime-workflow-manifest",
            packet_surface_ref=(
                "bijux_proteomics_runtime.workflows.plans.build_workflow_manifest_explanation_report"
            ),
            serialization_mode=WorkflowPacketSerializationMode.MODEL_DUMP,
            required_top_level_keys=("workflow_id", "entries"),
            consumer_stage_ids=("core-identification-review",),
        ),
        WorkflowStagePacketBoundaryContract(
            stage_id="core-identification-review",
            packet_surface_ref=(
                "bijux_proteomics.identification.contracts.build_review_ready_evidence_bundle"
            ),
            serialization_mode=WorkflowPacketSerializationMode.MODEL_DUMP,
            required_top_level_keys=(
                "document_schema",
                "protein_summary",
                "combined_evidence",
            ),
            consumer_stage_ids=(
                "core-quantification-review",
                "core-ptm-review",
                "knowledge-evidence-review",
            ),
        ),
        WorkflowStagePacketBoundaryContract(
            stage_id="core-quantification-review",
            packet_surface_ref=(
                "bijux_proteomics.quantification.review.build_quant_review_bundle"
            ),
            serialization_mode=WorkflowPacketSerializationMode.MODEL_DUMP,
            required_top_level_keys=(
                "decision_readiness",
                "missingness_profile",
                "effect_size_da_report",
            ),
            consumer_stage_ids=("knowledge-evidence-review", "intelligence-decision-review"),
        ),
        WorkflowStagePacketBoundaryContract(
            stage_id="core-ptm-review",
            packet_surface_ref=(
                "bijux_proteomics.ptm.review.build_ptm_lab_validation_packet"
            ),
            serialization_mode=WorkflowPacketSerializationMode.MODEL_DUMP,
            required_top_level_keys=("entries", "unresolved_risk_count"),
            consumer_stage_ids=("knowledge-evidence-review", "lab-review-packet"),
        ),
        WorkflowStagePacketBoundaryContract(
            stage_id="knowledge-evidence-review",
            packet_surface_ref=(
                "bijux_proteomics_knowledge.reviews.packets.build_knowledge_review_packet"
            ),
            serialization_mode=WorkflowPacketSerializationMode.MODEL_DUMP,
            required_top_level_keys=(
                "target_id",
                "gate_recommendation",
                "executive_summary",
            ),
            consumer_stage_ids=("intelligence-decision-review",),
        ),
        WorkflowStagePacketBoundaryContract(
            stage_id="intelligence-decision-review",
            packet_surface_ref=(
                "bijux_proteomics_intelligence.reviews.packets.build_intelligence_review_packet"
            ),
            serialization_mode=WorkflowPacketSerializationMode.MODEL_DUMP,
            required_top_level_keys=("consensus", "portfolio", "review_ready"),
            consumer_stage_ids=("lab-review-packet",),
        ),
        WorkflowStagePacketBoundaryContract(
            stage_id="lab-review-packet",
            packet_surface_ref=(
                "bijux_proteomics_lab.planning.assays.build_lab_review_packet_bundle"
            ),
            serialization_mode=WorkflowPacketSerializationMode.MODEL_DUMP,
            required_top_level_keys=(
                "target_evidence_ids",
                "assay_rationale_by_id",
                "unresolved_risks",
            ),
            consumer_stage_ids=("lab-operational-follow-up",),
        ),
        WorkflowStagePacketBoundaryContract(
            stage_id="lab-operational-follow-up",
            packet_surface_ref=(
                "bijux_proteomics_lab.reconciliation.follow_up.build_operational_follow_up_path"
            ),
            serialization_mode=WorkflowPacketSerializationMode.MODEL_DUMP,
            required_top_level_keys=("execution_request", "reconciliation"),
            consumer_stage_ids=(),
        ),
    )
