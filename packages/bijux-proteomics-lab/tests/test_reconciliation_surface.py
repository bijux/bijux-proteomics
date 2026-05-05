# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_lab import (
    AssayOutcome,
    AssayResultState,
    ExperimentOutcome,
    FailureClass,
    LabExecutionRequest,
    RerunPolicy,
    reconcile_planned_and_observed_outcome,
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
    assert report.intelligence_feedback.supported_assay_ids == ("assay-a",)
    assert report.intelligence_feedback.weakened_assay_ids == ("assay-b",)
    assert report.intelligence_feedback.recommended_action.startswith("send")
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
    assert "assay-b" in report.intelligence_feedback.blocked_assay_ids
