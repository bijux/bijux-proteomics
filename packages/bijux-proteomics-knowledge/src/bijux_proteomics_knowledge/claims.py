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


class EvidenceClaim(JsonModel):
    """A claim backed by one or more evidence records."""

    model_config = ConfigDict(extra="forbid")

    claim_id: EvidenceId = Field(..., description="Stable claim identifier.")
    target_id: TargetId = Field(..., description="Target identifier.")
    statement: str = Field(..., min_length=1, description="Human-readable claim statement.")
    evidence_ids: list[EvidenceId] = Field(
        default_factory=list,
        description="Evidence records supporting the claim.",
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


def build_claim(
    *,
    claim_id: str,
    target_id: str,
    statement: str,
    evidence_ids: list[str],
    status: ClaimStatus,
    polarity: ClaimPolarity = ClaimPolarity.SUPPORTING,
    resolution_state: ClaimResolutionState = ClaimResolutionState.OPEN,
) -> EvidenceClaim:
    """Build a claim from explicit evidence identifiers."""
    return EvidenceClaim(
        claim_id=claim_id,
        target_id=target_id,
        statement=statement,
        evidence_ids=evidence_ids,
        status=status,
        polarity=polarity,
        resolution_state=resolution_state,
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
