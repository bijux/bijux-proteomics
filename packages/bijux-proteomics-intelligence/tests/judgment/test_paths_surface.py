# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from bijux_proteomics.domain.criteria import MeasurementDirection, SuccessCriterion
from bijux_proteomics.domain.program_spec import create_program_spec
from bijux_proteomics.study.qc import (
    InstrumentBatchQcReport,
    InstrumentBatchQcRunEntry,
)
from bijux_proteomics.quantification import (
    QuantEntityLevel,
    ReplicateCorrelationEntry,
    ReplicateCorrelationReport,
)
from bijux_proteomics_foundation import DocumentSchema
from bijux_proteomics_intelligence.candidates.ranking import CandidateAssessment
from bijux_proteomics_intelligence.judgment.paths import (
    CautiousAnomalyInterpretationPath,
    FollowUpCandidatePath,
    ReviewBoardDecisionPath,
    build_cautious_anomaly_interpretation_path,
    build_follow_up_candidate_path,
    build_review_board_decision_path,
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


def _sparse_bundle() -> EvidenceBundle:
    now = datetime.now(UTC)
    return EvidenceBundle(
        bundle_id="bundle-follow-up-sparse",
        target_id="target-follow-up",
        records=[
            EvidenceRecord(
                evidence_id="evidence-literature-sparse",
                kind=EvidenceKind.LITERATURE,
                title="Literature-only support",
                source="PMID:follow-up-sparse",
                source_type=EvidenceSourceType.LITERATURE,
                claim="supports disease relevance but leaves assay readiness unresolved",
                confidence=0.73,
                strength=EvidenceStrength.SUPPORTING,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=45),
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


def test_follow_up_candidate_path_keeps_public_channels_separate() -> None:
    path = build_follow_up_candidate_path(
        _program(),
        [
            CandidateAssessment(
                candidate_id="candidate-sparse",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.79},
                manufacturability_score=0.62,
                uncertainty=0.24,
                evidence_support=0.41,
                reproducibility_score=0.38,
                effect_size_score=0.55,
                assay_feasibility_score=0.43,
                novelty_score=0.57,
                lab_cost_risk=0.36,
                operational_risk=0.34,
            ),
        ],
        _sparse_bundle(),
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )

    top = path.recommendations[0]

    assert top.recommendation.endswith("explicit blocker review")
    assert top.explanation
    assert top.unresolved_questions
    assert path.unresolved_questions
    assert set(top.explanation).isdisjoint(set(top.unresolved_questions))
    assert all(question not in top.recommendation for question in top.unresolved_questions)


def test_review_board_decision_path_builds_packet_from_evidence_and_candidates() -> (
    None
):
    path = build_review_board_decision_path(
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

    assert isinstance(path, ReviewBoardDecisionPath)
    assert path.packet.ranked_evidence
    assert path.packet.recommendation.reasons
    assert path.recommendation.endswith("review-board review")
    assert path.explanation


def test_review_board_decision_path_keeps_public_channels_separate() -> None:
    path = build_review_board_decision_path(
        _program(),
        [
            CandidateAssessment(
                candidate_id="candidate-sparse",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.79},
                manufacturability_score=0.62,
                uncertainty=0.24,
                evidence_support=0.41,
                reproducibility_score=0.38,
                effect_size_score=0.55,
                assay_feasibility_score=0.43,
                novelty_score=0.57,
                lab_cost_risk=0.36,
                operational_risk=0.34,
            ),
        ],
        _sparse_bundle(),
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )

    assert path.recommendation.endswith("review-board review")
    assert path.explanation
    assert path.unresolved_questions
    assert path.packet.recommendation.reasons
    assert set(path.explanation).isdisjoint(set(path.unresolved_questions))
    assert all(question not in path.recommendation for question in path.unresolved_questions)


def test_cautious_anomaly_interpretation_path_keeps_contract_fields_separate() -> None:
    batch_report = InstrumentBatchQcReport(
        document_schema=DocumentSchema(
            created_by="test",
            document_kind="instrument_batch_qc_report",
            package_name="test",
            status="generated",
        ),
        batch_id="batch-z",
        instrument="orbitrap-z",
        run_count=3,
        median_spectrum_count=9500.0,
        median_identification_rate=0.21,
        median_abs_mass_error_ppm=6.5,
        median_identified_retention_time_seconds=1800.0,
        outlier_run_ids=("run-t2",),
        runs=(
            InstrumentBatchQcRunEntry(
                run_id="run-c1",
                sample_id="C1",
                batch="batch-z",
                instrument="orbitrap-z",
                spectrum_count=10000,
                identification_rate=0.24,
                median_abs_mass_error_ppm=5.4,
                identified_retention_time_span_seconds=1820.0,
                retention_time_shift_seconds=0.0,
                outlier_reasons=(),
            ),
            InstrumentBatchQcRunEntry(
                run_id="run-t1",
                sample_id="T1",
                batch="batch-z",
                instrument="orbitrap-z",
                spectrum_count=9800,
                identification_rate=0.22,
                median_abs_mass_error_ppm=5.9,
                identified_retention_time_span_seconds=1790.0,
                retention_time_shift_seconds=12.0,
                outlier_reasons=(),
            ),
            InstrumentBatchQcRunEntry(
                run_id="run-t2",
                sample_id="T2",
                batch="batch-z",
                instrument="orbitrap-z",
                spectrum_count=7200,
                identification_rate=0.11,
                median_abs_mass_error_ppm=12.2,
                identified_retention_time_span_seconds=1650.0,
                retention_time_shift_seconds=95.0,
                outlier_reasons=("low_identification_rate", "high_mass_error"),
            ),
        ),
    )
    replicate_report = ReplicateCorrelationReport(
        entity_level=QuantEntityLevel.PROTEIN,
        entries=(
            ReplicateCorrelationEntry(
                sample_a="C1",
                sample_b="T2",
                condition_a="control",
                condition_b="treatment",
                correlation=0.62,
                shared_entity_count=12,
            ),
            ReplicateCorrelationEntry(
                sample_a="T1",
                sample_b="T2",
                condition_a="treatment",
                condition_b="treatment",
                correlation=0.62,
                shared_entity_count=12,
            ),
        ),
        within_condition_mean=None,
        between_condition_mean=0.62,
    )

    path = build_cautious_anomaly_interpretation_path(batch_report, replicate_report)

    assert isinstance(path, CautiousAnomalyInterpretationPath)
    assert path.interpretations
    assert "technical anomalies" in path.overall_recommendation
    assert path.interpretations[0].recommendation
    assert path.interpretations[0].explanation
    assert path.interpretations[0].unresolved_questions
    assert set(path.interpretations[0].explanation).isdisjoint(
        set(path.interpretations[0].unresolved_questions)
    )
    assert all(
        question not in path.interpretations[0].recommendation
        for question in path.interpretations[0].unresolved_questions
    )
    assert all(
        question not in path.overall_recommendation
        for question in path.unresolved_questions
    )
