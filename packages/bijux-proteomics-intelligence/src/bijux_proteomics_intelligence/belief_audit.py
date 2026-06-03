# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Belief-audit rows that balance support, contradiction, and falsification."""

from __future__ import annotations

import csv
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.claims.support import (
    ClaimSupportStatus,
    ClaimSupportValidationEntry,
    validate_claim_support,
)
from bijux_proteomics_intelligence.falsifiers import (
    ClaimFalsifierEntry,
    generate_falsifiers,
)
from bijux_proteomics_knowledge.memory.integrity.graph import EvidenceGraph
from bijux_proteomics_knowledge.memory.models.claims import (
    ClaimResolutionState,
    EvidenceClaim,
)

_TOP_CLAIM_CONFIDENCE_THRESHOLD = 0.8


class BeliefAuditEntry(JsonModel):
    """One balanced audit row for one analytical claim."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    evidence_for: tuple[str, ...] = Field(default_factory=tuple)
    evidence_against: tuple[str, ...] = Field(default_factory=tuple)
    uncertainty: tuple[str, ...] = Field(default_factory=tuple)
    falsifier: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    next_check: str = Field(..., min_length=1)


class BeliefAuditSummary(JsonModel):
    """Stable summary over one belief-audit pass."""

    model_config = ConfigDict(extra="forbid")

    claim_count: int = Field(..., ge=0)
    top_claim_count: int = Field(..., ge=0)
    top_claim_ids: tuple[str, ...] = Field(default_factory=tuple)
    conflicted_claim_count: int = Field(..., ge=0)
    invalid_claim_count: int = Field(..., ge=0)


class BeliefAuditReport(JsonModel):
    """Owned report over belief-audit rows for analytical claims."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[BeliefAuditEntry, ...] = Field(default_factory=tuple)
    summary: BeliefAuditSummary
    note: str = Field(..., min_length=1)


def build_belief_audit(
    claims: tuple[EvidenceClaim, ...] | list[EvidenceClaim],
    evidence_graph: EvidenceGraph,
) -> BeliefAuditReport:
    """Build one belief-audit row for every claim and enforce top-claim coverage."""

    claim_items = tuple(claims)
    support_report = validate_claim_support(claim_items, evidence_graph)
    support_by_claim_id = {entry.claim_id: entry for entry in support_report.entries}
    entries = tuple(
        sorted(
            (
                _belief_audit_entry(
                    claim=claim,
                    support_entry=support_by_claim_id[claim.claim_id],
                )
                for claim in claim_items
            ),
            key=lambda entry: (-entry.confidence, entry.claim_id),
        )
    )
    top_claim_ids = _top_claim_ids(claim_items)
    audited_claim_ids = {entry.claim_id for entry in entries}
    missing_top_claim_ids = tuple(
        claim_id for claim_id in top_claim_ids if claim_id not in audited_claim_ids
    )
    if missing_top_claim_ids:
        raise ValueError(
            "top claims are missing belief-audit rows: "
            + ", ".join(missing_top_claim_ids)
        )

    return BeliefAuditReport(
        entries=entries,
        summary=BeliefAuditSummary(
            claim_count=len(entries),
            top_claim_count=len(top_claim_ids),
            top_claim_ids=top_claim_ids,
            conflicted_claim_count=sum(
                support_by_claim_id[claim.claim_id].support_status
                is ClaimSupportStatus.CONFLICTED
                for claim in claim_items
            ),
            invalid_claim_count=sum(
                support_by_claim_id[claim.claim_id].support_status
                is ClaimSupportStatus.INVALID
                for claim in claim_items
            ),
        ),
        note=(
            "belief audit rows balance support, contradiction, uncertainty, "
            "falsification, and next checks for every claim, and they refuse to "
            "drop high-confidence claims from that review surface"
        ),
    )


