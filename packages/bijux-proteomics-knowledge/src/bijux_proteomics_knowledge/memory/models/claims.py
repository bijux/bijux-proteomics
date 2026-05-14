# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Claim-level models and lineage for evidence-backed decisions."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import ClaimId, EvidenceId, JsonModel, TargetId
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    compute_bundle_trust,
)


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


class ClaimEvidenceState(StrEnum):
    """Explicit scientific evidence state for one claim."""

    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    CONFLICTED = "conflicted"
    UNRESOLVED = "unresolved"


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

    claim_id: ClaimId = Field(..., description="Stable claim identifier.")
    target_id: TargetId = Field(..., description="Target identifier.")
    statement: str = Field(
        ..., min_length=1, description="Human-readable claim statement."
    )
    subject: str | None = Field(default=None, description="Claim subject entity.")
    relation: str | None = Field(default=None, description="Claim relation predicate.")
    object: str | None = Field(default=None, description="Claim object entity.")
    condition: str | None = Field(
        default=None, description="Experimental condition for the claim."
    )
    direction: str | None = Field(
        default=None, description="Directionality such as increases or decreases."
    )
    magnitude: float | None = Field(
        default=None, description="Optional claim magnitude."
    )
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
    status: ClaimStatus = Field(
        ..., description="Current support status for the claim."
    )
    polarity: ClaimPolarity = Field(
        default=ClaimPolarity.SUPPORTING,
        description="Whether the claim supports or contradicts progression.",
    )
    resolution_state: ClaimResolutionState = Field(
        default=ClaimResolutionState.OPEN,
        description="Whether the claim still needs active resolution.",
    )
    evidence_state: ClaimEvidenceState = Field(
        default=ClaimEvidenceState.UNRESOLVED,
        description="Explicit scientific evidence state for the claim.",
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
    claim_ids: list[ClaimId] = Field(
        default_factory=list,
        description="Claims that inform the decision.",
    )
    disputed_claim_ids: list[ClaimId] = Field(
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

    claim_id: ClaimId = Field(..., description="Claim identifier.")
    previous_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence before update."
    )
    updated_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence after update."
    )
    rationale: str = Field(..., min_length=1, description="Why confidence changed.")


class ClaimValidationIssue(JsonModel):
    """Scientific validity issue detected in a claim."""

    model_config = ConfigDict(extra="forbid")

    claim_id: ClaimId = Field(..., description="Claim identifier.")
    code: str = Field(..., min_length=1, description="Stable validation issue code.")
    message: str = Field(..., min_length=1, description="Human-readable issue message.")


class HypothesisDossier(JsonModel):
    """Structured summary of claim evidence for a decision hypothesis."""

    model_config = ConfigDict(extra="forbid")

    target_id: TargetId = Field(..., description="Target identifier.")
    decision_tag: str = Field(
        ..., min_length=1, description="Decision tag under review."
    )
    supporting_claim_ids: list[ClaimId] = Field(
        default_factory=list, description="Supporting claim identifiers."
    )
    contradicting_claim_ids: list[ClaimId] = Field(
        default_factory=list, description="Contradicting claim identifiers."
    )
    unresolved_claim_ids: list[ClaimId] = Field(
        default_factory=list, description="Open claims requiring more work."
    )
    required_resolution_assays: list[str] = Field(
        default_factory=list, description="Unique assays needed for resolution."
    )
    support_confidence_mean: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Mean confidence of supporting claims."
    )


class ResolutionAssayOutcome(JsonModel):
    """Outcome payload for an assay used to resolve a claim."""

    model_config = ConfigDict(extra="forbid")

    claim_id: ClaimId = Field(..., description="Claim identifier.")
    assay_name: str = Field(..., min_length=1, description="Assay used for resolution.")
    confirms_claim: bool = Field(
        ..., description="Whether the assay confirms the claim direction."
    )
    confidence_delta: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Bounded confidence update magnitude from this assay outcome.",
    )
    note: str | None = Field(default=None, description="Optional interpretation note.")


