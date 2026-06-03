# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification.confidence import ProteinInferenceStrategyKind
from bijux_proteomics.identification.protein_inference_benchmarks import (
    IdentificationWorkflowClaimReview,
    ProteinInferenceBenchmarkScenarioKind,
    build_core_protein_inference_benchmark_scenarios,
    build_core_protein_inference_benchmark_suite,
    build_identification_workflow_claim_review,
    build_picked_group_fdr_benchmark_plan,
    build_protein_inference_benchmark_report,
    render_protein_inference_benchmark_assessments_tsv,
    render_protein_inference_benchmark_scenarios_tsv,
    render_protein_inference_benchmark_summary_tsv,
)


def test_core_protein_inference_benchmark_catalog_covers_goal_pressure_families() -> (
    None
):
    scenarios = build_core_protein_inference_benchmark_scenarios()

    assert len(scenarios) == 8
    assert {
        ProteinInferenceBenchmarkScenarioKind.SHARED_PEPTIDE_HEAVY,
        ProteinInferenceBenchmarkScenarioKind.ISOFORM_HEAVY,
        ProteinInferenceBenchmarkScenarioKind.HOMOLOG_FAMILY_HEAVY,
        ProteinInferenceBenchmarkScenarioKind.CONTAMINANT_HEAVY,
        ProteinInferenceBenchmarkScenarioKind.ALL_DECOY,
        ProteinInferenceBenchmarkScenarioKind.ALL_TARGET,
        ProteinInferenceBenchmarkScenarioKind.TIED_SCORE,
        ProteinInferenceBenchmarkScenarioKind.MISSING_FASTA_ENTRY,
    } == {scenario.scenario_kind for scenario in scenarios}


def test_protein_inference_benchmark_report_scores_named_pressure_families_and_ambiguity() -> (
    None
):
    reports = {
        scenario.scenario_kind: build_protein_inference_benchmark_report(scenario)
        for scenario in build_core_protein_inference_benchmark_scenarios()
    }

    homolog = reports[ProteinInferenceBenchmarkScenarioKind.HOMOLOG_FAMILY_HEAVY]
    contaminant = reports[ProteinInferenceBenchmarkScenarioKind.CONTAMINANT_HEAVY]
    decoy = reports[ProteinInferenceBenchmarkScenarioKind.ALL_DECOY]
    tied = reports[ProteinInferenceBenchmarkScenarioKind.TIED_SCORE]
    missing_fasta = reports[ProteinInferenceBenchmarkScenarioKind.MISSING_FASTA_ENTRY]

    assert homolog.homolog_family_pressure is True
    assert contaminant.contaminant_pressure is True
    assert decoy.all_decoy_pressure is True
    assert tied.tied_score_pressure is True
    assert tied.ambiguity_should_be_visible is True
    assert tied.ambiguity_exposed is True
    assert missing_fasta.missing_fasta_pressure is True
    assert missing_fasta.ambiguity_should_be_visible is True
    assert missing_fasta.ambiguity_exposed is True

    homolog_grouped = next(
        assessment
        for assessment in homolog.method_assessments
        if assessment.strategy_kind is ProteinInferenceStrategyKind.GROUPED
    )
    contaminant_grouped = next(
        assessment
        for assessment in contaminant.method_assessments
        if assessment.strategy_kind is ProteinInferenceStrategyKind.GROUPED
    )
    decoy_grouped = next(
        assessment
        for assessment in decoy.method_assessments
        if assessment.strategy_kind is ProteinInferenceStrategyKind.GROUPED
    )
    missing_fasta_parsimony = next(
        assessment
        for assessment in missing_fasta.method_assessments
        if assessment.strategy_kind is ProteinInferenceStrategyKind.PARSIMONY
    )

    assert len(homolog_grouped.false_positive_proteins) == 1
    assert homolog_grouped.false_positive_proteins[0] in {"Q22222", "Q33333"}
    assert contaminant_grouped.false_positive_proteins == ("CON__KERATIN1",)
    assert decoy_grouped.false_positive_proteins == ("DECOY_P88888", "DECOY_Q99999")
    assert missing_fasta_parsimony.selected_missing_fasta_proteins == ("P60606",)


