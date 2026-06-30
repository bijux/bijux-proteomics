# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed public workflow facade catalogs and compatibility targets."""

from __future__ import annotations

from bijux_proteomics.workflow.facade_catalog import (
    WorkflowFacadeOwner,
    copy_facade_owners,
)
from bijux_proteomics.workflow.facade_pipeline_catalog import (
    ADVANCED_PIPELINE_FACADE_OWNERS,
    BENCHMARKING_PIPELINE_FACADE_OWNERS,
    BENCHMARKING_PIPELINE_OWNER_MODULES,
    COMPARATIVE_PIPELINE_FACADE_OWNERS,
    COMPARATIVE_PIPELINE_OWNER_MODULES,
    ENGINE_PIPELINE_FACADE_OWNERS,
    OPERATIONS_PIPELINE_FACADE_OWNERS,
    OPERATIONS_PIPELINE_OWNER_MODULES,
    PIPELINE_FACADE_OWNERS,
    PIPELINE_ROOT_CANONICAL_SUBFACADE_OWNER_MODULES,
    PIPELINE_ROOT_OWNERS,
    PIPELINE_SUBMODULES,
    SYNTHESIS_PIPELINE_FACADE_OWNERS,
    SYNTHESIS_PIPELINE_OWNER_MODULES,
    WORKFLOW_ROOT_ADVANCED_PIPELINE_HELPER_EXPORTS,
    WORKFLOW_ROOT_ADVANCED_PIPELINE_OWNERS,
    WORKFLOW_ROOT_ADVANCED_PIPELINE_VALIDATION_EXPORTS,
    WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNER_MODULES,
    WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNERS,
    WORKFLOW_ROOT_BENCHMARK_PIPELINE_REPORT_EXPORTS,
    WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNER_MODULES,
    WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNERS,
    WORKFLOW_ROOT_COMPARATIVE_PIPELINE_REPORT_EXPORTS,
    WORKFLOW_ROOT_ENGINE_PIPELINE_EXPORT_OPERATIONS,
    WORKFLOW_ROOT_ENGINE_PIPELINE_HELPER_EXPORTS,
    WORKFLOW_ROOT_ENGINE_PIPELINE_OWNERS,
    WORKFLOW_ROOT_ENGINE_PIPELINE_RENDER_EXPORTS,
    WORKFLOW_ROOT_FLAGSHIP_PIPELINE_EXPORT_OPERATIONS,
    WORKFLOW_ROOT_FLAGSHIP_PIPELINE_HELPER_EXPORTS,
    WORKFLOW_ROOT_FLAGSHIP_PIPELINE_OWNERS,
    WORKFLOW_ROOT_PIPELINE_OWNERS,
    WORKFLOW_ROOT_STUDY_PIPELINE_OWNER_MODULES,
    WORKFLOW_ROOT_STUDY_PIPELINE_OWNERS,
    WORKFLOW_ROOT_STUDY_PIPELINE_REPORT_EXPORTS,
)
from bijux_proteomics.workflow.facade_runtime import (
    build_lazy_export_index,
    list_owned_public_names,
    load_public_export,
    load_public_submodule,
    module_directory,
    ordered_facade_owners,
)
from bijux_proteomics.workflow.facade_targets import (
    WORKFLOW_BENCHMARK_ROOT_OWNER_FILES,
    WORKFLOW_BENCHMARK_WRAPPER_TARGETS,
    WORKFLOW_PIPELINE_ADVANCED_WRAPPER_TARGETS,
    WORKFLOW_PIPELINE_DEMO_WRAPPER_TARGETS,
    WORKFLOW_PIPELINE_ENGINE_WRAPPER_TARGETS,
    WORKFLOW_ROOT_OWNER_FILES,
    WORKFLOW_ROOT_PIPELINE_WRAPPER_TARGETS,
    WORKFLOW_ROOT_WRAPPER_TARGETS,
)


