# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pipeline facade ledgers that define the workflow compatibility surface."""

from __future__ import annotations

from bijux_proteomics.workflow.facade_catalog import (
    WorkflowFacadeOwner,
    copy_facade_owners,
    facade_owner_modules,
    select_facade_owners,
)


ADVANCED_PIPELINE_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module=(
            "bijux_proteomics.workflow.pipelines.advanced.advanced_workflow_family"
        ),
        rationale="advanced workflow family ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced.advanced_diann",
        rationale="advanced DIA-NN pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced.advanced_fragpipe",
        rationale="advanced FragPipe pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module=("bijux_proteomics.workflow.pipelines.advanced.advanced_maxquant"),
        rationale="advanced MaxQuant pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced.advanced_ptm",
        rationale="advanced PTM pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced.advanced_targeted",
        rationale="advanced targeted pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced.advanced_tmt",
        rationale="advanced TMT pipeline ownership",
    ),
)

WORKFLOW_ROOT_ADVANCED_PIPELINE_HELPER_EXPORTS = (
    "render_advanced_diann_protein_decisions_tsv",
    "render_advanced_diann_workflow_summary_tsv",
    "render_advanced_fragpipe_discrepancy_tsv",
    "render_advanced_fragpipe_peptide_evidence_tsv",
    "render_advanced_fragpipe_workflow_summary_tsv",
    "render_advanced_maxquant_peptide_contributions_tsv",
    "render_advanced_maxquant_workflow_summary_tsv",
    "render_advanced_ptm_excluded_ambiguity_tsv",
    "render_advanced_ptm_workflow_summary_tsv",
    "render_advanced_targeted_evidence_cards_tsv",
    "render_advanced_targeted_workflow_summary_tsv",
    "render_advanced_tmt_evidence_cards_tsv",
    "render_advanced_tmt_peptide_confidence_tsv",
    "render_advanced_tmt_protein_compression_tsv",
    "render_advanced_tmt_workflow_summary_tsv",
)

WORKFLOW_ROOT_ADVANCED_PIPELINE_VALIDATION_EXPORTS = (
    "validate_advanced_workflow_family_contract",
)

WORKFLOW_ROOT_ADVANCED_PIPELINE_OWNERS = copy_facade_owners(
    ADVANCED_PIPELINE_FACADE_OWNERS,
    excluded_exports=WORKFLOW_ROOT_ADVANCED_PIPELINE_HELPER_EXPORTS,
)

ENGINE_PIPELINE_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.engines.dda_biological_workflow",
        rationale="DDA biological workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.engines.diann_biological_workflow",
        rationale="DIA-NN biological workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.engines.label_based_reporting",
        rationale="label-based reporting workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module=(
            "bijux_proteomics.workflow.pipelines.engines.maxquant_biological_workflow"
        ),
        rationale="MaxQuant biological workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.engines.ptm_site_workflow",
        rationale="PTM site workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.engines.tmt_experiment_workflow",
        rationale="TMT experiment workflow ownership",
    ),
)

WORKFLOW_ROOT_ENGINE_PIPELINE_HELPER_EXPORTS = (
    "render_dda_biological_workflow_summary_tsv",
    "render_filtered_dda_psms_tsv",
    "render_rejected_psm_rows_tsv",
    "render_protein_group_discrepancies_tsv",
    "write_dda_biological_workflow_bundle",
    "render_diann_biological_workflow_summary_tsv",
    "write_diann_biological_workflow_bundle",
    "write_label_based_report_bundle",
    "render_maxquant_biological_workflow_summary_tsv",
    "render_filtered_maxquant_protein_groups_tsv",
    "render_maxquant_enrichment_foreground_tsv",
    "render_maxquant_lfq_summary_tsv",
    "render_maxquant_lfq_matrix_tsv",
    "write_maxquant_biological_workflow_bundle",
    "render_ptm_site_workflow_summary_tsv",
    "render_ptm_site_workflow_accepted_evidence_tsv",
    "render_ptm_site_workflow_rejected_evidence_tsv",
    "write_ptm_site_workflow_bundle",
    "render_tmt_experiment_workflow_summary_tsv",
    "render_tmt_workflow_import_summary_tsv",
    "render_tmt_workflow_accepted_reporter_rows_tsv",
    "render_tmt_workflow_rejected_reporter_rows_tsv",
    "write_tmt_experiment_workflow_bundle",
)

