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
    AssayResultState,
    ExperimentOutcome,
    FailureClass,
    RerunPolicy,
    evaluate_assay_acceptance,
    LabFeedbackQuery,
    LabFeedbackRecord,
    promote_outcome_to_evidence,
    query_feedback_records,
    recommend_rerun_policy,
    summarize_experiment_outcome,
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


def test_recommend_rerun_policy_can_return_biological_failure() -> None:
    outcome = ExperimentOutcome(
        batch_id="batch-2",
        assay_outcomes=[
            AssayOutcome(
                assay_id="assay-2",
                passed=False,
                result_state=AssayResultState.FAILED_BIOLOGICAL,
                observation_summary="Biological endpoint missed.",
                failure_class=FailureClass.BIOLOGICAL,
            )
        ],
        rerun_policy=RerunPolicy.NEVER,
    )

    assert recommend_rerun_policy(outcome) is RerunPolicy.ON_BIOLOGICAL_FAILURE


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
    assert outcome.result_state is AssayResultState.PASSED
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
    assert payload.decision_tags == ["progression"]
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


def test_evaluate_assay_acceptance_marks_unit_mismatch_as_inconclusive() -> None:
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
                unit="uM",
            ),
        ),
        AssayObservationRecord(
            assay_id="binding-assay",
            metric="binding_score",
            value=0.83,
            unit="nM",
        ),
    )

    assert outcome.result_state is AssayResultState.INCONCLUSIVE
    assert outcome.failure_class is FailureClass.INTERPRETATION


def test_evaluate_assay_acceptance_flags_qc_failure_as_technical() -> None:
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
            value=0.85,
            replicate_values=[0.82, 0.85, 0.88],
            qc_passed=False,
            dispersion=0.05,
        ),
    )

    assert outcome.result_state is AssayResultState.FAILED_TECHNICAL
    assert outcome.failure_class is FailureClass.TECHNICAL
    assert outcome.replicate_count == 3


def test_evaluate_assay_acceptance_supports_bounded_ranges() -> None:
    outcome = evaluate_assay_acceptance(
        AssayDefinition(
            assay_id="stability-assay",
            category=AssayCategory.STABILITY,
            purpose="confirm neutral stability window",
            acceptance_rule=AssayAcceptanceRule(
                assay_id="stability-assay",
                metric="delta_tm",
                operator=AcceptanceOperator.BETWEEN,
                threshold=1.0,
                upper_threshold=3.0,
            ),
        ),
        AssayObservationRecord(
            assay_id="stability-assay",
            metric="delta_tm",
            value=2.0,
        ),
    )

    assert outcome.passed is True
    assert outcome.result_state is AssayResultState.PASSED


def test_query_feedback_records_filters_by_cycle_and_assay() -> None:
    records = [
        LabFeedbackRecord(
            feedback_id="f1",
            program_id="prog-1",
            cycle_id="cycle-1",
            summary="binding risk",
            related_assay_ids=["a1"],
            related_evidence_ids=["e1"],
        ),
        LabFeedbackRecord(
            feedback_id="f2",
            program_id="prog-1",
            cycle_id="cycle-2",
            summary="stability risk",
            related_assay_ids=["a2"],
            related_evidence_ids=["e2"],
        ),
    ]

    filtered = query_feedback_records(
        records,
        LabFeedbackQuery(program_id="prog-1", cycle_id="cycle-1", related_assay_id="a1"),
    )

    assert [record.feedback_id for record in filtered] == ["f1"]


def test_evaluate_assay_acceptance_marks_below_detection_as_inconclusive() -> None:
    outcome = evaluate_assay_acceptance(
        AssayDefinition(
            assay_id="activity-assay",
            category=AssayCategory.ACTIVITY,
            purpose="measure weak activity signals",
            acceptance_rule=AssayAcceptanceRule(
                assay_id="activity-assay",
                metric="activity_signal",
                operator=AcceptanceOperator.GREATER_EQUAL,
                threshold=0.2,
            ),
        ),
        AssayObservationRecord(
            assay_id="activity-assay",
            metric="activity_signal",
            value=0.05,
            detection_limit=0.1,
            below_detection_limit=True,
            normalization_method="median-center",
        ),
    )

    assert outcome.result_state is AssayResultState.INCONCLUSIVE
    assert outcome.failure_class is FailureClass.INTERPRETATION


def test_promote_outcome_to_evidence_adds_uncertainty_tags_for_inconclusive_results() -> None:
    payload = promote_outcome_to_evidence(
        AssayOutcome(
            assay_id="activity-assay",
            passed=False,
            result_state=AssayResultState.INCONCLUSIVE,
            observation_summary="activity signal below detection limit",
            failure_class=FailureClass.INTERPRETATION,
            uncertainty=0.6,
        ),
        target_id="target-2",
        batch_id="batch-2",
    )

    assert "uncertainty" in payload.decision_tags


def test_summarize_experiment_outcome_counts_result_states() -> None:
    summary = summarize_experiment_outcome(
        ExperimentOutcome(
            batch_id="batch-summary",
            assay_outcomes=[
                AssayOutcome(
                    assay_id="a1",
                    passed=True,
                    result_state=AssayResultState.PASSED,
                    observation_summary="pass",
                ),
                AssayOutcome(
                    assay_id="a2",
                    passed=False,
                    result_state=AssayResultState.FAILED_TECHNICAL,
                    observation_summary="tech",
                    failure_class=FailureClass.TECHNICAL,
                ),
                AssayOutcome(
                    assay_id="a3",
                    passed=False,
                    result_state=AssayResultState.INCONCLUSIVE,
                    observation_summary="inc",
                    failure_class=FailureClass.INTERPRETATION,
                ),
            ],
            rerun_policy=RerunPolicy.ON_INCONCLUSIVE_RESULT,
        )
    )

    assert summary.total_assays == 3
    assert summary.passed_count == 1
    assert summary.failed_technical_count == 1
    assert summary.inconclusive_count == 1