CARD_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.cross_study_evidence_cards",
        rationale="cross-study evidence card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.mechanisms",
        rationale="mechanism card workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.pathway_evidence_cards",
        rationale="pathway evidence card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.protein_evidence_cards",
        rationale="protein evidence card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.protein_mechanism_cards",
        rationale="protein mechanism card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.sample_evidence_cards",
        rationale="sample evidence card ownership",
    ),
)

WORKFLOW_ROOT_CARD_HELPER_EXPORTS = (
    "render_cross_study_evidence_card_summary_tsv",
    "render_cross_study_evidence_card_tsv",
    "render_cross_study_evidence_dataset_tsv",
    "render_mechanism_card_summary_tsv",
    "render_mechanism_cards_tsv",
    "export_pathway_evidence_card_tsv",
    "render_pathway_evidence_card_tsv",
    "export_protein_evidence_card_summary_tsv",
    "export_protein_evidence_card_tsv",
    "render_protein_evidence_card_summary_tsv",
    "render_protein_evidence_card_tsv",
    "export_protein_mechanism_card_summary_tsv",
    "export_protein_mechanism_card_tsv",
    "render_protein_mechanism_card_summary_tsv",
    "render_protein_mechanism_card_tsv",
    "export_sample_evidence_card_tsv",
    "render_sample_evidence_card_tsv",
)

WORKFLOW_ROOT_CARD_OWNERS = copy_facade_owners(CARD_FACADE_OWNERS)

BENCHMARK_SYNTHETIC_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.benchmarks.synthetic.synthetic_quant_truth",
        rationale="synthetic quantification truth ownership",
    ),
)

BENCHMARK_FIDELITY_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.benchmarks.fidelity.diann_benchmarks",
        rationale="DIA-NN benchmark ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.benchmarks.fidelity.maxquant_benchmarks",
        rationale="MaxQuant benchmark ownership",
    ),
)

BENCHMARK_DATASET_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.benchmarks.datasets.public_benchmark_descriptors",
        rationale="public benchmark descriptor ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.benchmarks.datasets.public_benchmark_subset",
        rationale="public benchmark subset ownership",
    ),
)

BENCHMARK_FACADE_OWNERS = (
    *BENCHMARK_FIDELITY_FACADE_OWNERS,
    *BENCHMARK_DATASET_FACADE_OWNERS,
    *BENCHMARK_SYNTHETIC_FACADE_OWNERS,
)

EXPORT_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.artifact_layout",
        rationale="artifact layout ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.interactive_result_bundle",
        rationale="interactive result bundle ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.interactive_result_comparison",
        rationale="interactive result comparison ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.output_validation",
        rationale="output validation ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.result_archive",
        rationale="result archive ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.result_manifest",
        rationale="result manifest ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.result_search_index",
        rationale="result search index ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.targeted_review_workflow",
        rationale="targeted review export ownership",
    ),
)

WORKFLOW_ROOT_EXPORT_HELPER_EXPORTS = (
    "classify_workflow_artifact_name",
    "find_workflow_artifact_by_id",
    "find_workflow_artifact_by_legacy_path",
    "index_workflow_artifact_manifest",
    "render_workflow_artifact_inventory_summary_tsv",
    "render_workflow_artifact_inventory_tsv",
    "load_result_archive",
    "export_targeted_assay_qc_workflow_artifacts",
    "export_targeted_matrix_workflow_artifacts",
)

WORKFLOW_ROOT_EXPORT_OPERATIONS = (
    "load_workflow_artifact_manifest",
    "validate_workflow_artifact_inventory",
    "validate_workflow_artifact_completeness",
    "validate_workflow_artifact_manifest",
    "render_interactive_result_bundle_summary_tsv",
    "render_interactive_result_comparison_pathway_tsv",
    "render_interactive_result_comparison_protein_tsv",
    "render_interactive_result_comparison_ptm_site_tsv",
    "render_interactive_result_comparison_qc_tsv",
    "render_interactive_result_comparison_summary_tsv",
    "write_result_archive_lab_action_packets",
    "render_result_manifest_command_tsv",
    "render_result_manifest_file_tsv",
    "render_result_manifest_input_tsv",
    "render_result_manifest_summary_tsv",
    "render_result_manifest_warning_tsv",
    "render_result_search_hit_tsv",
    "render_result_search_summary_tsv",
)

