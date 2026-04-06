# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge import (
    ClaimPolarity,
    ClaimResolutionState,
    ClaimStatus,
    ClaimType,
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
    build_claim,
    close_claim,
    link_evidence_to_claim,
    build_decision_lineage,
)


def test_build_decision_lineage_links_supported_claims_to_evidence() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-1",
        target_id="target-1",
        records=[
            EvidenceRecord(
                evidence_id="lit-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:1",
                source_type=EvidenceSourceType.LITERATURE,
                claim="Target is disease-relevant.",
                decision_tags=["progression"],
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )
    claim = build_claim(
        claim_id="claim-1",
        target_id="target-1",
        statement="Target relevance is supported.",
        evidence_ids=["lit-1"],
        status=ClaimStatus.SUPPORTED,
    )
    contradicting_claim = build_claim(
        claim_id="claim-2",
        target_id="target-1",
        statement="Target relevance is contradicted.",
        evidence_ids=["lit-1"],
        status=ClaimStatus.DISPUTED,
        polarity=ClaimPolarity.CONTRADICTING,
    )

    lineage = build_decision_lineage(bundle, [claim, contradicting_claim], "progression")

    assert lineage.claim_ids == ["claim-1"]
    assert lineage.disputed_claim_ids == ["claim-2"]
    assert lineage.evidence_ids == ["lit-1"]


def test_close_claim_marks_resolution_state_closed() -> None:
    claim = build_claim(
        claim_id="claim-3",
        target_id="target-1",
        statement="Needs resolution",
        evidence_ids=["lit-1"],
        status=ClaimStatus.INSUFFICIENT,
    )

    closed = close_claim(claim)

    assert closed.resolution_state is ClaimResolutionState.CLOSED


def test_link_evidence_to_claim_attaches_bundle_evidence_ids() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-2",
        target_id="target-1",
        records=[
            EvidenceRecord(
                evidence_id="ev-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:1",
                source_type=EvidenceSourceType.LITERATURE,
                claim="Target is disease-relevant.",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )
    claim = build_claim(
        claim_id="claim-4",
        target_id="target-1",
        statement="Linked claim",
        evidence_ids=[],
        status=ClaimStatus.SUPPORTED,
    )

    linked = link_evidence_to_claim(claim, bundle)

    assert linked.evidence_ids == ["ev-1"]


def test_build_claim_supports_structured_decision_metadata() -> None:
    claim = build_claim(
        claim_id="claim-5",
        target_id="target-1",
        statement="Candidate is likely developable at scale.",
        evidence_ids=["ev-1"],
        status=ClaimStatus.SUPPORTED,
        claim_type=ClaimType.DEVELOPABILITY,
        confidence=0.82,
        contradiction_group="scale-readiness",
        decision_impact="blocking_gate_input",
    )

    assert claim.claim_type is ClaimType.DEVELOPABILITY
    assert claim.confidence == 0.82
    assert claim.contradiction_group == "scale-readiness"


def test_build_claim_supports_mechanistic_structure_fields() -> None:
    claim = build_claim(
        claim_id="claim-6",
        target_id="target-1",
        statement="Treatment increases phospho-signal in cells.",
        evidence_ids=["ev-2"],
        status=ClaimStatus.SUPPORTED,
        subject="target-1",
        relation="increases",
        object="phospho-signal",
        condition="cellular assay under treatment",
        direction="up",
        magnitude=1.6,
    )

    assert claim.subject == "target-1"
    assert claim.relation == "increases"
    assert claim.object == "phospho-signal"
    assert claim.direction == "up"
