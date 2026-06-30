# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility target ledgers for governed workflow facade wrappers."""

from __future__ import annotations


WORKFLOW_ROOT_OWNER_FILES = frozenset(
    {
        "__init__.py",
        "facade_benchmark_catalog.py",
        "blueprint.py",
        "facade_catalog.py",
        "facade_pipeline_catalog.py",
        "facade_runtime.py",
        "facade_targets.py",
        "public_api.py",
        "result_types.py",
    }
)

WORKFLOW_ROOT_WRAPPER_TARGETS = {
    "artifact_layout.py": "bijux_proteomics.workflow.exports.artifact_layout",
    "biological_report_assembly.py": (
        "bijux_proteomics.workflow.reports.biological_report_assembly"
    ),
    "biological_report_claims.py": (
        "bijux_proteomics.workflow.reports.biological_report_claims"
    ),
    "biological_report_html.py": (
        "bijux_proteomics.workflow.reports.biological_report_html"
    ),
    "biological_report_html_support.py": (
        "bijux_proteomics.workflow.reports.biological_report_html_support"
    ),
    "biological_report_models.py": (
        "bijux_proteomics.workflow.reports.biological_report_models"
    ),
    "biological_report_ranking.py": (
        "bijux_proteomics.workflow.reports.biological_report_ranking"
    ),
    "biological_report_rendering.py": (
        "bijux_proteomics.workflow.reports.biological_report_rendering"
    ),
    "biological_report_section_confidence.py": (
        "bijux_proteomics.workflow.reports.biological_report_section_confidence"
    ),
    "biological_report_selection.py": (
        "bijux_proteomics.workflow.reports.biological_report_selection"
    ),
    "biological_reporting.py": "bijux_proteomics.workflow.reports.biological_reporting",
    "biological_result_graph.py": (
        "bijux_proteomics.workflow.reports.biological_result_graph"
    ),
    "cohort_stratification.py": (
        "bijux_proteomics.workflow.studies.cohort_stratification"
    ),
    "cross_species_effect_comparison.py": (
        "bijux_proteomics.workflow.studies.cross_species_effect_comparison"
    ),
    "cross_study_effect_comparison.py": (
        "bijux_proteomics.workflow.studies.cross_study_effect_comparison"
    ),
    "cross_study_evidence_cards.py": (
        "bijux_proteomics.workflow.cards.cross_study_evidence_cards"
    ),
    "cross_study_meta_analysis.py": (
        "bijux_proteomics.workflow.studies.cross_study_meta_analysis"
    ),
    "cross_study_pathway_comparison.py": (
        "bijux_proteomics.workflow.studies.cross_study_pathway_comparison"
    ),
    "cross_study_protein_harmonization.py": (
        "bijux_proteomics.workflow.studies.cross_study_protein_harmonization"
    ),
    "diann_benchmarks.py": "bijux_proteomics.workflow.benchmarks.diann_benchmarks",
    "interactive_result_bundle.py": (
        "bijux_proteomics.workflow.exports.interactive_result_bundle"
    ),
    "interactive_result_comparison.py": (
        "bijux_proteomics.workflow.exports.interactive_result_comparison"
    ),
    "maxquant_benchmarks.py": (
        "bijux_proteomics.workflow.benchmarks.maxquant_benchmarks"
    ),
    "mechanisms.py": "bijux_proteomics.workflow.cards.mechanisms",
    "output_validation.py": "bijux_proteomics.workflow.exports.output_validation",
    "protein_evidence_cards.py": (
        "bijux_proteomics.workflow.cards.protein_evidence_cards"
    ),
    "protein_mechanism_cards.py": (
        "bijux_proteomics.workflow.cards.protein_mechanism_cards"
    ),
    "public_benchmark_descriptors.py": (
        "bijux_proteomics.workflow.benchmarks.public_benchmark_descriptors"
    ),
    "public_benchmark_subset.py": (
        "bijux_proteomics.workflow.benchmarks.public_benchmark_subset"
    ),
    "public_dataset_comparison.py": (
        "bijux_proteomics.workflow.studies.public_dataset_comparison"
    ),
    "result_archive.py": "bijux_proteomics.workflow.exports.result_archive",
    "result_manifest.py": "bijux_proteomics.workflow.exports.result_manifest",
    "result_search_index.py": "bijux_proteomics.workflow.exports.result_search_index",
    "scale_demo.py": "bijux_proteomics.workflow.pipelines.scale_demo",
    "study_result.py": "bijux_proteomics.workflow.studies.study_result",
    "synthetic_quant_truth.py": (
        "bijux_proteomics.workflow.benchmarks.synthetic_quant_truth"
    ),
    "targeted_review_workflow.py": (
        "bijux_proteomics.workflow.exports.targeted_review_workflow"
    ),
    "weak_evidence.py": "bijux_proteomics.workflow.pipelines.weak_evidence",
}

