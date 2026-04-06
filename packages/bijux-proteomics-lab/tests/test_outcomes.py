# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_lab import (
    AcceptanceOperator,
    AssayAcceptanceRule,
    AssayCategory,
    AssayDefinition,
    AssayObservationRecord,
    AssayOutcome,
    ExperimentOutcome,
    FailureClass,
    RerunPolicy,
    evaluate_assay_acceptance,
    LabFeedbackRecord,
    promote_outcome_to_evidence,
    recommend_rerun_policy,
)


def test_recommend_rerun_policy_prefers_technical_reruns() -> None:
    outcome = ExperimentOutcome(
        batch_id="batch-1",
        assay_outcomes=[
            AssayOutcome(
                assay_id="assay-1",
                passed=False,
                observation_summary="Plate handling issue.",
                failure_class=FailureClass.TECHNICAL,
                replicate_count=2,
                uncertainty=0.1,
            )
        ],
        rerun_policy=RerunPolicy.NEVER,
    )

    assert recommend_rerun_policy(outcome) is RerunPolicy.ON_TECHNICAL_FAILURE


def test_evaluate_assay_acceptance_applies_explicit_rule() -> None:
    outcome = evaluate_assay_acceptance(
        AssayDefinition(
            assay_id="binding-assay",
            category=AssayCategory.BINDING,
            purpose="confirm target engagement",
            acceptance_rule=AssayAcceptanceRule(
                assay_id="binding-assay",
                metric="binding_score",
                operator=AcceptanceOperator.GREATER_EQUAL,
                threshold=0.8,
            ),
        ),
        AssayObservationRecord(
            assay_id="binding-assay",
            metric="binding_score",
            value=0.83,
        ),
    )

    assert outcome.passed is True
    assert outcome.failure_class is None


def test_promote_outcome_to_evidence_builds_normalized_payload() -> None:
    payload = promote_outcome_to_evidence(
        AssayOutcome(
            assay_id="binding-assay",
            passed=True,
            observation_summary="binding_score=0.83 met greater_equal 0.8",
            failure_class=None,
            uncertainty=0.2,
        ),
        target_id="target-1",
        batch_id="batch-1",
    )

    assert payload.kind.value == "assay"
    assert payload.source_type.value == "lab_assay"
    assert payload.related_targets == ["target-1"]
    assert payload.confidence < 0.9


def test_lab_feedback_record_keeps_cycle_and_lineage_refs() -> None:
    record = LabFeedbackRecord(
        feedback_id="feedback-1",
        program_id="prog-1",
        cycle_id="cycle-2026-01",
        summary="assay run indicates progression risk",
        related_assay_ids=["binding-assay"],
        related_evidence_ids=["assay:batch-1:binding-assay"],
    )

    assert record.cycle_id == "cycle-2026-01"
    assert record.related_evidence_ids == ["assay:batch-1:binding-assay"]
