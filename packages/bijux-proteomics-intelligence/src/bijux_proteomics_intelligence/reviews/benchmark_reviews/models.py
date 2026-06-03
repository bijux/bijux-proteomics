# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared benchmark review contracts for release-facing workflow scrutiny."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.review.collaboration import ExternalReviewerBundle
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_foundation.support.states import SupportState
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparator_failures import (
    ComparatorClaimSupportState,
)
from bijux_proteomics_knowledge.references.workflows.comparators import (
    ProteomicsComparatorTool,
)
from bijux_proteomics_knowledge.references.workflows.registry import (
    BenchmarkAuthorityStatus,
)
from bijux_proteomics_knowledge.references.workflows.scientific_release import (
    ScientificReleasePacket,
)


class BenchmarkReviewClaim(JsonModel):
    """One benchmark-backed claim with explicit support posture and review notes."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    support_state: SupportState
    summary: str = Field(..., min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    scientific_limits: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkReviewArtifact(JsonModel):
    """One reviewable artifact that anchors a benchmark-backed workflow claim."""

    model_config = ConfigDict(extra="forbid")

    owner_package: str = Field(..., min_length=1)
    surface_name: str = Field(..., min_length=1)
    artifact_kind: str = Field(..., min_length=1)
    artifact_id: str = Field(..., min_length=1)


class BenchmarkComparatorPosition(JsonModel):
    """Exact comparator-tool posture carried into benchmark reviews."""

    model_config = ConfigDict(extra="forbid")

    comparator_tool: ProteomicsComparatorTool
    comparator_path_ids: tuple[str, ...] = Field(default_factory=tuple)
    matched_behaviors: tuple[str, ...] = Field(default_factory=tuple)
    partial_behaviors: tuple[str, ...] = Field(default_factory=tuple)
    refused_behaviors: tuple[str, ...] = Field(default_factory=tuple)
    not_attempted_behaviors: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowVendorCaveatEntry(JsonModel):
    """One vendor-facing caveat that must stay visible in release review."""

    model_config = ConfigDict(extra="forbid")

    surface: str = Field(..., min_length=1)
    severity: SupportState
    note: str = Field(..., min_length=1)


class WorkflowVendorCaveatLedger(JsonModel):
    """Release-facing ledger of vendor and execution-parity caveats."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[WorkflowVendorCaveatEntry, ...] = Field(default_factory=tuple)
    vendor_support_state: SupportState


class PtmFamilyReleaseTrack(JsonModel):
    """Release-facing PTM family track with explicit support posture."""

    model_config = ConfigDict(extra="forbid")

    family_name: str = Field(..., min_length=1)
    support_state: SupportState
    summary: str = Field(..., min_length=1)
    scientific_limits: tuple[str, ...] = Field(default_factory=tuple)


class ReviewerGroundingState(StrEnum):
    """How strong the biological grounding is in a release-facing review summary."""

    DECISION_GRADE = "decision_grade"
    REVIEW_GRADE = "review_grade"
    THIN = "thin"


class WorkflowBenchmarkReview(JsonModel):
    """Release-facing review output for one benchmark-backed workflow path."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    benchmark_authority_status: BenchmarkAuthorityStatus
    title: str = Field(..., min_length=1)
    reviewer_summary: str = Field(..., min_length=1)
    benchmark_package_id: str | None = None
    benchmark_package_summary: str | None = None
    benchmark_package_artifact_ids: tuple[str, ...] = Field(default_factory=tuple)
    comparator_positions: tuple[BenchmarkComparatorPosition, ...] = Field(
        default_factory=tuple
    )
    public_claim_support_state: ComparatorClaimSupportState
    comparator_failure_summaries: tuple[str, ...] = Field(default_factory=tuple)
    improvement_targets: tuple[str, ...] = Field(default_factory=tuple)
    known_loss_to_established_tool: bool = False
    reviewer_grounding_state: ReviewerGroundingState
    reviewer_grounding_limits: tuple[str, ...] = Field(default_factory=tuple)
    curated_reference_context: tuple[str, ...] = Field(default_factory=tuple)
    decision_grade_criteria: tuple[str, ...] = Field(default_factory=tuple)
    minimum_controls_required: tuple[str, ...] = Field(default_factory=tuple)
    scientific_release_packet: ScientificReleasePacket
    supported_repo_claims: tuple[str, ...] = Field(default_factory=tuple)
    authorized_claim_scope: tuple[str, ...] = Field(default_factory=tuple)
    owner_surfaces: tuple[str, ...] = Field(default_factory=tuple)
    review_artifacts: tuple[BenchmarkReviewArtifact, ...] = Field(default_factory=tuple)
    claim_summaries: tuple[BenchmarkReviewClaim, ...] = Field(default_factory=tuple)
    scientific_limits: tuple[str, ...] = Field(default_factory=tuple)
    comparison_notes: tuple[str, ...] = Field(default_factory=tuple)
    vendor_caveat_ledger: WorkflowVendorCaveatLedger | None = None
    supported_ptm_families: tuple[str, ...] = Field(default_factory=tuple)
    ptm_family_tracks: tuple[PtmFamilyReleaseTrack, ...] = Field(default_factory=tuple)
    external_reviewer_bundle: ExternalReviewerBundle
    ready_for_release_review: bool


__all__ = [
    "BenchmarkComparatorPosition",
    "BenchmarkReviewArtifact",
    "BenchmarkReviewClaim",
    "PtmFamilyReleaseTrack",
    "ReviewerGroundingState",
    "WorkflowBenchmarkReview",
    "WorkflowVendorCaveatEntry",
    "WorkflowVendorCaveatLedger",
]