class KnowledgeGap(JsonModel):
    """A concrete unresolved gap that blocks stronger scientific confidence."""

    model_config = ConfigDict(extra="forbid")

    gap_code: str = Field(..., min_length=1, description="Stable knowledge gap code.")
    message: str = Field(
        ..., min_length=1, description="Human-readable gap description."
    )
    related_claim_ids: list[ClaimId] = Field(
        default_factory=list, description="Claim identifiers tied to this gap."
    )


class ClaimTrustGapReport(JsonModel):
    """What is still missing before one claim can be trusted for a decision."""

    model_config = ConfigDict(extra="forbid")

    claim_id: ClaimId = Field(..., description="Claim identifier under review.")
    decision_tag: str = Field(..., min_length=1)
    evidence_state: ClaimEvidenceState
    trust_score: float = Field(..., ge=0.0, le=1.0)
    minimum_trust_score: float = Field(..., ge=0.0, le=1.0)
    trust_ready: bool
    supporting_evidence_ids: list[EvidenceId] = Field(default_factory=list)
    contradicting_evidence_ids: list[EvidenceId] = Field(default_factory=list)
    blocking_gaps: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class ClaimQuery(JsonModel):
    """Structured query for filtering target claims."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1, description="Target identifier.")
    status: ClaimStatus | None = Field(
        default=None, description="Optional status filter."
    )
    claim_type: ClaimType | None = Field(
        default=None, description="Optional claim-type filter."
    )
    polarity: ClaimPolarity | None = Field(
        default=None, description="Optional polarity filter."
    )
    resolution_state: ClaimResolutionState | None = Field(
        default=None, description="Optional resolution-state filter."
    )
    minimum_confidence: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Optional confidence floor."
    )
    decision_impact: str | None = Field(
        default=None, description="Optional decision-impact filter."
    )
    contradiction_group: str | None = Field(
        default=None, description="Optional contradiction-group filter."
    )


class ClaimConsistencyReport(JsonModel):
    """Consistency diagnostics for a claim set under one decision scope."""

    model_config = ConfigDict(extra="forbid")

    target_id: TargetId = Field(..., description="Target identifier.")
    claim_count: int = Field(default=0, ge=0, description="Number of claims evaluated.")
    open_claim_count: int = Field(default=0, ge=0, description="Number of open claims.")
    contradiction_group_count: int = Field(
        default=0, ge=0, description="Number of contradiction groups."
    )
    inconsistent_groups: list[str] = Field(
        default_factory=list,
        description="Contradiction groups missing both polarities.",
    )
    notes: list[str] = Field(default_factory=list, description="Consistency notes.")


class MechanisticCompletenessReport(JsonModel):
    """Completeness report for mechanistic claim structure."""

    model_config = ConfigDict(extra="forbid")

    claim_id: ClaimId = Field(..., description="Claim identifier.")
    completeness_score: float = Field(
        ..., ge=0.0, le=1.0, description="Mechanistic completeness score."
    )
    missing_fields: list[str] = Field(
        default_factory=list, description="Missing mechanistic fields."
    )


class ClaimContradictionMatrix(JsonModel):
    """Pairwise contradiction relationships among scoped claims."""

    model_config = ConfigDict(extra="forbid")

    decision_tag: str = Field(
        ..., min_length=1, description="Decision tag for scoped claims."
    )
    rows: list[str] = Field(
        default_factory=list, description="Claim IDs in matrix order."
    )
    relations: dict[str, str] = Field(
        default_factory=dict,
        description="Pair relation map using '<left>|<right>' keys and relation labels.",
    )


class ClaimEvidenceLinkIssue(JsonModel):
    """Issue in claim-to-evidence linkage integrity."""

    model_config = ConfigDict(extra="forbid")

    claim_id: ClaimId = Field(..., description="Claim identifier.")
    code: str = Field(..., min_length=1, description="Stable issue code.")
    message: str = Field(..., min_length=1, description="Human-readable issue message.")


class ClaimFalsifiabilityReport(JsonModel):
    """Falsifiability assessment for a scientific claim."""

    model_config = ConfigDict(extra="forbid")

    claim_id: ClaimId = Field(..., description="Claim identifier.")
    falsifiable: bool = Field(
        ..., description="Whether claim is structured for falsification."
    )
    missing_fields: list[str] = Field(
        default_factory=list, description="Missing mechanistic fields."
    )
    notes: list[str] = Field(
        default_factory=list, description="Falsifiability rationale notes."
    )


def classify_claim_evidence_state(
    *,
    status: ClaimStatus,
    polarity: ClaimPolarity,
    resolution_state: ClaimResolutionState,
    evidence_ids: list[str],
    contradicting_evidence_ids: list[str],
) -> ClaimEvidenceState:
    """Classify one claim into an explicit scientific evidence state."""
    if resolution_state is ClaimResolutionState.OPEN and (
        status is ClaimStatus.INSUFFICIENT or not evidence_ids
    ):
        return ClaimEvidenceState.UNRESOLVED
    if contradicting_evidence_ids and evidence_ids:
        return ClaimEvidenceState.CONFLICTED
    if polarity is ClaimPolarity.CONTRADICTING:
        return ClaimEvidenceState.CONTRADICTED
    if status is ClaimStatus.SUPPORTED:
        return ClaimEvidenceState.SUPPORTED
    if status in {ClaimStatus.DISPUTED, ClaimStatus.INSUFFICIENT}:
        return ClaimEvidenceState.UNRESOLVED
    return ClaimEvidenceState.SUPPORTED


def build_claim(
    *,
    claim_id: ClaimId,
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
    object_value: str | None = None,
    condition: str | None = None,
    direction: str | None = None,
    magnitude: float | None = None,
) -> EvidenceClaim:
    """Build a claim from explicit evidence identifiers."""
    resolved_contradicting_evidence_ids = contradicting_evidence_ids or []
    resolved_evidence_ids = evidence_ids
    return EvidenceClaim(
        claim_id=claim_id,
        target_id=target_id,
        statement=statement,
        evidence_ids=resolved_evidence_ids,
        contradicting_evidence_ids=resolved_contradicting_evidence_ids,
        assumptions=assumptions or [],
        resolution_assays=resolution_assays or [],
        status=status,
        polarity=polarity,
        resolution_state=resolution_state,
        evidence_state=classify_claim_evidence_state(
            status=status,
            polarity=polarity,
            resolution_state=resolution_state,
            evidence_ids=resolved_evidence_ids,
            contradicting_evidence_ids=resolved_contradicting_evidence_ids,
        ),
        claim_type=claim_type,
        confidence=confidence,
        contradiction_group=contradiction_group,
        decision_impact=decision_impact,
        subject=subject,
        relation=relation,
        object=object_value,
        condition=condition,
        direction=direction,
        magnitude=magnitude,
    )


def evaluate_claim_falsifiability(claim: EvidenceClaim) -> ClaimFalsifiabilityReport:
    """Evaluate whether a claim is structured for falsification."""
    missing_fields: list[str] = []
    if not claim.subject:
        missing_fields.append("subject")
    if not claim.relation:
        missing_fields.append("relation")
    if not claim.object:
        missing_fields.append("object")
    if not claim.condition:
        missing_fields.append("condition")
    if not claim.resolution_assays:
        missing_fields.append("resolution_assays")
    falsifiable = not missing_fields
    notes = (
        ["claim is falsifiable via defined resolution assays"]
        if falsifiable
        else ["claim lacks falsifiable structure"]
    )
    return ClaimFalsifiabilityReport(
        claim_id=claim.claim_id,
        falsifiable=falsifiable,
        missing_fields=missing_fields,
        notes=notes,
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
            record.evidence_id in claim.evidence_ids
            and decision_tag in record.decision_tags
            for record in bundle.records
        )
    ]
    disputed_claims = [
        claim
        for claim in claims
        if claim.polarity is ClaimPolarity.CONTRADICTING
        and any(
            record.evidence_id in claim.evidence_ids
            and decision_tag in record.decision_tags
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
    return claim.model_copy(
        update={
            "resolution_state": ClaimResolutionState.CLOSED,
            "evidence_state": classify_claim_evidence_state(
                status=claim.status,
                polarity=claim.polarity,
                resolution_state=ClaimResolutionState.CLOSED,
                evidence_ids=claim.evidence_ids,
                contradicting_evidence_ids=claim.contradicting_evidence_ids,
            ),
        }
    )


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
    return claim.model_copy(
        update={
            "evidence_ids": linked,
            "evidence_state": classify_claim_evidence_state(
                status=claim.status,
                polarity=claim.polarity,
                resolution_state=claim.resolution_state,
                evidence_ids=linked,
                contradicting_evidence_ids=claim.contradicting_evidence_ids,
            ),
        }
    )


def strengthen_claim(
    claim: EvidenceClaim,
    *,
    delta: float,
    rationale: str,
) -> tuple[EvidenceClaim, ClaimStrengthUpdate]:
    """Increase claim confidence by a bounded delta."""
    updated_confidence = min(1.0, round(claim.confidence + max(delta, 0.0), 4))
    updated = claim.model_copy(
        update={
            "confidence": updated_confidence,
            "status": ClaimStatus.SUPPORTED,
            "evidence_state": classify_claim_evidence_state(
                status=ClaimStatus.SUPPORTED,
                polarity=claim.polarity,
                resolution_state=claim.resolution_state,
                evidence_ids=claim.evidence_ids,
                contradicting_evidence_ids=claim.contradicting_evidence_ids,
            ),
        }
    )
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
    updated = claim.model_copy(
        update={
            "confidence": updated_confidence,
            "status": updated_status,
            "evidence_state": classify_claim_evidence_state(
                status=updated_status,
                polarity=claim.polarity,
                resolution_state=claim.resolution_state,
                evidence_ids=claim.evidence_ids,
                contradicting_evidence_ids=claim.contradicting_evidence_ids,
            ),
        }
    )
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
    contradiction_groups = {
        claim.contradiction_group for claim in claims if claim.contradiction_group
    }
    for claim in claims:
        if not claim.evidence_ids:
            issues.append(
                ClaimValidationIssue(
                    claim_id=claim.claim_id,
                    code="claim-evidence-missing",
                    message="claim should reference at least one evidence_id",
                )
            )
        if (
            claim.polarity is ClaimPolarity.CONTRADICTING
            and not claim.contradicting_evidence_ids
        ):
            issues.append(
                ClaimValidationIssue(
                    claim_id=claim.claim_id,
                    code="contradicting-evidence-missing",
                    message="contradicting claims should include contradicting_evidence_ids",
                )
            )
        if (
            claim.evidence_state is ClaimEvidenceState.CONFLICTED
            and not claim.contradicting_evidence_ids
        ):
            issues.append(
                ClaimValidationIssue(
                    claim_id=claim.claim_id,
                    code="conflicted-claim-missing-contradiction-links",
                    message="conflicted claims should link both supporting and contradicting evidence identifiers",
                )
            )
        if (
            claim.resolution_state is ClaimResolutionState.OPEN
            and not claim.resolution_assays
        ):
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
        if (
            claim.resolution_state is ClaimResolutionState.CLOSED
            and claim.status is ClaimStatus.INSUFFICIENT
        ):
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
        if all(
            claim.polarity is ClaimPolarity.SUPPORTING for claim in group_claims
        ) or all(
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
            decision_tag in record.decision_tags
            and record.evidence_id in claim.evidence_ids
            for record in bundle.records
        )
    ]
    supporting = [
        claim for claim in scoped_claims if claim.polarity is ClaimPolarity.SUPPORTING
    ]
    contradicting = [
        claim
        for claim in scoped_claims
        if claim.polarity is ClaimPolarity.CONTRADICTING
    ]
    unresolved = [
        claim
        for claim in scoped_claims
        if claim.resolution_state is ClaimResolutionState.OPEN
    ]
    support_confidence_mean = (
        round(sum(claim.confidence for claim in supporting) / len(supporting), 4)
        if supporting
        else 0.0
    )
    required_assays = sorted(
        {assay for claim in unresolved for assay in claim.resolution_assays}
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
        updated_confidence = min(
            1.0, round(claim.confidence + outcome.confidence_delta, 4)
        )
        updated_status = (
            ClaimStatus.SUPPORTED if updated_confidence >= 0.5 else claim.status
        )
        rationale = f"{outcome.assay_name} confirms claim direction"
    else:
        updated_confidence = max(
            0.0, round(claim.confidence - outcome.confidence_delta, 4)
        )
        updated_status = (
            ClaimStatus.DISPUTED if updated_confidence < 0.5 else claim.status
        )
        rationale = f"{outcome.assay_name} does not confirm claim direction"
    if outcome.note:
        rationale = f"{rationale}; {outcome.note}"
    updated_claim = claim.model_copy(
        update={
            "confidence": updated_confidence,
            "status": updated_status,
            "evidence_state": classify_claim_evidence_state(
                status=updated_status,
                polarity=claim.polarity,
                resolution_state=claim.resolution_state,
                evidence_ids=claim.evidence_ids,
                contradicting_evidence_ids=claim.contradicting_evidence_ids,
            ),
        }
    )
    return updated_claim, ClaimStrengthUpdate(
        claim_id=claim.claim_id,
        previous_confidence=claim.confidence,
        updated_confidence=updated_confidence,
        rationale=rationale,
    )


def identify_knowledge_gaps(
    bundle: EvidenceBundle,
    claims: list[EvidenceClaim],
    *,
    decision_tag: str,
) -> list[KnowledgeGap]:
    """Identify unresolved claim and evidence gaps for one decision dimension."""
    gaps: list[KnowledgeGap] = []
    decision_claims = [
        claim
        for claim in claims
        if any(
            decision_tag in record.decision_tags
            and record.evidence_id in claim.evidence_ids
            for record in bundle.records
        )
    ]
    if not decision_claims:
        gaps.append(
            KnowledgeGap(
                gap_code="no-claims-for-decision-tag",
                message=f"no claims are linked to decision tag '{decision_tag}'",
            )
        )
        return gaps
    open_claims = [
        claim
        for claim in decision_claims
        if claim.resolution_state is ClaimResolutionState.OPEN
    ]
    if open_claims:
        gaps.append(
            KnowledgeGap(
                gap_code="open-claims-require-resolution",
                message="one or more claims remain open and require resolution assays",
                related_claim_ids=[claim.claim_id for claim in open_claims],
            )
        )
    unresolved_assay_claims = [
        claim for claim in open_claims if not claim.resolution_assays
    ]
    if unresolved_assay_claims:
        gaps.append(
            KnowledgeGap(
                gap_code="resolution-assays-not-defined",
                message="open claims are missing required resolution assays",
                related_claim_ids=[claim.claim_id for claim in unresolved_assay_claims],
            )
        )
    contradicting = [
        claim
        for claim in decision_claims
        if claim.polarity is ClaimPolarity.CONTRADICTING
    ]
    if contradicting and not any(
        claim.contradicting_evidence_ids for claim in contradicting
    ):
        gaps.append(
            KnowledgeGap(
                gap_code="contradiction-evidence-not-linked",
                message="contradicting claims exist without linked contradicting evidence identifiers",
                related_claim_ids=[claim.claim_id for claim in contradicting],
            )
        )
    decisive_records = [
        record
        for record in bundle.records
        if decision_tag in record.decision_tags and record.strength.value == "decisive"
    ]
    if not decisive_records:
        gaps.append(
            KnowledgeGap(
                gap_code="no-decisive-evidence",
                message=f"decision tag '{decision_tag}' has no decisive evidence records",
            )
        )
    return gaps


def build_claim_trust_gap_report(
    bundle: EvidenceBundle,
    claim: EvidenceClaim,
    *,
    decision_tag: str,
    minimum_trust_score: float = 0.7,
) -> ClaimTrustGapReport:
    """Summarize what still blocks trusting one claim for a concrete decision."""
    claim_evidence_ids = set(claim.evidence_ids) | set(claim.contradicting_evidence_ids)
    scoped_records = [
        record for record in bundle.records if record.evidence_id in claim_evidence_ids
    ]
    scoped_bundle = bundle.model_copy(update={"records": scoped_records})
    trust_score = (
        compute_bundle_trust(scoped_bundle).trust_score if scoped_records else 0.0
    )
    evidence_state = classify_claim_evidence_state(
        status=claim.status,
        polarity=claim.polarity,
        resolution_state=claim.resolution_state,
        evidence_ids=claim.evidence_ids,
        contradicting_evidence_ids=claim.contradicting_evidence_ids,
    )
    knowledge_gaps = identify_knowledge_gaps(
        scoped_bundle, [claim], decision_tag=decision_tag
    )
    blocking_gaps = [gap.message for gap in knowledge_gaps]
    recommendations = []
    if trust_score < minimum_trust_score:
        blocking_gaps.append(
            f"trust score {trust_score:.2f} is below minimum {minimum_trust_score:.2f}"
        )
        recommendations.append(
            "strengthen the claim with higher-trust or orthogonal evidence"
        )
    if not claim.evidence_ids:
        blocking_gaps.append("claim has no linked supporting evidence")
        recommendations.append(
            "link the claim to at least one supporting evidence record"
        )
    if claim.contradicting_evidence_ids:
        recommendations.append(
            "resolve contradicting evidence before treating the claim as trusted"
        )
    if claim.resolution_state is ClaimResolutionState.OPEN and claim.resolution_assays:
        recommendations.append(
            "close the open claim with the declared resolution assays"
        )
    trust_ready = not blocking_gaps and evidence_state is ClaimEvidenceState.SUPPORTED
    return ClaimTrustGapReport(
        claim_id=claim.claim_id,
        decision_tag=decision_tag,
        evidence_state=evidence_state,
        trust_score=round(trust_score, 4),
        minimum_trust_score=minimum_trust_score,
        trust_ready=trust_ready,
        supporting_evidence_ids=list(claim.evidence_ids),
        contradicting_evidence_ids=list(claim.contradicting_evidence_ids),
        blocking_gaps=blocking_gaps,
        recommendations=sorted(set(recommendations)),
    )


def evaluate_claim_consistency(
    claims: list[EvidenceClaim], *, target_id: str
) -> ClaimConsistencyReport:
    """Summarize claim-set consistency for one target."""
    scoped = [claim for claim in claims if claim.target_id == target_id]
    groups = sorted(
        {claim.contradiction_group for claim in scoped if claim.contradiction_group}
    )
    inconsistent_groups: list[str] = []
    for group in groups:
        group_claims = [claim for claim in scoped if claim.contradiction_group == group]
        polarities = {claim.polarity for claim in group_claims}
        if polarities != {ClaimPolarity.SUPPORTING, ClaimPolarity.CONTRADICTING}:
            inconsistent_groups.append(group)
    notes: list[str] = []
    if inconsistent_groups:
        notes.append(
            "some contradiction groups are missing balanced supporting and contradicting claims"
        )
    if any(claim.resolution_state is ClaimResolutionState.OPEN for claim in scoped):
        notes.append("open claims still require resolution work")
    if not notes:
        notes.append("claim set looks internally consistent")
    return ClaimConsistencyReport(
        target_id=target_id,
        claim_count=len(scoped),
        open_claim_count=sum(
            1 for claim in scoped if claim.resolution_state is ClaimResolutionState.OPEN
        ),
        contradiction_group_count=len(groups),
        inconsistent_groups=inconsistent_groups,
        notes=notes,
    )


def evaluate_mechanistic_completeness(
    claim: EvidenceClaim,
) -> MechanisticCompletenessReport:
    """Score how completely a mechanistic claim is specified."""
    required = {
        "subject": claim.subject,
        "relation": claim.relation,
        "object": claim.object,
        "condition": claim.condition,
        "direction": claim.direction,
    }
    missing = [
        name
        for name, value in required.items()
        if value is None or not str(value).strip()
    ]
    score = round((len(required) - len(missing)) / len(required), 4)
    return MechanisticCompletenessReport(
        claim_id=claim.claim_id,
        completeness_score=score,
        missing_fields=missing,
    )


def build_contradiction_matrix(
    bundle: EvidenceBundle,
    claims: list[EvidenceClaim],
    *,
    decision_tag: str,
) -> ClaimContradictionMatrix:
    """Build pairwise contradiction matrix for decision-scoped claims."""
    scoped = [
        claim
        for claim in claims
        if any(
            record.evidence_id in claim.evidence_ids
            and decision_tag in record.decision_tags
            for record in bundle.records
        )
    ]
    rows = [claim.claim_id for claim in scoped]
    relations: dict[str, str] = {}
    for left in scoped:
        for right in scoped:
            key = f"{left.claim_id}|{right.claim_id}"
            if left.claim_id == right.claim_id:
                relations[key] = "self"
                continue
            if (
                left.contradiction_group
                and left.contradiction_group == right.contradiction_group
            ):
                if left.polarity is right.polarity:
                    relations[key] = "same-group-same-polarity"
                else:
                    relations[key] = "same-group-opposing-polarity"
            elif set(left.evidence_ids).intersection(
                set(right.contradicting_evidence_ids)
            ) or set(right.evidence_ids).intersection(
                set(left.contradicting_evidence_ids)
            ):
                relations[key] = "cross-linked-contradiction"
            else:
                relations[key] = "independent"
    return ClaimContradictionMatrix(
        decision_tag=decision_tag,
        rows=rows,
        relations=relations,
    )


def query_claims(claims: list[EvidenceClaim], query: ClaimQuery) -> list[EvidenceClaim]:
    """Filter claims for one target using structured query fields."""

    filtered = [claim for claim in claims if claim.target_id == query.target_id]
    if query.status is not None:
        filtered = [claim for claim in filtered if claim.status is query.status]
    if query.claim_type is not None:
        filtered = [claim for claim in filtered if claim.claim_type is query.claim_type]
    if query.polarity is not None:
        filtered = [claim for claim in filtered if claim.polarity is query.polarity]
    if query.resolution_state is not None:
        filtered = [
            claim
            for claim in filtered
            if claim.resolution_state is query.resolution_state
        ]
    if query.minimum_confidence is not None:
        filtered = [
            claim for claim in filtered if claim.confidence >= query.minimum_confidence
        ]
    if query.decision_impact is not None:
        filtered = [
            claim
            for claim in filtered
            if claim.decision_impact == query.decision_impact
        ]
    if query.contradiction_group is not None:
        filtered = [
            claim
            for claim in filtered
            if claim.contradiction_group == query.contradiction_group
        ]
    return filtered


def audit_claim_evidence_links(
    bundle: EvidenceBundle,
    claims: list[EvidenceClaim],
) -> list[ClaimEvidenceLinkIssue]:
    """Audit claim references against evidence IDs present in the bundle."""
    known_ids = {record.evidence_id for record in bundle.records}
    issues: list[ClaimEvidenceLinkIssue] = []
    for claim in claims:
        missing_support = [
            evidence_id
            for evidence_id in claim.evidence_ids
            if evidence_id not in known_ids
        ]
        missing_contradictions = [
            evidence_id
            for evidence_id in claim.contradicting_evidence_ids
            if evidence_id not in known_ids
        ]
        if missing_support:
            issues.append(
                ClaimEvidenceLinkIssue(
                    claim_id=claim.claim_id,
                    code="support-evidence-missing-in-bundle",
                    message=f"missing support evidence ids: {', '.join(sorted(missing_support))}",
                )
            )
        if missing_contradictions:
            issues.append(
                ClaimEvidenceLinkIssue(
                    claim_id=claim.claim_id,
                    code="contradiction-evidence-missing-in-bundle",
                    message=f"missing contradiction evidence ids: {', '.join(sorted(missing_contradictions))}",
                )
            )
    return issues
