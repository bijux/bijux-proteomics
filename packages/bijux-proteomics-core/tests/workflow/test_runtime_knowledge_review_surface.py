# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.runtime.control.workflow_runs import (
    KnowledgeEvidenceInput,
    run_knowledge_review_workflow_end_to_end,
)


def test_run_knowledge_review_workflow_end_to_end_tracks_ranking_and_contradictions() -> (
    None
):
    evidence = (
        KnowledgeEvidenceInput(
            evidence_id="E1",
            claim="PTM site S5 is condition-enriched",
            source="paper-a",
            trust_score=0.91,
            contradicts=("E2",),
        ),
        KnowledgeEvidenceInput(
            evidence_id="E2",
            claim="PTM site S5 is unchanged",
            source="paper-b",
            trust_score=0.63,
            contradicts=("E1",),
        ),
        KnowledgeEvidenceInput(
            evidence_id="E3",
            claim="Protein P11111 is observed in treatment group",
            source="study-c",
            trust_score=0.82,
        ),
    )

    report = run_knowledge_review_workflow_end_to_end(evidence)

    assert report.status.value == "completed"
    assert report.evidence_node_count == 3
    assert report.ranked_evidence_count == 3
    assert report.contradiction_count == 1
    assert report.contested_claim_count == 2
    assert report.accepted_claim_count == 1
    assert report.steps[2].step_id == "resolve-contradictions"
