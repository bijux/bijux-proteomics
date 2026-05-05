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
from bijux_proteomics_knowledge.reviews.explanations import (
    CandidateDecisionDisposition,
    CandidateDecisionGraphExplanation,
    CandidateDecisionGraphQuery,
    explain_candidate_decision_with_graph,
)


def test_explain_candidate_decision_with_graph_surfaces_support_and_blockers() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-graph-explain",
        target_id="target-graph-explain",
        records=[
            EvidenceRecord(
                evidence_id="ev-support",
                kind=EvidenceKind.ASSAY,
                title="supportive assay",
                source="lab",
                claim="candidate supports progression",
                decision_tags=["progression"],
                confidence=0.84,
                strength=EvidenceStrength.DECISIVE,
                endpoint="activity_ratio",
            ),
            EvidenceRecord(
                evidence_id="ev-contradict",
                kind=EvidenceKind.STRUCTURE,
                title="structure caution",
                source="model",
                claim="candidate may miss progression",
                decision_tags=["progression"],
                confidence=0.66,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )
    claims = [
        build_claim(
            claim_id="claim-support",
            target_id="target-graph-explain",
            statement="candidate can progress",
            evidence_ids=["ev-support"],
            contradicting_evidence_ids=["ev-contradict"],
            status=ClaimStatus.SUPPORTED,
            resolution_assays=["orthogonal assay"],
        )
    ]

    explanation = explain_candidate_decision_with_graph(
        bundle,
        claims,
        query=CandidateDecisionGraphQuery(
            candidate_id="candidate-accepted",
            decision_tag="progression",
            disposition=CandidateDecisionDisposition.ACCEPTED,
        ),
        required_modalities=[EvidenceKind.ASSAY.value, EvidenceKind.STRUCTURE.value],
    )

    assert isinstance(explanation, CandidateDecisionGraphExplanation)
    assert explanation.candidate_id == "candidate-accepted"
    assert explanation.supporting_evidence_ids == ["ev-support"]
    assert explanation.contradicting_evidence_ids == ["ev-contradict"]
    assert explanation.unresolved_question_ids == [
        "progression:open-claims-require-resolution"
    ]
    assert explanation.decision_subgraph.target_id == "target-graph-explain"
    assert explanation.decision_paths
    assert any(
        "candidate-accepted is accepted" in line
        for line in explanation.explanation_lines
    )
