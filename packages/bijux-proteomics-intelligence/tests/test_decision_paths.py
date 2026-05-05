# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from bijux_proteomics import SuccessCriterion, create_program_spec
from bijux_proteomics.programs import MeasurementDirection
from bijux_proteomics_intelligence import (
    CandidateAssessment,
    FollowUpCandidatePath,
    build_follow_up_candidate_path,
)
from bijux_proteomics_knowledge import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
)
from bijux_proteomics_knowledge.references import KnowledgeWorkflowFamily


def _program() -> object:
    program = create_program_spec(
        program_id="prog-follow-up",
        name="follow-up path",
        objective="turn evidence into readable candidate follow-up decisions",
        target_id="target-follow-up",
        target_name="Target Follow Up",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="preserve disease-relevant target engagement",
    )
    program.success_criteria.append(
        SuccessCriterion(
            criterion_id="binding",
            metric="binding_score",
            direction=MeasurementDirection.MAXIMIZE,
            threshold=0.75,
        )
    )
    return program


def _bundle() -> EvidenceBundle:
    now = datetime.now(UTC)
    return EvidenceBundle(
        bundle_id="bundle-follow-up",
        target_id="target-follow-up",
        records=[
            EvidenceRecord(
                evidence_id="evidence-assay",
                kind=EvidenceKind.ASSAY,
                title="Orthogonal assay support",
                source="lab-assay-1",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="supports progression with reproducible assay signal",
                confidence=0.92,
                strength=EvidenceStrength.DECISIVE,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=10),
            ),
            EvidenceRecord(
                evidence_id="evidence-literature",
                kind=EvidenceKind.LITERATURE,
                title="Recent literature support",
                source="PMID:follow-up",
                source_type=EvidenceSourceType.LITERATURE,
                claim="supports disease-relevant target engagement",
                confidence=0.81,
                strength=EvidenceStrength.SUPPORTING,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=30),
            ),
            EvidenceRecord(
                evidence_id="evidence-structure",
                kind=EvidenceKind.STRUCTURE,
                title="Structure support",
                source="model",
                source_type=EvidenceSourceType.STRUCTURE_MODEL,
                claim="supports a stable folded state for follow-up planning",
                confidence=0.84,
                strength=EvidenceStrength.SUPPORTING,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=18),
            ),
        ],
    )


def test_follow_up_candidate_path_builds_readable_ranked_recommendations() -> None:
    path = build_follow_up_candidate_path(
        _program(),
        [
            CandidateAssessment(
                candidate_id="candidate-a",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.88},
                manufacturability_score=0.86,
                uncertainty=0.08,
                evidence_support=0.89,
                reproducibility_score=0.91,
                effect_size_score=0.8,
                assay_feasibility_score=0.87,
                novelty_score=0.58,
                lab_cost_risk=0.14,
                operational_risk=0.11,
            ),
            CandidateAssessment(
                candidate_id="candidate-b",
                sequence="ACDEFGHIKLMNPQRSTVWYA",
                metric_scores={"binding_score": 0.82},
                manufacturability_score=0.72,
                uncertainty=0.16,
                evidence_support=0.74,
                reproducibility_score=0.67,
                effect_size_score=0.69,
                assay_feasibility_score=0.64,
                novelty_score=0.71,
                lab_cost_risk=0.24,
                operational_risk=0.27,
            ),
        ],
        _bundle(),
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )

    assert isinstance(path, FollowUpCandidatePath)
    assert path.decision_ready is True
    assert path.ranking.ranked_candidates[0].candidate_id == "candidate-a"
    top = path.recommendations[0]
    assert top.recommendation.startswith("prioritize candidate-a")
    assert top.explanation
    assert "scientific_value" in " ".join(top.explanation)
