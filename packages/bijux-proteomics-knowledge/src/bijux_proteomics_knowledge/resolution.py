# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Conflict resolution policies for evidence contradictions."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.evidence import (
    BundleTrustReport,
    EvidenceBundle,
    EvidenceConflict,
    compute_bundle_trust,
)


class ResolutionAction(StrEnum):
    """Actions available when evidence conflicts are detected."""

    ACCEPT_HIGHER_TRUST = "accept_higher_trust"
    REQUIRE_CURATION = "require_curation"
    HOLD_DECISION = "hold_decision"


class ConflictResolution(JsonModel):
    """Resolution proposal for a conflicting evidence pair."""

    model_config = ConfigDict(extra="forbid")

    left_evidence_id: str = Field(..., min_length=1, description="First evidence identifier.")
    right_evidence_id: str = Field(..., min_length=1, description="Second evidence identifier.")
    action: ResolutionAction = Field(..., description="Recommended resolution action.")
    rationale: str = Field(..., min_length=1, description="Why this resolution was chosen.")


def resolve_conflicts(bundle: EvidenceBundle) -> tuple[BundleTrustReport, list[ConflictResolution]]:
    """Resolve conflicting evidence using trust and curation heuristics."""
    trust = compute_bundle_trust(bundle)
    resolutions: list[ConflictResolution] = []
    for conflict in trust.conflicts:
        left = next(record for record in bundle.records if record.evidence_id == conflict.left_evidence_id)
        right = next(record for record in bundle.records if record.evidence_id == conflict.right_evidence_id)
        if left.source_type is right.source_type and left.confidence == right.confidence:
            resolutions.append(
                ConflictResolution(
                    left_evidence_id=left.evidence_id,
                    right_evidence_id=right.evidence_id,
                    action=ResolutionAction.REQUIRE_CURATION,
                    rationale="records have similar trust; a curator should resolve the conflict",
                )
            )
        elif left.confidence >= right.confidence:
            resolutions.append(
                ConflictResolution(
                    left_evidence_id=left.evidence_id,
                    right_evidence_id=right.evidence_id,
                    action=ResolutionAction.ACCEPT_HIGHER_TRUST,
                    rationale=f"{left.evidence_id} carries the stronger confidence signal",
                )
            )
        else:
            resolutions.append(
                ConflictResolution(
                    left_evidence_id=left.evidence_id,
                    right_evidence_id=right.evidence_id,
                    action=ResolutionAction.ACCEPT_HIGHER_TRUST,
                    rationale=f"{right.evidence_id} carries the stronger confidence signal",
                )
            )
    if trust.conflicts and not resolutions:
        resolutions.append(
            ConflictResolution(
                left_evidence_id=trust.conflicts[0].left_evidence_id,
                right_evidence_id=trust.conflicts[0].right_evidence_id,
                action=ResolutionAction.HOLD_DECISION,
                rationale="conflicts exist without a usable trust separation",
            )
        )
    return trust, resolutions
