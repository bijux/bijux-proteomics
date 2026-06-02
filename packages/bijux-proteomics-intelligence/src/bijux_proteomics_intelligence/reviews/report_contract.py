# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Typed intelligence contract for report-facing analytical claim review."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.belief_audit import (
    BeliefAuditEntry,
    BeliefAuditReport,
    build_belief_audit,
)
from bijux_proteomics_intelligence.claims.support import (
    ClaimSupportValidationEntry,
    ClaimSupportValidationReport,
    ClaimSupportStatus,
    validate_claim_support,
)
from bijux_proteomics_intelligence.contradictions import (
    ClaimContradictionEntry,
    ClaimContradictionReport,
    find_claim_contradictions,
)
from bijux_proteomics_intelligence.falsifiers import ClaimFalsifierEntry, generate_falsifiers
from bijux_proteomics_intelligence.refusal import (
    ClaimRefusalEntry,
    ClaimRefusalReport,
    ClaimRefusalThresholds,
    refuse_unsupported_claims,
)
from bijux_proteomics_knowledge.memory.integrity.graph import EvidenceGraph
from bijux_proteomics_knowledge.memory.models.claims import ClaimStatus, EvidenceClaim


class IntelligenceReportClaimEntry(JsonModel):
    """One claim-level report contract entry with typed intelligence decisions."""

    model_config = ConfigDict(extra="forbid")

    claim: EvidenceClaim
    support_validation: ClaimSupportValidationEntry
    refusal: ClaimRefusalEntry
    falsifier: ClaimFalsifierEntry
    contradictions: tuple[ClaimContradictionEntry, ...] = Field(default_factory=tuple)
    belief_audit: BeliefAuditEntry | None = None


class IntelligenceReportContractSummary(JsonModel):
    """Stable summary over the report-facing intelligence contract."""

    model_config = ConfigDict(extra="forbid")

    claim_count: int = Field(..., ge=0)
    supported_claim_count: int = Field(..., ge=0)
    unresolved_claim_count: int = Field(..., ge=0)
    refused_claim_count: int = Field(..., ge=0)
    top_claim_count: int = Field(..., ge=0)
    belief_audited_claim_count: int = Field(..., ge=0)
    contradiction_pair_count: int = Field(..., ge=0)


class IntelligenceReportContract(JsonModel):
    """Owned intelligence object that a narrative/report layer must consume."""

    model_config = ConfigDict(extra="forbid")

    claim_entries: tuple[IntelligenceReportClaimEntry, ...] = Field(default_factory=tuple)
    support_validation_report: ClaimSupportValidationReport
    contradiction_report: ClaimContradictionReport
    refusal_report: ClaimRefusalReport
    belief_audit_report: BeliefAuditReport
    summary: IntelligenceReportContractSummary
    note: str = Field(..., min_length=1)


def build_intelligence_report_contract(
    claims: tuple[EvidenceClaim, ...] | list[EvidenceClaim],
    evidence_graph: EvidenceGraph,
    *,
    refusal_thresholds: ClaimRefusalThresholds | None = None,
) -> IntelligenceReportContract:
    """Assemble the typed intelligence bundle consumed by final reports."""

    claim_items = tuple(claims)
    support_validation_report = validate_claim_support(claim_items, evidence_graph)
    contradiction_report = find_claim_contradictions(claim_items)
    refusal_report = refuse_unsupported_claims(
        claim_items,
        thresholds=refusal_thresholds,
    )
    belief_audit_report = build_belief_audit(claim_items, evidence_graph)

    support_by_claim_id = {
        entry.claim_id: entry for entry in support_validation_report.entries
    }
    refusal_by_claim_id = {entry.claim_id: entry for entry in refusal_report.entries}
    belief_audit_by_claim_id = {
        entry.claim_id: entry for entry in belief_audit_report.entries
    }
    contradictions_by_claim_id = _contradictions_by_claim_id(contradiction_report.entries)

    claim_entries = tuple(
        IntelligenceReportClaimEntry(
            claim=claim,
            support_validation=support_by_claim_id[claim.claim_id],
            refusal=refusal_by_claim_id[claim.claim_id],
            falsifier=generate_falsifiers(claim).entries[0],
            contradictions=contradictions_by_claim_id.get(claim.claim_id, ()),
            belief_audit=belief_audit_by_claim_id.get(claim.claim_id),
        )
        for claim in claim_items
    )

    contract = IntelligenceReportContract(
        claim_entries=claim_entries,
        support_validation_report=support_validation_report,
        contradiction_report=contradiction_report,
        refusal_report=refusal_report,
        belief_audit_report=belief_audit_report,
        summary=IntelligenceReportContractSummary(
            claim_count=len(claim_entries),
            supported_claim_count=sum(
                entry.claim.status is ClaimStatus.SUPPORTED for entry in claim_entries
            ),
            unresolved_claim_count=sum(
                entry.claim.status is not ClaimStatus.SUPPORTED for entry in claim_entries
            ),
            refused_claim_count=sum(entry.refusal.refused for entry in claim_entries),
            top_claim_count=belief_audit_report.summary.top_claim_count,
            belief_audited_claim_count=sum(
                entry.belief_audit is not None for entry in claim_entries
            ),
            contradiction_pair_count=contradiction_report.summary.pair_count,
        ),
        note=(
            "report-facing intelligence contract keeps claims, support validation, "
            "refusals, falsifiers, contradictions, and belief audits aligned by "
            "claim id so narrative layers cannot synthesize unsupported results"
        ),
    )
    validate_intelligence_report_contract(contract)
    return contract


