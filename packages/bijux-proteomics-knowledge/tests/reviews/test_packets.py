# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.memory.models.claims import ClaimStatus, build_claim
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStrength,
)
from bijux_proteomics_knowledge.reviews.packets import (
    DecisionGateProfile,
    OperationalDecisionLabel,
    ScientificConclusion,
    build_knowledge_review_packet,
    summarize_multi_decision_readiness,
)

def test_build_knowledge_review_packet_returns_integrated_sections(
    supported_progression_bundle: EvidenceBundle,
    supported_progression_claims: list[object],
) -> None:
    packet = build_knowledge_review_packet(
        supported_progression_bundle,
        supported_progression_claims,
        decision_tag="progression",
        required_modalities=[EvidenceKind.ASSAY.value, EvidenceKind.STRUCTURE.value],
    )

    assert packet.target_id == "target-review"
    assert packet.decision_tag == "progression"
    assert len(packet.evidence_ranking) == 1
    assert packet.hypothesis_dossier.supporting_claim_ids == ["claim-review-1"]
    assert any(
        gap.gap_code == "open-claims-require-resolution"
        for gap in packet.knowledge_gaps
    )
    assert packet.gate_recommendation in {
        "hold-for-conflict-resolution",
        "advance-with-targeted-gap-closure",
        "advance-with-evidence-hardening",
        "advance",
    }
    assert any("gate recommendation" in line for line in packet.executive_summary)
    assert isinstance(packet.blocker_highlights, list)
    assert isinstance(packet.scientific_conclusions[0], ScientificConclusion)
    assert packet.scientific_conclusions[0].statement == "Candidate can progress."
    assert isinstance(packet.operational_labels[0], OperationalDecisionLabel)
    assert packet.operational_labels[0].label == packet.gate_recommendation
    assert 0.0 <= packet.decision_intelligence_index <= 1.0


def test_summarize_multi_decision_readiness_reports_portfolio_score() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-multi",
        target_id="target-multi",
        records=[
            EvidenceRecord(
                evidence_id="m1",
                kind=EvidenceKind.ASSAY,
                title="assay",
                source="lab",
                claim="progression support",
                decision_tags=["progression", "synthesis"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
                endpoint="activity_ratio",
            )
        ],
    )
    claims = [
        build_claim(
            claim_id="claim-multi-1",
            target_id="target-multi",
            statement="candidate is viable",
            evidence_ids=["m1"],
            status=ClaimStatus.SUPPORTED,
            resolution_assays=["orthogonal assay"],
        )
    ]

    summary = summarize_multi_decision_readiness(
        bundle,
        claims,
        decision_tags=["progression", "synthesis"],
    )

    assert set(summary.decision_scores) == {"progression", "synthesis"}
    assert 0.0 <= summary.portfolio_score <= 1.0


def test_build_knowledge_review_packet_supports_gate_profiles() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-gate-profile",
        target_id="target-gate-profile",
        records=[
            EvidenceRecord(
                evidence_id="gp-1",
                kind=EvidenceKind.LITERATURE,
                title="lit",
                source="pmid",
                claim="support",
                decision_tags=["progression"],
                confidence=0.72,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )
    claims = [
        build_claim(
            claim_id="claim-gp-1",
            target_id="target-gate-profile",
            statement="claim",
            evidence_ids=["gp-1"],
            status=ClaimStatus.SUPPORTED,
            resolution_assays=["assay"],
        )
    ]
    packet = build_knowledge_review_packet(
        bundle,
        claims,
        decision_tag="progression",
        gate_profile=DecisionGateProfile(
            profile_id="strict-profile",
            minimum_trust_score=0.9,
            minimum_triangulation_score=0.9,
        ),
    )

    assert (
        packet.gate_recommendation == "advance-with-targeted-gap-closure"
        or packet.gate_recommendation == "advance-with-evidence-hardening"
    )
