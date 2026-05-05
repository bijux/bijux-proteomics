# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics_lab.outcomes import (
    AssayOutcome,
    AssayResultState,
    ExperimentOutcome,
    FailureClass,
    RerunPolicy,
)
from bijux_proteomics_lab.planning import LabExecutionRequest
from bijux_proteomics_lab.reconciliation import reconcile_planned_and_observed_outcome


def _outcome_fixture(name: str) -> dict[str, object]:
    return json.loads(
        (Path(__file__).parent / "fixtures" / "outcomes" / name).read_text(
            encoding="utf-8"
        )
    )


def test_reconcile_planned_and_observed_outcome_emits_feedback_signal() -> None:
    report = reconcile_planned_and_observed_outcome(
        candidate_id="cand-1",
        execution_request=LabExecutionRequest(
            program_id="prog-1",
            batch_id="batch-1",
            evidence_ids=["ev-1"],
            requested_instruction_ids=["batch-1:assay-a", "batch-1:assay-b"],
            requested_assay_ids=["assay-a", "assay-b"],
            scientific_rationale=["run orthogonal follow-up assays"],
            unresolved_risks=["review contradiction pressure after the batch"],
            ready_for_lab_review=True,
        ),
        outcome=ExperimentOutcome(
            batch_id="batch-1",
            assay_outcomes=[
                AssayOutcome(
                    assay_id="assay-a",
                    passed=True,
                    result_state=AssayResultState.PASSED,
                    observation_summary="targeted assay passed",
                    replicate_count=2,
                    uncertainty=0.1,
                ),
                AssayOutcome(
                    assay_id="assay-b",
                    passed=False,
                    result_state=AssayResultState.FAILED_BIOLOGICAL,
                    observation_summary="targeted assay missed the biological endpoint",
                    failure_class=FailureClass.BIOLOGICAL,
                    replicate_count=2,
                    uncertainty=0.2,
                ),
            ],
            rerun_policy=RerunPolicy.NEVER,
        ),
        target_id="target-1",
        claim_links={"assay-a": ["claim-1"], "assay-b": ["claim-2"]},
    )

    assert report.ready_for_feedback is True
    assert report.belief_posture == "mixed"
    assert report.intelligence_feedback.supported_assay_ids == ("assay-a",)
    assert report.intelligence_feedback.weakened_assay_ids == ("assay-b",)
    assert report.intelligence_feedback.belief_update_summary == (
        "reinforcing claims: claim-1",
        "weakening claims: claim-2",
    )
    assert report.intelligence_feedback.recommended_action.startswith("send")
    assert (
        "route weakened assays back into candidate review: assay-b"
        in report.operational_follow_through
    )
    assert report.claim_belief_update.contributing_assay_count == 2


def test_reconcile_planned_and_observed_outcome_flags_missing_requested_assays() -> (
    None
):
    report = reconcile_planned_and_observed_outcome(
        candidate_id="cand-2",
        execution_request=LabExecutionRequest(
            program_id="prog-2",
            batch_id="batch-2",
            evidence_ids=["ev-2"],
            requested_instruction_ids=["batch-2:assay-a", "batch-2:assay-b"],
            requested_assay_ids=["assay-a", "assay-b"],
            scientific_rationale=["complete the targeted confirmation panel"],
            unresolved_risks=[],
            ready_for_lab_review=True,
        ),
        outcome=ExperimentOutcome(
            batch_id="batch-2",
            assay_outcomes=[
                AssayOutcome(
                    assay_id="assay-a",
                    passed=False,
                    result_state=AssayResultState.FAILED_TECHNICAL,
                    observation_summary="instrument issue prevented the run",
                    failure_class=FailureClass.TECHNICAL,
                    replicate_count=2,
                    uncertainty=0.3,
                ),
            ],
            rerun_policy=RerunPolicy.NEVER,
        ),
        target_id="target-2",
    )

    assert any(
        delta.execution_gap == "requested assay did not produce an observed outcome"
        for delta in report.assay_deltas
    )
    assert report.belief_posture == "blocked"
    assert any(
        action.startswith("resolve blocked assays before downstream confidence")
        for action in report.operational_follow_through
    )
    assert "assay-b" in report.intelligence_feedback.blocked_assay_ids


def test_reconciliation_fixtures_cover_confirm_weaken_and_overturn_feedback() -> None:
    confirmed = _outcome_fixture("confirmed_follow_up_outcome.json")
    weakened = _outcome_fixture("weakened_follow_up_outcome.json")
    overturned = _outcome_fixture("overturned_follow_up_outcome.json")

    confirmed_report = reconcile_planned_and_observed_outcome(
        candidate_id=str(confirmed["candidate_id"]),
        execution_request=LabExecutionRequest.model_validate(
            confirmed["execution_request"]
        ),
        outcome=ExperimentOutcome.model_validate(confirmed["outcome"]),
        target_id=str(confirmed["target_id"]),
        claim_links=confirmed["claim_links"],
    )
    weakened_report = reconcile_planned_and_observed_outcome(
        candidate_id=str(weakened["candidate_id"]),
        execution_request=LabExecutionRequest.model_validate(
            weakened["execution_request"]
        ),
        outcome=ExperimentOutcome.model_validate(weakened["outcome"]),
        target_id=str(weakened["target_id"]),
        claim_links=weakened["claim_links"],
    )
    overturned_report = reconcile_planned_and_observed_outcome(
        candidate_id=str(overturned["candidate_id"]),
        execution_request=LabExecutionRequest.model_validate(
            overturned["execution_request"]
        ),
        outcome=ExperimentOutcome.model_validate(overturned["outcome"]),
        target_id=str(overturned["target_id"]),
        claim_links=overturned["claim_links"],
    )

    assert confirmed_report.belief_posture == "reinforcing"
    assert confirmed_report.intelligence_feedback.supported_assay_ids == (
        "assay-confirmed",
    )
    assert weakened_report.belief_posture == "weakening"
    assert weakened_report.intelligence_feedback.weakened_assay_ids == (
        "assay-weakened",
    )
    assert overturned_report.belief_posture == "weakening"
    assert overturned_report.claim_belief_update.updates[0].delta == -0.4
    assert overturned_report.intelligence_feedback.weakened_assay_ids == (
        "assay-overturn-a",
        "assay-overturn-b",
    )
