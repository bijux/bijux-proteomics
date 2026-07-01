# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Export facade ledgers for workflow delivery surfaces."""

from __future__ import annotations

from bijux_proteomics.workflow.facade_catalog import (
    WorkflowFacadeOwner,
    copy_facade_owners,
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


__all__ = [
    "EXPORT_FACADE_OWNERS",
    "WORKFLOW_ROOT_EXPORT_HELPER_EXPORTS",
    "WORKFLOW_ROOT_EXPORT_OPERATIONS",
    "WORKFLOW_ROOT_EXPORT_OWNERS",
    "WorkflowFacadeOwner",
]
