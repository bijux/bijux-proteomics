# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from bijux_proteomics_lab.design import SampleTrackingPlateAdvisory
from bijux_proteomics_lab.handoffs import (
    AlternativeAssayPlanOption,
    TargetedTransitionReview,
    build_handoff_explanation,
    compare_alternative_assay_plans,
    refuse_irresponsible_assay_handoff,
)
from bijux_proteomics_lab.lifecycle import (
    CandidateHandoffValidation,
    ReviewQueueDecision,
)
from bijux_proteomics_lab.outcomes import ExperimentOutcome
from bijux_proteomics_lab.planning import (
    ExecutableAssayPlan,
    ReviewPacket,
)
from bijux_proteomics_lab.readiness.workflow import WorkflowReadinessSummary
from bijux_proteomics_lab.reconciliation import (
    OperationalFollowUpPath,
    build_operational_follow_up_path,
)


def _handoff_fixture(name: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(
            (Path(__file__).parent / "fixtures" / "handoffs" / name).read_text(
                encoding="utf-8"
            )
        ),
    )


def _follow_up_path_from_fixture(fixture: dict[str, Any]) -> OperationalFollowUpPath:
    return build_operational_follow_up_path(
        candidate_id=cast(str, fixture["candidate_id"]),
        handoff_validation=CandidateHandoffValidation.model_validate(
            fixture["handoff_validation"]
        ),
        transition_review=TargetedTransitionReview.model_validate(
            fixture["transition_review"]
        ),
        review_packet=ReviewPacket.model_validate(fixture["review_packet"]),
        executable_plan=ExecutableAssayPlan.model_validate(fixture["executable_plan"]),
        outcome=ExperimentOutcome.model_validate(fixture["outcome"]),
        target_id=cast(str, fixture["target_id"]),
        claim_links=cast(dict[str, list[str]], fixture.get("claim_links", {})),
    )


def test_supported_fixture_builds_complete_operational_follow_up_path() -> None:
    fixture = _handoff_fixture("supported_targeted_follow_up.json")
    review_queue = ReviewQueueDecision.model_validate(fixture["review_queue_decision"])
    workflow = WorkflowReadinessSummary.model_validate(
        fixture["workflow_readiness_summary"]
    )
    plate = SampleTrackingPlateAdvisory.model_validate(fixture["plate_advisory"])
    handoff_validation = CandidateHandoffValidation.model_validate(
        fixture["handoff_validation"]
    )
    transition_review = TargetedTransitionReview.model_validate(
        fixture["transition_review"]
    )
    review_packet = ReviewPacket.model_validate(fixture["review_packet"])
    executable_plan = ExecutableAssayPlan.model_validate(fixture["executable_plan"])
    outcome = ExperimentOutcome.model_validate(fixture["outcome"])

    path = _follow_up_path_from_fixture(fixture)

    comparison = compare_alternative_assay_plans(
        tuple(
            AlternativeAssayPlanOption.model_validate(option)
            for option in cast(
                list[dict[str, Any]], fixture["alternative_plan_options"]
            )
        )
    )

    assert isinstance(path, OperationalFollowUpPath)
    assert review_queue.state.value == "approved"
    assert workflow.blocked_step_count == 0
    assert plate.control_well_ids == ("A12", "B12")
    assert plate.contamination_watch_well_ids == ("B12",)
    assert handoff_validation.accepted is True
    assert path.refusal is None
    assert path.execution_request.ready_for_lab_review is True
    assert path.reconciliation.ready_for_feedback is True
    assert path.reconciliation.intelligence_feedback.supported_assay_ids == (
        "prm-assay",
    )
    assert path.reconciliation.intelligence_feedback.weakened_assay_ids == (
        "orthogonal-assay",
    )
    assert comparison.recommended_plan_id == "orthogonal-first"