WORKFLOW_ROOT_ENGINE_PIPELINE_RENDER_EXPORTS = (
    "render_label_based_report_summary_tsv",
    "render_label_based_sample_qc_tsv",
)

WORKFLOW_ROOT_ENGINE_PIPELINE_EXPORT_OPERATIONS = (
    "export_dda_biological_workflow_bundle",
    "export_diann_biological_workflow_bundle",
    "export_label_based_report_bundle",
    "export_maxquant_biological_workflow_bundle",
    "export_ptm_site_workflow_bundle",
    "export_tmt_experiment_workflow_bundle",
)

WORKFLOW_ROOT_ENGINE_PIPELINE_OWNERS = copy_facade_owners(
    ENGINE_PIPELINE_FACADE_OWNERS,
    excluded_exports=WORKFLOW_ROOT_ENGINE_PIPELINE_HELPER_EXPORTS,
)

PIPELINE_SUBMODULES = {
    "advanced": "bijux_proteomics.workflow.pipelines.advanced",
    "benchmarking": "bijux_proteomics.workflow.pipelines.benchmarking",
    "comparative": "bijux_proteomics.workflow.pipelines.comparative",
    "engines": "bijux_proteomics.workflow.pipelines.engines",
    "operations": "bijux_proteomics.workflow.pipelines.operations",
    "synthesis": "bijux_proteomics.workflow.pipelines.synthesis",
}

PIPELINE_FACADE_OWNERS = (
    *ADVANCED_PIPELINE_FACADE_OWNERS,
    *ENGINE_PIPELINE_FACADE_OWNERS,
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.dia_dda_comparison",
        rationale="DIA versus DDA comparison ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.dia_differential_analysis",
        rationale="DIA differential analysis ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.synthesis.discovery_to_assay",
        rationale="discovery-to-assay workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.operations.flagship_run",
        rationale="flagship workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module=(
            "bijux_proteomics.workflow.pipelines.synthesis.integrated_scientific_report"
        ),
        rationale="integrated scientific report ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.label_based_differential",
        rationale="label-based differential workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.synthesis.multi_study",
        rationale="multi-study workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.operations.orchestrator",
        rationale="workflow orchestrator ownership",
        excluded_exports=("WorkflowResult",),
    ),
    WorkflowFacadeOwner(
        owner_module=(
            "bijux_proteomics.workflow.pipelines.benchmarking.public_benchmark_runner"
        ),
        rationale="public benchmark runner ownership",
        excluded_exports=("load_public_benchmark_descriptor",),
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.scale_demo",
        rationale="scale demo pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.surprising_demo",
        rationale="surprising demo pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.surprising_demo_interrogation",
        rationale="surprising demo interrogation ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.benchmarking.trust_bundle",
        rationale="trust bundle workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.benchmarking.weak_evidence",
        rationale="weak evidence workflow ownership",
    ),
)

COMPARATIVE_PIPELINE_OWNER_MODULES = {
    "bijux_proteomics.workflow.pipelines.dia_dda_comparison",
    "bijux_proteomics.workflow.pipelines.dia_differential_analysis",
    "bijux_proteomics.workflow.pipelines.label_based_differential",
}

COMPARATIVE_PIPELINE_FACADE_OWNERS = select_facade_owners(
    PIPELINE_FACADE_OWNERS,
    COMPARATIVE_PIPELINE_OWNER_MODULES,
)