def validate_intelligence_report_contract(contract: IntelligenceReportContract) -> None:
    """Reject report contracts that have drifted away from typed intelligence state."""

    claim_entries_by_id = {entry.claim.claim_id: entry for entry in contract.claim_entries}
    if len(claim_entries_by_id) != len(contract.claim_entries):
        raise ValueError("intelligence report contract requires unique claim ids")

    support_ids = {
        entry.claim_id for entry in contract.support_validation_report.entries
    }
    refusal_ids = {entry.claim_id for entry in contract.refusal_report.entries}
    belief_ids = {entry.claim_id for entry in contract.belief_audit_report.entries}

    for claim_id, claim_entry in claim_entries_by_id.items():
        if claim_entry.support_validation.claim_id != claim_id:
            raise ValueError(
                f"intelligence report contract support mismatch for claim {claim_id}"
            )
        if claim_entry.refusal.claim_id != claim_id:
            raise ValueError(
                f"intelligence report contract refusal mismatch for claim {claim_id}"
            )
        if claim_entry.falsifier.claim_id != claim_id:
            raise ValueError(
                f"intelligence report contract falsifier mismatch for claim {claim_id}"
            )
        if claim_id not in support_ids:
            raise ValueError(
                f"intelligence report contract is missing support validation for {claim_id}"
            )
        if claim_id not in refusal_ids:
            raise ValueError(
                f"intelligence report contract is missing refusal entry for {claim_id}"
            )
        if (
            claim_entry.belief_audit is not None
            and claim_entry.belief_audit.claim_id != claim_id
        ):
            raise ValueError(
                f"intelligence report contract belief-audit mismatch for claim {claim_id}"
            )
        if claim_entry.support_validation.support_status is ClaimSupportStatus.INVALID:
            continue

    for contradiction in contract.contradiction_report.entries:
        if contradiction.claim_a not in claim_entries_by_id:
            raise ValueError(
                f"intelligence report contract contradiction references unknown claim {contradiction.claim_a}"
            )
        if contradiction.claim_b not in claim_entries_by_id:
            raise ValueError(
                f"intelligence report contract contradiction references unknown claim {contradiction.claim_b}"
            )

    for claim_id in contract.belief_audit_report.summary.top_claim_ids:
        top_claim_entry = claim_entries_by_id.get(claim_id)
        if top_claim_entry is None:
            raise ValueError(
                f"intelligence report contract is missing top claim {claim_id}"
            )
        if top_claim_entry.belief_audit is None or claim_id not in belief_ids:
            raise ValueError(
                f"intelligence report contract is missing belief audit for top claim {claim_id}"
            )


def _contradictions_by_claim_id(
    entries: tuple[ClaimContradictionEntry, ...],
) -> dict[str, tuple[ClaimContradictionEntry, ...]]:
    by_claim_id: dict[str, list[ClaimContradictionEntry]] = {}
    for entry in entries:
        by_claim_id.setdefault(entry.claim_a, []).append(entry)
        by_claim_id.setdefault(entry.claim_b, []).append(entry)
    return {
        claim_id: tuple(
            sorted(
                claim_entries,
                key=lambda contradiction: (
                    contradiction.claim_a,
                    contradiction.claim_b,
                    contradiction.contradiction_type.value,
                ),
            )
        )
        for claim_id, claim_entries in by_claim_id.items()
    }


__all__ = [
    "IntelligenceReportClaimEntry",
    "IntelligenceReportContract",
    "IntelligenceReportContractSummary",
    "build_intelligence_report_contract",
    "validate_intelligence_report_contract",
]
