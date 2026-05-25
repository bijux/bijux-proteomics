"""Scientific workflow blueprints, planning, and runtime reports."""

from __future__ import annotations

from importlib import import_module

_WORKFLOW_EXPORT_MODULES = (
    "bijux_proteomics.workflow.blueprint",
    "bijux_proteomics.workflow.advanced_fragpipe",
    "bijux_proteomics.workflow.advanced_maxquant",
    "bijux_proteomics.workflow.advanced_ptm",
    "bijux_proteomics.workflow.advanced_targeted",
    "bijux_proteomics.workflow.advanced_tmt",
    "bijux_proteomics.workflow.artifact_layout",
    "bijux_proteomics.workflow.biological_reporting",
    "bijux_proteomics.workflow.biological_result_graph",
    "bijux_proteomics.workflow.advanced_diann",
    "bijux_proteomics.workflow.cohort_stratification",
    "bijux_proteomics.workflow.cross_study_effect_comparison",
    "bijux_proteomics.workflow.cross_study_evidence_cards",
    "bijux_proteomics.workflow.cross_study_meta_analysis",
    "bijux_proteomics.workflow.cross_study_pathway_comparison",
    "bijux_proteomics.workflow.cross_study_protein_harmonization",
    "bijux_proteomics.workflow.cross_species_effect_comparison",
    "bijux_proteomics.workflow.discovery_to_assay",
    "bijux_proteomics.workflow.dda_biological_workflow",
    "bijux_proteomics.workflow.diann_benchmarks",
    "bijux_proteomics.workflow.diann_biological_workflow",
    "bijux_proteomics.workflow.flagship_run",
    "bijux_proteomics.workflow.interactive_result_comparison",
    "bijux_proteomics.workflow.interactive_result_bundle",
    "bijux_proteomics.workflow.integrated_scientific_report",
    "bijux_proteomics.workflow.maxquant_benchmarks",
    "bijux_proteomics.workflow.maxquant_biological_workflow",
    "bijux_proteomics.workflow.mechanisms",
    "bijux_proteomics.workflow.multi_study",
    "bijux_proteomics.workflow.orchestrator",
    "bijux_proteomics.workflow.ptm_site_workflow",
    "bijux_proteomics.workflow.protein_evidence_cards",
    "bijux_proteomics.workflow.protein_mechanism_cards",
    "bijux_proteomics.workflow.public_benchmark_descriptors",
    "bijux_proteomics.workflow.public_benchmark_subset",
    "bijux_proteomics.workflow.public_benchmark_runner",
    "bijux_proteomics.workflow.public_dataset_comparison",
    "bijux_proteomics.workflow.result_archive",
    "bijux_proteomics.workflow.result_manifest",
    "bijux_proteomics.workflow.result_search_index",
    "bijux_proteomics.workflow.result_types",
    "bijux_proteomics.workflow.study_result",
    "bijux_proteomics.workflow.surprising_demo",
    "bijux_proteomics.workflow.surprising_demo_interrogation",
    "bijux_proteomics.workflow.synthetic_quant_truth",
    "bijux_proteomics.workflow.targeted_review_workflow",
    "bijux_proteomics.workflow.tmt_experiment_workflow",
    "bijux_proteomics.workflow.trust_bundle",
    "bijux_proteomics.workflow.dia_differential_analysis",
    "bijux_proteomics.workflow.dia_dda_comparison",
    "bijux_proteomics.workflow.label_based_differential_analysis",
    "bijux_proteomics.workflow.label_based_reporting",
)


def __getattr__(name: str) -> object:
    for module_path in _WORKFLOW_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
