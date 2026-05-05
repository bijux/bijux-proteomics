# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path

import pytest

from bijux_proteomics import SuccessCriterion, create_program_spec
from bijux_proteomics.programs import MeasurementDirection
from bijux_proteomics_intelligence import (
    CandidateAssessment,
    ScenarioAction,
    ScenarioEvaluation,
    ScenarioSetEvaluation,
    build_review_board_packet,
    prioritize_candidates,
)
from bijux_proteomics_knowledge import EvidenceBundle, EvidenceRecord
from bijux_proteomics_knowledge.references import KnowledgeWorkflowFamily


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

    assert ranking.ranked_candidates[0].candidate_id == payload["expected_top_candidate_id"]
    assert packet.ranked_evidence[0].candidate_id == payload["expected_top_candidate_id"]
    assert packet.qc_caveats == [str(item) for item in qc_caveats]
