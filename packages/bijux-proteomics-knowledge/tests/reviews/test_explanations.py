# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.memory.models.claims import EvidenceClaim
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    EvidenceKind,
)
from bijux_proteomics_knowledge.reviews.explanations import (
    CandidateDecisionDisposition,
    CandidateDecisionGraphExplanation,
    CandidateDecisionGraphQuery,
    explain_candidate_decision_with_graph,
)


def test_explain_candidate_decision_with_graph_surfaces_support_and_blockers(
    contradictory_progression_bundle: EvidenceBundle,
    contradictory_progression_claims: list[EvidenceClaim],
) -> None:
    explanation = explain_candidate_decision_with_graph(
        contradictory_progression_bundle,
        contradictory_progression_claims,
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
