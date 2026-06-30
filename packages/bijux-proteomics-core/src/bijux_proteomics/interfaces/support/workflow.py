# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Workflow-domain imports shared by CLI command modules."""

from __future__ import annotations

from bijux_proteomics.workflow.benchmarks.datasets.public_benchmark_descriptors import (
    resolve_public_benchmark_path,
    resolve_public_benchmark_root,
)
from bijux_proteomics.workflow.benchmarks.fidelity.diann_benchmarks import (
    build_diann_benchmark_report,
    render_diann_benchmark_count_comparisons_tsv,
    render_diann_benchmark_protein_quantities_tsv,
    render_diann_benchmark_summary_tsv,
)
from bijux_proteomics.workflow.benchmarks.fidelity.maxquant_benchmarks import (
    build_maxquant_benchmark_report,
    render_maxquant_benchmark_summary_tsv,
    render_maxquant_differential_comparison_tsv,
    render_maxquant_filtering_comparison_tsv,
    render_maxquant_lfq_comparison_tsv,
    render_maxquant_protein_identity_comparison_tsv,
)
from bijux_proteomics.workflow.cards.cross_study_evidence_cards import (
    build_public_dataset_evidence_card_report,
    render_cross_study_evidence_card_summary_tsv,
    render_cross_study_evidence_card_tsv,
    render_cross_study_evidence_dataset_tsv,
)
from bijux_proteomics.workflow.demo.scale_demo import (
    ScaleDemoConfig,
    render_scale_demo_stage_metrics_tsv,
    render_scale_demo_summary_tsv,
    render_scale_demo_validation_tsv,
    run_scale_demo,
)
from bijux_proteomics.workflow.demo.surprising_demo import (
    SurprisingDemoConfig,
    render_surprising_demo_findings_tsv,
    render_surprising_demo_summary_tsv,
    run_surprising_demo,
)
from bijux_proteomics.workflow.demo.surprising_demo_interrogation import (
    SurprisingDemoQueryKind,
    SurprisingDemoQueryRequest,
    build_surprising_demo_example_requests,
    build_surprising_demo_interrogation_report,
    ensure_surprising_demo_outputs,
    render_surprising_demo_interrogation_answers_tsv,
    render_surprising_demo_interrogation_summary_tsv,
)
from bijux_proteomics.workflow.exports.interactive_result_bundle import (
    build_interactive_result_bundle_from_artifacts,
    render_interactive_result_bundle_summary_tsv,
)
from bijux_proteomics.workflow.exports.interactive_result_comparison import (
    build_interactive_result_comparison_from_artifacts,
    render_interactive_result_comparison_pathway_tsv,
    render_interactive_result_comparison_protein_tsv,
    render_interactive_result_comparison_ptm_site_tsv,
    render_interactive_result_comparison_qc_tsv,
    render_interactive_result_comparison_summary_tsv,
)
from bijux_proteomics.workflow.exports.result_manifest import (
    build_result_manifest_from_artifacts,
    render_result_manifest_command_tsv,
    render_result_manifest_file_tsv,
    render_result_manifest_input_tsv,
    render_result_manifest_summary_tsv,
    render_result_manifest_warning_tsv,
)
from bijux_proteomics.workflow.exports.result_search_index import (
    build_result_search_index_from_artifacts,
    render_result_search_hit_tsv,
    render_result_search_summary_tsv,
    search_result_index,
)
from bijux_proteomics.workflow.pipelines.dia_dda_comparison import (
    build_diann_vs_dda_psm_comparison_report,
    render_dia_dda_comparison_summary_tsv,
    render_dia_dda_conflicting_evidence_tsv,
    render_dia_dda_differential_comparison_tsv,
    render_dia_dda_exclusive_evidence_tsv,
    render_dia_dda_peptide_overlap_tsv,
    render_dia_dda_protein_overlap_tsv,
    render_dia_dda_shared_intensity_correlation_tsv,
)
from bijux_proteomics.workflow.pipelines.dia_differential_analysis import (
    DiaDifferentialSourceKind,
    build_dia_differential_volcano_plot,
    build_diann_differential_analysis_report,
    build_spectronaut_differential_analysis_report,
    export_dia_differential_matrix_tsv,
    export_dia_differential_qc_summary_tsv,
    export_dia_differential_results_tsv,
    export_dia_differential_volcano_plot_tsv,
    export_dia_normalization_balance_plot_tsv,
)
from bijux_proteomics.workflow.pipelines.flagship_run import (
    ProteomicsRunEngine,
    build_proteomics_run_bundle,
    render_proteomics_run_summary_tsv,
    write_proteomics_run_bundle,
)
from bijux_proteomics.workflow.pipelines.integrated_scientific_report import (
    build_integrated_scientific_report,
    render_integrated_scientific_report_sentences_tsv,
    render_integrated_scientific_report_summary_tsv,
)
from bijux_proteomics.workflow.pipelines.label_based_differential import (
    build_label_based_differential_volcano_plot,
    build_silac_differential_analysis_report,
    build_tmt_differential_analysis_report,
    export_label_based_differential_matrix_tsv,
    export_label_based_differential_results_tsv,
    export_label_based_differential_volcano_plot_tsv,
    export_label_based_normalization_balance_plot_tsv,
)
from bijux_proteomics.workflow.pipelines.public_benchmark_runner import (
    render_public_benchmark_suite_failures_tsv,
    render_public_benchmark_suite_signal_assessments_tsv,
    render_public_benchmark_suite_summary_tsv,
    run_public_benchmark_descriptor,
    run_public_benchmark_descriptor_suite,
)
from bijux_proteomics.workflow.pipelines.trust_bundle import (
    build_public_benchmark_trust_bundle,
    render_trust_bundle_run_summary_tsv,
)
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultSelectionPolicy,
)
from bijux_proteomics.workflow.studies.public_dataset_comparison import (
    build_public_dataset_comparison_report,
    render_public_dataset_combined_summary_tsv,
    render_public_dataset_dataset_summary_tsv,
    render_public_dataset_effect_comparison_tsv,
    render_public_dataset_failure_tsv,
    render_public_dataset_meta_analysis_tsv,
    render_public_dataset_pathway_comparison_tsv,
)
from bijux_proteomics.workflow.pipelines.orchestrator import (
    DdaWorkflowConfig,
    DiannWorkflowConfig,
    LabelFreeWorkflowConfig,
    MaxquantWorkflowConfig,
    PtmWorkflowConfig,
    SilacWorkflowConfig,
    TargetedWorkflowConfig,
    TargetedWorkflowStage,
    TmtWorkflowConfig,
    WorkflowConfig,
    WorkflowMode,
    WorkflowResult,
)
from bijux_proteomics.workflow.pipelines.orchestrator import (
    run_proteomics_workflow as _orchestrator_run_proteomics_workflow,
)