def test_refused_fixture_keeps_weak_science_blockers_explicit() -> None:
    fixture = _handoff_fixture("refused_targeted_follow_up.json")
    review_queue = ReviewQueueDecision.model_validate(fixture["review_queue_decision"])
    workflow = WorkflowReadinessSummary.model_validate(
        fixture["workflow_readiness_summary"]
    )
    plate = SampleTrackingPlateAdvisory.model_validate(fixture["plate_advisory"])
    handoff_validation = CandidateHandoffValidation.model_validate(
        fixture["handoff_validation"]
    )
    transition_review = TargetedTransitionReview.model_validate(
        fixture["transition_review"]
    )
    review_packet = ReviewPacket.model_validate(fixture["review_packet"])
    executable_plan = ExecutableAssayPlan.model_validate(fixture["executable_plan"])

    explanation = build_handoff_explanation(
        candidate_id=cast(str, fixture["candidate_id"]),
        handoff_validation=handoff_validation,
        transition_review=transition_review,
        review_packet=review_packet,
        executable_plan=executable_plan,
    )
    refusal = refuse_irresponsible_assay_handoff(
        candidate_id=cast(str, fixture["candidate_id"]),
        handoff_validation=handoff_validation,
        transition_review=transition_review,
        review_packet=review_packet,
        executable_plan=executable_plan,
    )
    comparison = compare_alternative_assay_plans(
        tuple(
            AlternativeAssayPlanOption.model_validate(option)
            for option in cast(
                list[dict[str, Any]], fixture["alternative_plan_options"]
            )
        )
    )

    assert review_queue.state.value == "deferred"
    assert workflow.blocked_step_count == 4
    assert plate.blocked_layout_labels == ("missing-reference-control", "weak-lineage")
    assert handoff_validation.accepted is False
    assert any(
        "too weak for irreversible lab spend" in blocker
        for blocker in handoff_validation.blockers
    )
    assert refusal is not None
    assert refusal.result.refusal is not None
    assert refusal.result.refusal.code == "irresponsible_assay_handoff"
    assert any(
        "unresolved contradiction pressure" in statement.summary
        for statement in explanation.blocked
    )
    assert comparison.recommended_plan_id == "orthogonal-rebuild"


def test_ambiguous_peptide_fixture_keeps_weak_target_follow_up_blocked() -> None:
    fixture = _handoff_fixture("ambiguous_peptide_weak_target_follow_up.json")
    review_queue = ReviewQueueDecision.model_validate(fixture["review_queue_decision"])
    workflow = WorkflowReadinessSummary.model_validate(
        fixture["workflow_readiness_summary"]
    )
    handoff_validation = CandidateHandoffValidation.model_validate(
        fixture["handoff_validation"]
    )
    transition_review = TargetedTransitionReview.model_validate(
        fixture["transition_review"]
    )
    review_packet = ReviewPacket.model_validate(fixture["review_packet"])
    executable_plan = ExecutableAssayPlan.model_validate(fixture["executable_plan"])

    explanation = build_handoff_explanation(
        candidate_id=cast(str, fixture["candidate_id"]),
        handoff_validation=handoff_validation,
        transition_review=transition_review,
        review_packet=review_packet,
        executable_plan=executable_plan,
    )
    refusal = refuse_irresponsible_assay_handoff(
        candidate_id=cast(str, fixture["candidate_id"]),
        handoff_validation=handoff_validation,
        transition_review=transition_review,
        review_packet=review_packet,
        executable_plan=executable_plan,
    )

    assert review_queue.state.value == "deferred"
    assert workflow.blocked_step_count == 4
    assert handoff_validation.accepted is False
    assert any("ambiguous" in blocker for blocker in handoff_validation.blockers)
    assert any("weak target signal" in blocker for blocker in handoff_validation.blockers)
    assert transition_review.refused_transition_ids == ("tr-her2-ambiguous",)
    assert refusal is not None
    assert "refused_targeted_transition" in refusal.refusal_reason_codes
    assert any(
        "ambiguous" in statement.summary or "weak target" in statement.summary
        for statement in explanation.blocked
    )


def test_failed_transition_fixture_refuses_execution_after_review_clearance() -> None:
    fixture = _handoff_fixture("failed_targeted_transition_follow_up.json")
    review_queue = ReviewQueueDecision.model_validate(fixture["review_queue_decision"])
    path = _follow_up_path_from_fixture(fixture)

    assert review_queue.state.value == "approved"
    assert path.handoff_validation.accepted is True
    assert path.refusal is not None
    assert path.execution_request.ready_for_lab_review is False
    assert "refused_targeted_transition" in path.refusal.refusal_reason_codes
    assert "execution_plan_blocked" in path.refusal.refusal_reason_codes
    assert path.transition_review.refused_transition_ids == ("tr-met-failed",)
    assert path.reconciliation.belief_posture == "blocked"
    assert path.reconciliation.intelligence_feedback.blocked_assay_ids == (
        "prm-transition-panel",
    )
