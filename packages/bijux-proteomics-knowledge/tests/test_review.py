# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge import (
    ClaimStatus,
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStrength,
    build_claim,
    build_knowledge_review_packet,
)


def test_build_knowledge_review_packet_returns_integrated_sections() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-review",
        target_id="target-review",
        records=[
            EvidenceRecord(
                evidence_id="review-1",
                kind=EvidenceKind.ASSAY,
                title="assay support",
                source="lab",
                claim="Candidate meets progression gate.",
                decision_tags=["progression"],
                confidence=0.82,
                strength=EvidenceStrength.SUPPORTING,
                endpoint="activity_ratio",
            )
        ],
    )
    claims = [
        build_claim(
            claim_id="claim-review-1",
            target_id="target-review",
            statement="Candidate can progress.",
            evidence_ids=["review-1"],
            status=ClaimStatus.SUPPORTED,
            resolution_assays=["orthogonal assay"],
        )
    ]

    packet = build_knowledge_review_packet(
        bundle,
        claims,
        decision_tag="progression",
        required_modalities=[EvidenceKind.ASSAY.value, EvidenceKind.STRUCTURE.value],
    )

    assert packet.target_id == "target-review"
    assert packet.decision_tag == "progression"
    assert len(packet.evidence_ranking) == 1
    assert packet.hypothesis_dossier.supporting_claim_ids == ["claim-review-1"]
    assert any(gap.gap_code == "open-claims-require-resolution" for gap in packet.knowledge_gaps)
    assert packet.gate_recommendation in {
        "hold-for-conflict-resolution",
        "advance-with-targeted-gap-closure",
        "advance-with-evidence-hardening",
        "advance",
    }
    assert any("gate recommendation" in line for line in packet.executive_summary)
