# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Conflict resolution policies for evidence contradictions."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.claims import ClaimStatus, EvidenceClaim
from bijux_proteomics_knowledge.evidence import (
    BundleTrustReport,
    EvidenceBundle,
    EvidenceRecord,
    compute_bundle_trust,
)


class ResolutionAction(StrEnum):
    """Actions available when evidence conflicts are detected."""

    ACCEPT_HIGHER_TRUST = "accept_higher_trust"
    REQUIRE_CURATION = "require_curation"
    HOLD_DECISION = "hold_decision"
    SPLIT_BY_CONTEXT = "split_by_context"
    SPLIT_BY_MODALITY = "split_by_modality"


class ConflictResolution(JsonModel):
    """Resolution proposal for a conflicting evidence pair."""

    model_config = ConfigDict(extra="forbid")

    left_evidence_id: str = Field(..., min_length=1, description="First evidence identifier.")
    right_evidence_id: str = Field(..., min_length=1, description="Second evidence identifier.")
    action: ResolutionAction = Field(..., description="Recommended resolution action.")
    rationale: str = Field(..., min_length=1, description="Why this resolution was chosen.")


class ResolutionPolicy(JsonModel):
    """Policy that controls automatic conflict resolution behavior."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable resolution policy identifier.")
    minimum_confidence_delta_for_auto_accept: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Minimum confidence gap required to auto-accept one side.",
    )
    source_precedence: dict[EvidenceSourceType, float] = Field(
        default_factory=lambda: {
            EvidenceSourceType.LAB_ASSAY: 1.0,
            EvidenceSourceType.LITERATURE: 0.9,
            EvidenceSourceType.EXTERNAL_DATABASE: 0.8,
            EvidenceSourceType.STRUCTURE_MODEL: 0.75,
            EvidenceSourceType.CURATED_NOTE: 0.7,
        },
        description="Multiplier applied by source type before comparing conflict sides.",
    )
    high_severity_requires_hold: bool = Field(
        default=True,
        description="Whether high-severity conflicts should avoid automatic acceptance.",
    )
    split_context_conflicts: bool = Field(
        default=True,
        description="Whether context mismatch conflicts should be split by context.",
    )
    split_modality_conflicts: bool = Field(
        default=True,
        description="Whether cross-modality conflicts should be split by modality.",
    )


class ResolutionSummary(JsonModel):
    """Action-level summary of resolution outcomes for one bundle."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Resolution policy identifier.")
    action_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Count of conflicts grouped by selected action.",
    )
    hold_required: bool = Field(
        default=False,
        description="Whether any conflict requires an explicit hold decision.",
    )


