"""Machine-readable public facade contract for identification owner packages."""

from __future__ import annotations

from bijux_proteomics.identification.facade_ledger import (
    ADAPTERS_FACADE_BUDGET,
    CONTRACTS_FACADE_BUDGET,
    FDR_FACADE_BUDGET,
    IdentificationFacadeBudget,
    IdentificationFacadeModule,
    PEPTIDE_FACADE_BUDGET,
    PROTEIN_FACADE_BUDGET,
    PSM_FACADE_BUDGET,
    build_facade_export_map,
    flatten_facade_exports,
    list_identification_adapter_api_modules,
    list_identification_contract_api_modules,
    list_identification_fdr_api_modules,
    list_identification_peptide_api_modules,
    list_identification_protein_api_modules,
    list_identification_psm_api_modules,
    merge_facade_export_maps,
)
from bijux_proteomics.identification.search_adapters.public_api import (
    build_search_adapter_export_owner_map,
)

IDENTIFICATION_OWNER_SUBMODULE_NAMES = (
    "adapters",
    "contracts",
    "fdr",
    "peptide",
    "protein",
    "psm",
    "search_adapters",
)
IDENTIFICATION_COMPATIBILITY_SUBMODULE_NAMES = ("confidence",)
IDENTIFICATION_ROOT_FACADE_ORDER = (
    "adapters",
    "search_adapters",
    "contracts",
    "fdr",
    "peptide",
    "protein",
    "psm",
)
IDENTIFICATION_ROOT_SUBMODULES = {
    "adapters": "bijux_proteomics.identification.adapters",
    "confidence": "bijux_proteomics.identification.confidence",
    "contracts": "bijux_proteomics.identification.contracts",
    "fdr": "bijux_proteomics.identification.fdr",
    "peptide": "bijux_proteomics.identification.peptide",
    "protein": "bijux_proteomics.identification.protein",
    "psm": "bijux_proteomics.identification.psm",
    "search_adapters": "bijux_proteomics.identification.search_adapters",
}

IDENTIFICATION_ROOT_SEARCH_ADAPTER_EXCLUDED_EXPORTS = (
    "ExternalEngineDisagreementEntry",
    "ExternalEngineDisagreementKind",
    "ExternalEngineDisagreementReport",
    "SearchAdapterCapability",
    "SearchAdapterDialectManifest",
    "SearchAdapterFieldAccounting",
    "SearchAdapterManifest",
    "SearchAdapterNormalizationReport",
    "SearchEngineObservation",
    "SearchAdapterCorpusConformanceEntry",
    "SearchAdapterCorpusConformanceMatrix",
    "SearchAdapterConformanceReport",
    "SearchAdapterProvenanceManifest",
    "SearchConfigValidationIssue",
    "SearchConfigValidationReport",
    "SearchCorpusInputSpecification",
    "SearchCorpusNormalizationEntry",
    "SearchEngineCorpusReport",
    "SearchInputAssessmentReport",
    "SearchInputRefusal",
    "SearchInputRefusalKind",
    "SearchMergeAgreementStatus",
    "SearchMergeCompatibilityIssue",
    "SearchMergeCompatibilityReport",
    "SearchParameterComparisonReport",
    "SearchParameterDifferenceEntry",
    "SearchParameterReport",
    "SearchRegressionCorpusEntry",
    "SearchRegressionCorpusManifest",
    "SearchResultFamily",
    "SearchResultFamilyPolicy",
    "SearchScoreFamily",
    "SearchToleranceUnit",
    "assess_search_merge_compatibility",
    "assess_search_result_input",
    "build_comet_output_corpus_report",
    "build_diann_output_corpus_report",
    "build_maxquant_output_corpus_report",
    "build_msfragger_output_corpus_report",
    "build_sage_output_corpus_report",
    "build_search_adapter_capability_matrix",
    "build_search_adapter_corpus_conformance_matrix",
    "build_search_adapter_conformance_report",
    "build_search_adapter_field_accounting",
    "build_search_adapter_provenance_manifest",
    "build_search_adapter_regression_corpus_manifest",
    "build_external_engine_disagreement_report",
    "build_search_engine_corpus_report",
    "build_search_result_family_policy",
    "build_spectronaut_output_corpus_report",
    "compare_search_parameters",
    "compare_search_result_reports",
    "get_search_adapter_manifest",
    "merge_search_result_reports",
    "merge_search_result_reports_with_compatibility",
    "normalize_search_results_with_adapter",
    "parse_search_parameter_file",
    "search_adapter_dialect_registry",
    "search_adapter_registry",
    "validate_search_parameters",
)


def build_identification_root_search_adapter_export_owner_map() -> dict[str, str]:
    """Return the root-visible search-adapter exports after root exclusions."""

    export_owner_map = build_search_adapter_export_owner_map()
    return {
        export_name: owner_module
        for export_name, owner_module in export_owner_map.items()
        if export_name not in IDENTIFICATION_ROOT_SEARCH_ADAPTER_EXCLUDED_EXPORTS
    }


def build_identification_root_export_owner_map() -> dict[str, str]:
    """Return the governed root export-owner map for identification."""

    return merge_facade_export_maps(
        build_facade_export_map(list_identification_adapter_api_modules()),
        build_identification_root_search_adapter_export_owner_map(),
        build_facade_export_map(list_identification_contract_api_modules()),
        build_facade_export_map(list_identification_fdr_api_modules()),
        build_facade_export_map(list_identification_peptide_api_modules()),
        build_facade_export_map(list_identification_protein_api_modules()),
        build_facade_export_map(list_identification_psm_api_modules()),
    )


def list_identification_root_export_names() -> tuple[str, ...]:
    """Return the ordered governed root export names for identification."""

    return tuple(build_identification_root_export_owner_map())


__all__ = [
    "ADAPTERS_FACADE_BUDGET",
    "IDENTIFICATION_COMPATIBILITY_SUBMODULE_NAMES",
    "IDENTIFICATION_ROOT_FACADE_ORDER",
    "IDENTIFICATION_ROOT_SEARCH_ADAPTER_EXCLUDED_EXPORTS",
    "IDENTIFICATION_ROOT_SUBMODULES",
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
    "build_identification_root_export_owner_map",
    "build_identification_root_search_adapter_export_owner_map",
    "list_identification_adapter_api_modules",
    "list_identification_contract_api_modules",
    "list_identification_fdr_api_modules",
    "list_identification_peptide_api_modules",
    "list_identification_protein_api_modules",
    "list_identification_psm_api_modules",
    "list_identification_root_export_names",
]
