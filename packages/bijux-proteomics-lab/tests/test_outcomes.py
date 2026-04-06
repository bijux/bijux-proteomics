# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations
from datetime import UTC, datetime

from bijux_proteomics_lab import (
    AcceptanceOperator,
    AssayAcceptanceRule,
    AssayCategory,
    AssayDefinition,
    AssayObservationRecord,
    AssayOutcome,
    AssayResultState,
    QcState,
    ExperimentOutcome,
    FailureClass,
    RerunPolicy,
    evaluate_assay_acceptance,
    LabFeedbackQuery,
    LabFeedbackRecord,
    OutcomePromotionPolicy,
    promote_outcome_to_evidence,
    query_feedback_records,
    summarize_feedback_trend,
    query_review_queue,
    summarize_review_queue,
    summarize_review_queue_workload,
    summarize_feedback_cycle_latency,
    detect_feedback_anomalies,
    forecast_cycle_workload,
    ReviewQueueEntry,
    ReviewQueueQuery,
    recommend_rerun_policy,
    summarize_experiment_outcome,
    summarize_observation,
    assess_evidence_promotion_readiness,
    recommend_claim_belief_deltas,
    assess_batch_outcome,
    validate_assay_observation_record,
    generate_feedback_records_from_outcome,
    promote_batch_outcome_to_evidence,
    triage_assay_failure,
    triage_batch_failures,
    consolidate_claim_belief_updates,
    assess_observation_quality,
    BatchPromotionPolicy,
    ObservationQualityProfile,
    assess_outcome_reliability,
    OutcomeReliabilityTier,
    build_batch_readiness_matrix,
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


def test_promote_outcome_to_evidence_supports_custom_promotion_policy() -> None:
    payload = promote_outcome_to_evidence(
        AssayOutcome(
            assay_id="binding-assay",
            passed=False,
            observation_summary="binding did not pass threshold",
            failure_class=FailureClass.BIOLOGICAL,
            uncertainty=0.1,
        ),
        target_id="target-1",
        batch_id="batch-1",
        policy=OutcomePromotionPolicy(
            policy_id="strict-policy",
            failed_base_confidence=0.35,
            uncertainty_penalty_factor=0.5,
        ),
    )

    assert payload.confidence == 0.3


def test_triage_assay_failure_handles_reproducibility_breakdown() -> None:
    triage = triage_assay_failure(
        AssayOutcome(
            assay_id="binding-assay",
            passed=False,
            result_state=AssayResultState.FAILED_REPRODUCIBILITY,
            observation_summary="replicate spread was too high",
            failure_class=FailureClass.INTERPRETATION,
            uncertainty=0.3,
        )
    )

    assert triage.triage_code == "reproducibility-breakdown"
    assert triage.escalation_required is True
    assert any("orthogonal assay" in action for action in triage.recommended_actions)


def test_triage_batch_failures_tracks_escalation_assays() -> None:
    report = triage_batch_failures(
        ExperimentOutcome(
            batch_id="batch-1",
            assay_outcomes=[
                AssayOutcome(
                    assay_id="assay-tech",
                    passed=False,
                    result_state=AssayResultState.FAILED_TECHNICAL,
                    observation_summary="plate handling failure",
                    failure_class=FailureClass.TECHNICAL,
                ),
                AssayOutcome(
                    assay_id="assay-bio",
                    passed=False,
                    result_state=AssayResultState.FAILED_BIOLOGICAL,
                    observation_summary="activity endpoint missed",
                    failure_class=FailureClass.BIOLOGICAL,
                ),
            ],
            rerun_policy=RerunPolicy.NEVER,
        )
    )

    assert report.escalation_assay_ids == ["assay-bio"]
    assert any("technical execution issues" in note for note in report.summary_notes)


def test_consolidate_claim_belief_updates_aggregates_assay_deltas() -> None:
    batch = ExperimentOutcome(
        batch_id="batch-agg",
        assay_outcomes=[
            AssayOutcome(
                assay_id="a1",
                passed=True,
                result_state=AssayResultState.PASSED,
                observation_summary="binding passed",
                uncertainty=0.1,
            ),
            AssayOutcome(
                assay_id="a2",
                passed=False,
                result_state=AssayResultState.FAILED_BIOLOGICAL,
                observation_summary="cellular miss",
                failure_class=FailureClass.BIOLOGICAL,
                uncertainty=0.2,
            ),
        ],
        rerun_policy=RerunPolicy.NEVER,
    )

    update = consolidate_claim_belief_updates(
        batch,
        claim_links={"a1": ["claim-1"], "a2": ["claim-1", "claim-2"]},
    )

    assert update.contributing_assay_count == 2
    assert {item.claim_id for item in update.updates} == {"claim-1", "claim-2"}


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


def test_evaluate_assay_acceptance_marks_qc_warning_as_inconclusive() -> None:
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
            qc_state=QcState.WARNING,
            interpretation_confidence=0.6,
        ),
    )

    assert outcome.result_state is AssayResultState.INCONCLUSIVE
    assert outcome.failure_class is FailureClass.INTERPRETATION


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


