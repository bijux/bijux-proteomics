# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from bijux_proteomics.domain.criteria import MeasurementDirection, SuccessCriterion
from bijux_proteomics.domain.program_spec import create_program_spec
from bijux_proteomics_intelligence.candidates.ranking import CandidateAssessment
from bijux_proteomics_intelligence.judgment.paths import (
    build_review_board_decision_path,
)
from bijux_proteomics_intelligence.posture.skeptical import (
    ReviewChallengeSeverity,
    SkepticalReviewReport,
    build_skeptical_review_report,
)
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import KnowledgeWorkflowFamily


def _program() -> object:
    program = create_program_spec(
        program_id="prog-skeptical-review",
        name="skeptical review",
        objective="force recommendations to survive analytical challenge",
        target_id="target-skeptical-review",
        target_name="Target Skeptical Review",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="preserve evidence-first progression discipline",
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
        bundle_id="bundle-skeptical-grounded",
        target_id="target-skeptical-review",
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
                observed_at=now - timedelta(days=6),
            ),
            EvidenceRecord(
                evidence_id="evidence-literature",
                kind=EvidenceKind.LITERATURE,
                title="Recent literature support",
                source="PMID:skeptical",
                source_type=EvidenceSourceType.LITERATURE,
                claim="supports disease-relevant target engagement",
                confidence=0.84,
                strength=EvidenceStrength.SUPPORTING,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=18),
            ),
            EvidenceRecord(
                evidence_id="evidence-structure",
                kind=EvidenceKind.STRUCTURE,
                title="Structure support",
                source="model",
                source_type=EvidenceSourceType.STRUCTURE_MODEL,
                claim="supports a stable folded state for follow-up planning",
                confidence=0.83,
                strength=EvidenceStrength.SUPPORTING,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=11),
            ),
        ],
    )


def _contradictory_bundle() -> EvidenceBundle:
    now = datetime.now(UTC)
    return EvidenceBundle(
        bundle_id="bundle-skeptical-contradictory",
        target_id="target-skeptical-review",
        records=[
            EvidenceRecord(
                evidence_id="evidence-assay-support",
                kind=EvidenceKind.ASSAY,
                title="Supportive assay",
                source="lab-assay-1",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="supports progression with stable assay response",
                confidence=0.89,
                strength=EvidenceStrength.DECISIVE,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=10),
            ),
            EvidenceRecord(
                evidence_id="evidence-assay-contradiction",
                kind=EvidenceKind.ASSAY,
                title="Contradictory assay",
                source="lab-assay-2",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="fails progression because the assay response worsens",
                confidence=0.87,
                strength=EvidenceStrength.DECISIVE,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=9),
            ),
            EvidenceRecord(
                evidence_id="evidence-literature",
                kind=EvidenceKind.LITERATURE,
                title="Supporting literature",
                source="PMID:skeptical-contradiction",
                source_type=EvidenceSourceType.LITERATURE,
                claim="supports disease-relevant target engagement",
                confidence=0.82,
                strength=EvidenceStrength.SUPPORTING,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=21),
            ),
        ],
    )


def _aging_bundle() -> EvidenceBundle:
    now = datetime.now(UTC)
    return EvidenceBundle(
        bundle_id="bundle-skeptical-aging",
        target_id="target-skeptical-review",
        records=[
            EvidenceRecord(
                evidence_id="evidence-assay-aging",
                kind=EvidenceKind.ASSAY,
                title="Aging assay support",
                source="lab-assay-aging",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="supports progression with historical assay support",
                confidence=0.88,
                strength=EvidenceStrength.DECISIVE,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=170),
            ),
            EvidenceRecord(
                evidence_id="evidence-literature-aging",
                kind=EvidenceKind.LITERATURE,
                title="Aging literature support",
                source="PMID:skeptical-aging",
                source_type=EvidenceSourceType.LITERATURE,
                claim="supports disease-relevant target engagement",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=340),
            ),
        ],
    )


def test_skeptical_review_report_confirms_grounded_recommendation_value() -> None:
    path = build_review_board_decision_path(
        _program(),
        [
            CandidateAssessment(
                candidate_id="candidate-grounded",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.88},
                manufacturability_score=0.86,
                uncertainty=0.07,
                evidence_support=0.9,
                reproducibility_score=0.92,
                effect_size_score=0.81,
                assay_feasibility_score=0.89,
                novelty_score=0.53,
                lab_cost_risk=0.1,
                operational_risk=0.08,
            )
        ],
        _grounded_bundle(),
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )

    report = build_skeptical_review_report(path)

    assert isinstance(report, SkepticalReviewReport)
    assert report.release_ready is True
    assert not any(
        finding.severity is ReviewChallengeSeverity.BLOCK
        for finding in [*report.software_findings, *report.scientific_findings]
    )
    assert len(report.analytical_value_signals) >= 4
    assert report.recommended_action == "proceed with review-board recommendation"


def test_skeptical_review_report_blocks_contradictory_recommendation() -> None:
    path = build_review_board_decision_path(
        _program(),
        [
            CandidateAssessment(
                candidate_id="candidate-polished",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.9},
                manufacturability_score=0.87,
                uncertainty=0.04,
                evidence_support=0.91,
                reproducibility_score=0.89,
                effect_size_score=0.82,
                assay_feasibility_score=0.9,
                novelty_score=0.51,
                lab_cost_risk=0.09,
                operational_risk=0.08,
            )
        ],
        _contradictory_bundle(),
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )

    report = build_skeptical_review_report(path)

    assert report.release_ready is False
    assert any(
        finding.code == "unresolved_contradiction_pressure"
        and finding.severity is ReviewChallengeSeverity.BLOCK
        for finding in report.scientific_findings
    )
    assert report.recommended_action.startswith("hold recommendation")


def test_skeptical_review_report_blocks_degraded_support_and_operational_fragility() -> (
    None
):
    path = build_review_board_decision_path(
        _program(),
        [
            CandidateAssessment(
                candidate_id="candidate-fragile",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.91},
                manufacturability_score=0.73,
                uncertainty=0.18,
                evidence_support=0.63,
                reproducibility_score=0.58,
                effect_size_score=0.74,
                assay_feasibility_score=0.57,
                novelty_score=0.88,
                lab_cost_risk=0.52,
                operational_risk=0.61,
            )
        ],
        _aging_bundle(),
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )

    report = build_skeptical_review_report(path)

    assert report.release_ready is False
    assert any(
        finding.code == "degraded_recommendation_support"
        and finding.severity is ReviewChallengeSeverity.BLOCK
        for finding in report.software_findings
    )
    assert any(
        finding.code in {"novelty_outpaces_grounding", "fragile_follow_up_plan"}
        and finding.severity is ReviewChallengeSeverity.BLOCK
        for finding in report.scientific_findings
    )
    assert report.recommended_action.startswith("hold recommendation")