WORKFLOW_ROOT_EXPORT_OWNERS = copy_facade_owners(
    EXPORT_FACADE_OWNERS,
    excluded_exports=WORKFLOW_ROOT_EXPORT_HELPER_EXPORTS,
)

BENCHMARK_SUBMODULES = {
    "datasets": "bijux_proteomics.workflow.benchmarks.datasets",
    "fidelity": "bijux_proteomics.workflow.benchmarks.fidelity",
    "synthetic": "bijux_proteomics.workflow.benchmarks.synthetic",
}

DEMO_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.scale_demo",
        rationale="generated scale demo ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.surprising_demo",
        rationale="shipped surprising demo ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.surprising_demo_interrogation",
        rationale="surprising demo interrogation ownership",
    ),
)

WORKFLOW_ROOT_DEMO_HELPER_EXPORTS = (
    "render_scale_demo_stage_metrics_tsv",
    "render_scale_demo_summary_tsv",
    "render_scale_demo_validation_tsv",
    "load_surprising_demo_manifest",
    "render_surprising_demo_findings_tsv",
    "render_surprising_demo_summary_tsv",
    "render_surprising_demo_interrogation_answers_tsv",
    "render_surprising_demo_interrogation_summary_tsv",
)

WORKFLOW_ROOT_DEMO_OWNERS = copy_facade_owners(DEMO_FACADE_OWNERS)

STUDY_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cohort_stratification",
        rationale="cohort stratification ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_study_effect_comparison",
        rationale="cross-study effect comparison ownership",
        excluded_exports=("CrossStudyProteinStudyInput",),
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_study_meta_analysis",
        rationale="cross-study meta-analysis ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_study_pathway_comparison",
        rationale="cross-study pathway comparison ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_study_protein_harmonization",
        rationale="cross-study protein harmonization ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_species_effect_comparison",
        rationale="cross-species effect comparison ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.public_dataset_comparison",
        rationale="public dataset comparison ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.study_result",
        rationale="study result ownership",
    ),
)

WORKFLOW_ROOT_STUDY_SERIALIZATION_EXPORTS = (
    "render_cohort_interaction_candidate_tsv",
    "render_cohort_stratification_summary_tsv",
    "render_cohort_stratum_tsv",
    "render_cohort_subgroup_effect_tsv",
    "export_cross_study_conflicting_hit_tsv",
    "export_cross_study_effect_comparison_tsv",
    "export_cross_study_effect_detail_tsv",
    "export_cross_study_replicated_hit_tsv",
    "export_cross_study_study_specific_hit_tsv",
    "render_cross_study_conflicting_hit_tsv",
    "render_cross_study_effect_comparison_tsv",
    "render_cross_study_effect_detail_tsv",
    "render_cross_study_replicated_hit_tsv",
    "render_cross_study_study_specific_hit_tsv",
    "export_cross_study_meta_analysis_rejected_tsv",
    "export_cross_study_meta_analysis_study_weight_tsv",
    "export_cross_study_meta_analysis_tsv",
    "render_cross_study_meta_analysis_rejected_tsv",
    "render_cross_study_meta_analysis_study_weight_tsv",
    "render_cross_study_meta_analysis_tsv",
    "export_cross_study_opposite_pathway_signal_tsv",
    "export_cross_study_pathway_comparison_tsv",
    "export_cross_study_pathway_detail_tsv",
    "export_cross_study_shared_pathway_signal_tsv",
    "export_cross_study_study_specific_pathway_tsv",
    "render_cross_study_opposite_pathway_signal_tsv",
    "render_cross_study_pathway_comparison_tsv",
    "render_cross_study_pathway_detail_tsv",
    "render_cross_study_shared_pathway_signal_tsv",
    "render_cross_study_study_specific_pathway_tsv",
    "export_cross_study_protein_harmonization_tsv",
    "export_cross_study_protein_unresolved_tsv",
    "render_cross_study_protein_harmonization_tsv",
    "render_cross_study_protein_unresolved_tsv",
    "export_cross_species_effect_comparison_tsv",
    "render_cross_species_effect_comparison_tsv",
    "export_public_dataset_combined_summary_tsv",
    "export_public_dataset_dataset_summary_tsv",
    "export_public_dataset_effect_comparison_tsv",
    "export_public_dataset_failure_tsv",
    "export_public_dataset_meta_analysis_tsv",
    "export_public_dataset_pathway_comparison_tsv",
    "render_public_dataset_combined_summary_tsv",
    "render_public_dataset_dataset_summary_tsv",
    "render_public_dataset_effect_comparison_tsv",
    "render_public_dataset_failure_tsv",
    "render_public_dataset_meta_analysis_tsv",
    "render_public_dataset_pathway_comparison_tsv",
)

