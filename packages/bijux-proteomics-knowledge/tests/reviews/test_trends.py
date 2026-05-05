# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.memory.claims import ClaimStatus, build_claim
from bijux_proteomics_knowledge.memory.evidence import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStrength,
)
from bijux_proteomics_knowledge.reviews.packets import (
    KnowledgeReviewPacket,
    build_knowledge_review_packet,
)
from bijux_proteomics_knowledge.reviews.trends import (
    compare_review_packets,
    summarize_review_trend,
)


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
