"""Machine-readable public facade contract for identification owner packages."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IdentificationFacadeBudget:
    """Budget for one durable identification facade."""

    max_public_symbols: int
    max_init_lines: int


@dataclass(frozen=True)
class IdentificationFacadeModule:
    """One owner module grouped under an identification facade."""

    owner_module: str
    export_names: tuple[str, ...]
    classification: str
    rationale: str


PSM_FACADE_BUDGET = IdentificationFacadeBudget(
    max_public_symbols=60,
    max_init_lines=70,
)
PEPTIDE_FACADE_BUDGET = IdentificationFacadeBudget(
    max_public_symbols=35,
    max_init_lines=60,
)
PROTEIN_FACADE_BUDGET = IdentificationFacadeBudget(
    max_public_symbols=90,
    max_init_lines=80,
)
FDR_FACADE_BUDGET = IdentificationFacadeBudget(
    max_public_symbols=115,
    max_init_lines=80,
)
CONTRACTS_FACADE_BUDGET = IdentificationFacadeBudget(
    max_public_symbols=140,
    max_init_lines=90,
)
ADAPTERS_FACADE_BUDGET = IdentificationFacadeBudget(
    max_public_symbols=180,
    max_init_lines=90,
)

IDENTIFICATION_OWNER_SUBMODULE_NAMES = (
    "adapters",
    "contracts",
    "fdr",
    "peptide",
    "protein",
    "psm",
)
IDENTIFICATION_COMPATIBILITY_SUBMODULE_NAMES = ("confidence",)
IDENTIFICATION_ROOT_FACADE_ORDER = (
    "adapters",
    "contracts",
    "fdr",
    "peptide",
    "protein",
    "psm",
)


def _module(
    owner_module: str,
    classification: str,
    rationale: str,
    export_names: tuple[str, ...],
) -> IdentificationFacadeModule:
    return IdentificationFacadeModule(
        owner_module=owner_module,
        export_names=export_names,
        classification=classification,
        rationale=rationale,
    )


def flatten_facade_exports(
    modules: tuple[IdentificationFacadeModule, ...],
) -> tuple[str, ...]:
    """Return the flattened export names for a facade module tuple."""

    return tuple(
        export_name
        for module in modules
        for export_name in module.export_names
    )


def build_facade_export_map(
    modules: tuple[IdentificationFacadeModule, ...],
) -> dict[str, str]:
    """Return the export-name to owner-module map for a facade module tuple."""

    return {
        export_name: module.owner_module
        for module in modules
        for export_name in module.export_names
    }


def merge_facade_export_maps(*export_owner_maps: dict[str, str]) -> dict[str, str]:
    """Merge facade export maps while preserving first-owner precedence."""

    merged: dict[str, str] = {}
    for export_owner_map in export_owner_maps:
        for export_name, owner_module in export_owner_map.items():
            merged.setdefault(export_name, owner_module)
    return merged


def list_identification_psm_api_modules() -> tuple[IdentificationFacadeModule, ...]:
    """Return the supported PSM owner-facade modules."""

    return (
        _module(
            "bijux_proteomics.identification.psm.contaminant_audit",
            "psm_audit_owner",
            "PSM contaminant audit and strategy-shift owner surface.",
            (
                "ContaminantStrategyShift",
                "ContaminantAwareProteinInferenceAudit",
                "ContaminantPeptideMatchReport",
                "build_contaminant_aware_protein_inference_audit",
                "build_contaminant_peptide_match_report",
            ),
        ),
        _module(
            "bijux_proteomics.identification.psm.contaminant_evidence",
            "psm_evidence_owner",
            "PSM contaminant evidence and burden rendering owner surface.",
            (
                "ContaminantBurdenEntry",
                "ContaminantEvidenceReport",
                "ContaminantEvidenceSummary",
                "ContaminantSeparatedPeptideEntry",
                "ContaminantSeparatedProteinEntry",
                "ContaminantSeparatedPsmEntry",
                "build_contaminant_evidence_report",
                "render_contaminant_burden_tsv",
                "render_contaminant_proteins_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.psm.generic_psm_mapper",
            "psm_mapping_owner",
            "Generic external PSM table mapping owner surface.",
            (
                "GenericPsmTableColumnMapping",
                "GenericMappedPsmRow",
                "GenericPsmMapperSummary",
                "GenericPsmMapperReport",
                "load_generic_psm_table_mapping",
                "build_generic_psm_mapper_report",
                "render_generic_psm_mapper_tsv",
                "render_generic_psm_rejected_row_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.psm.psm_features",
            "psm_feature_owner",
            "PSM feature extraction owner surface.",
            (
                "PsmFeatureRow",
                "extract_psm_features",
                "render_psm_feature_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.psm.psm_inspection",
            "psm_inspection_owner",
            "PSM evidence inspection and distribution owner surface.",
            (
                "PsmInspectionDistributionEntry",
                "PsmEvidenceInspectionReport",
                "build_psm_evidence_inspection_report",
                "render_psm_evidence_inspection_summary_tsv",
                "render_psm_inspection_distribution_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.psm.psm_rescoring",
            "psm_rescoring_owner",
            "PSM rescoring model and explanation owner surface.",
            (
                "PsmRescoringFeatureParameter",
                "PsmRescoringModel",
                "PsmRescoringEntry",
                "PsmRescoringExplanationEntry",
                "PsmRescoringSummary",
                "PsmRescoringReport",
                "fit_target_decoy_logistic_model",
                "explain_rescored_psm",
                "render_psm_rescoring_tsv",
                "render_psm_rescoring_explanation_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.psm.rejected_evidence_table",
            "psm_refusal_owner",
            "Rejected evidence table owner surface for parsed PSM rows.",
            (
                "RejectedEvidenceTableEntry",
                "build_rejected_evidence_rows_from_psm_rows",
                "build_rejected_evidence_rows_from_scientific_rows",
                "render_rejected_evidence_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.psm.score_separation_diagnostic",
            "psm_diagnostic_owner",
            "Score separation diagnostic owner surface for PSM evidence.",
            (
                "ScoreSeparationBin",
                "ScoreSeparationDiagnosticPolicy",
                "ScoreSeparationDiagnosticReport",
                "ScoreSeparationDiagnosticSummary",
                "ScoreSeparationWarningTier",
                "build_score_separation_diagnostic_report",
                "render_score_separation_bins_tsv",
                "render_score_separation_summary_tsv",
            ),
        ),
    )


def list_identification_peptide_api_modules() -> tuple[IdentificationFacadeModule, ...]:
    """Return the supported peptide owner-facade modules."""

    return (
        _module(
            "bijux_proteomics.identification.peptide.cross_run_reproducibility",
            "peptide_reproducibility_owner",
            "Cross-run reproducibility owner for peptide and protein evidence.",
            (
                "CrossRunEntityType",
                "CrossRunReproducibilityClass",
                "CrossRunReproducibilityEntry",
                "CrossRunReproducibilityReport",
                "CrossRunReproducibilitySummary",
                "RunDetectionContext",
                "build_peptide_cross_run_reproducibility_report",
                "build_protein_cross_run_reproducibility_report",
                "render_cross_run_reproducibility_entries_tsv",
                "render_cross_run_reproducibility_summary_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.peptide.error_rate_annotation",
            "peptide_annotation_owner",
            "Error-rate annotation owner for PSM-derived peptide evidence.",
            (
                "ErrorRateProvenanceFlag",
                "PsmErrorRateAnnotationEntry",
                "PsmErrorRateAnnotationPolicy",
                "PsmErrorRateAnnotationReport",
                "PsmErrorRateAnnotationSummary",
                "annotate_psm_error_rates",
                "build_psm_error_rate_annotation_report",
                "render_psm_error_rate_annotation_summary_tsv",
                "render_psm_error_rate_annotation_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.peptide.peptide_evidence",
            "peptide_evidence_owner",
            "Peptide evidence owner surface.",
            (
                "PeptideEvidenceClass",
                "PeptideEvidenceEntry",
                "PeptideEvidenceReport",
                "PeptideEvidenceSummary",
                "PeptideEvidenceTag",
                "build_peptide_evidence_report",
                "render_peptide_evidence_entries_tsv",
                "render_peptide_evidence_summary_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.peptide.peptide_evidence_review",
            "peptide_review_owner",
            "Peptide evidence review owner surface.",
            (
                "PeptideEvidencePrimaryClass",
                "PeptideEvidenceReviewEntry",
                "PeptideEvidenceReviewReport",
                "PeptideEvidenceReviewSummary",
                "build_peptide_evidence_review_report",
            ),
        ),
    )


def list_identification_protein_api_modules() -> tuple[IdentificationFacadeModule, ...]:
    """Return the supported protein owner-facade modules."""

    return (
        _module(
            "bijux_proteomics.identification.protein.parsimony_review",
            "protein_review_owner",
            "Parsimony review owner surface.",
            (
                "ParsimonyReviewSummary",
                "ParsimonyReviewProteinEntry",
                "ParsimonyAmbiguityEntry",
                "ParsimonyReviewReport",
                "build_parsimony_review_report",
                "render_parsimony_review_summary_tsv",
                "render_parsimony_review_proteins_tsv",
                "render_parsimony_review_ambiguities_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.protein.protein_ambiguity_review",
            "protein_review_owner",
            "Protein ambiguity review owner surface.",
            (
                "ProteinAmbiguityReviewSummary",
                "ProteinAmbiguityReviewEntry",
                "ProteinAmbiguityReviewReport",
                "build_protein_ambiguity_review_report",
                "render_protein_ambiguity_summary_tsv",
                "render_protein_ambiguity_entries_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.protein.protein_coverage",
            "protein_coverage_owner",
            "Protein coverage owner surface.",
            (
                "ProteinCoverageCoordinateStatus",
                "ProteinCoverageSummary",
                "ProteinCoverageProteinEntry",
                "ProteinCoverageRegionEntry",
                "ProteinCoverageUncoveredRegionEntry",
                "ProteinCoveragePeptideCoordinateEntry",
                "ProteinCoverageReport",
                "build_protein_coverage_report",
                "render_protein_coverage_summary_tsv",
                "render_protein_coverage_entries_tsv",
                "render_protein_coverage_regions_tsv",
                "render_protein_coverage_uncovered_regions_tsv",
                "render_protein_coverage_peptide_coordinates_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.protein.protein_coverage_review",
            "protein_coverage_owner",
            "Protein coverage review owner surface.",
            (
                "ProteinCoverageReviewEntry",
                "ProteinCoverageReviewReport",
                "ProteinCoverageReviewSummary",
                "build_protein_coverage_review_report",
            ),
        ),
        _module(
            "bijux_proteomics.identification.protein.protein_coverage_visualization",
            "protein_visualization_owner",
            "Protein coverage visualization owner surface.",
            (
                "ProteinCoveragePlotEntry",
                "ProteinCoveragePlotTrack",
                "ProteinCoveragePlotUnmatchedEntry",
                "ProteinCoveragePlotSummary",
                "ProteinCoveragePlotReport",
                "build_protein_coverage_plot_report",
                "render_protein_coverage_plot_positions_tsv",
                "render_protein_coverage_plot_svg",
                "render_protein_coverage_plot_html",
            ),
        ),
        _module(
            "bijux_proteomics.identification.protein.protein_evidence",
            "protein_evidence_owner",
            "Protein evidence owner surface.",
            (
                "ProteinEvidenceTier",
                "ProteinEvidenceDowngradeReason",
                "ProteinEvidenceEntry",
                "ProteinEvidenceSummary",
                "ProteinEvidenceReport",
                "build_protein_evidence_report",
                "render_protein_evidence_summary_tsv",
                "render_protein_evidence_entries_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.protein.protein_evidence_review",
            "protein_evidence_owner",
            "Protein evidence review owner surface.",
            (
                "ProteinEvidenceReviewEntry",
                "ProteinEvidenceReviewReport",
                "ProteinEvidenceReviewSummary",
                "build_protein_evidence_review_report",
            ),
        ),
        _module(
            "bijux_proteomics.identification.protein.protein_grouping",
            "protein_grouping_owner",
            "Protein grouping owner surface.",
            (
                "ProteinGroupingSummary",
                "ProteinGroupingEntry",
                "ProteinGroupingReport",
                "build_protein_grouping_report",
                "render_protein_grouping_summary_tsv",
                "render_protein_grouping_entries_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.protein.protein_grouping_review",
            "protein_grouping_owner",
            "Protein grouping review owner surface.",
            ("build_protein_grouping_review_report",),
        ),
        _module(
            "bijux_proteomics.identification.protein.protein_inference_benchmarks",
            "protein_benchmark_owner",
            "Protein inference benchmark owner surface.",
            (
                "ProteinInferenceBenchmarkScenarioKind",
                "ProteinInferenceBenchmarkScenario",
                "ProteinInferenceMethodAssessment",
                "ProteinInferenceBenchmarkReport",
                "ProteinInferenceBenchmarkSuiteReport",
                "PickedGroupBenchmarkPressure",
                "PickedGroupFdrBenchmarkScenarioPlan",
                "PickedGroupFdrBenchmarkPlan",
                "WorkflowTrustCriterionResult",
                "IdentificationWorkflowClaimReview",
                "build_core_protein_inference_benchmark_scenarios",
                "build_protein_inference_benchmark_report",
                "build_protein_inference_benchmark_suite",
                "build_core_protein_inference_benchmark_suite",
                "render_protein_inference_benchmark_summary_tsv",
                "render_protein_inference_benchmark_scenarios_tsv",
                "render_protein_inference_benchmark_assessments_tsv",
                "build_picked_group_fdr_benchmark_plan",
                "build_identification_workflow_claim_review",
            ),
        ),
        _module(
            "bijux_proteomics.identification.protein.protein_parsimony",
            "protein_parsimony_owner",
            "Protein parsimony owner surface.",
            (
                "ProteinParsimonySummary",
                "ProteinParsimonyProteinEntry",
                "ProteinParsimonyAmbiguityEntry",
                "ProteinParsimonyReport",
                "build_protein_parsimony_report",
                "render_protein_parsimony_summary_tsv",
                "render_protein_parsimony_proteins_tsv",
                "render_protein_parsimony_ambiguities_tsv",
            ),
        ),
    )


def list_identification_fdr_api_modules() -> tuple[IdentificationFacadeModule, ...]:
    """Return the supported FDR owner-facade modules."""

    return (
        _module(
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
        _module(
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
        _module(
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
        _module(
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
        _module(
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
        _module(
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
        _module(
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
        _module(
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
        _module(
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
        _module(
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
        _module(
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


def list_identification_contract_api_modules() -> tuple[IdentificationFacadeModule, ...]:
    """Return the supported identification contract-facade modules."""

    return (
        _module(
            "bijux_proteomics.identification.contracts.psm",
            "identification_contract_owner",
            "Canonical PSM contract owner surface.",
            (
                "TargetDecoyLabel",
                "TargetDecoyContaminantClass",
                "PsmSortField",
                "SearchResultColumnMapping",
                "TargetDecoyLabelPolicy",
                "TargetDecoyContaminantClassification",
                "PsmRecord",
                "SearchResultValidationIssue",
                "RejectedPsmRow",
                "PsmParseReport",
                "TargetDecoyCollisionEntry",
                "TargetDecoyCollisionReport",
                "DecoyStrategyValidationIssue",
                "DecoyStrategyValidationReport",
                "classify_target_decoy_contaminant",
                "is_biological_foreground_class",
                "validate_target_decoy_policy",
                "parse_target_decoy_label",
                "validate_target_decoy_accession_collisions",
            ),
        ),
        _module(
            "bijux_proteomics.identification.contracts.psm_io",
            "identification_contract_owner",
            "PSM parsing and export contract owner surface.",
            (
                "parse_psm_tsv",
                "parse_psm_tsv_chunked",
                "normalize_psm_records",
                "export_psm_jsonl",
                "export_psm_tsv",
                "sort_psm_records",
                "select_best_psm_per_spectrum",
            ),
        ),
        _module(
            "bijux_proteomics.identification.contracts.evidence",
            "identification_contract_owner",
            "Peptide and protein evidence rollup contract owner surface.",
            (
                "PeptideEvidenceEntry",
                "ProteinEvidenceEntry",
                "PsmSummaryReport",
                "PeptideSummaryReport",
                "ProteinSummaryEntry",
                "ProteinSummaryReport",
                "rollup_peptide_evidence",
                "rollup_protein_evidence",
                "build_psm_summary_report",
                "build_peptide_summary_report",
                "build_protein_summary_report",
            ),
        ),
        _module(
            "bijux_proteomics.identification.contracts.confidence",
            "identification_contract_owner",
            "Confidence assignment contract owner surface.",
            (
                "ConfidenceLabel",
                "ConfidenceAssignment",
                "GroupedConfidenceEntry",
                "GroupedConfidenceReport",
                "LevelSpecificConfidenceAssignment",
                "LevelSpecificConfidenceReport",
                "ConfidenceThresholdSensitivityEntry",
                "ConfidenceThresholdSensitivityReport",
                "assign_confidence_labels",
                "build_grouped_confidence_report",
                "assign_level_specific_confidence_labels",
                "build_confidence_threshold_sensitivity_report",
            ),
        ),
        _module(
            "bijux_proteomics.identification.contracts.fdr_levels",
            "identification_contract_owner",
            "Level-specific and grouped FDR contract owner surface.",
            (
                "LevelSpecificFdrReport",
                "FdrQValueMonotonicityCheck",
                "FdrQValueMonotonicityReport",
                "FdrEvidenceLevel",
                "FdrLevelEntry",
                "GroupedFdrBucket",
                "GroupedFdrReport",
                "NormalizedScoreEntry",
                "AcceptedPsmProvenanceEntry",
                "AcceptedPsmProvenanceReport",
                "build_accepted_psm_provenance_report",
                "calculate_level_specific_fdr",
                "calculate_grouped_fdr",
                "calculate_basic_target_decoy_fdr",
                "normalize_psm_score_orientation",
                "verify_fdr_q_value_monotonicity",
            ),
        ),
        _module(
            "bijux_proteomics.identification.contracts.grouping",
            "identification_contract_owner",
            "Grouping and razor-peptide contract owner surface.",
            (
                "SharedPeptideAmbiguityReason",
                "ProteinGroupEntry",
                "SharedPeptideAmbiguityEntry",
                "SharedPeptideAmbiguityReport",
                "RazorPeptideAssignment",
                "RazorPeptideProvenanceEntry",
                "RazorPeptideProvenanceReport",
                "build_protein_groups",
                "build_shared_peptide_ambiguity_report",
                "assign_razor_peptides",
                "build_razor_peptide_provenance_report",
            ),
        ),
        _module(
            "bijux_proteomics.identification.contracts.protein_inference",
            "identification_contract_owner",
            "Protein inference contract owner surface.",
            (
                "ParsimonyVariant",
                "ParsimonyProteinEntry",
                "InferenceDisagreementKind",
                "InferenceDisagreementEntry",
                "InferenceDisagreementReport",
                "ParsimonyVariantResult",
                "ParsimonyVariantDifferenceEntry",
                "ParsimonyVariantComparisonReport",
                "build_inference_disagreement_report",
                "infer_proteins_by_parsimony",
                "compare_parsimony_variants",
            ),
        ),
        _module(
            "bijux_proteomics.identification.contracts.protein_review",
            "identification_contract_owner",
            "Protein review contract owner surface.",
            (
                "CombinedEvidenceQuantSupport",
                "CombinedEvidenceEntry",
                "CombinedEvidenceReport",
                "PeptideProteinTraceEntry",
                "PeptideProteinTraceReport",
                "ProteinCoverageEntry",
                "DatabasePeptideUniqueness",
                "DatabasePeptideUniquenessEntry",
                "PickedProteinFdrEntry",
                "build_combined_evidence_report",
                "build_peptide_protein_trace_report",
                "export_peptide_protein_trace_jsonl",
                "export_peptide_protein_trace_tsv",
                "build_protein_coverage_map",
                "build_peptide_uniqueness_across_database",
                "calculate_picked_protein_fdr",
            ),
        ),
        _module(
            "bijux_proteomics.identification.contracts.score_fdr",
            "identification_contract_owner",
            "Score and audit contract owner surface for FDR outputs.",
            (
                "FdrPolicy",
                "FdrAnnotatedPsm",
                "CalibrationPlotBin",
                "CalibrationPlotData",
                "ScoreOrientationAdvisoryCandidate",
                "ScoreOrientationAdvisory",
                "FdrAuditEntry",
                "FdrAuditTrail",
                "FdrEdgeCaseKind",
                "FdrEdgeCaseReport",
                "ConfidenceCalibrationLevel",
                "ConfidenceCalibrationEntry",
                "ConfidenceCalibrationReport",
                "detect_score_orientation_advisory",
                "build_confidence_calibration_report",
                "build_calibration_plot_data",
                "build_fdr_edge_case_report",
                "compute_fdr_reproducibility_hash",
                "build_fdr_audit_trail",
                "apply_q_values",
                "filter_psms_by_fdr",
            ),
        ),
        _module(
            "bijux_proteomics.identification.contracts.review",
            "identification_contract_owner",
            "Review-bundle contract owner surface for identification outputs.",
            (
                "SearchResultProvenanceManifest",
                "ReviewReadyEvidenceBundle",
                "PtmIdentificationObservation",
                "PtmIdentificationConfidenceIssue",
                "PtmIdentificationConfidenceEntry",
                "PtmIdentificationConfidenceReport",
                "validate_ptm_identification_confidence",
                "build_review_ready_evidence_bundle",
                "export_review_ready_evidence_bundle",
                "write_review_ready_evidence_bundle",
                "build_search_result_provenance_manifest",
            ),
        ),
    )


def list_identification_adapter_api_modules() -> tuple[IdentificationFacadeModule, ...]:
    """Return the supported identification adapter-facade modules."""

    return (
        _module(
            "bijux_proteomics.identification.adapters.comet_import",
            "adapter_import_owner",
            "Comet import owner surface.",
            (
                "CometImportKind",
                "CometPsmReviewEntry",
                "CometCanonicalPsmEntry",
                "CometImportSummary",
                "CometImportReport",
                "build_comet_import_report",
                "render_comet_summary_tsv",
                "render_comet_canonical_psm_tsv",
                "render_comet_psm_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.adapters.diann_import",
            "adapter_import_owner",
            "DIA-NN import owner surface.",
            (
                "DiaNnPrecursorReviewEntry",
                "DiaNnProteinGroupReviewEntry",
                "DiaNnImportSummary",
                "DiaNnRejectedRowEntry",
                "DiaNnBundleImportReport",
                "build_diann_import_report",
                "render_diann_summary_tsv",
                "render_diann_precursor_tsv",
                "render_diann_protein_group_tsv",
                "render_diann_rejected_row_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.adapters.fragpipe_benchmarks",
            "adapter_benchmark_owner",
            "FragPipe import benchmark owner surface.",
            (
                "FragpipeCountComparisonEntry",
                "FragpipeImportBenchmarkReport",
                "FragpipeImportBenchmarkSummary",
                "FragpipeProteinGroupComparison",
                "FragpipeQValueBehaviorComparison",
                "FragpipeQValueComparisonEntry",
                "build_fragpipe_import_benchmark_report",
                "render_fragpipe_benchmark_summary_tsv",
                "render_fragpipe_count_comparisons_tsv",
                "render_fragpipe_protein_group_comparison_tsv",
                "render_fragpipe_q_value_comparison_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.adapters.fragpipe_import",
            "adapter_import_owner",
            "FragPipe import owner surface.",
            (
                "FragpipePsmReviewEntry",
                "FragpipeCanonicalPsmEntry",
                "FragpipePeptideReviewEntry",
                "FragpipeProteinReviewEntry",
                "FragpipeOpenSearchEvidenceEntry",
                "FragpipeProteinQuantityEntry",
                "FragpipeImportSummary",
                "FragpipeImportReport",
                "build_fragpipe_import_report",
                "render_fragpipe_summary_tsv",
                "render_fragpipe_canonical_psm_tsv",
                "render_fragpipe_psm_tsv",
                "render_fragpipe_peptide_tsv",
                "render_fragpipe_protein_tsv",
                "render_fragpipe_open_search_evidence_tsv",
                "render_fragpipe_protein_quantity_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.adapters.maxquant_import",
            "adapter_import_owner",
            "MaxQuant import owner surface.",
            (
                "MaxquantLfqIntensityEntry",
                "MaxquantEvidenceReviewEntry",
                "MaxquantPeptideReviewEntry",
                "MaxquantProteinGroupReviewEntry",
                "MaxquantLfqMatrixCandidateEntry",
                "MaxquantImportSummary",
                "MaxquantImportReport",
                "build_maxquant_import_report",
                "render_maxquant_summary_tsv",
                "render_maxquant_evidence_tsv",
                "render_maxquant_peptide_tsv",
                "render_maxquant_protein_group_tsv",
                "render_maxquant_lfq_candidate_tsv",
                "build_maxquant_lfq_matrix_candidates",
            ),
        ),
        _module(
            "bijux_proteomics.identification.adapters.openms_import",
            "adapter_import_owner",
            "OpenMS import owner surface.",
            (
                "OpenMsPsmReviewEntry",
                "OpenMsProteinReviewEntry",
                "OpenMsFeatureReviewEntry",
                "OpenMsFeatureValidationIssue",
                "OpenMsRejectedFeatureRow",
                "OpenMsImportSummary",
                "OpenMsFeatureParseSummary",
                "OpenMsImportReport",
                "build_openms_import_report",
                "render_openms_summary_tsv",
                "render_openms_psm_tsv",
                "render_openms_protein_tsv",
                "render_openms_feature_tsv",
                "render_openms_rejected_feature_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.adapters.sage_import",
            "adapter_import_owner",
            "Sage import owner surface.",
            (
                "SagePsmReviewEntry",
                "SageCanonicalPsmEntry",
                "SageImportSummary",
                "SageImportReport",
                "build_sage_import_report",
                "render_sage_summary_tsv",
                "render_sage_canonical_psm_tsv",
                "render_sage_psm_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.adapters.search_adapter_loss",
            "adapter_review_owner",
            "Search-adapter loss and parity owner surface.",
            (
                "SearchAdapterInformationLossReport",
                "ProteinInferenceDisagreementEntry",
                "ProteinInferenceEngineDisagreementDossier",
                "SearchAdapterParityCheck",
                "SearchAdapterParityReport",
                "build_search_adapter_information_loss_report",
                "build_protein_inference_engine_disagreement_dossier",
                "build_search_adapter_parity_report",
            ),
        ),
        _module(
            "bijux_proteomics.identification.adapters.spectronaut_import",
            "adapter_import_owner",
            "Spectronaut import owner surface.",
            (
                "SpectronautPrecursorReviewEntry",
                "SpectronautProteinGroupReviewEntry",
                "SpectronautPrecursorQuantityEntry",
                "SpectronautProteinGroupQuantityEntry",
                "SpectronautImportSummary",
                "SpectronautImportReport",
                "build_spectronaut_import_report",
                "render_spectronaut_summary_tsv",
                "render_spectronaut_precursor_tsv",
                "render_spectronaut_protein_group_tsv",
                "render_spectronaut_precursor_quantity_tsv",
                "render_spectronaut_protein_group_quantity_tsv",
            ),
        ),
        _module(
            "bijux_proteomics.identification.search_adapters",
            "search_adapter_owner",
            "Typed search-adapter family facade for normalized search-result workflows.",
            (
                "CalibrationPlotData",
                "FdrAuditTrail",
                "PsmParseReport",
                "PsmRecord",
                "ScoreOrientation",
                "SearchAdapterCapability",
                "SearchAdapterConformanceCheck",
                "SearchAdapterConformanceReport",
                "SearchAdapterCorpusConformanceEntry",
                "SearchAdapterCorpusConformanceMatrix",
                "SearchAdapterDialectManifest",
                "SearchAdapterFieldAccounting",
                "SearchAdapterKind",
                "SearchAdapterManifest",
                "SearchAdapterNormalizationReport",
                "SearchAdapterProvenanceManifest",
                "SearchConfigValidationIssue",
                "SearchConfigValidationReport",
                "SearchCorpusInputSpecification",
                "SearchCorpusNormalizationEntry",
                "SearchEngineCorpusReport",
                "SearchEngineObservation",
                "SearchInputAssessmentReport",
                "SearchInputRefusal",
                "SearchInputRefusalKind",
                "SearchMergeAgreementStatus",
                "SearchMergeCompatibilityIssue",
                "SearchMergeCompatibilityReport",
                "SearchModificationDefinition",
                "SearchNormalizedEvidenceEntry",
                "SearchParameterComparisonReport",
                "SearchParameterDifferenceEntry",
                "SearchParameterReport",
                "SearchRegressionCorpusEntry",
                "SearchRegressionCorpusManifest",
                "SearchRegressionFixtureKind",
                "SearchResultColumnMapping",
                "SearchResultComparabilityReport",
                "SearchResultFamily",
                "SearchResultFamilyPolicy",
                "SearchResultMergeReport",
                "SearchResultProvenanceManifest",
                "SearchResultValidationIssue",
                "SearchScoreFamily",
                "SearchToleranceUnit",
                "TargetDecoyLabel",
                "TargetDecoyLabelPolicy",
                "assess_search_merge_compatibility",
                "assess_search_result_input",
                "build_search_adapter_capability_matrix",
                "build_search_adapter_conformance_report",
                "build_search_adapter_corpus_conformance_matrix",
                "build_search_adapter_provenance_manifest",
                "build_search_adapter_regression_corpus_manifest",
                "build_search_result_family_policy",
                "compare_search_parameters",
                "compare_search_result_reports",
                "get_search_adapter_manifest",
                "merge_search_result_reports",
                "merge_search_result_reports_with_compatibility",
                "normalize_search_results_with_adapter",
                "parse_psm_tsv",
                "parse_search_parameter_file",
                "search_adapter_dialect_registry",
                "search_adapter_registry",
                "validate_search_parameters",
                "build_comet_output_corpus_report",
                "build_diann_output_corpus_report",
                "build_external_engine_disagreement_report",
                "build_maxquant_output_corpus_report",
                "build_msfragger_output_corpus_report",
                "build_sage_output_corpus_report",
                "build_search_engine_corpus_report",
                "build_spectronaut_output_corpus_report",
            ),
        ),
    )


__all__ = [
    "ADAPTERS_FACADE_BUDGET",
    "IDENTIFICATION_COMPATIBILITY_SUBMODULE_NAMES",
    "IDENTIFICATION_ROOT_FACADE_ORDER",
    "CONTRACTS_FACADE_BUDGET",
    "FDR_FACADE_BUDGET",
    "IDENTIFICATION_OWNER_SUBMODULE_NAMES",
    "PEPTIDE_FACADE_BUDGET",
    "PROTEIN_FACADE_BUDGET",
    "PSM_FACADE_BUDGET",
    "IdentificationFacadeBudget",
    "IdentificationFacadeModule",
    "build_facade_export_map",
    "merge_facade_export_maps",
    "flatten_facade_exports",
    "list_identification_adapter_api_modules",
    "list_identification_contract_api_modules",
    "list_identification_fdr_api_modules",
    "list_identification_peptide_api_modules",
    "list_identification_protein_api_modules",
    "list_identification_psm_api_modules",
]