BENCHMARKING_PIPELINE_OWNER_MODULES = {
    "bijux_proteomics.workflow.pipelines.benchmarking.public_benchmark_runner",
    "bijux_proteomics.workflow.pipelines.benchmarking.trust_bundle",
    "bijux_proteomics.workflow.pipelines.benchmarking.weak_evidence",
}

BENCHMARKING_PIPELINE_FACADE_OWNERS = select_facade_owners(
    PIPELINE_FACADE_OWNERS,
    BENCHMARKING_PIPELINE_OWNER_MODULES,
)

SYNTHESIS_PIPELINE_OWNER_MODULES = {
    "bijux_proteomics.workflow.pipelines.synthesis.discovery_to_assay",
    "bijux_proteomics.workflow.pipelines.synthesis.integrated_scientific_report",
    "bijux_proteomics.workflow.pipelines.synthesis.multi_study",
}

SYNTHESIS_PIPELINE_FACADE_OWNERS = select_facade_owners(
    PIPELINE_FACADE_OWNERS,
    SYNTHESIS_PIPELINE_OWNER_MODULES,
)

OPERATIONS_PIPELINE_OWNER_MODULES = {
    "bijux_proteomics.workflow.pipelines.operations.flagship_run",
    "bijux_proteomics.workflow.pipelines.operations.orchestrator",
}

OPERATIONS_PIPELINE_FACADE_OWNERS = select_facade_owners(
    PIPELINE_FACADE_OWNERS,
    OPERATIONS_PIPELINE_OWNER_MODULES,
)

PIPELINE_ROOT_CANONICAL_SUBFACADE_OWNER_MODULES = frozenset().union(
    facade_owner_modules(ADVANCED_PIPELINE_FACADE_OWNERS),
    BENCHMARKING_PIPELINE_OWNER_MODULES,
    COMPARATIVE_PIPELINE_OWNER_MODULES,
    {
        "bijux_proteomics.workflow.demo.scale_demo",
        "bijux_proteomics.workflow.demo.surprising_demo",
        "bijux_proteomics.workflow.demo.surprising_demo_interrogation",
    },
    facade_owner_modules(ENGINE_PIPELINE_FACADE_OWNERS),
    OPERATIONS_PIPELINE_OWNER_MODULES,
    SYNTHESIS_PIPELINE_OWNER_MODULES,
)

PIPELINE_ROOT_OWNERS = tuple(
    owner
    for owner in PIPELINE_FACADE_OWNERS
    if owner.owner_module not in PIPELINE_ROOT_CANONICAL_SUBFACADE_OWNER_MODULES
)

WORKFLOW_ROOT_STUDY_PIPELINE_REPORT_EXPORTS = (
    "render_discovery_to_assay_assay_tsv",
    "render_discovery_to_assay_omitted_targets_tsv",
    "render_discovery_to_assay_panel_tsv",
    "render_discovery_to_assay_rejected_peptides_tsv",
    "render_discovery_to_assay_rejected_transitions_tsv",
    "render_discovery_to_assay_selected_peptides_tsv",
    "render_discovery_to_assay_selected_transitions_tsv",
    "render_discovery_to_assay_summary_tsv",
    "render_discovery_to_assay_targets_tsv",
    "render_discovery_to_assay_validation_candidate_assays_tsv",
    "render_discovery_to_assay_validation_candidate_cards_tsv",
    "render_discovery_to_assay_validation_candidate_summary_tsv",
    "render_discovery_to_assay_validation_candidate_warnings_tsv",
    "render_integrated_scientific_report_examples_tsv",
    "render_integrated_scientific_report_html",
    "render_integrated_scientific_report_sentences_tsv",
    "render_integrated_scientific_report_summary_tsv",
    "render_multi_study_comparison_summary_tsv",
    "render_multi_study_conflicting_effects_tsv",
    "render_multi_study_harmonized_proteins_tsv",
    "render_multi_study_shared_effects_tsv",
    "render_multi_study_shared_pathways_tsv",
    "render_multi_study_study_specific_pathways_tsv",
    "render_multi_study_unresolved_proteins_tsv",
)

