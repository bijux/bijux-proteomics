# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path

import pytest

from bijux_proteomics.domain.criteria import MeasurementDirection, SuccessCriterion
from bijux_proteomics.domain.program_spec import create_program_spec
from bijux_proteomics_intelligence.briefs import (
    CandidateAssessment,
    prioritize_candidates,
)
from bijux_proteomics_intelligence.evaluators import (
    ScenarioAction,
    ScenarioEvaluation,
    ScenarioSetEvaluation,
)
from bijux_proteomics_intelligence.evidence_posture import (
    assess_recommendation_readiness,
)
from bijux_proteomics_intelligence.recommendations import (
    build_final_decision_recommendation,
)
from bijux_proteomics_intelligence.review_packets import build_review_board_packet
from bijux_proteomics_knowledge.evidence import EvidenceBundle, EvidenceRecord
from bijux_proteomics_knowledge.references.benchmarks import KnowledgeWorkflowFamily


def _fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures" / "review_scenarios"


def _load_scenario_fixture(name: str) -> dict[str, object]:
    return json.loads((_fixture_dir() / f"{name}.json").read_text())


def _program_from_fixture(payload: dict[str, object]) -> object:
    program_data = payload["program"]
    assert isinstance(program_data, dict)
    criterion_data = payload["criterion"]
    assert isinstance(criterion_data, dict)
    program = create_program_spec(
        program_id=str(program_data["program_id"]),
        name=str(program_data["name"]),
        objective=str(program_data["objective"]),
        target_id=str(program_data["target_id"]),
        target_name=str(program_data["target_name"]),
        sequence=str(program_data["sequence"]),
        organism=str(program_data["organism"]),
        mechanism=str(program_data["mechanism"]),
    )
    program.success_criteria.append(
        SuccessCriterion(
            criterion_id=str(criterion_data["criterion_id"]),
            metric=str(criterion_data["metric"]),
            direction=MeasurementDirection.MAXIMIZE,
            threshold=float(criterion_data["threshold"]),
        )
    )
    return program


def _assessments_from_fixture(payload: dict[str, object]) -> list[CandidateAssessment]:
    candidates = payload["candidates"]
    assert isinstance(candidates, list)
    return [CandidateAssessment.model_validate(item) for item in candidates]


def _bundle_from_fixture(payload: dict[str, object]) -> EvidenceBundle:
    records_payload = payload["evidence_records"]
    assert isinstance(records_payload, list)
    program_data = payload["program"]
    assert isinstance(program_data, dict)
    records: list[EvidenceRecord] = []
    now = datetime.now(UTC)
    for item in records_payload:
        record_payload = dict(item)
        observed_days_ago = int(record_payload.pop("observed_days_ago", 0))
        record_payload["observed_at"] = now - timedelta(days=observed_days_ago)
        records.append(EvidenceRecord.model_validate(record_payload))
    return EvidenceBundle(
        bundle_id=f"{program_data['program_id']}-bundle",
        target_id=str(program_data["target_id"]),
        records=records,
    )


def _grouped_review_state() -> ScenarioSetEvaluation:
    return ScenarioSetEvaluation(
        progression=ScenarioEvaluation(
            scenario="progression",
            action=ScenarioAction.ADVANCE,
            confidence=0.84,
        ),
        synthesis=ScenarioEvaluation(
            scenario="synthesis",
            action=ScenarioAction.ADVANCE,
            confidence=0.8,
        ),
        scale_up=ScenarioEvaluation(
            scenario="scale_up",
            action=ScenarioAction.SCALE_UP,
            confidence=0.78,
        ),
        redesign=ScenarioEvaluation(
            scenario="redesign",
            action=ScenarioAction.ADVANCE,
            confidence=0.76,
        ),
    )


@pytest.mark.parametrize(
    ("fixture_name", "workflow_family"),
    [
        ("phospho_prioritization", KnowledgeWorkflowFamily.PTM),
        ("lfq_follow_up", KnowledgeWorkflowFamily.LFQ),
        ("dia_follow_up", KnowledgeWorkflowFamily.DIA),
        ("targeted_assay_review", KnowledgeWorkflowFamily.TARGETED),
    ],
)
def test_realistic_review_scenarios_rank_grounded_follow_up_candidates(
    fixture_name: str,
    workflow_family: KnowledgeWorkflowFamily,
) -> None:
    payload = _load_scenario_fixture(fixture_name)
    program = _program_from_fixture(payload)
    assessments = _assessments_from_fixture(payload)
    bundle = _bundle_from_fixture(payload)

    ranking = prioritize_candidates(
        program,
        assessments,
        evidence_bundle=bundle,
        workflow_family=workflow_family,
    )
    qc_caveats = payload.get("qc_caveats", [])
    assert isinstance(qc_caveats, list)
    packet = build_review_board_packet(
        _grouped_review_state(),
        ranking,
        assessments,
        evidence_bundle=bundle,
        qc_caveats=[str(item) for item in qc_caveats],
        workflow_family=workflow_family,
    )

    assert (
        ranking.ranked_candidates[0].candidate_id
        == payload["expected_top_candidate_id"]
    )
    assert (
        packet.ranked_evidence[0].candidate_id == payload["expected_top_candidate_id"]
    )
    assert packet.qc_caveats == [str(item) for item in qc_caveats]


def test_novelty_trap_fixture_does_not_outrank_grounded_follow_up() -> None:
    payload = _load_scenario_fixture("novelty_overclaim_guard")
    program = _program_from_fixture(payload)
    assessments = _assessments_from_fixture(payload)
    bundle = _bundle_from_fixture(payload)

    ranking = prioritize_candidates(
        program,
        assessments,
        evidence_bundle=bundle,
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )

    assert (
        ranking.ranked_candidates[0].candidate_id
        == payload["expected_top_candidate_id"]
    )
    assert ranking.ranked_candidates[1].candidate_id == "novelty-trap"
    assert (
        ranking.ranked_candidates[1].explainability["priority_inputs"]["novelty"]
        > (ranking.ranked_candidates[0].explainability["priority_inputs"]["novelty"])
    )


