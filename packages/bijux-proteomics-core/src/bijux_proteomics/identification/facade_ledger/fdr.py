# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed FDR facade ledger for identification owner modules."""

from __future__ import annotations

from bijux_proteomics.identification.facade_ledger.models import (
    IdentificationFacadeBudget,
    IdentificationFacadeModule,
    build_facade_module,
)

FDR_FACADE_BUDGET = IdentificationFacadeBudget(
    max_public_symbols=115,
    max_init_lines=80,
)


def list_identification_fdr_api_modules() -> tuple[IdentificationFacadeModule, ...]:
    """Return the supported FDR owner-facade modules."""

    return (
        build_facade_module(
            "bijux_proteomics.identification.fdr.calibration_benchmarks",
            "fdr_calibration_owner",
            "Adapter calibration benchmark owner surface.",
            (
                "AdapterCalibrationBenchmarkEntry",
                "AdapterCalibrationBenchmarkInput",
                "AdapterCalibrationBenchmarkSuiteReport",
                "build_adapter_calibration_benchmark_suite",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.fdr.calibration_drift",
            "fdr_calibration_owner",
            "Calibration drift and release-gate owner surface.",
            (
                "CalibrationAcceptanceComparison",
                "CalibrationDriftBinDelta",
                "CalibrationReleaseAlert",
                "CalibrationReleaseAlertSeverity",
                "CalibrationReleaseGateReport",
                "CalibrationSnapshotBin",
                "CalibrationDriftReport",
                "EmpiricalCalibrationSnapshot",
                "build_calibration_drift_report",
                "build_calibration_release_gate_report",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.fdr.confidence",
            "fdr_confidence_owner",
            "Confidence, strategy, and stress-case owner surface for FDR.",
            (
                "TargetDecoyStrategyKind",
                "TargetDecoyStrategyDefinition",
                "TargetDecoyStrategyRegistry",
                "build_target_decoy_strategy_registry",
                "EmpiricalScoreCalibrationBin",
                "EmpiricalScoreCalibrationReport",
                "build_empirical_score_calibration_report",
                "EntrapmentEvaluationReport",
                "build_entrapment_evaluation_report",
                "FdrStressScenarioKind",
                "FdrStressTrustState",
                "FdrStressCaseReport",
                "build_fdr_stress_case_report",
                "ProteinInferenceStrategyKind",
                "ProteinInferenceStrategySelection",
                "ProteinInferenceStrategyComparisonEntry",
                "ProteinInferenceStrategyComparisonReport",
                "compare_protein_inference_strategies",
                "PsmPeptideProteinTraceBundle",
                "build_psm_peptide_protein_trace_bundle",
                "write_psm_peptide_protein_trace_bundle",
                "export_psm_peptide_protein_trace_bundle",
                "ConfidenceThresholdBundleEntry",
                "ConfidenceThresholdSensitivityBundle",
                "build_confidence_threshold_sensitivity_bundle",
                "GroupedConfidenceCategory",
                "GroupedConfidenceSummaryEntry",
                "GroupedConfidenceSummaryReport",
                "build_grouped_confidence_summary_report",
                "CustomDecoyValidationReport",
                "validate_custom_decoy_strategy",
                "ConfidenceResultFamily",
                "LibrarySearchConfidenceBoundaryInput",
                "LibrarySearchConfidenceBoundaryIssue",
                "LibrarySearchConfidenceBoundaryReport",
                "evaluate_library_search_confidence_boundary",
                "DiaFdrRefusalIssue",
                "DiaFdrThresholdSnapshot",
                "DiaNativeFdrModelReport",
                "build_dia_native_fdr_model_report",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.fdr.evidence_level_fdr_review",
            "fdr_review_owner",
            "Evidence-level FDR review owner surface.",
            (
                "EvidenceLevelFdrThresholdSummary",
                "EvidenceLevelFdrAcceptedEntry",
                "EvidenceLevelFdrReviewReport",
                "build_evidence_level_fdr_review_report",
                "render_evidence_level_fdr_summary_tsv",
                "render_evidence_level_fdr_entries_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.fdr.peptide_target_decoy_fdr",
            "fdr_policy_owner",
            "Peptide target-decoy FDR owner surface.",
            (
                "PeptideFdrEvidence",
                "PeptideTargetDecoyFdrPolicy",
                "PeptideTargetDecoyFdrEntry",
                "PeptideTargetDecoyFdrSummary",
                "PeptideTargetDecoyFdrReport",
                "collapse_peptide_fdr_evidence",
                "build_peptide_target_decoy_fdr_report",
                "render_peptide_target_decoy_fdr_tsv",
                "render_peptide_target_decoy_fdr_summary_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.fdr.picked_protein_fdr",
            "fdr_policy_owner",
            "Picked protein FDR owner surface.",
            (
                "PickedProteinFdrPolicy",
                "PickedProteinPairEntry",
                "PickedProteinFdrSummary",
                "PickedProteinFdrReport",
                "build_picked_protein_fdr_report",
                "build_picked_protein_fdr_report_from_psm_records",
                "render_picked_protein_pair_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.fdr.picked_protein_fdr_review",
            "fdr_review_owner",
            "Picked protein FDR review owner surface.",
            (
                "PickedProteinFdrThresholdSummary",
                "PickedProteinFdrReviewEntry",
                "PickedProteinFdrReviewReport",
                "build_picked_protein_fdr_review_report",
                "render_picked_protein_fdr_summary_tsv",
                "render_picked_protein_fdr_entries_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.fdr.protein_target_decoy_fdr",
            "fdr_policy_owner",
            "Protein target-decoy FDR owner surface.",
            (
                "ProteinTargetDecoyFdrPolicy",
                "ProteinTargetDecoyFdrEntry",
                "ProteinTargetDecoyFdrSummary",
                "ProteinTargetDecoyFdrReport",
                "build_protein_target_decoy_fdr_report",
                "render_protein_target_decoy_fdr_tsv",
                "render_protein_target_decoy_fdr_summary_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.fdr.psm_target_decoy_fdr",
            "fdr_policy_owner",
            "PSM target-decoy FDR owner surface.",
            (
                "PsmTargetDecoyFdrPolicy",
                "PsmTargetDecoyFdrEntry",
                "PsmTargetDecoyFdrSummary",
                "PsmTargetDecoyFdrReport",
                "build_psm_target_decoy_fdr_report",
                "render_psm_target_decoy_fdr_tsv",
                "render_psm_target_decoy_fdr_summary_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.fdr.target_decoy_benchmarks",
            "fdr_benchmark_owner",
            "Target-decoy calibration benchmark owner surface.",
            (
                "TargetDecoyCalibrationBenchmarkInput",
                "TargetDecoyCalibrationBenchmarkEntry",
                "TargetDecoyCalibrationBenchmarkReport",
                "build_target_decoy_calibration_benchmark_report",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.fdr.target_decoy_reference_validation",
            "fdr_reference_owner",
            "Target-decoy reference validation owner surface.",
            (
                "TargetDecoyReferenceExpectation",
                "TargetDecoyReferenceCase",
                "TargetDecoyReferenceValidationEntry",
                "TargetDecoyReferenceCaseReport",
                "TargetDecoyReferenceValidationReport",
                "build_target_decoy_reference_validation_report",
                "render_target_decoy_reference_summary_tsv",
                "render_target_decoy_reference_entries_tsv",
            ),
        ),
    )


__all__ = ["FDR_FACADE_BUDGET", "list_identification_fdr_api_modules"]