class ClaimBeliefUpdate(JsonModel):
    """Belief update applied to one claim after conflict resolution."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1, description="Claim identifier.")
    previous_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence before update.")
    updated_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence after update.")
    updated_status: ClaimStatus = Field(..., description="Updated claim status after applying resolutions.")
    reason: str = Field(..., min_length=1, description="Summary of why the update was applied.")


def resolve_conflicts(
    bundle: EvidenceBundle,
    *,
    policy: ResolutionPolicy | None = None,
) -> tuple[BundleTrustReport, list[ConflictResolution]]:
    """Resolve conflicting evidence using trust and curation heuristics."""
    policy = policy or ResolutionPolicy(policy_id="default-resolution-policy")
    trust = compute_bundle_trust(bundle)
    resolutions: list[ConflictResolution] = []
    now = datetime.now(UTC)
    for conflict in trust.conflicts:
        left = next(record for record in bundle.records if record.evidence_id == conflict.left_evidence_id)
        right = next(record for record in bundle.records if record.evidence_id == conflict.right_evidence_id)
        left_weighted = _resolution_score(left, policy, now=now)
        right_weighted = _resolution_score(right, policy, now=now)
        confidence_gap = abs(left_weighted - right_weighted)
        if (
            policy.split_context_conflicts
            and conflict.conflict_type in {"species_context_mismatch", "biological_system_mismatch"}
        ):
            resolutions.append(
                ConflictResolution(
                    left_evidence_id=left.evidence_id,
                    right_evidence_id=right.evidence_id,
                    action=ResolutionAction.SPLIT_BY_CONTEXT,
                    rationale="conflict reflects context mismatch and should be split by biological context",
                )
            )
            continue
        if (
            policy.split_modality_conflicts
            and left.kind is not right.kind
            and conflict.conflict_type in {"opposite_claim_polarity", "assay_readout_disagreement"}
        ):
            resolutions.append(
                ConflictResolution(
                    left_evidence_id=left.evidence_id,
                    right_evidence_id=right.evidence_id,
                    action=ResolutionAction.SPLIT_BY_MODALITY,
                    rationale="conflict spans different assay modalities and should be tracked by modality",
                )
            )
            continue
        if conflict.conflict_type == "quantitative_direction_conflict":
            resolutions.append(
                ConflictResolution(
                    left_evidence_id=left.evidence_id,
                    right_evidence_id=right.evidence_id,
                    action=ResolutionAction.HOLD_DECISION,
                    rationale="opposite quantitative effect directions require explicit adjudication",
                )
            )
            continue
        if conflict.conflict_type == "quantitative_magnitude_conflict":
            resolutions.append(
                ConflictResolution(
                    left_evidence_id=left.evidence_id,
                    right_evidence_id=right.evidence_id,
                    action=ResolutionAction.REQUIRE_CURATION,
                    rationale="large effect-size disagreement should be resolved with curation and rerun planning",
                )
            )
            continue
        if policy.high_severity_requires_hold and conflict.severity == "high":
            resolutions.append(
                ConflictResolution(
                    left_evidence_id=left.evidence_id,
                    right_evidence_id=right.evidence_id,
                    action=ResolutionAction.HOLD_DECISION,
                    rationale="high-severity conflict requires curator adjudication before progression",
                )
            )
            continue
        if left.source_type is right.source_type and left.confidence == right.confidence:
            resolutions.append(
                ConflictResolution(
                    left_evidence_id=left.evidence_id,
                    right_evidence_id=right.evidence_id,
                    action=ResolutionAction.REQUIRE_CURATION,
                    rationale="records have similar trust; a curator should resolve the conflict",
                )
            )
        elif (left_weighted - right_weighted) >= policy.minimum_confidence_delta_for_auto_accept:
            resolutions.append(
                ConflictResolution(
                    left_evidence_id=left.evidence_id,
                    right_evidence_id=right.evidence_id,
                    action=ResolutionAction.ACCEPT_HIGHER_TRUST,
                    rationale=f"{left.evidence_id} carries the stronger weighted trust signal",
                )
            )
        elif (right_weighted - left_weighted) >= policy.minimum_confidence_delta_for_auto_accept:
            resolutions.append(
                ConflictResolution(
                    left_evidence_id=left.evidence_id,
                    right_evidence_id=right.evidence_id,
                    action=ResolutionAction.ACCEPT_HIGHER_TRUST,
                    rationale=f"{right.evidence_id} carries the stronger weighted trust signal",
                )
            )
        else:
            resolutions.append(
                ConflictResolution(
                    left_evidence_id=left.evidence_id,
                    right_evidence_id=right.evidence_id,
                    action=ResolutionAction.REQUIRE_CURATION,
                    rationale=f"weighted trust separation ({confidence_gap:.2f}) is too small for automatic acceptance",
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


def _resolution_score(record: EvidenceRecord, policy: ResolutionPolicy, *, now: datetime) -> float:
    source_weight = policy.source_precedence.get(record.source_type, 0.7)
    age_days = max((now - record.observed_at).total_seconds() / 86400.0, 0.0)
    recency_multiplier = 1.0 if age_days <= 30 else 0.9
    return round(record.confidence * source_weight * recency_multiplier, 4)


def summarize_resolutions(
    resolutions: list[ConflictResolution],
    *,
    policy: ResolutionPolicy,
) -> ResolutionSummary:
    """Summarize conflict resolutions into auditable action counts."""
    counts: dict[str, int] = {}
    hold_required = False
    for resolution in resolutions:
        action = resolution.action.value
        counts[action] = counts.get(action, 0) + 1
        if resolution.action is ResolutionAction.HOLD_DECISION:
            hold_required = True
    return ResolutionSummary(
        policy_id=policy.policy_id,
        action_counts=counts,
        hold_required=hold_required,
    )


def apply_resolution_updates(
    claims: list[EvidenceClaim],
    resolutions: list[ConflictResolution],
) -> tuple[list[EvidenceClaim], list[ClaimBeliefUpdate]]:
    """Apply conflict-resolution outcomes as bounded belief updates on claims."""
    updated_claims: list[EvidenceClaim] = []
    updates: list[ClaimBeliefUpdate] = []
    for claim in claims:
        confidence = claim.confidence
        status = claim.status
        reasons: list[str] = []
        for resolution in resolutions:
            pair_ids = {resolution.left_evidence_id, resolution.right_evidence_id}
            if not pair_ids.intersection(set(claim.evidence_ids)):
                continue
            if resolution.action is ResolutionAction.HOLD_DECISION:
                confidence = max(0.0, confidence - 0.15)
                status = ClaimStatus.DISPUTED
                reasons.append("high-severity unresolved conflict requires hold")
            elif resolution.action is ResolutionAction.REQUIRE_CURATION:
                confidence = max(0.0, confidence - 0.05)
                reasons.append("claim linked to conflict requiring curation")
            elif resolution.action in {ResolutionAction.SPLIT_BY_CONTEXT, ResolutionAction.SPLIT_BY_MODALITY}:
                confidence = max(0.0, confidence - 0.1)
                status = ClaimStatus.DISPUTED
                reasons.append("claim must be interpreted with narrower context boundaries")
            elif resolution.action is ResolutionAction.ACCEPT_HIGHER_TRUST:
                preferred = resolution.rationale.split(" ", maxsplit=1)[0]
                if preferred in claim.evidence_ids:
                    confidence = min(1.0, confidence + 0.1)
                    status = ClaimStatus.SUPPORTED
                    reasons.append(f"higher-trust evidence {preferred} supports this claim")
                else:
                    confidence = max(0.0, confidence - 0.1)
                    reasons.append("claim aligns with lower-trust side of conflict")
        if reasons:
            updated = claim.model_copy(update={"confidence": round(confidence, 4), "status": status})
            updated_claims.append(updated)
            updates.append(
                ClaimBeliefUpdate(
                    claim_id=claim.claim_id,
                    previous_confidence=claim.confidence,
                    updated_confidence=round(confidence, 4),
                    updated_status=status,
                    reason="; ".join(reasons),
                )
            )
        else:
            updated_claims.append(claim)
    return updated_claims, updates