WORKFLOW_ROOT_STUDY_OWNERS = copy_facade_owners(STUDY_FACADE_OWNERS)

REPORT_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.reports.biological_reporting",
        rationale="biological result report ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.reports.biological_result_graph",
        rationale="biological result graph ownership",
    ),
)

WORKFLOW_ROOT_REPORT_HELPER_EXPORTS = (
    "write_biological_result_report_bundle",
    "render_biological_report_section_confidence_tsv",
    "render_biological_result_report_summary_tsv",
)

WORKFLOW_ROOT_REPORT_EXPORT_OPERATIONS = ("export_biological_result_report_bundle",)

WORKFLOW_ROOT_REPORT_OWNERS = copy_facade_owners(
    REPORT_FACADE_OWNERS,
    excluded_exports=WORKFLOW_ROOT_REPORT_HELPER_EXPORTS,
)

WORKFLOW_ROOT_SUBMODULES = {
    "benchmarks": "bijux_proteomics.workflow.benchmarks",
    "cards": "bijux_proteomics.workflow.cards",
    "cross_study_protein_harmonization": "bijux_proteomics.workflow.cross_study_protein_harmonization",
    "demo": "bijux_proteomics.workflow.demo",
    "exports": "bijux_proteomics.workflow.exports",
    "pipelines": "bijux_proteomics.workflow.pipelines",
    "public_benchmark_descriptors": "bijux_proteomics.workflow.public_benchmark_descriptors",
    "reports": "bijux_proteomics.workflow.reports",
    "studies": "bijux_proteomics.workflow.studies",
}

WORKFLOW_ROOT_SHARED_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.result_types",
        rationale="shared workflow result record ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.blueprint",
        rationale="workflow blueprint ownership",
    ),
)

WORKFLOW_ROOT_OWNERS = (
    *WORKFLOW_ROOT_SHARED_OWNERS,
    *WORKFLOW_ROOT_REPORT_OWNERS,
    *WORKFLOW_ROOT_EXPORT_OWNERS,
    *WORKFLOW_ROOT_PIPELINE_OWNERS,
    *WORKFLOW_ROOT_STUDY_OWNERS,
    *WORKFLOW_ROOT_CARD_OWNERS,
    *BENCHMARK_FACADE_OWNERS,
    *WORKFLOW_ROOT_DEMO_OWNERS,
)