WORKFLOW_ROOT_STUDY_PIPELINE_OWNER_MODULES = {
    "bijux_proteomics.workflow.pipelines.synthesis.discovery_to_assay",
    "bijux_proteomics.workflow.pipelines.synthesis.integrated_scientific_report",
    "bijux_proteomics.workflow.pipelines.synthesis.multi_study",
}

WORKFLOW_ROOT_STUDY_PIPELINE_OWNERS = select_facade_owners(
    PIPELINE_FACADE_OWNERS,
    WORKFLOW_ROOT_STUDY_PIPELINE_OWNER_MODULES,
)

WORKFLOW_ROOT_BENCHMARK_PIPELINE_REPORT_EXPORTS = (
    "render_public_benchmark_suite_failures_tsv",
    "render_public_benchmark_suite_signal_assessments_tsv",
    "render_public_benchmark_suite_summary_tsv",
    "render_trust_bundle_run_summary_tsv",
    "render_weak_evidence_benchmark_criteria_tsv",
    "render_weak_evidence_benchmark_summary_tsv",
)

WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNER_MODULES = {
    "bijux_proteomics.workflow.pipelines.benchmarking.public_benchmark_runner",
    "bijux_proteomics.workflow.pipelines.benchmarking.trust_bundle",
    "bijux_proteomics.workflow.pipelines.benchmarking.weak_evidence",
}

WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNERS = select_facade_owners(
    PIPELINE_FACADE_OWNERS,
    WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNER_MODULES,
)

WORKFLOW_ROOT_COMPARATIVE_PIPELINE_REPORT_EXPORTS = (
    "render_dia_dda_comparison_summary_tsv",
    "render_dia_dda_protein_overlap_tsv",
    "render_dia_dda_peptide_overlap_tsv",
    "render_dia_dda_shared_intensity_correlation_tsv",
    "render_dia_dda_exclusive_evidence_tsv",
    "render_dia_dda_conflicting_evidence_tsv",
    "render_dia_dda_differential_comparison_tsv",
    "render_dia_differential_matrix_tsv",
    "render_dia_differential_missingness_tsv",
    "render_dia_differential_results_tsv",
    "render_dia_differential_qc_summary_tsv",
    "render_dia_normalization_balance_plot_tsv",
    "render_dia_differential_volcano_plot_tsv",
    "export_dia_differential_matrix_tsv",
    "export_dia_differential_missingness_tsv",
    "export_dia_differential_results_tsv",
    "export_dia_differential_qc_summary_tsv",
    "export_dia_normalization_balance_plot_tsv",
    "export_dia_differential_volcano_plot_tsv",
    "export_label_based_differential_matrix_tsv",
    "export_label_based_differential_missingness_tsv",
    "export_label_based_differential_results_tsv",
    "export_label_based_differential_volcano_plot_tsv",
    "export_label_based_normalization_balance_plot_tsv",
    "render_label_based_differential_matrix_tsv",
    "render_label_based_differential_missingness_tsv",
    "render_label_based_differential_results_tsv",
    "render_label_based_differential_volcano_plot_tsv",
    "render_label_based_normalization_balance_plot_tsv",
)

WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNER_MODULES = {
    "bijux_proteomics.workflow.pipelines.dia_dda_comparison",
    "bijux_proteomics.workflow.pipelines.dia_differential_analysis",
    "bijux_proteomics.workflow.pipelines.label_based_differential",
}

WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNERS = select_facade_owners(
    PIPELINE_FACADE_OWNERS,
    WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNER_MODULES,
)

WORKFLOW_ROOT_FLAGSHIP_PIPELINE_HELPER_EXPORTS = (
    "write_proteomics_run_bundle",
    "render_proteomics_run_qc_summary_tsv",
    "render_proteomics_run_summary_tsv",
)

