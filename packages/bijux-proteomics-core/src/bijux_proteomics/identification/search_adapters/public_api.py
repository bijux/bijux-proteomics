# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed public facade contract for search-adapter owner modules."""

from __future__ import annotations

from bijux_proteomics.identification.facade_ledger.models import (
    IdentificationFacadeBudget,
)

SEARCH_ADAPTER_FACADE_BUDGET = IdentificationFacadeBudget(
    max_public_symbols=100,
    max_init_lines=40,
)

_SEARCH_ADAPTER_PUBLIC_EXPORTS: tuple[tuple[str, str], ...] = (
    ("CalibrationPlotData", "bijux_proteomics.identification.contracts"),
    ("ExternalEngineDisagreementEntry", "bijux_proteomics.identification.search_adapters.contracts"),
    ("ExternalEngineDisagreementKind", "bijux_proteomics.identification.search_adapters.contracts"),
    ("ExternalEngineDisagreementReport", "bijux_proteomics.identification.search_adapters.contracts"),
    ("FdrAuditTrail", "bijux_proteomics.identification.contracts"),
    ("MergedSearchSpectrumEntry", "bijux_proteomics.identification.search_adapters.contracts"),
    ("PsmParseReport", "bijux_proteomics.identification.contracts"),
    ("PsmRecord", "bijux_proteomics.identification.contracts"),
    ("ScoreOrientation", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchAdapterCapability", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchAdapterConformanceCheck", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchAdapterConformanceReport", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchAdapterCorpusConformanceEntry", "bijux_proteomics.identification.search_adapters.corpus"),
    ("SearchAdapterCorpusConformanceMatrix", "bijux_proteomics.identification.search_adapters.corpus"),
    ("SearchAdapterDialectManifest", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchAdapterFieldAccounting", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchAdapterKind", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchAdapterManifest", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchAdapterNormalizationReport", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchAdapterProvenanceManifest", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchConfigValidationIssue", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchConfigValidationReport", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchCorpusInputSpecification", "bijux_proteomics.identification.search_adapters.corpus"),
    ("SearchCorpusNormalizationEntry", "bijux_proteomics.identification.search_adapters.corpus"),
    ("SearchEngineCorpusReport", "bijux_proteomics.identification.search_adapters.corpus"),
    ("SearchEngineObservation", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchInputAssessmentReport", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchInputRefusal", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchInputRefusalKind", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchMergeAgreementStatus", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchMergeCompatibilityIssue", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchMergeCompatibilityReport", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchModificationDefinition", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchNormalizedEvidenceEntry", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchParameterComparisonReport", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchParameterDifferenceEntry", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchParameterReport", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchRegressionCorpusEntry", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchRegressionCorpusManifest", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchRegressionFixtureKind", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchResultColumnMapping", "bijux_proteomics.identification.contracts"),
    ("SearchResultComparabilityReport", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchResultFamily", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchResultFamilyPolicy", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchResultMergeReport", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchResultProvenanceManifest", "bijux_proteomics.identification.contracts"),
    ("SearchResultValidationIssue", "bijux_proteomics.identification.contracts"),
    ("SearchScoreFamily", "bijux_proteomics.identification.search_adapters.contracts"),
    ("SearchToleranceUnit", "bijux_proteomics.identification.search_adapters.contracts"),
    ("TargetDecoyLabel", "bijux_proteomics.identification.contracts"),
    ("TargetDecoyLabelPolicy", "bijux_proteomics.identification.contracts"),
    ("assess_search_merge_compatibility", "bijux_proteomics.identification.search_adapters.comparison"),
    ("assess_search_result_input", "bijux_proteomics.identification.search_adapters.input_review"),
    ("build_calibration_plot_data", "bijux_proteomics.identification.contracts"),
    ("build_comet_output_corpus_report", "bijux_proteomics.identification.search_adapters.engines.comet"),
    ("build_diann_output_corpus_report", "bijux_proteomics.identification.search_adapters.engines.diann"),
    ("build_external_engine_disagreement_report", "bijux_proteomics.identification.search_adapters.comparison"),
    ("build_fdr_audit_trail", "bijux_proteomics.identification.contracts"),
    ("build_maxquant_output_corpus_report", "bijux_proteomics.identification.search_adapters.engines.maxquant"),
    ("build_msfragger_output_corpus_report", "bijux_proteomics.identification.search_adapters.engines.msfragger"),
    ("build_sage_output_corpus_report", "bijux_proteomics.identification.search_adapters.engines.sage"),
    ("build_search_adapter_capability_matrix", "bijux_proteomics.identification.search_adapters.registry"),
    ("build_search_adapter_conformance_report", "bijux_proteomics.identification.search_adapters.conformance"),
    ("build_search_adapter_corpus_conformance_matrix", "bijux_proteomics.identification.search_adapters.corpus_matrix"),
    ("build_search_adapter_field_accounting", "bijux_proteomics.identification.search_adapters.input_review"),
    ("build_search_adapter_provenance_manifest", "bijux_proteomics.identification.search_adapters.conformance"),
    ("build_search_adapter_regression_corpus_manifest", "bijux_proteomics.identification.search_adapters.regression"),
    ("build_search_engine_corpus_report", "bijux_proteomics.identification.search_adapters.corpus"),
    ("build_search_result_family_policy", "bijux_proteomics.identification.search_adapters.family_policy"),
    ("build_spectronaut_output_corpus_report", "bijux_proteomics.identification.search_adapters.engines.spectronaut"),
    ("compare_search_parameters", "bijux_proteomics.identification.search_adapters.parameter_review"),
    ("compare_search_result_reports", "bijux_proteomics.identification.search_adapters.comparison"),
    ("get_search_adapter_manifest", "bijux_proteomics.identification.search_adapters.registry"),
    ("merge_search_result_reports", "bijux_proteomics.identification.search_adapters.comparison"),
    ("merge_search_result_reports_with_compatibility", "bijux_proteomics.identification.search_adapters.comparison"),
    ("normalize_psm_records", "bijux_proteomics.identification.contracts"),
    ("normalize_psm_score_orientation", "bijux_proteomics.identification.contracts"),
    ("normalize_search_results_with_adapter", "bijux_proteomics.identification.search_adapters.normalization"),
    ("parse_psm_tsv", "bijux_proteomics.identification.contracts"),
    ("parse_psm_tsv_chunked", "bijux_proteomics.identification.contracts"),
    ("parse_search_parameter_file", "bijux_proteomics.identification.search_adapters.parameter_review"),
    ("search_adapter_dialect_registry", "bijux_proteomics.identification.search_adapters.registry"),
    ("search_adapter_registry", "bijux_proteomics.identification.search_adapters.registry"),
    ("select_best_psm_per_spectrum", "bijux_proteomics.identification.contracts"),
    ("validate_search_parameters", "bijux_proteomics.identification.search_adapters.parameter_review"),
)


def build_search_adapter_export_owner_map() -> dict[str, str]:
    """Return the governed export-owner map for the search-adapter facade."""

    export_owner_map: dict[str, str] = {}
    for export_name, owner_module in _SEARCH_ADAPTER_PUBLIC_EXPORTS:
        if export_name in export_owner_map:
            raise ValueError(f"duplicate search-adapter export: {export_name}")
        export_owner_map[export_name] = owner_module
    return export_owner_map


def list_search_adapter_export_names() -> tuple[str, ...]:
    """Return ordered governed export names for the search-adapter facade."""

    return tuple(export_name for export_name, _owner in _SEARCH_ADAPTER_PUBLIC_EXPORTS)


__all__ = [
    "SEARCH_ADAPTER_FACADE_BUDGET",
    "build_search_adapter_export_owner_map",
    "list_search_adapter_export_names",
]