__all__ = [
    "ADVANCED_PIPELINE_FACADE_OWNERS",
    "BENCHMARKING_PIPELINE_FACADE_OWNERS",
    "BENCHMARKING_PIPELINE_OWNER_MODULES",
    "BENCHMARK_FIDELITY_FACADE_OWNERS",
    "BENCHMARK_DATASET_FACADE_OWNERS",
    "BENCHMARK_FACADE_OWNERS",
    "BENCHMARK_SYNTHETIC_FACADE_OWNERS",
    "BENCHMARK_SUBMODULES",
    "CARD_FACADE_OWNERS",
    "COMPARATIVE_PIPELINE_FACADE_OWNERS",
    "COMPARATIVE_PIPELINE_OWNER_MODULES",
    "DEMO_FACADE_OWNERS",
    "EXPORT_FACADE_OWNERS",
    "ENGINE_PIPELINE_FACADE_OWNERS",
    "OPERATIONS_PIPELINE_FACADE_OWNERS",
    "OPERATIONS_PIPELINE_OWNER_MODULES",
    "PIPELINE_ROOT_CANONICAL_SUBFACADE_OWNER_MODULES",
    "PIPELINE_ROOT_OWNERS",
    "PIPELINE_SUBMODULES",
    "WORKFLOW_ROOT_ADVANCED_PIPELINE_HELPER_EXPORTS",
    "WORKFLOW_ROOT_ADVANCED_PIPELINE_OWNERS",
    "WORKFLOW_BENCHMARK_ROOT_OWNER_FILES",
    "WORKFLOW_BENCHMARK_WRAPPER_TARGETS",
    "WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNER_MODULES",
    "WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_BENCHMARK_PIPELINE_REPORT_EXPORTS",
    "WORKFLOW_ROOT_CARD_HELPER_EXPORTS",
    "WORKFLOW_ROOT_CARD_OWNERS",
    "WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNER_MODULES",
    "WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_COMPARATIVE_PIPELINE_REPORT_EXPORTS",
    "WORKFLOW_ROOT_DEMO_HELPER_EXPORTS",
    "WORKFLOW_ROOT_DEMO_OWNERS",
    "WORKFLOW_ROOT_ENGINE_PIPELINE_RENDER_EXPORTS",
    "WORKFLOW_ROOT_EXPORT_OPERATIONS",
    "WORKFLOW_ROOT_ADVANCED_PIPELINE_VALIDATION_EXPORTS",
    "WORKFLOW_ROOT_ENGINE_PIPELINE_EXPORT_OPERATIONS",
    "WORKFLOW_ROOT_ENGINE_PIPELINE_HELPER_EXPORTS",
    "WORKFLOW_ROOT_ENGINE_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_EXPORT_HELPER_EXPORTS",
    "WORKFLOW_ROOT_EXPORT_OWNERS",
    "WORKFLOW_ROOT_FLAGSHIP_PIPELINE_EXPORT_OPERATIONS",
    "WORKFLOW_ROOT_FLAGSHIP_PIPELINE_HELPER_EXPORTS",
    "WORKFLOW_ROOT_FLAGSHIP_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_OWNER_FILES",
    "WORKFLOW_PIPELINE_ADVANCED_WRAPPER_TARGETS",
    "WORKFLOW_PIPELINE_DEMO_WRAPPER_TARGETS",
    "WORKFLOW_PIPELINE_ENGINE_WRAPPER_TARGETS",
    "WORKFLOW_ROOT_REPORT_HELPER_EXPORTS",
    "WORKFLOW_ROOT_REPORT_EXPORT_OPERATIONS",
    "WORKFLOW_ROOT_REPORT_OWNERS",
    "WORKFLOW_ROOT_SHARED_OWNERS",
    "PIPELINE_FACADE_OWNERS",
    "REPORT_FACADE_OWNERS",
    "STUDY_FACADE_OWNERS",
    "SYNTHESIS_PIPELINE_FACADE_OWNERS",
    "SYNTHESIS_PIPELINE_OWNER_MODULES",
    "WORKFLOW_ROOT_OWNERS",
    "WORKFLOW_ROOT_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_STUDY_PIPELINE_OWNER_MODULES",
    "WORKFLOW_ROOT_STUDY_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_STUDY_PIPELINE_REPORT_EXPORTS",
    "WORKFLOW_ROOT_STUDY_OWNERS",
    "WORKFLOW_ROOT_STUDY_SERIALIZATION_EXPORTS",
    "WORKFLOW_ROOT_SUBMODULES",
    "WORKFLOW_ROOT_PIPELINE_WRAPPER_TARGETS",
    "WORKFLOW_ROOT_WRAPPER_TARGETS",
    "WorkflowFacadeOwner",
    "build_lazy_export_index",
    "list_owned_public_names",
    "load_public_export",
    "load_public_submodule",
    "module_directory",
    "ordered_facade_owners",
]
