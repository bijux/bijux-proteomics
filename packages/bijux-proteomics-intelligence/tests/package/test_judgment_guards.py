# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

from bijux_proteomics.domain.criteria import MeasurementDirection, SuccessCriterion
from bijux_proteomics.domain.program_spec import ProgramSpec, create_program_spec
from bijux_proteomics_intelligence.candidates.ranking import (
    CandidateAssessment,
    RankedCandidate,
    build_ranking_sensitivity_report,
    prioritize_candidates,
)
from bijux_proteomics_intelligence.governance.charter import (
    DEFAULT_INTELLIGENCE_CHARTER,
    DEFAULT_INTELLIGENCE_MODULE_AUDIT,
    IntelligenceModuleClassification,
)
from bijux_proteomics_intelligence.judgment.paths import (
    build_review_board_decision_path,
)
from bijux_proteomics_intelligence.judgment.recommendations import (
    build_final_decision_recommendation,
)
from bijux_proteomics_intelligence.judgment.scenarios import (
    ScenarioAction,
    ScenarioEvaluation,
    ScenarioSetEvaluation,
)
from bijux_proteomics_intelligence.posture.skeptical import (
    build_skeptical_review_report,
)
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
)
from bijux_proteomics_knowledge.references.grounding.rules import (
    build_ranking_rule_grounding_ledger,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


def _program() -> ProgramSpec:
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


def _explainability_section(
    candidate: RankedCandidate,
    section: str,
) -> dict[str, object]:
    return cast(dict[str, object], candidate.explainability[section])


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
    multi_objective_profile = _explainability_section(
        top_candidate, "multi_objective_profile"
    )
    assert float(cast(int | float, multi_objective_profile["scientific_value"])) > 0
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
    package_dir = (
        Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics_intelligence"
    )
    assert not (package_dir / "serialization.py").exists()


def test_intelligence_package_keeps_multiple_analytical_modules_release_blocking() -> (
    None
):
    analytical_modules = [
        entry
        for entry in DEFAULT_INTELLIGENCE_MODULE_AUDIT
        if entry.classification is IntelligenceModuleClassification.ANALYTICAL_VALUE
    ]

    assert len(analytical_modules) >= 8


def test_skeptical_review_guard_proves_value_beyond_core_and_runtime() -> None:
    path = build_review_board_decision_path(
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
        _bundle(contradictory=False),
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )

    report = build_skeptical_review_report(path)

    assert len(report.analytical_value_signals) >= 4


def test_intelligence_readme_advertises_live_judgment_entrypoints() -> None:
    readme_path = Path(__file__).resolve().parents[2] / "README.md"
    readme_text = readme_path.read_text()

    assert "posture/skeptical.py" in readme_text
    assert "grounding.py" not in readme_text
