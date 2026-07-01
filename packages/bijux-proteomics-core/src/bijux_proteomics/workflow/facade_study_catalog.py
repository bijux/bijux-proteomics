# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Study facade ledgers for workflow analysis surfaces."""

from __future__ import annotations

from bijux_proteomics.workflow.facade_catalog import (
    WorkflowFacadeOwner,
    copy_facade_owners,
)

STUDY_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cohort_stratification",
        rationale="cohort stratification ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_study.effect_comparison",
        rationale="cross-study effect comparison ownership",
        excluded_exports=("CrossStudyProteinStudyInput",),
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_study.meta_analysis",
        rationale="cross-study meta-analysis ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_study.pathway_comparison",
        rationale="cross-study pathway comparison ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_study.protein_harmonization",
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
        owner_module="bijux_proteomics.workflow.studies.study_results",
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


__all__ = [
    "STUDY_FACADE_OWNERS",
    "WORKFLOW_ROOT_STUDY_OWNERS",
    "WORKFLOW_ROOT_STUDY_SERIALIZATION_EXPORTS",
    "WorkflowFacadeOwner",
]
