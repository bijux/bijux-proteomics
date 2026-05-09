# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Workflow-scoped decision briefs for the flagship evidence chain."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class WorkflowClaimTier(StrEnum):
    """Repository claim taxonomy for workflow-scoped proof surfaces."""

    OWNED_CONTRACT = "owned_contract"
    BENCHMARK_BACKED_BEHAVIOR = "benchmark_backed_behavior"
    RUNTIME_PROVEN_WORKFLOW = "runtime_proven_workflow"
    FUTURE_WORK = "future_work"


class FlagshipEvidenceDecisionBrief(JsonModel):
    """Evidence decision brief for the flagship workflow chain."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    flagship_family_id: str = Field(..., min_length=1)
    claim_tier: WorkflowClaimTier
    artifact_path: str = Field(..., min_length=1)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    accepted_claim_count: int = Field(..., ge=0)
    contested_claim_count: int = Field(..., ge=0)
    limitation_notes: tuple[str, ...] = Field(default_factory=tuple)
    review_complete: bool
    note: str = Field(..., min_length=1)


def build_flagship_evidence_decision_brief(
    *,
    workflow_id: str,
    artifact_path: str,
    evidence_pointers: tuple[str, ...],
    accepted_claim_count: int,
    contested_claim_count: int,
    claim_tier: WorkflowClaimTier = WorkflowClaimTier.RUNTIME_PROVEN_WORKFLOW,
    flagship_family_id: str = "flagship-workflows",
    limitation_notes: tuple[str, ...] = (),
) -> FlagshipEvidenceDecisionBrief:
    """Build the evidence decision brief for the flagship workflow chain."""

    if not artifact_path.startswith("artifacts/"):
        raise ValueError("artifact_path must live under artifacts/")
    review_complete = bool(evidence_pointers) and (
        accepted_claim_count + contested_claim_count
    ) > 0
    return FlagshipEvidenceDecisionBrief(
        workflow_id=workflow_id,
        flagship_family_id=flagship_family_id,
        claim_tier=claim_tier,
        artifact_path=artifact_path,
        evidence_pointers=evidence_pointers,
        accepted_claim_count=accepted_claim_count,
        contested_claim_count=contested_claim_count,
        limitation_notes=limitation_notes,
        review_complete=review_complete,
        note=(
            "The flagship evidence decision brief uses the repository claim taxonomy "
            "so users can distinguish the checked workflow chain from benchmark-only or future-work claims."
        ),
    )
