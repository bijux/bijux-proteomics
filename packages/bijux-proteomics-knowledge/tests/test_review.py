# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge import (
    ClaimStatus,
    DecisionGateProfile,
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStrength,
    KnowledgeReviewPacket,
    build_claim,
    build_knowledge_review_packet,
    compare_review_packets,
    summarize_multi_decision_readiness,
    summarize_review_trend,
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


def test_compare_review_packets_reports_delta() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-delta",
        target_id="target-delta",
        records=[
            EvidenceRecord(
                evidence_id="d1",
                kind=EvidenceKind.ASSAY,
                title="assay",
                source="lab",
                claim="progression support",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
                endpoint="activity_ratio",
            )
        ],
    )
    claims = [
        build_claim(
            claim_id="claim-delta-1",
            target_id="target-delta",
            statement="candidate can progress",
            evidence_ids=["d1"],
            status=ClaimStatus.SUPPORTED,
            resolution_assays=["assay"],
        )
    ]
    previous = build_knowledge_review_packet(bundle, claims, decision_tag="progression")
    improved_bundle = bundle.model_copy(
        update={
            "records": [
                bundle.records[0].model_copy(
                    update={"confidence": 0.9, "strength": EvidenceStrength.DECISIVE}
                )
            ]
        }
    )
    current = build_knowledge_review_packet(
        improved_bundle, claims, decision_tag="progression"
    )
    delta = compare_review_packets(previous, current)

    assert delta.decision_tag == "progression"
    assert isinstance(delta.intelligence_index_delta, float)


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


def test_summarize_review_trend_accumulates_delta_direction() -> None:
    delta_a = compare_review_packets(
        KnowledgeReviewPacket.model_validate(
            {
                "target_id": "t",
                "decision_tag": "progression",
                "evidence_ranking": [],
                "quality_audit": {
                    "bundle_id": "b",
                    "target_id": "t",
                    "decision_tag": "progression",
                    "trust_score": 0.5,
                    "triangulation_score": 0.5,
                    "low_context_records": [],
                    "weak_quantitative_records": [],
                    "conflict_count": 0,
                    "recommendations": [],
                },
                "hypothesis_dossier": {
                    "target_id": "t",
                    "decision_tag": "progression",
                    "supporting_claim_ids": [],
                    "contradicting_claim_ids": [],
                    "unresolved_claim_ids": [],
                    "required_resolution_assays": [],
                    "support_confidence_mean": 0.0,
                },
                "knowledge_gaps": [],
                "conflict_clusters": [],
                "gate_recommendation": "advance",
                "executive_summary": [],
                "blocker_highlights": [],
                "decision_intelligence_index": 0.4,
            }
        ),
        KnowledgeReviewPacket.model_validate(
            {
                "target_id": "t",
                "decision_tag": "progression",
                "evidence_ranking": [],
                "quality_audit": {
                    "bundle_id": "b",
                    "target_id": "t",
                    "decision_tag": "progression",
                    "trust_score": 0.6,
                    "triangulation_score": 0.6,
                    "low_context_records": [],
                    "weak_quantitative_records": [],
                    "conflict_count": 0,
                    "recommendations": [],
                },
                "hypothesis_dossier": {
                    "target_id": "t",
                    "decision_tag": "progression",
                    "supporting_claim_ids": [],
                    "contradicting_claim_ids": [],
                    "unresolved_claim_ids": [],
                    "required_resolution_assays": [],
                    "support_confidence_mean": 0.0,
                },
                "knowledge_gaps": [],
                "conflict_clusters": [],
                "gate_recommendation": "advance",
                "executive_summary": [],
                "blocker_highlights": [],
                "decision_intelligence_index": 0.6,
            }
        ),
    )
    trend = summarize_review_trend([delta_a])

    assert trend.improving_steps == 1