def test_summarize_review_queue_workload_reports_stale_pressure() -> None:
    now = datetime(2026, 4, 1, tzinfo=UTC)
    entries = [
        ReviewQueueEntry(
            program_id="prog-1",
            gate_id="gate-1",
            summary="primary gate blocked",
            created_at=datetime(2026, 3, 1, tzinfo=UTC),
        ),
        ReviewQueueEntry(
            program_id="prog-1",
            gate_id="gate-2",
            summary="secondary gate blocked",
            created_at=datetime(2026, 3, 20, tzinfo=UTC),
        ),
        ReviewQueueEntry(
            program_id="prog-2",
            gate_id="gate-1",
            summary="new blocker",
            created_at=datetime(2026, 3, 30, tzinfo=UTC),
        ),
    ]

    report = summarize_review_queue_workload(entries, now=now, stale_after_days=10)

    assert report.stale_entry_count == 2
    assert report.by_program["prog-1"] == 2
    assert report.pressure_score > 0.0


def test_summarize_feedback_cycle_latency_reports_median() -> None:
    records = [
        LabFeedbackRecord(
            feedback_id="f1",
            program_id="prog-lat",
            cycle_id="cycle-1",
            summary="first",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        LabFeedbackRecord(
            feedback_id="f2",
            program_id="prog-lat",
            cycle_id="cycle-2",
            summary="second cycle",
            created_at=datetime(2026, 1, 4, tzinfo=UTC),
        ),
        LabFeedbackRecord(
            feedback_id="f3",
            program_id="prog-lat",
            cycle_id="cycle-3",
            summary="third cycle",
            created_at=datetime(2026, 1, 9, tzinfo=UTC),
        ),
    ]

    report = summarize_feedback_cycle_latency(records, program_id="prog-lat")

    assert report.cycle_to_first_feedback_days["cycle-2"] == 3.0
    assert report.median_latency_days == 3.0


def test_assess_observation_quality_decomposes_quality_dimensions() -> None:
    quality = assess_observation_quality(
        AssayObservationRecord(
            assay_id="assay-1",
            metric="binding_score",
            value=0.8,
            replicate_values=[0.78, 0.81, 0.79],
            dispersion=0.05,
            qc_state=QcState.WARNING,
            interpretation_confidence=0.9,
            below_detection_limit=True,
            normalization_method=None,
        )
    )

    assert quality.assay_id == "assay-1"
    assert quality.qc_reliability == 0.5
    assert quality.composite_quality < 0.9


def test_detect_feedback_anomalies_flags_cycle_and_assay_concentration() -> None:
    records = [
        LabFeedbackRecord(
            feedback_id=f"f{i}",
            program_id="prog-anom",
            cycle_id="cycle-1",
            summary="feedback",
            related_assay_ids=["assay-1"],
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        for i in range(6)
    ] + [
        LabFeedbackRecord(
            feedback_id="f6",
            program_id="prog-anom",
            cycle_id="cycle-2",
            summary="feedback",
            related_assay_ids=["assay-2"],
            created_at=datetime(2026, 1, 2, tzinfo=UTC),
        )
    ]

    report = detect_feedback_anomalies(records, program_id="prog-anom", cycle_volume_threshold=5, assay_dominance_ratio=0.7)

    assert report.high_volume_cycles == ["cycle-1"]
    assert report.dominant_assay_ids == ["assay-1"]


def test_forecast_cycle_workload_estimates_pressure_from_history() -> None:
    feedback = [
        LabFeedbackRecord(
            feedback_id=f"f{i}",
            program_id="prog-forecast",
            cycle_id=f"cycle-{(i // 2) + 1}",
            summary="feedback",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        for i in range(6)
    ]
    queue = [
        ReviewQueueEntry(program_id="prog-forecast", gate_id="gate-1", summary="blocked"),
        ReviewQueueEntry(program_id="prog-forecast", gate_id="gate-2", summary="blocked"),
    ]

    forecast = forecast_cycle_workload(
        program_id="prog-forecast",
        feedback_records=feedback,
        review_entries=queue,
    )

    assert forecast.forecast_feedback_count > 0
    assert forecast.forecast_review_entries == 2


def test_promote_batch_outcome_to_evidence_respects_quality_policy() -> None:
    outcome = ExperimentOutcome(
        batch_id="batch-quality",
        assay_outcomes=[
            AssayOutcome(
                assay_id="assay-1",
                passed=True,
                result_state=AssayResultState.PASSED,
                observation_summary="passed",
                uncertainty=0.1,
            )
        ],
        rerun_policy=RerunPolicy.NEVER,
    )
    promoted, report = promote_batch_outcome_to_evidence(
        outcome,
        target_id="target-1",
        batch_policy=BatchPromotionPolicy(policy_id="strict", minimum_quality_score=0.8),
        quality_profiles={
            "assay-1": ObservationQualityProfile(
                assay_id="assay-1",
                technical_reproducibility=0.7,
                qc_reliability=0.7,
                interpretability=0.7,
                composite_quality=0.7,
                notes=["low"],
            )
        },
    )

    assert promoted == []
    assert report.blocked_assay_ids == ["assay-1"]


def test_assess_outcome_reliability_uses_quality_and_uncertainty() -> None:
    assessment = assess_outcome_reliability(
        AssayOutcome(
            assay_id="assay-rel",
            passed=True,
            result_state=AssayResultState.PASSED,
            observation_summary="good result",
            replicate_count=3,
            uncertainty=0.1,
        ),
        quality_profile=ObservationQualityProfile(
            assay_id="assay-rel",
            technical_reproducibility=0.9,
            qc_reliability=0.9,
            interpretability=0.8,
            composite_quality=0.88,
            notes=[],
        ),
    )

    assert assessment.tier is OutcomeReliabilityTier.ROBUST
    assert assessment.score >= 0.75


def test_build_batch_readiness_matrix_tracks_ready_count() -> None:
    matrix = build_batch_readiness_matrix(
        ExperimentOutcome(
            batch_id="batch-readiness",
            assay_outcomes=[
                AssayOutcome(
                    assay_id="a1",
                    passed=True,
                    result_state=AssayResultState.PASSED,
                    observation_summary="pass",
                    replicate_count=3,
                    uncertainty=0.1,
                ),
                AssayOutcome(
                    assay_id="a2",
                    passed=False,
                    result_state=AssayResultState.FAILED_TECHNICAL,
                    observation_summary="fail",
                    replicate_count=2,
                    uncertainty=0.3,
                ),
            ],
            rerun_policy=RerunPolicy.NEVER,
        )
    )

    assert matrix.batch_id == "batch-readiness"
    assert matrix.ready_count == 1


def test_query_feedback_records_supports_evidence_and_time_filters() -> None:
    records = [
        LabFeedbackRecord(
            feedback_id="f-old",
            program_id="prog-1",
            cycle_id="cycle-1",
            summary="old feedback",
            related_assay_ids=["a1"],
            related_evidence_ids=["e1"],
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        LabFeedbackRecord(
            feedback_id="f-new",
            program_id="prog-1",
            cycle_id="cycle-1",
            summary="new feedback",
            related_assay_ids=["a1"],
            related_evidence_ids=["e2"],
            created_at=datetime(2026, 2, 1, tzinfo=UTC),
        ),
    ]
    filtered = query_feedback_records(
        records,
        LabFeedbackQuery(
            program_id="prog-1",
            related_evidence_id="e2",
            created_after=datetime(2026, 1, 15, tzinfo=UTC),
        ),
    )

    assert [record.feedback_id for record in filtered] == ["f-new"]


def test_summarize_feedback_trend_reports_cycle_and_assay_coverage() -> None:
    report = summarize_feedback_trend(
        [
            LabFeedbackRecord(
                feedback_id="t1",
                program_id="prog-trend",
                cycle_id="cycle-1",
                summary="first",
                related_assay_ids=["a1"],
                related_evidence_ids=[],
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
            LabFeedbackRecord(
                feedback_id="t2",
                program_id="prog-trend",
                cycle_id="cycle-2",
                summary="second",
                related_assay_ids=["a1", "a2"],
                related_evidence_ids=[],
                created_at=datetime(2026, 2, 1, tzinfo=UTC),
            ),
        ],
        program_id="prog-trend",
    )

    assert report.feedback_count == 2
    assert report.cycle_ids == ["cycle-1", "cycle-2"]
    assert report.assay_coverage["a1"] == 2


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
                AssayOutcome(
                    assay_id="a4",
                    passed=False,
                    result_state=AssayResultState.FAILED_REPRODUCIBILITY,
                    observation_summary="replicate drift",
                    failure_class=FailureClass.INTERPRETATION,
                ),
            ],
            rerun_policy=RerunPolicy.ON_INCONCLUSIVE_RESULT,
        )
    )

    assert summary.total_assays == 4
    assert summary.passed_count == 1
    assert summary.failed_technical_count == 1
    assert summary.failed_reproducibility_count == 1
    assert summary.inconclusive_count == 1


def test_summarize_observation_uses_replicate_statistics() -> None:
    summary = summarize_observation(
        AssayObservationRecord(
            assay_id="assay-stat",
            metric="activity_ratio",
            value=1.0,
            replicate_values=[0.8, 1.0, 1.2],
            dispersion=0.2,
        )
    )

    assert summary.replicate_count == 3
    assert summary.mean_value == 1.0
    assert summary.median_value == 1.0


def test_assess_evidence_promotion_readiness_blocks_uncertain_inconclusive_outcomes() -> None:
    readiness = assess_evidence_promotion_readiness(
        AssayOutcome(
            assay_id="assay-promote",
            passed=False,
            result_state=AssayResultState.INCONCLUSIVE,
            observation_summary="signal below detection",
            failure_class=FailureClass.INTERPRETATION,
            replicate_count=1,
            uncertainty=0.7,
        )
    )

    assert readiness.ready is False
    assert any("result_state" in blocker for blocker in readiness.blockers)


def test_recommend_claim_belief_deltas_supports_closed_loop_updates() -> None:
    deltas = recommend_claim_belief_deltas(
        AssayOutcome(
            assay_id="assay-belief",
            passed=True,
            result_state=AssayResultState.PASSED,
            observation_summary="signal met acceptance",
            uncertainty=0.2,
        ),
        linked_claim_ids=["claim-1", "claim-2"],
    )

    assert len(deltas) == 2
    assert all(delta.delta > 0 for delta in deltas)


def test_assess_batch_outcome_reports_promotion_readiness_and_rerun_posture() -> None:
    assessment = assess_batch_outcome(
        ExperimentOutcome(
            batch_id="batch-assess",
            assay_outcomes=[
                AssayOutcome(
                    assay_id="a1",
                    passed=False,
                    result_state=AssayResultState.FAILED_TECHNICAL,
                    observation_summary="instrument issue",
                    failure_class=FailureClass.TECHNICAL,
                    replicate_count=2,
                    uncertainty=0.2,
                ),
                AssayOutcome(
                    assay_id="a2",
                    passed=True,
                    result_state=AssayResultState.PASSED,
                    observation_summary="passed",
                    replicate_count=2,
                    uncertainty=0.1,
                ),
            ],
            rerun_policy=RerunPolicy.NEVER,
        )
    )

    assert assessment.total_assays == 2
    assert assessment.technical_or_repro_failures == 1
    assert assessment.rerun_policy is RerunPolicy.ON_TECHNICAL_FAILURE


def test_validate_assay_observation_record_reports_qc_and_detection_issues() -> None:
    issues = validate_assay_observation_record(
        AssayObservationRecord(
            assay_id="assay-validate",
            metric="activity_signal",
            value=0.1,
            replicate_values=[0.1],
            dispersion=0.2,
            below_detection_limit=True,
            qc_state=QcState.FAILED,
            qc_passed=True,
        )
    )

    assert {issue.code for issue in issues} == {
        "replicate-count-low",
        "detection-limit-missing",
        "qc-state-inconsistent",
    }


def test_generate_feedback_records_from_outcome_preserves_assay_lineage() -> None:
    records, mapping = generate_feedback_records_from_outcome(
        ExperimentOutcome(
            batch_id="batch-feedback",
            assay_outcomes=[
                AssayOutcome(
                    assay_id="assay-1",
                    passed=True,
                    observation_summary="assay passed",
                )
            ],
            rerun_policy=RerunPolicy.NEVER,
        ),
        program_id="prog-feedback",
        cycle_id="cycle-feedback-1",
    )

    assert mapping.feedback_ids == ["feedback:batch-feedback:assay-1"]
    assert records[0].related_evidence_ids == ["assay:batch-feedback:assay-1"]


def test_promote_batch_outcome_to_evidence_reports_promoted_and_blocked_assays() -> None:
    payloads, report = promote_batch_outcome_to_evidence(
        ExperimentOutcome(
            batch_id="batch-promote",
            assay_outcomes=[
                AssayOutcome(
                    assay_id="assay-pass",
                    passed=True,
                    result_state=AssayResultState.PASSED,
                    observation_summary="pass",
                    replicate_count=2,
                    uncertainty=0.1,
                ),
                AssayOutcome(
                    assay_id="assay-fail",
                    passed=False,
                    result_state=AssayResultState.INCONCLUSIVE,
                    observation_summary="inconclusive",
                    replicate_count=1,
                    uncertainty=0.7,
                ),
            ],
            rerun_policy=RerunPolicy.ON_INCONCLUSIVE_RESULT,
        ),
        target_id="target-promote",
    )

    assert [payload.evidence_id for payload in payloads] == ["assay:batch-promote:assay-pass"]
    assert report.blocked_assay_ids == ["assay-fail"]


def test_evaluate_assay_acceptance_marks_high_dispersion_as_reproducibility_failure() -> None:
    outcome = evaluate_assay_acceptance(
        AssayDefinition(
            assay_id="binding-assay",
            category=AssayCategory.BINDING,
            purpose="confirm reproducibility",
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
            value=0.84,
            replicate_values=[0.61, 0.84, 1.01],
            dispersion=0.35,
        ),
    )

    assert outcome.result_state is AssayResultState.FAILED_REPRODUCIBILITY
    assert outcome.passed is False


def test_recommend_rerun_policy_can_return_reproducibility_failure() -> None:
    outcome = ExperimentOutcome(
        batch_id="batch-repro",
        assay_outcomes=[
            AssayOutcome(
                assay_id="assay-repro",
                passed=False,
                result_state=AssayResultState.FAILED_REPRODUCIBILITY,
                observation_summary="high replicate drift",
                failure_class=FailureClass.INTERPRETATION,
            )
        ],
        rerun_policy=RerunPolicy.NEVER,
    )

    assert recommend_rerun_policy(outcome) is RerunPolicy.ON_REPRODUCIBILITY_FAILURE


def test_query_and_summarize_review_queue_support_gate_workload_views() -> None:
    entries = [
        ReviewQueueEntry(program_id="prog-1", gate_id="gate-a", summary="a"),
        ReviewQueueEntry(program_id="prog-1", gate_id="gate-b", summary="b"),
        ReviewQueueEntry(program_id="prog-2", gate_id="gate-a", summary="c"),
    ]
    filtered = query_review_queue(entries, ReviewQueueQuery(program_id="prog-1"))
    summary = summarize_review_queue(filtered)

    assert len(filtered) == 2
    assert summary.total_entries == 2
    assert summary.by_gate["gate-a"] == 1