WORKFLOW_BENCHMARK_ROOT_OWNER_FILES = frozenset({"__init__.py"})

WORKFLOW_BENCHMARK_WRAPPER_TARGETS = {
    "diann_benchmarks.py": (
        "bijux_proteomics.workflow.benchmarks.fidelity.diann_benchmarks"
    ),
    "maxquant_benchmarks.py": (
        "bijux_proteomics.workflow.benchmarks.fidelity.maxquant_benchmarks"
    ),
    "public_benchmark_descriptors.py": (
        "bijux_proteomics.workflow.benchmarks.datasets.public_benchmark_descriptors"
    ),
    "public_benchmark_subset.py": (
        "bijux_proteomics.workflow.benchmarks.datasets.public_benchmark_subset"
    ),
    "synthetic_quant_truth.py": (
        "bijux_proteomics.workflow.benchmarks.synthetic.synthetic_quant_truth"
    ),
}

WORKFLOW_ROOT_PIPELINE_WRAPPER_TARGETS = {
    "advanced_workflow_family.py": (
        "bijux_proteomics.workflow.pipelines.advanced_workflow_family"
    ),
    "advanced_diann.py": "bijux_proteomics.workflow.pipelines.advanced_diann",
    "advanced_fragpipe.py": "bijux_proteomics.workflow.pipelines.advanced_fragpipe",
    "advanced_maxquant.py": "bijux_proteomics.workflow.pipelines.advanced_maxquant",
    "advanced_ptm.py": "bijux_proteomics.workflow.pipelines.advanced_ptm",
    "advanced_targeted.py": "bijux_proteomics.workflow.pipelines.advanced_targeted",
    "advanced_tmt.py": "bijux_proteomics.workflow.pipelines.advanced_tmt",
    "dda_biological_workflow.py": (
        "bijux_proteomics.workflow.pipelines.dda_biological_workflow"
    ),
    "dia_dda_comparison.py": (
        "bijux_proteomics.workflow.pipelines.dia_dda_comparison"
    ),
    "dia_differential_analysis.py": (
        "bijux_proteomics.workflow.pipelines.dia_differential_analysis"
    ),
    "diann_biological_workflow.py": (
        "bijux_proteomics.workflow.pipelines.diann_biological_workflow"
    ),
    "discovery_to_assay.py": "bijux_proteomics.workflow.pipelines.discovery_to_assay",
    "flagship_run.py": "bijux_proteomics.workflow.pipelines.flagship_run",
    "integrated_scientific_report.py": (
        "bijux_proteomics.workflow.pipelines.integrated_scientific_report"
    ),
    "label_based_differential_analysis.py": (
        "bijux_proteomics.workflow.pipelines.label_based_differential_analysis"
    ),
    "label_based_reporting.py": (
        "bijux_proteomics.workflow.pipelines.label_based_reporting"
    ),
    "maxquant_biological_workflow.py": (
        "bijux_proteomics.workflow.pipelines.maxquant_biological_workflow"
    ),
    "multi_study.py": "bijux_proteomics.workflow.pipelines.multi_study",
    "orchestrator.py": "bijux_proteomics.workflow.pipelines.orchestrator",
    "ptm_site_workflow.py": "bijux_proteomics.workflow.pipelines.ptm_site_workflow",
    "public_benchmark_runner.py": (
        "bijux_proteomics.workflow.pipelines.public_benchmark_runner"
    ),
    "scale_demo.py": "bijux_proteomics.workflow.pipelines.scale_demo",
    "surprising_demo.py": "bijux_proteomics.workflow.pipelines.surprising_demo",
    "surprising_demo_interrogation.py": (
        "bijux_proteomics.workflow.pipelines.surprising_demo_interrogation"
    ),
    "tmt_experiment_workflow.py": (
        "bijux_proteomics.workflow.pipelines.tmt_experiment_workflow"
    ),
    "trust_bundle.py": "bijux_proteomics.workflow.pipelines.trust_bundle",
    "weak_evidence.py": "bijux_proteomics.workflow.pipelines.weak_evidence",
}

