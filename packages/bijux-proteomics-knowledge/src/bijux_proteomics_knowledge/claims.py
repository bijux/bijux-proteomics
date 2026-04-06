# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Claim-level models and lineage for evidence-backed decisions."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import EvidenceId, JsonModel, TargetId
from bijux_proteomics_knowledge.evidence import EvidenceBundle


class ClaimStatus(StrEnum):
    """Support status for a scientific claim."""

    SUPPORTED = "supported"
    DISPUTED = "disputed"
    STALE = "stale"
    INSUFFICIENT = "insufficient"


class ClaimPolarity(StrEnum):
    """Polarity of a scientific claim."""

    SUPPORTING = "supporting"
    CONTRADICTING = "contradicting"
    NEUTRAL = "neutral"


class ClaimResolutionState(StrEnum):
    """Resolution state for a claim in a decision workflow."""

    OPEN = "open"
    CLOSED = "closed"


class ClaimType(StrEnum):
    """Structured taxonomy for scientific claim content."""

    MECHANISTIC = "mechanistic"
    EFFICACY = "efficacy"
    SAFETY = "safety"
    DEVELOPABILITY = "developability"
    BIOMARKER = "biomarker"


class EvidenceClaim(JsonModel):
    """A claim backed by one or more evidence records."""

    model_config = ConfigDict(extra="forbid")

    claim_id: EvidenceId = Field(..., description="Stable claim identifier.")
    target_id: TargetId = Field(..., description="Target identifier.")
    statement: str = Field(..., min_length=1, description="Human-readable claim statement.")
    subject: str | None = Field(default=None, description="Claim subject entity.")
    relation: str | None = Field(default=None, description="Claim relation predicate.")
    object: str | None = Field(default=None, description="Claim object entity.")
    condition: str | None = Field(default=None, description="Experimental condition for the claim.")
    direction: str | None = Field(default=None, description="Directionality such as increases or decreases.")
    magnitude: float | None = Field(default=None, description="Optional claim magnitude.")
    claim_type: ClaimType = Field(
        default=ClaimType.MECHANISTIC,
        description="Claim taxonomy for policy and reporting.",
    )
    evidence_ids: list[EvidenceId] = Field(
        default_factory=list,
        description="Evidence records supporting the claim.",
    )
    contradicting_evidence_ids: list[EvidenceId] = Field(
        default_factory=list,
        description="Evidence records that currently contradict the claim.",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Scientific assumptions that this claim depends on.",
    )
    resolution_assays: list[str] = Field(
        default_factory=list,
        description="Assays that can resolve or falsify the claim.",
    )
    status: ClaimStatus = Field(..., description="Current support status for the claim.")
    polarity: ClaimPolarity = Field(
        default=ClaimPolarity.SUPPORTING,
        description="Whether the claim supports or contradicts progression.",
    )
    resolution_state: ClaimResolutionState = Field(
        default=ClaimResolutionState.OPEN,
        description="Whether the claim still needs active resolution.",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Aggregate confidence in the claim.",
    )
    contradiction_group: str | None = Field(
        default=None,
        description="Optional contradiction group for mutually exclusive claims.",
    )
    decision_impact: str = Field(
        default="supporting_context",
        min_length=1,
        description="How strongly this claim influences decision flow.",
    )


class DecisionLineage(JsonModel):
    """Lineage from a decision area to claims and supporting evidence."""

    model_config = ConfigDict(extra="forbid")

    decision_tag: str = Field(..., min_length=1, description="Decision area label.")
    claim_ids: list[EvidenceId] = Field(
        default_factory=list,
        description="Claims that inform the decision.",
    )
    disputed_claim_ids: list[EvidenceId] = Field(
        default_factory=list,
        description="Claims that dispute or contradict the decision context.",
    )
    evidence_ids: list[EvidenceId] = Field(
        default_factory=list,
        description="Evidence records linked through the claims.",
    )


class ClaimStrengthUpdate(JsonModel):
    """Structured confidence update for a claim after new evidence."""

    model_config = ConfigDict(extra="forbid")

    claim_id: EvidenceId = Field(..., description="Claim identifier.")
    previous_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence before update.")
    updated_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence after update.")
    rationale: str = Field(..., min_length=1, description="Why confidence changed.")


