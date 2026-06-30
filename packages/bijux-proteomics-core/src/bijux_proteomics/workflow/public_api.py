# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed public workflow facade catalogs and lazy export helpers."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WorkflowFacadeOwner:
    """One owned module that contributes public symbols to a workflow facade."""

    owner_module: str
    rationale: str
    excluded_exports: tuple[str, ...] = ()


def copy_facade_owners(
    owners: tuple[WorkflowFacadeOwner, ...],
    *,
    excluded_exports: tuple[str, ...] = (),
) -> tuple[WorkflowFacadeOwner, ...]:
    """Copy facade owners while preserving order and extending exclusions."""

    return tuple(
        WorkflowFacadeOwner(
            owner_module=owner.owner_module,
            rationale=owner.rationale,
            excluded_exports=(*owner.excluded_exports, *excluded_exports),
        )
        for owner in owners
    )


def facade_owner_modules(
    owners: tuple[WorkflowFacadeOwner, ...],
) -> frozenset[str]:
    """Return the canonical owner modules represented by a facade catalog."""

    return frozenset(owner.owner_module for owner in owners)


def select_facade_owners(
    owners: tuple[WorkflowFacadeOwner, ...],
    owner_modules: set[str] | frozenset[str],
    *,
    excluded_exports: tuple[str, ...] = (),
) -> tuple[WorkflowFacadeOwner, ...]:
    """Copy only the owners whose modules belong to the selected compatibility set."""

    return tuple(
        WorkflowFacadeOwner(
            owner_module=owner.owner_module,
            rationale=owner.rationale,
            excluded_exports=(*owner.excluded_exports, *excluded_exports),
        )
        for owner in owners
        if owner.owner_module in owner_modules
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
        owner_module="bijux_proteomics.workflow.pipelines.discovery_to_assay",
        rationale="discovery-to-assay workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.flagship_run",
        rationale="flagship workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.integrated_scientific_report",
        rationale="integrated scientific report ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.label_based_differential",
        rationale="label-based differential workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.multi_study",
        rationale="multi-study workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.orchestrator",
        rationale="workflow orchestrator ownership",
        excluded_exports=("WorkflowResult",),
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.public_benchmark_runner",
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
        owner_module="bijux_proteomics.workflow.pipelines.trust_bundle",
        rationale="trust bundle workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.weak_evidence",
        rationale="weak evidence workflow ownership",
    ),
)

COMPARATIVE_PIPELINE_OWNER_MODULES = {
    "bijux_proteomics.workflow.pipelines.dia_dda_comparison",
    "bijux_proteomics.workflow.pipelines.dia_differential_analysis",
    "bijux_proteomics.workflow.pipelines.label_based_differential",
}

COMPARATIVE_PIPELINE_FACADE_OWNERS = tuple(
    owner
    for owner in PIPELINE_FACADE_OWNERS
    if owner.owner_module in COMPARATIVE_PIPELINE_OWNER_MODULES
)

BENCHMARKING_PIPELINE_OWNER_MODULES = {
    "bijux_proteomics.workflow.pipelines.public_benchmark_runner",
    "bijux_proteomics.workflow.pipelines.trust_bundle",
    "bijux_proteomics.workflow.pipelines.weak_evidence",
}

BENCHMARKING_PIPELINE_FACADE_OWNERS = tuple(
    owner
    for owner in PIPELINE_FACADE_OWNERS
    if owner.owner_module in BENCHMARKING_PIPELINE_OWNER_MODULES
)

SYNTHESIS_PIPELINE_OWNER_MODULES = {
    "bijux_proteomics.workflow.pipelines.discovery_to_assay",
    "bijux_proteomics.workflow.pipelines.integrated_scientific_report",
    "bijux_proteomics.workflow.pipelines.multi_study",
}

SYNTHESIS_PIPELINE_FACADE_OWNERS = tuple(
    owner
    for owner in PIPELINE_FACADE_OWNERS
    if owner.owner_module in SYNTHESIS_PIPELINE_OWNER_MODULES
)