def test_novelty_pressure_fixture_keeps_grounded_follow_up_on_top() -> None:
    payload = _load_scenario_fixture("novelty_pressure_trap")
    program = _program_from_fixture(payload)
    assessments = _assessments_from_fixture(payload)
    bundle = _bundle_from_fixture(payload)

    ranking = prioritize_candidates(
        program,
        assessments,
        evidence_bundle=bundle,
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )

    assert ranking.ranked_candidates[0].candidate_id == payload["expected_top_candidate_id"]
    assert ranking.ranked_candidates[1].candidate_id == "novelty-pressure-candidate"
    assert (
        ranking.ranked_candidates[1].explainability["priority_inputs"]["novelty"]
        > ranking.ranked_candidates[0].explainability["priority_inputs"]["novelty"]
    )
    assert (
        ranking.ranked_candidates[1].explainability["priority_inputs"]["evidence_strength"]
        < ranking.ranked_candidates[0].explainability["priority_inputs"]["evidence_strength"]
    )


@pytest.mark.parametrize(
    ("fixture_name", "workflow_family", "seductive_candidate_id"),
    [
        (
            "clean_score_sparse_support_guard",
            KnowledgeWorkflowFamily.DDA,
            "clean-score-trap",
        ),
        (
            "multiplex_channel_overclaim_guard",
            KnowledgeWorkflowFamily.MULTIPLEX,
            "multiplex-polish-trap",
        ),
    ],
)
def test_seductive_weak_candidate_fixtures_do_not_outrank_grounded_follow_up(
    fixture_name: str,
    workflow_family: KnowledgeWorkflowFamily,
    seductive_candidate_id: str,
) -> None:
    payload = _load_scenario_fixture(fixture_name)
    program = _program_from_fixture(payload)
    assessments = _assessments_from_fixture(payload)
    bundle = _bundle_from_fixture(payload)

    ranking = prioritize_candidates(
        program,
        assessments,
        evidence_bundle=bundle,
        workflow_family=workflow_family,
    )

    seductive_candidate = next(
        candidate
        for candidate in ranking.ranked_candidates
        if candidate.candidate_id == seductive_candidate_id
    )
    grounded_candidate = ranking.ranked_candidates[0]

    assert grounded_candidate.candidate_id == payload["expected_top_candidate_id"]
    assert (
        seductive_candidate.explainability["priority_inputs"]["criteria_strength"]
        > (grounded_candidate.explainability["priority_inputs"]["criteria_strength"])
    )
    assert (
        seductive_candidate.explainability["priority_inputs"]["evidence_strength"]
        < (grounded_candidate.explainability["priority_inputs"]["evidence_strength"])
    )
    assert (
        seductive_candidate.explainability["priority_inputs"]["reproducibility"]
        < (grounded_candidate.explainability["priority_inputs"]["reproducibility"])
    )


def test_aging_evidence_fixture_downgrades_recommendation_readiness() -> None:
    payload = _load_scenario_fixture("aging_evidence_guard")
    bundle = _bundle_from_fixture(payload)

    result = assess_recommendation_readiness(bundle)

    assert result.disposition.value == "degraded_success"
    assert "explicit evidence posture caveats" in result.summary
    assert any("aging-support-1:" in reason for reason in result.degradation_reasons)


def test_stale_polish_fixture_degrades_polished_recommendation_readiness() -> None:
    payload = _load_scenario_fixture("stale_polish_trap")
    bundle = _bundle_from_fixture(payload)

    result = assess_recommendation_readiness(bundle)

    assert result.disposition.value == "degraded_success"
    assert any(
        reason.startswith("stale-polish-assay:") for reason in result.degradation_reasons
    )
    assert any(
        "stale and should be refreshed" in reason for reason in result.degradation_reasons
    )


def test_thin_grounding_fixture_refuses_polished_candidate_without_decisive_support() -> (
    None
):
    payload = _load_scenario_fixture("thin_grounding_trap")
    bundle = _bundle_from_fixture(payload)

    result = assess_recommendation_readiness(bundle)

    assert result.disposition.value == "refused"
    assert result.refusal is not None
    assert result.refusal.code == "thin_grounding_support"
    assert any(
        "lacks decisive evidence records" in detail
        for detail in result.refusal.reason_details
    )


def test_contradiction_fixture_refuses_recommendation_and_keeps_conflicts_explicit() -> (
    None
):
    payload = _load_scenario_fixture("contradiction_refusal_guard")
    program = _program_from_fixture(payload)
    assessments = _assessments_from_fixture(payload)
    bundle = _bundle_from_fixture(payload)

    ranking = prioritize_candidates(
        program,
        assessments,
        evidence_bundle=bundle,
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )
    packet = build_review_board_packet(
        _grouped_review_state(),
        ranking,
        assessments,
        evidence_bundle=bundle,
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )
    recommendation = build_final_decision_recommendation(
        _grouped_review_state(),
        evidence_bundle=bundle,
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )

    assert recommendation.action is ScenarioAction.HOLD
    assert recommendation.gate_result is not None
    assert recommendation.gate_result.disposition.value == "refused"
    assert packet.contradiction_summary is not None
    assert packet.contradiction_summary.conflict_count >= 1
    assert packet.ranked_evidence[0].contradiction_pressure > 0.0
    assert packet.ranked_evidence[0].freshness_pressure >= 0.0
