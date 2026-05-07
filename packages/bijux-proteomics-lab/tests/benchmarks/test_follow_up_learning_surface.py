# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_lab.benchmarks import (
    build_benchmark_follow_up_learning_artifact,
)
from bijux_proteomics_lab.handoffs import TargetedTransitionReview
from bijux_proteomics_lab.lifecycle import CandidateHandoffValidation
from bijux_proteomics_lab.outcomes import (
    AssayOutcome,
    AssayResultState,
    ExperimentOutcome,
)
from bijux_proteomics_lab.planning import ExecutableAssayPlan, ReviewPacket
from bijux_proteomics_lab.reconciliation import (
    OperationalFollowUpPath,
    build_operational_follow_up_path,
)


def _handoff_fixture(name: str) -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "fixtures" / "handoffs" / name
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _supported_operational_path() -> OperationalFollowUpPath:
    fixture = _handoff_fixture("supported_targeted_follow_up.json")
    handoff_validation = CandidateHandoffValidation.model_validate(
        fixture["handoff_validation"]
    )
    transition_review = TargetedTransitionReview.model_validate(
        fixture["transition_review"]
    ).model_copy(
        update={
            "approved_transition_ids": ("tr-egfr-1", "tr-egfr-2"),
            "exploratory_transition_ids": (),
        }
    )
    review_packet = ReviewPacket.model_validate(fixture["review_packet"])
    executable_plan = ExecutableAssayPlan.model_validate(fixture["executable_plan"])
    outcome = ExperimentOutcome.model_validate(fixture["outcome"]).model_copy(
        update={
            "assay_outcomes": [
                AssayOutcome(
                    assay_id="prm-assay",
                    passed=True,
                    result_state=AssayResultState.PASSED,
                    observation_summary="PRM transition cluster reproduced the prioritized phosphosite signal",
                    replicate_count=3,
                    uncertainty=0.08,
                ),
                AssayOutcome(
                    assay_id="orthogonal-assay",
                    passed=True,
                    result_state=AssayResultState.PASSED,
                    observation_summary="orthogonal immunoblot agreed with the targeted direction",
                    replicate_count=2,
                    uncertainty=0.12,
                ),
            ]
        }
    )
    return build_operational_follow_up_path(
        candidate_id=cast(str, fixture["candidate_id"]),
        handoff_validation=handoff_validation,
        transition_review=transition_review,
        review_packet=review_packet,
        executable_plan=executable_plan,
        outcome=outcome,
        target_id=cast(str, fixture["target_id"]),
        claim_links=cast(dict[str, list[str]], fixture["claim_links"]),
    )


def test_benchmark_follow_up_learning_artifact_keeps_requested_vs_observed_loop_visible() -> (
    None
):
    artifact = build_benchmark_follow_up_learning_artifact(
        benchmark_id="benchmark:targeted_transition_quality_control",
        workflow_family=KnowledgeWorkflowFamily.TARGETED,
        operational_path=_supported_operational_path(),
    )

    assert artifact.artifact_id == "benchmark_follow_up_learning:targeted"
    assert artifact.artifact_path.startswith("artifacts/")
    assert artifact.requested_assay_ids == ("prm-assay", "orthogonal-assay")
    assert artifact.observed_assay_ids == ("prm-assay", "orthogonal-assay")
    assert artifact.matched_assay_ids == ("prm-assay", "orthogonal-assay")
    assert artifact.missing_requested_assay_ids == ()
    assert artifact.unexpected_observed_assay_ids == ()
    assert artifact.promoted_evidence_ids
    assert artifact.ready_for_feedback is True
    assert artifact.belief_posture in {"reinforcing", "mixed"}
    assert artifact.learning_points
