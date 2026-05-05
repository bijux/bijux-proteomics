# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from bijux_proteomics.domain.criteria import MeasurementDirection, SuccessCriterion
from bijux_proteomics.domain.program_spec import create_program_spec
from bijux_proteomics_intelligence.candidates.ranking import CandidateAssessment
from bijux_proteomics_intelligence.judgment.paths import (
    build_follow_up_candidate_path,
    build_review_board_decision_path,
)
from bijux_proteomics_knowledge.memory.evidence import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
)
from bijux_proteomics_knowledge.references.benchmarks import KnowledgeWorkflowFamily


def _program() -> object:
    program = create_program_spec(
        program_id="prog-calibration",
        name="decision calibration",
        objective="reject weak novelty and hold on contradictions",
        target_id="target-calibration",
        target_name="Target Calibration",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="preserve evidence-first review discipline",
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


def _grounded_bundle() -> EvidenceBundle:
    now = datetime.now(UTC)
    return EvidenceBundle(
        bundle_id="bundle-grounded-calibration",
        target_id="target-calibration",
        records=[
            EvidenceRecord(
                evidence_id="evidence-assay",
                kind=EvidenceKind.ASSAY,
                title="Orthogonal assay support",
                source="lab-assay-1",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="supports progression with reproducible assay signal",
                confidence=0.93,
                strength=EvidenceStrength.DECISIVE,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=8),
            ),
            EvidenceRecord(
                evidence_id="evidence-literature",
                kind=EvidenceKind.LITERATURE,
                title="Recent literature support",
                source="PMID:calibration",
                source_type=EvidenceSourceType.LITERATURE,
                claim="supports disease-relevant target engagement",
                confidence=0.84,
                strength=EvidenceStrength.SUPPORTING,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=20),
            ),
            EvidenceRecord(
                evidence_id="evidence-structure",
                kind=EvidenceKind.STRUCTURE,
                title="Structure support",
                source="model",
                source_type=EvidenceSourceType.STRUCTURE_MODEL,
                claim="supports a stable folded state for follow-up planning",
                confidence=0.82,
                strength=EvidenceStrength.SUPPORTING,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=14),
            ),
        ],
    )


def _contradictory_bundle() -> EvidenceBundle:
    now = datetime.now(UTC)
    return EvidenceBundle(
        bundle_id="bundle-contradictory-calibration",
        target_id="target-calibration",
        records=[
            EvidenceRecord(
                evidence_id="evidence-assay-supports",
                kind=EvidenceKind.ASSAY,
                title="Supportive assay",
                source="lab-assay-a",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="supports progression with stable assay response",
                confidence=0.89,
                strength=EvidenceStrength.DECISIVE,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=12),
            ),
            EvidenceRecord(
                evidence_id="evidence-assay-fails",
                kind=EvidenceKind.ASSAY,
                title="Contradictory assay",
                source="lab-assay-b",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="fails progression because the assay response worsens",
                confidence=0.85,
                strength=EvidenceStrength.DECISIVE,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=11),
            ),
            EvidenceRecord(
                evidence_id="evidence-literature",
                kind=EvidenceKind.LITERATURE,
                title="Recent literature support",
                source="PMID:calibration",
                source_type=EvidenceSourceType.LITERATURE,
                claim="supports disease-relevant target engagement",
                confidence=0.84,
                strength=EvidenceStrength.SUPPORTING,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=20),
            ),
            EvidenceRecord(
                evidence_id="evidence-structure",
                kind=EvidenceKind.STRUCTURE,
                title="Structure support",
                source="model",
                source_type=EvidenceSourceType.STRUCTURE_MODEL,
                claim="supports a stable folded state for follow-up planning",
                confidence=0.82,
                strength=EvidenceStrength.SUPPORTING,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=14),
            ),
        ],
    )


def test_follow_up_path_rejects_novelty_without_evidence_strength() -> None:
    path = build_follow_up_candidate_path(
        _program(),
        [
            CandidateAssessment(
                candidate_id="candidate-novel",
                sequence="ACDEFGHIKLMNPQRSTVWYA",
                metric_scores={"binding_score": 0.79},
                manufacturability_score=0.66,
                uncertainty=0.35,
                evidence_support=0.32,
                reproducibility_score=0.28,
                effect_size_score=0.35,
                assay_feasibility_score=0.61,
                novelty_score=0.98,
                lab_cost_risk=0.34,
                operational_risk=0.37,
            ),
            CandidateAssessment(
                candidate_id="candidate-grounded",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.88},
                manufacturability_score=0.85,
                uncertainty=0.06,
                evidence_support=0.9,
                reproducibility_score=0.92,
                effect_size_score=0.83,
                assay_feasibility_score=0.88,
                novelty_score=0.48,
                lab_cost_risk=0.11,
                operational_risk=0.09,
            ),
        ],
        _grounded_bundle(),
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )

    assert path.ranking.ranked_candidates[0].candidate_id == "candidate-grounded"
    assert path.recommendations[0].candidate_id == "candidate-grounded"
    assert path.recommendations[0].recommendation.startswith(
        "prioritize candidate-grounded"
    )


def test_review_board_path_holds_when_polished_candidates_face_contradictions() -> None:
    path = build_review_board_decision_path(
        _program(),
        [
            CandidateAssessment(
                candidate_id="candidate-polished",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.91},
                manufacturability_score=0.88,
                uncertainty=0.04,
                evidence_support=0.93,
                reproducibility_score=0.91,
                effect_size_score=0.86,
                assay_feasibility_score=0.89,
                novelty_score=0.52,
                lab_cost_risk=0.08,
                operational_risk=0.07,
            )
        ],
        _contradictory_bundle(),
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )

    assert path.packet.recommendation.action.value == "hold"
    assert any(
        "contradiction" in reason.lower() or "contradictory" in reason.lower()
        for reason in path.packet.recommendation.reasons
    )
    assert any(
        "contradiction" in question.lower() or "evidence" in question.lower()
        for question in path.unresolved_questions
    )
