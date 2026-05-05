# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics_lab


def test_design_public_api_contains_expected_exports() -> None:
    assert "AssayLifecycleStage" in bijux_proteomics_lab.__all__
    assert "CandidateFollowUpSignal" in bijux_proteomics_lab.__all__
    assert "CandidateHandoffValidation" in bijux_proteomics_lab.__all__
    assert "CandidateLabAdvancementDecision" in bijux_proteomics_lab.__all__
    assert "CandidatePrioritySignal" in bijux_proteomics_lab.__all__
    assert "ExecutionCapacityAdvisory" in bijux_proteomics_lab.__all__
    assert "FollowUpPracticalityReport" in bijux_proteomics_lab.__all__
    assert "ExecutionPlanUncertaintyReport" in bijux_proteomics_lab.__all__
    assert "ExperimentDesignStructureSummary" in bijux_proteomics_lab.__all__
    assert "EvidenceNeedWetLabAction" in bijux_proteomics_lab.__all__
    assert "LabExecutionRequest" in bijux_proteomics_lab.__all__
    assert "LabPriorityQueueAlignment" in bijux_proteomics_lab.__all__
    assert "InstrumentAvailability" in bijux_proteomics_lab.__all__
    assert "LabReviewPacketBundle" in bijux_proteomics_lab.__all__
    assert "OperationalReadinessReport" in bijux_proteomics_lab.__all__
    assert "OperationalFollowUpPath" in bijux_proteomics_lab.__all__
    assert "TargetedBenchmarkReport" in bijux_proteomics_lab.__all__
    assert "TargetedFailureRehearsalReport" in bijux_proteomics_lab.__all__
    assert "TargetedExternalReviewReport" in bijux_proteomics_lab.__all__
    assert "SamplePreparationMetadata" in bijux_proteomics_lab.__all__
    assert "SampleTrackingPlateAdvisory" in bijux_proteomics_lab.__all__
    assert "TargetedTransitionReview" in bijux_proteomics_lab.__all__
    assert "InstrumentMethodMetadata" in bijux_proteomics_lab.__all__
    assert "LimsExportBundle" in bijux_proteomics_lab.__all__
    assert "ReplicationStrategySummary" in bijux_proteomics_lab.__all__
    assert "WorkflowReadinessStep" in bijux_proteomics_lab.__all__
    assert "WorkflowReadinessSummary" in bijux_proteomics_lab.__all__
    assert "validate_experiment_design" in bijux_proteomics_lab.__all__
    assert "assess_assay_risk" in bijux_proteomics_lab.__all__
    assert "build_power_analysis_advisory" in bijux_proteomics_lab.__all__
    assert "plan_batch_randomization" in bijux_proteomics_lab.__all__
    assert "build_fractionation_plan" in bijux_proteomics_lab.__all__
    assert "build_follow_up_practicality_report" in bijux_proteomics_lab.__all__
    assert "build_lims_export_bundle" in bijux_proteomics_lab.__all__
    assert "build_targeted_benchmark_report" in bijux_proteomics_lab.__all__
    assert "build_targeted_failure_rehearsal" in bijux_proteomics_lab.__all__
    assert "build_targeted_external_review_report" in bijux_proteomics_lab.__all__
    assert "build_targeted_operator_run_report" in bijux_proteomics_lab.__all__
    assert "build_operational_follow_up_path" in bijux_proteomics_lab.__all__
    assert "plan_multiplex_labeling" in bijux_proteomics_lab.__all__
    assert "plan_spike_in_qc_samples" in bijux_proteomics_lab.__all__
    assert "assess_carryover_risk" in bijux_proteomics_lab.__all__
    assert "build_lab_protocol_evidence_bundle" in bijux_proteomics_lab.__all__
    assert "build_operational_readiness_report" in bijux_proteomics_lab.__all__
    assert "build_protocol_attachment" in bijux_proteomics_lab.__all__
    assert "refuse_irresponsible_assay_handoff" in bijux_proteomics_lab.__all__
    assert "review_targeted_transition_candidates" in bijux_proteomics_lab.__all__
    assert "validate_candidate_follow_up_handoff" in bijux_proteomics_lab.__all__
    assert "summarize_workflow_readiness" in bijux_proteomics_lab.__all__