def run_proteomics_workflow(config: WorkflowConfig) -> WorkflowResult:
    """Delegate workflow orchestration through the canonical scientific owner."""

    return _orchestrator_run_proteomics_workflow(config)


__all__ = [
    "BiologicalResultSelectionPolicy",
    "DdaWorkflowConfig",
    "DiaDifferentialSourceKind",
    "DiannWorkflowConfig",
    "LabelFreeWorkflowConfig",
    "MaxquantWorkflowConfig",
    "ProteomicsRunEngine",
    "PtmWorkflowConfig",
    "ScaleDemoConfig",
    "SilacWorkflowConfig",
    "SurprisingDemoConfig",
    "SurprisingDemoQueryKind",
    "SurprisingDemoQueryRequest",
    "TargetedWorkflowConfig",
    "TargetedWorkflowStage",
    "TmtWorkflowConfig",
    "WorkflowConfig",
    "WorkflowMode",
    "WorkflowResult",
    "_orchestrator_run_proteomics_workflow",
    "build_dia_differential_volcano_plot",
    "build_diann_benchmark_report",
    "build_diann_differential_analysis_report",
    "build_diann_vs_dda_psm_comparison_report",
    "build_integrated_scientific_report",
    "build_interactive_result_bundle_from_artifacts",
    "build_interactive_result_comparison_from_artifacts",
    "build_label_based_differential_volcano_plot",
    "build_maxquant_benchmark_report",
    "build_proteomics_run_bundle",
    "build_public_benchmark_trust_bundle",
    "build_public_dataset_comparison_report",
    "build_public_dataset_evidence_card_report",
    "build_result_manifest_from_artifacts",
    "build_result_search_index_from_artifacts",
    "build_silac_differential_analysis_report",
    "build_spectronaut_differential_analysis_report",
    "build_surprising_demo_example_requests",
    "build_surprising_demo_interrogation_report",
    "build_tmt_differential_analysis_report",
    "ensure_surprising_demo_outputs",
    "export_dia_differential_matrix_tsv",
    "export_dia_differential_qc_summary_tsv",
    "export_dia_differential_results_tsv",
    "export_dia_differential_volcano_plot_tsv",
    "export_dia_normalization_balance_plot_tsv",
    "export_label_based_differential_matrix_tsv",
    "export_label_based_differential_results_tsv",
    "export_label_based_differential_volcano_plot_tsv",
    "export_label_based_normalization_balance_plot_tsv",
    "render_cross_study_evidence_card_summary_tsv",
    "render_cross_study_evidence_card_tsv",
    "render_cross_study_evidence_dataset_tsv",
    "render_dia_dda_comparison_summary_tsv",
    "render_dia_dda_conflicting_evidence_tsv",
    "render_dia_dda_differential_comparison_tsv",
    "render_dia_dda_exclusive_evidence_tsv",
    "render_dia_dda_peptide_overlap_tsv",
    "render_dia_dda_protein_overlap_tsv",
    "render_dia_dda_shared_intensity_correlation_tsv",
    "render_diann_benchmark_count_comparisons_tsv",
    "render_diann_benchmark_protein_quantities_tsv",
    "render_diann_benchmark_summary_tsv",
    "render_integrated_scientific_report_sentences_tsv",
    "render_integrated_scientific_report_summary_tsv",
    "render_interactive_result_bundle_summary_tsv",
    "render_interactive_result_comparison_pathway_tsv",
    "render_interactive_result_comparison_protein_tsv",
    "render_interactive_result_comparison_ptm_site_tsv",
    "render_interactive_result_comparison_qc_tsv",
    "render_interactive_result_comparison_summary_tsv",
    "render_maxquant_benchmark_summary_tsv",
    "render_maxquant_differential_comparison_tsv",
    "render_maxquant_filtering_comparison_tsv",
    "render_maxquant_lfq_comparison_tsv",
    "render_maxquant_protein_identity_comparison_tsv",
    "render_proteomics_run_summary_tsv",
    "render_public_benchmark_suite_failures_tsv",
    "render_public_benchmark_suite_signal_assessments_tsv",
    "render_public_benchmark_suite_summary_tsv",
    "render_public_dataset_combined_summary_tsv",
    "render_public_dataset_dataset_summary_tsv",
    "render_public_dataset_effect_comparison_tsv",
    "render_public_dataset_failure_tsv",
    "render_public_dataset_meta_analysis_tsv",
    "render_public_dataset_pathway_comparison_tsv",
    "render_result_manifest_command_tsv",
    "render_result_manifest_file_tsv",
    "render_result_manifest_input_tsv",
    "render_result_manifest_summary_tsv",
    "render_result_manifest_warning_tsv",
    "render_result_search_hit_tsv",
    "render_result_search_summary_tsv",
    "render_scale_demo_stage_metrics_tsv",
    "render_scale_demo_summary_tsv",
    "render_scale_demo_validation_tsv",
    "render_surprising_demo_findings_tsv",
    "render_surprising_demo_interrogation_answers_tsv",
    "render_surprising_demo_interrogation_summary_tsv",
    "render_surprising_demo_summary_tsv",
    "render_trust_bundle_run_summary_tsv",
    "resolve_public_benchmark_path",
    "resolve_public_benchmark_root",
    "run_proteomics_workflow",
    "run_public_benchmark_descriptor",
    "run_public_benchmark_descriptor_suite",
    "run_scale_demo",
    "run_surprising_demo",
    "search_result_index",
    "write_proteomics_run_bundle",
]