WORKFLOW_ROOT_FLAGSHIP_PIPELINE_EXPORT_OPERATIONS = (
    "export_proteomics_run_bundle",
    "render_proteomics_run_enrichment_tsv",
)

WORKFLOW_ROOT_FLAGSHIP_PIPELINE_OWNERS = select_facade_owners(
    PIPELINE_FACADE_OWNERS,
    {"bijux_proteomics.workflow.pipelines.operations.flagship_run"},
    excluded_exports=WORKFLOW_ROOT_FLAGSHIP_PIPELINE_HELPER_EXPORTS,
)

WORKFLOW_ROOT_PIPELINE_OWNERS = (
    *WORKFLOW_ROOT_ADVANCED_PIPELINE_OWNERS,
    *WORKFLOW_ROOT_ENGINE_PIPELINE_OWNERS,
    *(
        owner
        for owner in PIPELINE_FACADE_OWNERS
        if owner not in ADVANCED_PIPELINE_FACADE_OWNERS
        and owner not in ENGINE_PIPELINE_FACADE_OWNERS
        and owner.owner_module not in WORKFLOW_ROOT_STUDY_PIPELINE_OWNER_MODULES
        and owner.owner_module not in WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNER_MODULES
        and owner.owner_module not in WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNER_MODULES
        and owner.owner_module
        != "bijux_proteomics.workflow.pipelines.operations.flagship_run"
        and not owner.owner_module.startswith("bijux_proteomics.workflow.demo.")
    ),
    *WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNERS,
    *WORKFLOW_ROOT_FLAGSHIP_PIPELINE_OWNERS,
    *WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNERS,
    *WORKFLOW_ROOT_STUDY_PIPELINE_OWNERS,
)


__all__ = [
    "ADVANCED_PIPELINE_FACADE_OWNERS",
    "BENCHMARKING_PIPELINE_FACADE_OWNERS",
    "BENCHMARKING_PIPELINE_OWNER_MODULES",
    "COMPARATIVE_PIPELINE_FACADE_OWNERS",
    "COMPARATIVE_PIPELINE_OWNER_MODULES",
    "ENGINE_PIPELINE_FACADE_OWNERS",
    "OPERATIONS_PIPELINE_FACADE_OWNERS",
    "OPERATIONS_PIPELINE_OWNER_MODULES",
    "PIPELINE_FACADE_OWNERS",
    "PIPELINE_ROOT_CANONICAL_SUBFACADE_OWNER_MODULES",
    "PIPELINE_ROOT_OWNERS",
    "PIPELINE_SUBMODULES",
    "SYNTHESIS_PIPELINE_FACADE_OWNERS",
    "SYNTHESIS_PIPELINE_OWNER_MODULES",
    "WORKFLOW_ROOT_ADVANCED_PIPELINE_HELPER_EXPORTS",
    "WORKFLOW_ROOT_ADVANCED_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_ADVANCED_PIPELINE_VALIDATION_EXPORTS",
    "WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNER_MODULES",
    "WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_BENCHMARK_PIPELINE_REPORT_EXPORTS",
    "WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNER_MODULES",
    "WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_COMPARATIVE_PIPELINE_REPORT_EXPORTS",
    "WORKFLOW_ROOT_ENGINE_PIPELINE_EXPORT_OPERATIONS",
    "WORKFLOW_ROOT_ENGINE_PIPELINE_HELPER_EXPORTS",
    "WORKFLOW_ROOT_ENGINE_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_ENGINE_PIPELINE_RENDER_EXPORTS",
    "WORKFLOW_ROOT_FLAGSHIP_PIPELINE_EXPORT_OPERATIONS",
    "WORKFLOW_ROOT_FLAGSHIP_PIPELINE_HELPER_EXPORTS",
    "WORKFLOW_ROOT_FLAGSHIP_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_STUDY_PIPELINE_OWNER_MODULES",
    "WORKFLOW_ROOT_STUDY_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_STUDY_PIPELINE_REPORT_EXPORTS",
    "WorkflowFacadeOwner",
]
