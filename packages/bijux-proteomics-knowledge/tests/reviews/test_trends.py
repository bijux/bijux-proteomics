# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.memory.models.claims import EvidenceClaim
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    EvidenceStrength,
)
from bijux_proteomics_knowledge.reviews.decision_briefs import (
    KnowledgeDecisionBrief,
    build_knowledge_decision_brief,
)
from bijux_proteomics_knowledge.reviews.trends import (
    compare_decision_briefs,
    summarize_decision_brief_trend,
)


def test_compare_decision_briefs_reports_delta(
    supported_progression_bundle: EvidenceBundle,
    supported_progression_claims: list[EvidenceClaim],
) -> None:
    previous = build_knowledge_decision_brief(
        supported_progression_bundle,
        supported_progression_claims,
        decision_tag="progression",
    )
    improved_bundle = supported_progression_bundle.model_copy(
        update={
            "records": [
                supported_progression_bundle.records[0].model_copy(
                    update={"confidence": 0.9, "strength": EvidenceStrength.DECISIVE}
                )
            ]
        }
    )
    current = build_knowledge_decision_brief(
        improved_bundle, supported_progression_claims, decision_tag="progression"
    )
    delta = compare_decision_briefs(previous, current)

    assert delta.decision_tag == "progression"
    assert isinstance(delta.intelligence_index_delta, float)


def test_summarize_decision_brief_trend_accumulates_delta_direction() -> None:
    evidence_state_index = {
        "bundle_id": "b",
        "target_id": "t",
        "decision_tag": "progression",
        "record_assessments": [],
        "trusted_record_ids": [],
        "fresh_record_ids": [],
        "contradictory_record_ids": [],
        "insufficient_record_ids": [],
        "high_uncertainty_record_ids": [],
        "caveat_codes": [],
    }
    delta_a = compare_decision_briefs(
        KnowledgeDecisionBrief.model_validate(
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
                "evidence_state_index": evidence_state_index,
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
        KnowledgeDecisionBrief.model_validate(
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
                "evidence_state_index": evidence_state_index,
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
    trend = summarize_decision_brief_trend([delta_a])

    assert trend.improving_steps == 1
