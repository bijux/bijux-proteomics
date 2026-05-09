# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification.confidence import ProteinInferenceStrategyKind
from bijux_proteomics.identification.contracts import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.protein_inference_benchmarks import (
    IdentificationWorkflowClaimReview,
    ProteinInferenceBenchmarkScenario,
    ProteinInferenceBenchmarkScenarioKind,
    build_identification_workflow_claim_review,
    build_picked_group_fdr_benchmark_plan,
    build_protein_inference_benchmark_report,
    build_protein_inference_benchmark_suite,
)


def _shared_peptide_heavy_scenario() -> ProteinInferenceBenchmarkScenario:
    return ProteinInferenceBenchmarkScenario(
        scenario_id="shared-peptide-pressure",
        scenario_kind=ProteinInferenceBenchmarkScenarioKind.SHARED_PEPTIDE_HEAVY,
        records=(
            PsmRecord(
                spectrum_id="s001",
                peptide="UNIQUEP1",
                canonical_peptide="UNIQUEP1",
                charge=2,
                score=120.0,
                q_value=0.001,
                protein_refs=("P11111",),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
            PsmRecord(
                spectrum_id="s002",
                peptide="SHAREDK",
                canonical_peptide="SHAREDK",
                charge=2,
                score=115.0,
                q_value=0.002,
                protein_refs=("P11111", "P22222"),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
            PsmRecord(
                spectrum_id="s003",
                peptide="UNIQUEP3",
                canonical_peptide="UNIQUEP3",
                charge=2,
                score=110.0,
                q_value=0.003,
                protein_refs=("P33333",),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
        ),
        expected_present_proteins=("P11111", "P33333"),
        expected_absent_proteins=("P22222",),
        note="One absent protein is attractive only because it shares peptide support.",
    )


def _isoform_heavy_scenario() -> ProteinInferenceBenchmarkScenario:
    return ProteinInferenceBenchmarkScenario(
        scenario_id="isoform-pressure",
        scenario_kind=ProteinInferenceBenchmarkScenarioKind.ISOFORM_HEAVY,
        records=(
            PsmRecord(
                spectrum_id="i001",
                peptide="ISOFORM1K",
                canonical_peptide="ISOFORM1K",
                charge=2,
                score=130.0,
                q_value=0.001,
                protein_refs=("P55555-1",),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
            PsmRecord(
                spectrum_id="i002",
                peptide="SHAREDISO",
                canonical_peptide="SHAREDISO",
                charge=2,
                score=118.0,
                q_value=0.002,
                protein_refs=("P55555-1", "P55555-2"),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
        ),
        expected_present_proteins=("P55555-1",),
        expected_absent_proteins=("P55555-2",),
        note="Isoform-specific support should keep the silent sibling isoform out.",
    )


def _false_negative_pressure_scenario() -> ProteinInferenceBenchmarkScenario:
    return ProteinInferenceBenchmarkScenario(
        scenario_id="false-negative-pressure",
        scenario_kind=ProteinInferenceBenchmarkScenarioKind.FALSE_NEGATIVE_PRESSURE,
        records=(
            PsmRecord(
                spectrum_id="f001",
                peptide="ANCHORP1",
                canonical_peptide="ANCHORP1",
                charge=2,
                score=125.0,
                q_value=0.001,
                protein_refs=("P10101",),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
            PsmRecord(
                spectrum_id="f002",
                peptide="BRIDGEP",
                canonical_peptide="BRIDGEP",
                charge=2,
                score=112.0,
                q_value=0.003,
                protein_refs=("P10101", "P20202"),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
        ),
        expected_present_proteins=("P10101", "P20202"),
        expected_absent_proteins=(),
        note="A conservative unique-only view should show explicit false-negative pressure.",
    )


def test_protein_inference_benchmark_report_scores_shared_peptide_pressure() -> None:
    report = build_protein_inference_benchmark_report(_shared_peptide_heavy_scenario())

    assert report.shared_peptide_pressure is True
    assert report.isoform_pressure is False
    by_kind = {entry.strategy_kind: entry for entry in report.method_assessments}
    assert ProteinInferenceStrategyKind.GROUPED in by_kind
    assert by_kind[ProteinInferenceStrategyKind.GROUPED].false_positive_proteins == (
        "P22222",
    )
    assert by_kind[ProteinInferenceStrategyKind.GROUPED].precision_interval_low < 1.0


def test_protein_inference_benchmark_report_scores_isoform_pressure() -> None:
    report = build_protein_inference_benchmark_report(_isoform_heavy_scenario())

    assert report.isoform_pressure is True
    grouped = next(
        entry
        for entry in report.method_assessments
        if entry.strategy_kind is ProteinInferenceStrategyKind.GROUPED
    )
    assert grouped.false_positive_proteins == ("P55555-2",)


def test_protein_inference_benchmark_suite_tracks_false_negative_pressure() -> None:
    suite = build_protein_inference_benchmark_suite(
        (
            _shared_peptide_heavy_scenario(),
            _isoform_heavy_scenario(),
            _false_negative_pressure_scenario(),
        )
    )

    assert suite.scenario_count == 3
    assert ProteinInferenceStrategyKind.PARSIMONY in suite.covered_strategy_kinds
    assert ProteinInferenceStrategyKind.PICKED in suite.covered_strategy_kinds
    assert suite.worst_precision_lower_bound <= 1.0
    assert suite.worst_recall_lower_bound < 1.0


def test_picked_group_fdr_benchmark_plan_stays_explicitly_unclaimed() -> None:
    plan = build_picked_group_fdr_benchmark_plan()

    assert plan.claim_ready is False
    assert len(plan.required_scenarios) == 4
    assert "picked-group FDR" in plan.required_scenarios[0].blocked_claim


def test_identification_workflow_claim_review_refuses_unproven_workflows() -> None:
    suite = build_protein_inference_benchmark_suite((_shared_peptide_heavy_scenario(),))

    review: IdentificationWorkflowClaimReview = (
        build_identification_workflow_claim_review(
            workflow_id="dda-identification",
            benchmark_suite=suite,
            material_loss_count=1,
            engine_disagreement_count=1,
            contaminant_risk=True,
            calibration_release_blocked=True,
        )
    )

    assert review.accepted is False
    assert "isoform-pressure-covered" in review.refusal_reasons
    assert "material-adapter-loss-absent" in review.refusal_reasons