def render_belief_audit_tsv(entries: tuple[BeliefAuditEntry, ...]) -> str:
    """Render belief-audit rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "claim_id",
            "evidence_for",
            "evidence_against",
            "uncertainty",
            "falsifier",
            "confidence",
            "next_check",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.claim_id,
                ";".join(entry.evidence_for),
                ";".join(entry.evidence_against),
                ";".join(entry.uncertainty),
                entry.falsifier,
                entry.confidence,
                entry.next_check,
            )
        )
    return handle.getvalue()


def _belief_audit_entry(
    *,
    claim: EvidenceClaim,
    support_entry: ClaimSupportValidationEntry,
) -> BeliefAuditEntry:
    """Assemble one stable audit row from a claim and its support validation."""

    falsifier_entry = generate_falsifiers(claim).entries[0]
    evidence_for = _stable_evidence_ids(claim.evidence_ids)
    evidence_against = _stable_evidence_ids(support_entry.contradicting_evidence)
    uncertainty = _uncertainty_messages(claim=claim, support_entry=support_entry)
    return BeliefAuditEntry(
        claim_id=claim.claim_id,
        evidence_for=evidence_for,
        evidence_against=evidence_against,
        uncertainty=uncertainty,
        falsifier=falsifier_entry.falsifier_type.value,
        confidence=_audited_confidence(claim=claim, support_entry=support_entry),
        next_check=_next_check(
            claim=claim,
            support_entry=support_entry,
            falsifier_entry=falsifier_entry,
            uncertainty=uncertainty,
        ),
    )


def _stable_evidence_ids(evidence_ids: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Sort and deduplicate evidence identifiers for stable TSV rendering."""

    return tuple(sorted(dict.fromkeys(evidence_ids)))


def _uncertainty_messages(
    *,
    claim: EvidenceClaim,
    support_entry: ClaimSupportValidationEntry,
) -> tuple[str, ...]:
    """Collect the uncertainty flags that still constrain the claim."""

    issues: list[str] = []
    if support_entry.support_status is ClaimSupportStatus.INVALID:
        issues.extend(
            f"missing_support:{item}" for item in support_entry.missing_support
        )
    if support_entry.support_status is ClaimSupportStatus.CONFLICTED:
        issues.append("contradicting_evidence_present")
    if claim.resolution_state is ClaimResolutionState.OPEN:
        issues.append("active_resolution_required")
    if claim.assumptions:
        issues.append("assumption_dependent")
    if claim.confidence < _TOP_CLAIM_CONFIDENCE_THRESHOLD:
        issues.append("baseline_confidence_below_top_claim_threshold")
    return tuple(dict.fromkeys(issues))


def _audited_confidence(
    *,
    claim: EvidenceClaim,
    support_entry: ClaimSupportValidationEntry,
) -> float:
    """Downgrade confidence when support quality or resolution state is weak."""

    confidence = claim.confidence
    if support_entry.support_status is ClaimSupportStatus.INVALID:
        confidence -= 0.35
    elif support_entry.support_status is ClaimSupportStatus.CONFLICTED:
        confidence -= 0.2
    if claim.resolution_state is ClaimResolutionState.OPEN:
        confidence -= 0.05
    if claim.assumptions:
        confidence -= 0.05
    return round(min(max(confidence, 0.0), 1.0), 4)


def _next_check(
    *,
    claim: EvidenceClaim,
    support_entry: ClaimSupportValidationEntry,
    falsifier_entry: ClaimFalsifierEntry,
    uncertainty: tuple[str, ...],
) -> str:
    """Pick the next concrete validation action for the audited claim."""

    if support_entry.missing_support:
        return support_entry.missing_support[0]
    if claim.resolution_assays:
        return claim.resolution_assays[0]
    if uncertainty:
        return uncertainty[0]
    return falsifier_entry.required_evidence[0]


def _top_claim_ids(claims: tuple[EvidenceClaim, ...]) -> tuple[str, ...]:
    """Return the high-confidence claim identifiers that must stay audited."""

    top_claims = tuple(
        sorted(
            (
                claim
                for claim in claims
                if claim.confidence >= _TOP_CLAIM_CONFIDENCE_THRESHOLD
            ),
            key=lambda claim: (-claim.confidence, claim.claim_id),
        )
    )
    if top_claims:
        return tuple(claim.claim_id for claim in top_claims)

    if not claims:
        return ()
    fallback = max(claims, key=lambda claim: (claim.confidence, claim.claim_id))
    return (fallback.claim_id,)


__all__ = [
    "BeliefAuditEntry",
    "BeliefAuditReport",
    "BeliefAuditSummary",
    "build_belief_audit",
    "render_belief_audit_tsv",
]