def test_core_protein_inference_benchmark_suite_tracks_goal_case_counts_and_ledgers() -> (
    None
):
    suite = build_core_protein_inference_benchmark_suite()

    assert suite.scenario_count == 8
    assert suite.shared_peptide_scenario_count == 1
    assert suite.isoform_scenario_count == 1
    assert suite.homolog_family_scenario_count == 1
    assert suite.contaminant_scenario_count == 1
    assert suite.all_decoy_scenario_count == 1
    assert suite.all_target_scenario_count == 1
    assert suite.tied_score_scenario_count == 1
    assert suite.missing_fasta_scenario_count == 1
    assert suite.ambiguity_visible_scenario_count == 4
    assert suite.hidden_ambiguity_scenario_count == 0
    assert ProteinInferenceStrategyKind.PARSIMONY in suite.covered_strategy_kinds
    assert ProteinInferenceStrategyKind.PICKED in suite.covered_strategy_kinds

    summary_tsv = render_protein_inference_benchmark_summary_tsv(suite)
    scenarios_tsv = render_protein_inference_benchmark_scenarios_tsv(suite)
    assessments_tsv = render_protein_inference_benchmark_assessments_tsv(suite)

    assert "homolog_family_scenario_count\t1" in summary_tsv
    assert "all_decoy_scenario_count\t1" in summary_tsv
    assert "hidden_ambiguity_scenario_count\t0" in summary_tsv
    assert "homolog-family-pressure" in scenarios_tsv
    assert "contaminant-pressure" in scenarios_tsv
    assert "tied-score-ambiguity" in scenarios_tsv
    assert "missing-fasta-entry" in scenarios_tsv
    assert "scenario_id\tscenario_kind\tstrategy_kind" in assessments_tsv
    assert "false_positive_proteins" in assessments_tsv
    assert "selected_missing_fasta_proteins" in assessments_tsv


def test_picked_group_fdr_benchmark_plan_stays_explicitly_unclaimed() -> None:
    plan = build_picked_group_fdr_benchmark_plan()

    assert plan.claim_ready is False
    assert len(plan.required_scenarios) == 4
    assert "picked-group FDR" in plan.required_scenarios[0].blocked_claim


def test_identification_workflow_claim_review_refuses_workflows_without_full_case_coverage() -> (
    None
):
    partial_suite = build_core_protein_inference_benchmark_suite()
    retained_scenarios = tuple(
        scenario
        for scenario in build_core_protein_inference_benchmark_scenarios()
        if scenario.scenario_kind
        not in {
            ProteinInferenceBenchmarkScenarioKind.CONTAMINANT_HEAVY,
            ProteinInferenceBenchmarkScenarioKind.ALL_DECOY,
            ProteinInferenceBenchmarkScenarioKind.ALL_TARGET,
            ProteinInferenceBenchmarkScenarioKind.TIED_SCORE,
            ProteinInferenceBenchmarkScenarioKind.MISSING_FASTA_ENTRY,
        }
    )
    partial_suite = partial_suite.model_copy(
        update={
            "reports": tuple(
                report
                for report in partial_suite.reports
                if report.scenario_kind
                not in {
                    ProteinInferenceBenchmarkScenarioKind.CONTAMINANT_HEAVY,
                    ProteinInferenceBenchmarkScenarioKind.ALL_DECOY,
                    ProteinInferenceBenchmarkScenarioKind.ALL_TARGET,
                    ProteinInferenceBenchmarkScenarioKind.TIED_SCORE,
                    ProteinInferenceBenchmarkScenarioKind.MISSING_FASTA_ENTRY,
                }
            ),
            "scenario_ids": tuple(
                scenario.scenario_id for scenario in retained_scenarios
            ),
            "scenario_kinds": tuple(
                scenario.scenario_kind for scenario in retained_scenarios
            ),
            "scenario_count": len(retained_scenarios),
            "contaminant_scenario_count": 0,
            "all_decoy_scenario_count": 0,
            "all_target_scenario_count": 0,
            "tied_score_scenario_count": 0,
            "missing_fasta_scenario_count": 0,
        }
    )

    review: IdentificationWorkflowClaimReview = (
        build_identification_workflow_claim_review(
            workflow_id="dda-identification",
            benchmark_suite=partial_suite,
            material_loss_count=1,
            engine_disagreement_count=1,
            contaminant_risk=True,
            calibration_release_blocked=True,
        )
    )

    assert review.accepted is False
    assert "contaminant-pressure-covered" in review.refusal_reasons
    assert "decoy-pressure-covered" in review.refusal_reasons
    assert "all-target-pressure-covered" in review.refusal_reasons
    assert "tied-score-pressure-covered" in review.refusal_reasons
    assert "missing-fasta-pressure-covered" in review.refusal_reasons
    assert "material-adapter-loss-absent" in review.refusal_reasons