WORKFLOW_PIPELINE_DEMO_WRAPPER_TARGETS = {
    "scale_demo.py": "bijux_proteomics.workflow.demo.scale_demo",
    "surprising_demo.py": "bijux_proteomics.workflow.demo.surprising_demo",
    "surprising_demo_interrogation.py": (
        "bijux_proteomics.workflow.demo.surprising_demo_interrogation"
    ),
}

WORKFLOW_PIPELINE_ADVANCED_WRAPPER_TARGETS = {
    "advanced_diann.py": (
        "bijux_proteomics.workflow.pipelines.advanced.advanced_diann"
    ),
    "advanced_fragpipe.py": (
        "bijux_proteomics.workflow.pipelines.advanced.advanced_fragpipe"
    ),
    "advanced_maxquant.py": (
        "bijux_proteomics.workflow.pipelines.advanced.advanced_maxquant"
    ),
    "advanced_ptm.py": "bijux_proteomics.workflow.pipelines.advanced.advanced_ptm",
    "advanced_targeted.py": (
        "bijux_proteomics.workflow.pipelines.advanced.advanced_targeted"
    ),
    "advanced_tmt.py": "bijux_proteomics.workflow.pipelines.advanced.advanced_tmt",
    "advanced_workflow_family.py": (
        "bijux_proteomics.workflow.pipelines.advanced.advanced_workflow_family"
    ),
}

WORKFLOW_PIPELINE_ENGINE_WRAPPER_TARGETS = {
    "dda_biological_workflow.py": (
        "bijux_proteomics.workflow.pipelines.engines.dda_biological_workflow"
    ),
    "diann_biological_workflow.py": (
        "bijux_proteomics.workflow.pipelines.engines.diann_biological_workflow"
    ),
    "label_based_reporting.py": (
        "bijux_proteomics.workflow.pipelines.engines.label_based_reporting"
    ),
    "maxquant_biological_workflow.py": (
        "bijux_proteomics.workflow.pipelines.engines.maxquant_biological_workflow"
    ),
    "ptm_site_workflow.py": (
        "bijux_proteomics.workflow.pipelines.engines.ptm_site_workflow"
    ),
    "tmt_experiment_workflow.py": (
        "bijux_proteomics.workflow.pipelines.engines.tmt_experiment_workflow"
    ),
}


__all__ = [
    "WORKFLOW_BENCHMARK_ROOT_OWNER_FILES",
    "WORKFLOW_BENCHMARK_WRAPPER_TARGETS",
    "WORKFLOW_PIPELINE_ADVANCED_WRAPPER_TARGETS",
    "WORKFLOW_PIPELINE_DEMO_WRAPPER_TARGETS",
    "WORKFLOW_PIPELINE_ENGINE_WRAPPER_TARGETS",
    "WORKFLOW_ROOT_OWNER_FILES",
    "WORKFLOW_ROOT_PIPELINE_WRAPPER_TARGETS",
    "WORKFLOW_ROOT_WRAPPER_TARGETS",
]