class ClaimValidationIssue(JsonModel):
    """Scientific validity issue detected in a claim."""

    model_config = ConfigDict(extra="forbid")

    claim_id: EvidenceId = Field(..., description="Claim identifier.")
    code: str = Field(..., min_length=1, description="Stable validation issue code.")
    message: str = Field(..., min_length=1, description="Human-readable issue message.")


class HypothesisDossier(JsonModel):
    """Structured summary of claim evidence for a decision hypothesis."""

    model_config = ConfigDict(extra="forbid")

    target_id: TargetId = Field(..., description="Target identifier.")
    decision_tag: str = Field(..., min_length=1, description="Decision tag under review.")
    supporting_claim_ids: list[EvidenceId] = Field(default_factory=list, description="Supporting claim identifiers.")
    contradicting_claim_ids: list[EvidenceId] = Field(default_factory=list, description="Contradicting claim identifiers.")
    unresolved_claim_ids: list[EvidenceId] = Field(default_factory=list, description="Open claims requiring more work.")
    required_resolution_assays: list[str] = Field(default_factory=list, description="Unique assays needed for resolution.")
    support_confidence_mean: float = Field(default=0.0, ge=0.0, le=1.0, description="Mean confidence of supporting claims.")


class ResolutionAssayOutcome(JsonModel):
    """Outcome payload for an assay used to resolve a claim."""

    model_config = ConfigDict(extra="forbid")

    claim_id: EvidenceId = Field(..., description="Claim identifier.")
    assay_name: str = Field(..., min_length=1, description="Assay used for resolution.")
    confirms_claim: bool = Field(..., description="Whether the assay confirms the claim direction.")
    confidence_delta: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Bounded confidence update magnitude from this assay outcome.",
    )
    note: str | None = Field(default=None, description="Optional interpretation note.")


def build_claim(
    *,
    claim_id: str,
    target_id: str,
    statement: str,
    evidence_ids: list[str],
    contradicting_evidence_ids: list[str] | None = None,
    assumptions: list[str] | None = None,
    resolution_assays: list[str] | None = None,
    status: ClaimStatus,
    polarity: ClaimPolarity = ClaimPolarity.SUPPORTING,
    resolution_state: ClaimResolutionState = ClaimResolutionState.OPEN,
    claim_type: ClaimType = ClaimType.MECHANISTIC,
    confidence: float = 0.5,
    contradiction_group: str | None = None,
    decision_impact: str = "supporting_context",
    subject: str | None = None,
    relation: str | None = None,
    object: str | None = None,
    condition: str | None = None,
    direction: str | None = None,
    magnitude: float | None = None,
) -> EvidenceClaim:
    """Build a claim from explicit evidence identifiers."""
    return EvidenceClaim(
        claim_id=claim_id,
        target_id=target_id,
        statement=statement,
        evidence_ids=evidence_ids,
        contradicting_evidence_ids=contradicting_evidence_ids or [],
        assumptions=assumptions or [],
        resolution_assays=resolution_assays or [],
        status=status,
        polarity=polarity,
        resolution_state=resolution_state,
        claim_type=claim_type,
        confidence=confidence,
        contradiction_group=contradiction_group,
        decision_impact=decision_impact,
        subject=subject,
        relation=relation,
        object=object,
        condition=condition,
        direction=direction,
        magnitude=magnitude,
    )


def build_decision_lineage(
    bundle: EvidenceBundle,
    claims: list[EvidenceClaim],
    decision_tag: str,
) -> DecisionLineage:
    """Build claim-and-evidence lineage for a decision tag."""
    selected_claims = [
        claim
        for claim in claims
        if claim.status is ClaimStatus.SUPPORTED
        and any(
            record.evidence_id in claim.evidence_ids and decision_tag in record.decision_tags
            for record in bundle.records
        )
    ]
    disputed_claims = [
        claim
        for claim in claims
        if claim.polarity is ClaimPolarity.CONTRADICTING
        and any(
            record.evidence_id in claim.evidence_ids and decision_tag in record.decision_tags
            for record in bundle.records
        )
    ]
    evidence_ids = [
        record.evidence_id
        for record in bundle.records
        if decision_tag in record.decision_tags
        and any(record.evidence_id in claim.evidence_ids for claim in selected_claims)
    ]
    return DecisionLineage(
        decision_tag=decision_tag,
        claim_ids=[claim.claim_id for claim in selected_claims],
        disputed_claim_ids=[claim.claim_id for claim in disputed_claims],
        evidence_ids=evidence_ids,
    )


