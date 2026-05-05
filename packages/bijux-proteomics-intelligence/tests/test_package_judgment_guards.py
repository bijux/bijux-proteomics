# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from bijux_proteomics import SuccessCriterion, create_program_spec
from bijux_proteomics.programs import MeasurementDirection
from bijux_proteomics_intelligence import (
    CandidateAssessment,
    DEFAULT_INTELLIGENCE_CHARTER,
    ScenarioAction,
    ScenarioEvaluation,
    ScenarioSetEvaluation,
    build_final_decision_recommendation,
    build_ranking_rule_grounding_ledger,
    build_ranking_sensitivity_report,
    prioritize_candidates,
)
from bijux_proteomics_knowledge import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
)
from bijux_proteomics_knowledge.references import KnowledgeWorkflowFamily


def _program():
    program = create_program_spec(
        program_id="prog-guard",
        name="judgment guard",
        objective="keep intelligence recommendation behavior explicit",
        target_id="target-guard",
        target_name="Target Guard",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="preserve explicit judgment signals",
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


def _bundle(*, contradictory: bool) -> EvidenceBundle:
    now = datetime.now(UTC)
    records = [
        EvidenceRecord(
            evidence_id="evidence-1",
            kind=EvidenceKind.ASSAY,
            title="Primary assay support",
            source="lab-assay-1",
            source_type=EvidenceSourceType.LAB_ASSAY,
            claim="supports progression with reproducible assay signal",
            confidence=0.9,
            strength=EvidenceStrength.DECISIVE,
            decision_tags=["progression"],
            observed_at=now - timedelta(days=12),
        ),
        EvidenceRecord(
            evidence_id="evidence-2",
            kind=EvidenceKind.LITERATURE,
            title="Literature context",
            source="PMID:guard",
            source_type=EvidenceSourceType.LITERATURE,
            claim=(
                "fails progression because the assay response worsens"
                if contradictory
                else "supports disease-relevant target engagement"
            ),
            confidence=0.82,
            strength=EvidenceStrength.SUPPORTING,
            decision_tags=["progression"],
            observed_at=now - timedelta(days=25),
        ),
    ]
    return EvidenceBundle(
        bundle_id="bundle-guard",
        target_id="target-guard",
        records=records,
    )


def test_grounding_ledger_covers_each_workflow_family_with_required_rules() -> None:
    required_rule_ids = {
        "rule:evidence_strength_priority",
        "rule:reproducibility_priority",
        "rule:freshness_penalty",
        "rule:contradiction_penalty",
        "rule:assay_feasibility_and_operational_risk_balance",
    }

    for workflow_family in KnowledgeWorkflowFamily:
        ledger = build_ranking_rule_grounding_ledger(workflow_family)
        assert {rule.rule_id for rule in ledger.rules} == required_rule_ids


def test_prioritization_guard_keeps_grounding_and_sensitivity_visible() -> None:
    ranking = prioritize_candidates(
        _program(),
        [
            CandidateAssessment(
                candidate_id="candidate-a",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.86},
                manufacturability_score=0.84,
                uncertainty=0.08,
                evidence_support=0.87,
                reproducibility_score=0.9,
                effect_size_score=0.78,
                assay_feasibility_score=0.88,
                novelty_score=0.61,
                lab_cost_risk=0.12,
                operational_risk=0.09,
            )
        ],
        evidence_bundle=_bundle(contradictory=False),
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )

    top_candidate = ranking.ranked_candidates[0]
    sensitivity = build_ranking_sensitivity_report(top_candidate)

    assert top_candidate.explainability["knowledge_grounding_rule_ids"]
    assert top_candidate.explainability["multi_objective_profile"]["scientific_value"] > 0
    assert sensitivity.dominant_inputs


def test_recommendation_guard_keeps_machine_readable_refusal_visible() -> None:
    recommendation = build_final_decision_recommendation(
        ScenarioSetEvaluation(
            progression=ScenarioEvaluation(
                scenario="progression",
                action=ScenarioAction.ADVANCE,
                confidence=0.8,
            ),
            synthesis=ScenarioEvaluation(
                scenario="synthesis",
                action=ScenarioAction.ADVANCE,
                confidence=0.78,
            ),
            scale_up=ScenarioEvaluation(
                scenario="scale_up",
                action=ScenarioAction.SCALE_UP,
                confidence=0.76,
            ),
            redesign=ScenarioEvaluation(
                scenario="redesign",
                action=ScenarioAction.ADVANCE,
                confidence=0.74,
            ),
        ),
        evidence_bundle=_bundle(contradictory=True),
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )

    assert DEFAULT_INTELLIGENCE_CHARTER.capabilities
    assert recommendation.action is ScenarioAction.HOLD
    assert recommendation.gate_result is not None
    assert recommendation.gate_result.disposition.value == "refused"


def test_intelligence_package_does_not_restore_wrapper_only_serialization_surface() -> (
    None
):
    package_dir = Path(__file__).resolve().parents[1] / "src" / "bijux_proteomics_intelligence"
    assert not (package_dir / "serialization.py").exists()
