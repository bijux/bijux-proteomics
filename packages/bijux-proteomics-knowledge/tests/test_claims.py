# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge import (
    ClaimPolarity,
    ClaimStatus,
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
    build_claim,
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
