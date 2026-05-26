# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Claim and evidence synthesis helpers for the shipped surprising demo."""

from __future__ import annotations

from datetime import UTC, datetime
import re

from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimDirection,
    BiologicalClaimStatus,
    BiologicalClaimValidationEntry,
)
from bijux_proteomics.workflow.reports.biological_reporting import BiologicalResultReportBundle
from bijux_proteomics_knowledge.memory.models.claims import (
    ClaimEvidenceState,
    ClaimPolarity,
    ClaimResolutionState,
    ClaimStatus,
    ClaimType,
    EvidenceClaim,
)
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    EvidenceExtractionMethod,
    EvidenceKind,
    EvidenceOrigin,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
    QuantitativeSupport,
)


def build_surprising_demo_claims(
    biological_report: BiologicalResultReportBundle,
) -> tuple[EvidenceClaim, ...]:
    """Build the shipped surprising demo claim set, including one contradiction case."""

    claim_validation_report = biological_report.claim_validation_report
    if claim_validation_report is None:
        raise ValueError("surprising demo biological report did not produce claim validation")

    base_claims = tuple(
        _build_demo_claim(entry)
        for entry in (
            claim_validation_report.supported_claims
            + claim_validation_report.rejected_claims
        )
    )
    contradictory_claim = _build_demo_contradictory_claim(base_claims)
    return (*base_claims, contradictory_claim)


def build_surprising_demo_evidence_bundle(
    claims: tuple[EvidenceClaim, ...],
) -> EvidenceBundle:
    """Build the shipped surprising demo evidence bundle from the synthesized claims."""

    records: list[EvidenceRecord] = []
    seen_record_ids: set[str] = set()
    for claim in claims:
        for evidence_id in claim.evidence_ids:
            if evidence_id in seen_record_ids:
                continue
            seen_record_ids.add(evidence_id)
            records.append(
                EvidenceRecord(
                    evidence_id=evidence_id,
                    kind=EvidenceKind.DIFFERENTIAL_PROTEOMICS,
                    title=evidence_id,
                    source="surprising_demo",
                    source_type=EvidenceSourceType.CURATED_NOTE,
                    origin=EvidenceOrigin.OBSERVED,
                    extraction_method=EvidenceExtractionMethod.AUTOMATED_IMPORT,
                    assay_modality="proteomics_demo",
                    biological_system="surprising_demo",
                    species="Homo sapiens",
                    quantitative_support=QuantitativeSupport(effect_size=claim.magnitude),
                    claim=claim.statement,
                    related_targets=[claim.target_id],
                    decision_tags=["demo_review"],
                    confidence=claim.confidence,
                    strength=(
                        EvidenceStrength.DECISIVE
                        if claim.confidence >= 0.8
                        else EvidenceStrength.SUPPORTING
                    ),
                    observed_at=datetime.now(UTC),
                )
            )
    return EvidenceBundle(
        bundle_id="surprising_demo_bundle",
        target_id="surprising_demo_target",
        records=records,
    )


def _build_demo_claim(entry: BiologicalClaimValidationEntry) -> EvidenceClaim:
    direction = _demo_claim_direction(entry.asserted_direction)
    evidence_ids = tuple(
        _stable_demo_id(source_id) for source_id in entry.source_ids
    ) or (_stable_demo_id(f"{entry.claim_id}:source"),)
    return EvidenceClaim(
        claim_id=_stable_demo_id(entry.claim_id),
        target_id=_stable_demo_id(f"{entry.claim_kind.value}:{entry.subject_id}"),
        statement=entry.claim_text,
        subject=entry.subject_id,
        relation=entry.claim_kind.value,
        object=direction,
        condition=f"{entry.condition_a}_vs_{entry.condition_b}",
        direction=direction,
        magnitude=entry.effect_size,
        claim_type=(
            ClaimType.BIOMARKER
            if entry.claim_kind.value == "protein_abundance_change"
            else ClaimType.MECHANISTIC
        ),
        evidence_ids=list(evidence_ids),
        assumptions=_demo_claim_assumptions(entry),
        resolution_assays=["demo_follow_up_assay"],
        status=(
            ClaimStatus.SUPPORTED
            if entry.status is BiologicalClaimStatus.SUPPORTED
            else ClaimStatus.INSUFFICIENT
        ),
        polarity=ClaimPolarity.SUPPORTING,
        resolution_state=(
            ClaimResolutionState.CLOSED
            if entry.status is BiologicalClaimStatus.SUPPORTED
            else ClaimResolutionState.OPEN
        ),
        evidence_state=(
            ClaimEvidenceState.SUPPORTED
            if entry.status is BiologicalClaimStatus.SUPPORTED
            else ClaimEvidenceState.UNRESOLVED
        ),
        confidence=0.88 if entry.status is BiologicalClaimStatus.SUPPORTED else 0.52,
        decision_impact="demo_review",
    )


def _build_demo_contradictory_claim(
    claims: tuple[EvidenceClaim, ...],
) -> EvidenceClaim:
    anchor = next(
        (
            claim
            for claim in claims
            if claim.claim_id == "protein-claim:p11111" and claim.status is ClaimStatus.SUPPORTED
        ),
        None,
    )
    if anchor is None:
        raise ValueError("surprising demo requires the supported P11111 claim as a contradiction anchor")
    return EvidenceClaim(
        claim_id="protein-claim:p11111-contradiction",
        target_id=anchor.target_id,
        statement="Protein PTM1 decreased in treated vs control despite the primary abundance signal.",
        subject=anchor.subject,
        relation=anchor.relation,
        object="down",
        condition=anchor.condition,
        direction="down",
        magnitude=anchor.magnitude,
        claim_type=anchor.claim_type,
        evidence_ids=["demo-contradiction-evidence:p11111-down"],
        contradicting_evidence_ids=list(anchor.evidence_ids),
        assumptions=[
            "design_valid=true",
            "qc_status=passed",
            "peptide_support_count=1",
            "contradiction_probe=true",
        ],
        resolution_assays=["orthogonal_protein_rerun"],
        status=ClaimStatus.DISPUTED,
        polarity=ClaimPolarity.SUPPORTING,
        resolution_state=ClaimResolutionState.OPEN,
        evidence_state=ClaimEvidenceState.CONFLICTED,
        confidence=0.41,
        contradiction_group="p11111-direction",
        decision_impact="contradictory_context",
    )


def _demo_claim_assumptions(
    entry: BiologicalClaimValidationEntry,
) -> list[str]:
    assumptions = [
        "design_valid=true",
        "qc_status=passed",
    ]
    if entry.status is BiologicalClaimStatus.SUPPORTED:
        assumptions.append("peptide_support_count=3")
    else:
        assumptions.append("peptide_support_count=1")
        assumptions.extend(reason.value for reason in entry.reason_codes)
    return assumptions


def _demo_claim_direction(direction: BiologicalClaimDirection) -> str:
    return {
        BiologicalClaimDirection.UP: "up",
        BiologicalClaimDirection.DOWN: "down",
        BiologicalClaimDirection.MIXED: "mixed",
        BiologicalClaimDirection.UNRESOLVED: "unchanged",
    }[direction]


def _stable_demo_id(value: str) -> str:
    normalized = value.lower().replace("/", ":")
    normalized = re.sub(r"[^a-z0-9._:-]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized


__all__ = [
    "build_surprising_demo_claims",
    "build_surprising_demo_evidence_bundle",
]