def close_claim(claim: EvidenceClaim) -> EvidenceClaim:
    """Return a claim marked as closed in the resolution workflow."""
    return claim.model_copy(update={"resolution_state": ClaimResolutionState.CLOSED})


def link_evidence_to_claim(
    claim: EvidenceClaim,
    bundle: EvidenceBundle,
) -> EvidenceClaim:
    """Attach known bundle evidence IDs to a claim without duplicating IDs."""
    known_ids = {record.evidence_id for record in bundle.records}
    linked = list(claim.evidence_ids)
    for evidence_id in sorted(known_ids):
        if evidence_id not in linked:
            linked.append(evidence_id)
    return claim.model_copy(update={"evidence_ids": linked})


def strengthen_claim(
    claim: EvidenceClaim,
    *,
    delta: float,
    rationale: str,
) -> tuple[EvidenceClaim, ClaimStrengthUpdate]:
    """Increase claim confidence by a bounded delta."""
    updated_confidence = min(1.0, round(claim.confidence + max(delta, 0.0), 4))
    updated = claim.model_copy(update={"confidence": updated_confidence, "status": ClaimStatus.SUPPORTED})
    return updated, ClaimStrengthUpdate(
        claim_id=claim.claim_id,
        previous_confidence=claim.confidence,
        updated_confidence=updated_confidence,
        rationale=rationale,
    )


def weaken_claim(
    claim: EvidenceClaim,
    *,
    delta: float,
    rationale: str,
) -> tuple[EvidenceClaim, ClaimStrengthUpdate]:
    """Decrease claim confidence by a bounded delta."""
    updated_confidence = max(0.0, round(claim.confidence - max(delta, 0.0), 4))
    updated_status = ClaimStatus.DISPUTED if updated_confidence < 0.5 else claim.status
    updated = claim.model_copy(update={"confidence": updated_confidence, "status": updated_status})
    return updated, ClaimStrengthUpdate(
        claim_id=claim.claim_id,
        previous_confidence=claim.confidence,
        updated_confidence=updated_confidence,
        rationale=rationale,
    )


def validate_claims(claims: list[EvidenceClaim]) -> list[ClaimValidationIssue]:
    """Validate scientific structure and contradiction hygiene for claims."""
    issues: list[ClaimValidationIssue] = []
    claim_ids = [claim.claim_id for claim in claims]
    if len(claim_ids) != len(set(claim_ids)):
        issues.append(
            ClaimValidationIssue(
                claim_id="claim-set",
                code="claim-id-duplicate",
                message="claims should use unique claim_id values",
            )
        )
    contradiction_groups = {claim.contradiction_group for claim in claims if claim.contradiction_group}
    for claim in claims:
        if not claim.evidence_ids:
            issues.append(
                ClaimValidationIssue(
                    claim_id=claim.claim_id,
                    code="claim-evidence-missing",
                    message="claim should reference at least one evidence_id",
                )
            )
        if claim.polarity is ClaimPolarity.CONTRADICTING and not claim.contradicting_evidence_ids:
            issues.append(
                ClaimValidationIssue(
                    claim_id=claim.claim_id,
                    code="contradicting-evidence-missing",
                    message="contradicting claims should include contradicting_evidence_ids",
                )
            )
        if claim.resolution_state is ClaimResolutionState.OPEN and not claim.resolution_assays:
            issues.append(
                ClaimValidationIssue(
                    claim_id=claim.claim_id,
                    code="resolution-assays-missing",
                    message="open claims should include at least one resolution assay",
                )
            )
        if claim.claim_type is ClaimType.MECHANISTIC and (
            not claim.subject or not claim.relation or not claim.object
        ):
            issues.append(
                ClaimValidationIssue(
                    claim_id=claim.claim_id,
                    code="mechanistic-structure-missing",
                    message="mechanistic claims should define subject, relation, and object",
                )
            )
        if claim.resolution_state is ClaimResolutionState.CLOSED and claim.status is ClaimStatus.INSUFFICIENT:
            issues.append(
                ClaimValidationIssue(
                    claim_id=claim.claim_id,
                    code="closed-insufficient-claim",
                    message="closed claims should not remain in insufficient status",
                )
            )
    for group in sorted(contradiction_groups):
        group_claims = [claim for claim in claims if claim.contradiction_group == group]
        if len(group_claims) < 2:
            issues.append(
                ClaimValidationIssue(
                    claim_id=group_claims[0].claim_id,
                    code="contradiction-group-singleton",
                    message=f"contradiction_group '{group}' should include at least two claims",
                )
            )
            continue
        if all(claim.polarity is ClaimPolarity.SUPPORTING for claim in group_claims) or all(
            claim.polarity is ClaimPolarity.CONTRADICTING for claim in group_claims
        ):
            issues.append(
                ClaimValidationIssue(
                    claim_id=group_claims[0].claim_id,
                    code="contradiction-group-polarity-unbalanced",
                    message=f"contradiction_group '{group}' should contain opposing claim polarities",
                )
            )
    return issues


