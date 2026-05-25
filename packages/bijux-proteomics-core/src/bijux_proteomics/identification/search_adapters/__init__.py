# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Search-engine adapter contracts over normalized PSM parsing."""

from __future__ import annotations

from bijux_proteomics.identification.contracts import (
    CalibrationPlotData,
    FdrAuditTrail,
    PsmParseReport,
    PsmRecord,
    SearchResultColumnMapping,
    SearchResultProvenanceManifest,
    SearchResultValidationIssue,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
    build_calibration_plot_data,
    build_fdr_audit_trail,
    normalize_psm_records,
    normalize_psm_score_orientation,
    parse_psm_tsv,
    select_best_psm_per_spectrum,
)
from bijux_proteomics.identification.search_adapters.comparison import (
    assess_search_merge_compatibility,
    build_external_engine_disagreement_report,
    compare_search_result_reports,
    merge_search_result_reports,
    merge_search_result_reports_with_compatibility,
)
from bijux_proteomics.identification.search_adapters.conformance import (
    build_search_adapter_conformance_report,
    build_search_adapter_provenance_manifest,
)
from bijux_proteomics.identification.search_adapters.contracts import (
    ExternalEngineDisagreementEntry,
    ExternalEngineDisagreementKind,
    ExternalEngineDisagreementReport,
    MergedSearchSpectrumEntry,
    ScoreOrientation,
    SearchAdapterCapability,
    SearchAdapterConformanceCheck,
    SearchAdapterConformanceReport,
    SearchAdapterDialectManifest,
    SearchAdapterFieldAccounting,
    SearchAdapterKind,
    SearchAdapterManifest,
    SearchAdapterNormalizationReport,
    SearchAdapterProvenanceManifest,
    SearchConfigValidationIssue,
    SearchConfigValidationReport,
    SearchEngineObservation,
    SearchInputAssessmentReport,
    SearchInputRefusal,
    SearchInputRefusalKind,
    SearchMergeAgreementStatus,
    SearchMergeCompatibilityIssue,
    SearchMergeCompatibilityReport,
    SearchModificationDefinition,
    SearchNormalizedEvidenceEntry,
    SearchParameterComparisonReport,
    SearchParameterDifferenceEntry,
    SearchParameterReport,
    SearchRegressionCorpusEntry,
    SearchRegressionCorpusManifest,
    SearchRegressionFixtureKind,
    SearchResultComparabilityReport,
    SearchResultFamily,
    SearchResultFamilyPolicy,
    SearchResultMergeReport,
    SearchScoreFamily,
    SearchToleranceUnit,
)
from bijux_proteomics.identification.search_adapters.corpus import (
    SearchAdapterCorpusConformanceEntry,
    SearchAdapterCorpusConformanceMatrix,
    SearchCorpusInputSpecification,
    SearchCorpusNormalizationEntry,
    SearchEngineCorpusReport,
    build_search_engine_corpus_report,
)
from bijux_proteomics.identification.search_adapters.corpus_matrix import (
    build_search_adapter_corpus_conformance_matrix,
)
from bijux_proteomics.identification.search_adapters.engines.comet import (
    build_comet_output_corpus_report,
)
from bijux_proteomics.identification.search_adapters.engines.diann import (
    build_diann_output_corpus_report,
)
from bijux_proteomics.identification.search_adapters.engines.maxquant import (
    build_maxquant_output_corpus_report,
)
from bijux_proteomics.identification.search_adapters.engines.msfragger import (
    build_msfragger_output_corpus_report,
)
from bijux_proteomics.identification.search_adapters.engines.sage import (
    build_sage_output_corpus_report,
)
from bijux_proteomics.identification.search_adapters.engines.spectronaut import (
    build_spectronaut_output_corpus_report,
)
from bijux_proteomics.identification.search_adapters.family_policy import (
    build_search_result_family_policy,
)
from bijux_proteomics.identification.search_adapters.input_review import (
    assess_search_result_input,
    build_search_adapter_field_accounting,
)
from bijux_proteomics.identification.search_adapters.normalization import (
    normalize_search_results_with_adapter,
)
from bijux_proteomics.identification.search_adapters.parameter_review import (
    compare_search_parameters,
    parse_search_parameter_file,
    validate_search_parameters,
)
from bijux_proteomics.identification.search_adapters.regression import (
    build_search_adapter_regression_corpus_manifest,
)
from bijux_proteomics.identification.search_adapters.registry import (
    build_search_adapter_capability_matrix,
    get_search_adapter_manifest,
    search_adapter_dialect_registry,
    search_adapter_registry,
)

__all__ = [
    "CalibrationPlotData",
    "ExternalEngineDisagreementEntry",
    "ExternalEngineDisagreementKind",
    "ExternalEngineDisagreementReport",
    "FdrAuditTrail",
    "MergedSearchSpectrumEntry",
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
    "build_calibration_plot_data",
    "build_comet_output_corpus_report",
    "build_diann_output_corpus_report",
    "build_external_engine_disagreement_report",
    "build_fdr_audit_trail",
    "build_maxquant_output_corpus_report",
    "build_msfragger_output_corpus_report",
    "build_sage_output_corpus_report",
    "build_search_adapter_capability_matrix",
    "build_search_adapter_conformance_report",
    "build_search_adapter_corpus_conformance_matrix",
    "build_search_adapter_field_accounting",
    "build_search_adapter_provenance_manifest",
    "build_search_adapter_regression_corpus_manifest",
    "build_search_engine_corpus_report",
    "build_search_result_family_policy",
    "build_spectronaut_output_corpus_report",
    "compare_search_parameters",
    "compare_search_result_reports",
    "get_search_adapter_manifest",
    "merge_search_result_reports",
    "merge_search_result_reports_with_compatibility",
    "normalize_psm_records",
    "normalize_psm_score_orientation",
    "normalize_search_results_with_adapter",
    "parse_psm_tsv",
    "parse_search_parameter_file",
    "search_adapter_dialect_registry",
    "search_adapter_registry",
    "select_best_psm_per_spectrum",
    "validate_search_parameters",
]