OPERATIONS_PIPELINE_OWNER_MODULES = {
    "bijux_proteomics.workflow.pipelines.flagship_run",
    "bijux_proteomics.workflow.pipelines.orchestrator",
}

OPERATIONS_PIPELINE_FACADE_OWNERS = tuple(
    owner
    for owner in PIPELINE_FACADE_OWNERS
    if owner.owner_module in OPERATIONS_PIPELINE_OWNER_MODULES
)

PIPELINE_ROOT_CANONICAL_SUBFACADE_OWNER_MODULES = {
    *(owner.owner_module for owner in ADVANCED_PIPELINE_FACADE_OWNERS),
    *BENCHMARKING_PIPELINE_OWNER_MODULES,
    *COMPARATIVE_PIPELINE_OWNER_MODULES,
    *(owner.owner_module for owner in DEMO_FACADE_OWNERS),
    *(owner.owner_module for owner in ENGINE_PIPELINE_FACADE_OWNERS),
    *OPERATIONS_PIPELINE_OWNER_MODULES,
    *SYNTHESIS_PIPELINE_OWNER_MODULES,
}

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
    "bijux_proteomics.workflow.pipelines.discovery_to_assay",
    "bijux_proteomics.workflow.pipelines.integrated_scientific_report",
    "bijux_proteomics.workflow.pipelines.multi_study",
}

WORKFLOW_ROOT_STUDY_PIPELINE_OWNERS = tuple(
    WorkflowFacadeOwner(
        owner_module=owner.owner_module,
        rationale=owner.rationale,
        excluded_exports=owner.excluded_exports,
    )
    for owner in PIPELINE_FACADE_OWNERS
    if owner.owner_module in WORKFLOW_ROOT_STUDY_PIPELINE_OWNER_MODULES
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
    "bijux_proteomics.workflow.pipelines.public_benchmark_runner",
    "bijux_proteomics.workflow.pipelines.trust_bundle",
    "bijux_proteomics.workflow.pipelines.weak_evidence",
}

WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNERS = tuple(
    WorkflowFacadeOwner(
        owner_module=owner.owner_module,
        rationale=owner.rationale,
        excluded_exports=owner.excluded_exports,
    )
    for owner in PIPELINE_FACADE_OWNERS
    if owner.owner_module in WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNER_MODULES
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

WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNERS = tuple(
    WorkflowFacadeOwner(
        owner_module=owner.owner_module,
        rationale=owner.rationale,
        excluded_exports=owner.excluded_exports,
    )
    for owner in PIPELINE_FACADE_OWNERS
    if owner.owner_module in WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNER_MODULES
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

WORKFLOW_ROOT_FLAGSHIP_PIPELINE_OWNERS = tuple(
    WorkflowFacadeOwner(
        owner_module=owner.owner_module,
        rationale=owner.rationale,
        excluded_exports=(
            *owner.excluded_exports,
            *WORKFLOW_ROOT_FLAGSHIP_PIPELINE_HELPER_EXPORTS,
        ),
    )
    for owner in PIPELINE_FACADE_OWNERS
    if owner.owner_module == "bijux_proteomics.workflow.pipelines.flagship_run"
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
        and owner.owner_module != "bijux_proteomics.workflow.pipelines.flagship_run"
        and not owner.owner_module.startswith("bijux_proteomics.workflow.demo.")
    ),
    *WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNERS,
    *WORKFLOW_ROOT_FLAGSHIP_PIPELINE_OWNERS,
    *WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNERS,
    *WORKFLOW_ROOT_STUDY_PIPELINE_OWNERS,
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

WORKFLOW_ROOT_OWNER_FILES = frozenset(
    {
        "__init__.py",
        "blueprint.py",
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


def ordered_facade_owners(
    owners: tuple[WorkflowFacadeOwner, ...],
) -> tuple[WorkflowFacadeOwner, ...]:
    """Return facade owners in their governed export order."""

    return owners


def list_owned_public_names(owner_module: str) -> tuple[str, ...]:
    """Return the owned public symbols for one workflow owner module."""

    source_path = _module_source_path(owner_module)
    module_tree = ast.parse(source_path.read_text(encoding="utf-8"))
    explicit_exports = _extract_explicit_exports(module_tree)
    if explicit_exports is not None:
        return explicit_exports
    if source_path.name == "__init__.py":
        runtime_exports = getattr(import_module(owner_module), "__all__", None)
        if runtime_exports is not None:
            return tuple(runtime_exports)
    return _extract_owned_public_symbols(module_tree)


def build_lazy_export_index(
    owners: tuple[WorkflowFacadeOwner, ...],
) -> tuple[tuple[str, ...], dict[str, tuple[str, str]]]:
    """Build one ordered export ledger and import target map for a facade."""

    public_names: list[str] = []
    export_index: dict[str, tuple[str, str]] = {}
    for owner in owners:
        for export_name in list_owned_public_names(owner.owner_module):
            if export_name in owner.excluded_exports:
                continue
            if export_name in export_index:
                conflict_owner, _ = export_index[export_name]
                raise ValueError(
                    "workflow facade export collision for "
                    f"{export_name!r}: {conflict_owner} vs {owner.owner_module}"
                )
            public_names.append(export_name)
            export_index[export_name] = (owner.owner_module, export_name)
    return tuple(public_names), export_index


def load_public_export(
    package_name: str,
    package_globals: dict[str, Any],
    export_index: dict[str, tuple[str, str]],
    name: str,
) -> Any:
    """Load one governed workflow export lazily from its owner module."""

    owner = export_index.get(name)
    if owner is None:
        raise AttributeError(f"module {package_name!r} has no attribute {name!r}")
    module_name, export_name = owner
    value = getattr(import_module(module_name), export_name)
    package_globals[name] = value
    return value


def load_public_submodule(
    package_name: str,
    package_globals: dict[str, Any],
    submodules: dict[str, str],
    name: str,
) -> Any:
    """Load one governed workflow submodule lazily from its canonical path."""

    module_name = submodules.get(name)
    if module_name is None:
        raise AttributeError(f"module {package_name!r} has no attribute {name!r}")
    module = import_module(module_name)
    package_globals[name] = module
    return module


def module_directory(
    package_globals: dict[str, Any],
    public_names: tuple[str, ...],
    *,
    submodule_names: tuple[str, ...] = (),
) -> list[str]:
    """Return a stable directory view for one governed workflow facade."""

    return sorted(set(package_globals) | set(public_names) | set(submodule_names))


def _module_source_path(owner_module: str) -> Path:
    spec = find_spec(owner_module)
    if spec is None or spec.origin is None:
        raise ValueError(
            f"workflow facade owner module is not discoverable: {owner_module}"
        )
    return Path(spec.origin)


def _extract_explicit_exports(module_tree: ast.Module) -> tuple[str, ...] | None:
    for node in module_tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in node.targets
        ):
            continue
        if not isinstance(node.value, ast.List | ast.Tuple):
            continue
        exports: list[str] = []
        for element in node.value.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                exports.append(element.value)
        return tuple(exports)
    return None


def _extract_owned_public_symbols(module_tree: ast.Module) -> tuple[str, ...]:
    owned_public_names: list[str] = []
    for node in module_tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                owned_public_names.append(node.name)
            continue
        if isinstance(node, ast.Assign):
            for target in node.targets:
                owned_public_names.extend(_public_assigned_names(target))
            continue
        if isinstance(node, ast.AnnAssign):
            owned_public_names.extend(_public_assigned_names(node.target))
    return tuple(dict.fromkeys(owned_public_names))


def _public_assigned_names(target: ast.expr) -> list[str]:
    if isinstance(target, ast.Name) and target.id.isupper():
        return [target.id]
    return []


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