def build_hypothesis_dossier(
    bundle: EvidenceBundle,
    claims: list[EvidenceClaim],
    *,
    decision_tag: str,
) -> HypothesisDossier:
    """Build a claim-level hypothesis dossier for one decision dimension."""
    scoped_claims = [
        claim
        for claim in claims
        if any(
            decision_tag in record.decision_tags and record.evidence_id in claim.evidence_ids
            for record in bundle.records
        )
    ]
    supporting = [claim for claim in scoped_claims if claim.polarity is ClaimPolarity.SUPPORTING]
    contradicting = [claim for claim in scoped_claims if claim.polarity is ClaimPolarity.CONTRADICTING]
    unresolved = [claim for claim in scoped_claims if claim.resolution_state is ClaimResolutionState.OPEN]
    support_confidence_mean = (
        round(sum(claim.confidence for claim in supporting) / len(supporting), 4)
        if supporting
        else 0.0
    )
    required_assays = sorted(
        {
            assay
            for claim in unresolved
            for assay in claim.resolution_assays
        }
    )
    target_id = scoped_claims[0].target_id if scoped_claims else bundle.target_id
    return HypothesisDossier(
        target_id=target_id,
        decision_tag=decision_tag,
        supporting_claim_ids=[claim.claim_id for claim in supporting],
        contradicting_claim_ids=[claim.claim_id for claim in contradicting],
        unresolved_claim_ids=[claim.claim_id for claim in unresolved],
        required_resolution_assays=required_assays,
        support_confidence_mean=support_confidence_mean,
    )


def apply_resolution_assay_outcome(
    claim: EvidenceClaim,
    outcome: ResolutionAssayOutcome,
) -> tuple[EvidenceClaim, ClaimStrengthUpdate]:
    """Apply a structured resolution-assay outcome to one claim."""
    if claim.claim_id != outcome.claim_id:
        raise ValueError("resolution assay outcome claim_id does not match claim")
    if outcome.confirms_claim:
        updated_confidence = min(1.0, round(claim.confidence + outcome.confidence_delta, 4))
        updated_status = ClaimStatus.SUPPORTED if updated_confidence >= 0.5 else claim.status
        rationale = f"{outcome.assay_name} confirms claim direction"
    else:
        updated_confidence = max(0.0, round(claim.confidence - outcome.confidence_delta, 4))
        updated_status = ClaimStatus.DISPUTED if updated_confidence < 0.5 else claim.status
        rationale = f"{outcome.assay_name} does not confirm claim direction"
    if outcome.note:
        rationale = f"{rationale}; {outcome.note}"
    updated_claim = claim.model_copy(update={"confidence": updated_confidence, "status": updated_status})
    return updated_claim, ClaimStrengthUpdate(
        claim_id=claim.claim_id,
        previous_confidence=claim.confidence,
        updated_confidence=updated_confidence,
        rationale=rationale,
    )
