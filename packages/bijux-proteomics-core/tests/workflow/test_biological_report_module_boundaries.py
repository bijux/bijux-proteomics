# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

WORKFLOW_ROOT = (
    Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics" / "workflow"
)
REPORTS_ROOT = WORKFLOW_ROOT / "reports"
BIOLOGICAL_REPORT_MODULES = tuple(sorted(REPORTS_ROOT.glob("biological_report*.py")))
BIOLOGICAL_REPORT_LINE_LIMIT = 1000
MODULE_SURFACES: dict[str, tuple[str, ...]] = {
    "biological_report_models.py": (
        "BiologicalReportSectionConfidenceEntry",
        "BiologicalReportSectionConfidenceLabel",
        "BiologicalReportSectionKey",
        "BiologicalResultReportBundle",
        "BiologicalResultReportExportManifest",
        "BiologicalResultReportSummary",
        "BiologicalResultSelectionPolicy",
    ),
    "biological_report_section_metadata.py": (
        "BiologicalReportSectionConfidenceEntry",
        "BiologicalReportSectionConfidenceLabel",
        "BiologicalReportSectionKey",
        "_BIOLOGICAL_REPORT_SECTION_TITLES",
    ),
    "biological_report_selection_policy.py": (
        "BiologicalResultSelectionPolicy",
        "_resolve_biological_result_selection_policy",
    ),
    "biological_report_bundle_contracts.py": (
        "BiologicalResultReportBundle",
    ),
    "biological_report_summary_contracts.py": (
        "BiologicalResultReportSummary",
    ),
    "biological_report_bundle_assembly.py": (
        "_assemble_biological_result_report_bundle",
    ),
    "biological_report_bundle_assembly_inputs.py": (
        "BiologicalReportBundleAssemblyInputs",
    ),
    "biological_report_bundle_confidence_state.py": (
        "BiologicalReportBundleConfidenceState",
        "_build_biological_report_bundle_confidence_state",
    ),
    "biological_report_bundle_materialization.py": (
        "_BIOLOGICAL_RESULT_REPORT_BUNDLE_NOTE",
        "_materialize_biological_result_report_bundle",
    ),
    "biological_report_export_contracts.py": (
        "BiologicalResultReportArtifactPaths",
        "BiologicalResultReportExportManifest",
    ),
    "biological_report_export_manifest_building.py": (
        "_build_biological_result_report_export_manifest",
    ),
    "biological_report_artifact_path_building.py": (
        "_build_biological_result_report_artifact_paths",
    ),
    "biological_report_export_manifest_metadata.py": (
        "BiologicalResultReportExportMetadata",
        "_build_biological_result_report_export_metadata",
    ),
    "biological_report_scientific_artifact_paths.py": (
        "_build_biological_scientific_artifact_path_fields",
    ),
    "biological_report_contextual_artifact_paths.py": (
        "_build_biological_contextual_artifact_path_fields",
    ),
    "biological_report_activity_artifact_paths.py": (
        "_build_biological_activity_artifact_path_fields",
    ),
    "biological_report_visual_enrichment_artifact_paths.py": (
        "_build_biological_visual_artifact_path_fields",
        "_build_biological_enrichment_artifact_path_fields",
    ),
    "biological_report_section_confidence.py": (
        "_build_biological_report_section_confidence_entries",
        "_count_section_confidence_labels",
    ),
    "biological_report_section_confidence_entry_building.py": (
        "_build_biological_report_section_confidence_entry",
    ),
    "biological_report_evidence_confidence.py": (
        "_build_evidence_section_confidence_entries",
    ),
    "biological_report_context_confidence.py": (
        "_build_context_section_confidence_entries",
    ),
    "biological_report_molecular_context_confidence.py": (
        "_build_disease_phenotype_entry",
        "_build_drug_target_entry",
    ),
    "biological_report_sample_context_confidence.py": (
        "_build_cohort_entry",
        "_build_tissue_context_entry",
    ),
    "biological_report_compartment_confidence.py": (
        "_build_compartment_entry",
    ),
    "biological_report_activity_confidence.py": (
        "_build_activity_section_confidence_entries",
    ),
    "biological_report_selection.py": (
        "_build_background_reference_entries",
        "_build_biological_foreground_filtering_policy",
        "_resolve_contrast",
        "_select_heatmap_entity_ids",
        "_select_significant_entity_ids",
    ),
    "biological_report_reference_entries.py": (
        "_build_background_reference_entries",
        "_build_differential_reference_entries",
        "_build_foreground_reference_entries",
        "_build_protein_reference_entries",
        "_build_protein_reference_entries_from_biological_set",
    ),
    "biological_report_filtering_policies.py": (
        "_build_biological_background_filtering_policy",
        "_build_biological_foreground_filtering_policy",
    ),
    "biological_report_contrast_selection.py": (
        "_resolve_contrast",
        "_select_heatmap_entity_ids",
        "_select_significant_entity_ids",
    ),
    "biological_report_graph_qc.py": (
        "_attach_lab_run_qc_feedback",
        "_qc_claim_state",
        "_qc_trust_class",
    ),
    "biological_result_graph_run_context.py": (
        "BiologicalResultGraphRunContext",
        "_add_biological_result_graph_run_context",
    ),
    "biological_result_graph_protein_claims.py": (
        "_add_biological_result_graph_protein_claims",
    ),
    "biological_result_graph_claim_policy.py": (
        "_claim_confidence",
        "_claim_state",
        "_protein_label",
        "_protein_trust_class",
        "_quant_trust_class",
    ),
    "biological_result_graph_peptide_support.py": (
        "_add_biological_result_graph_peptide_support",
    ),
    "biological_result_graph_quant_support.py": (
        "_add_biological_result_graph_quant_support",
        "_group_quant_values_by_entity",
    ),
    "biological_report_claims.py": (
        "_build_biological_claim_validation_report",
        "_build_biological_evidence_aware_ranking_report",
        "_build_biological_hypothesis_report",
    ),
    "biological_report_ranking_reports.py": (
        "_build_biological_evidence_aware_ranking_report",
    ),
    "biological_report_claim_validation_reports.py": (
        "_build_biological_claim_validation_report",
    ),
    "biological_report_hypothesis_reports.py": (
        "_build_biological_hypothesis_report",
    ),
    "biological_report_experiment_confidence.py": (
        "_build_experiment_confidence_entry",
    ),
    "biological_report_evidence_finding_confidence.py": (
        "_build_evidence_ranking_entry",
        "_build_claim_validation_entry",
        "_build_hypothesis_entry",
    ),
    "biological_report_mechanistic_confidence.py": (
        "_build_foreground_background_entry",
        "_build_regulator_inference_entry",
        "_build_protein_mechanism_entry",
    ),
    "biological_report_context_assembly.py": (
        "BiologicalContextAssemblyReports",
        "_build_biological_context_reports",
    ),
    "biological_report_annotation_context_assembly.py": (
        "BiologicalAnnotationContextReports",
        "_build_biological_annotation_context_reports",
    ),
    "biological_report_sample_context_assembly.py": (
        "_build_biological_sample_context_report",
    ),
    "biological_report_molecular_context_assembly.py": (
        "BiologicalMolecularContextReports",
        "_build_biological_molecular_context_reports",
    ),
    "biological_report_compartment_biology_assembly.py": (
        "_build_biological_compartment_biology_report",
    ),
    "biological_report_enrichment_assembly.py": (
        "BiologicalEnrichmentAssemblyReports",
        "_build_biological_enrichment_reports",
    ),
    "biological_report_foreground_background_assembly.py": (
        "BiologicalEnrichmentInputSets",
        "_build_biological_enrichment_input_sets",
    ),
    "biological_report_go_enrichment_assembly.py": (
        "_build_biological_go_enrichment_report",
    ),
    "biological_report_pathway_enrichment_assembly.py": (
        "BiologicalPathwayEnrichmentReports",
        "_build_biological_pathway_enrichment_reports",
    ),
    "biological_report_complex_enrichment_assembly.py": (
        "BiologicalComplexEnrichmentReports",
        "_build_biological_complex_enrichment_reports",
    ),
    "biological_report_source_data.py": (
        "BiologicalReportSourceData",
        "_build_biological_report_source_data",
    ),
    "biological_report_sequence_source_data.py": (
        "_load_biological_fasta_records",
        "_load_biological_protein_region_context_records",
        "_load_biological_variant_fasta_records",
        "_load_biological_variant_peptide_records",
    ),
    "biological_report_annotation_source_data.py": (
        "_build_biological_annotation_mapping_report",
        "_load_biological_complex_membership_records",
        "_load_biological_custom_annotation_records",
        "_load_biological_pathway_membership_records",
    ),
    "biological_report_quantification_analysis.py": (
        "BiologicalQuantificationAnalysis",
        "_build_biological_quantification_analysis",
    ),
    "biological_report_regulator_analysis.py": (
        "BiologicalRegulatorAnalysisReports",
        "_build_biological_regulator_analysis_reports",
    ),
    "biological_report_protein_evidence.py": (
        "BiologicalProteinEvidenceReports",
        "_build_biological_protein_evidence_reports",
    ),
    "biological_report_experiment_review.py": (
        "_build_biological_experiment_review_reports",
    ),
    "biological_report_experiment_review_contracts.py": (
        "BiologicalExperimentReviewReports",
    ),
    "biological_report_experiment_diagnostics.py": (
        "BiologicalExperimentDiagnosticsReports",
        "_build_biological_experiment_diagnostics_reports",
    ),
    "biological_report_experiment_confidence_assembly.py": (
        "_build_biological_experiment_confidence_report",
    ),
    "biological_report_quant_table_supporting_reports.py": (
        "BiologicalQuantTableSupportingReports",
        "_build_biological_quant_table_supporting_reports",
    ),
    "biological_report_quant_table_foundation_reports.py": (
        "BiologicalQuantTableFoundationReports",
        "_build_biological_quant_table_foundation_reports",
    ),
    "biological_report_quant_table_evidence_reports.py": (
        "BiologicalQuantTableEvidenceReports",
        "_build_biological_quant_table_evidence_reports",
    ),
    "biological_report_quant_table_review_reports.py": (
        "BiologicalQuantTableReviewReports",
        "_build_biological_quant_table_review_reports",
    ),
    "biological_report_quant_table_interpretation_reports.py": (
        "BiologicalQuantTableInterpretationReports",
        "_build_biological_quant_table_interpretation_reports",
    ),
    "biological_report_bundle_summary.py": (
        "_build_biological_result_report_summary",
    ),
    "biological_report_protein_claim_candidates.py": (
        "_build_biological_protein_claim_candidates",
    ),
    "biological_report_pathway_claim_candidates.py": (
        "_build_biological_pathway_claim_candidates",
    ),
    "biological_report_regulator_claim_candidates.py": (
        "_build_biological_regulator_claim_candidates",
    ),
    "biological_report_protein_hypothesis_candidates.py": (
        "_build_biological_protein_hypothesis_candidates",
    ),
    "biological_report_pathway_hypothesis_candidates.py": (
        "_build_biological_pathway_hypothesis_candidates",
    ),
    "biological_report_regulator_hypothesis_candidates.py": (
        "_build_biological_regulator_hypothesis_candidates",
    ),
    "biological_report_hypothesis_scoring.py": (
        "_protein_hypothesis_base_confidence",
        "_pathway_hypothesis_base_confidence",
        "_regulator_hypothesis_base_confidence",
        "_evidence_tier_score",
        "_confidence_tier_score",
        "_pathway_confidence_score",
    ),
    "biological_report_hypothesis_evidence.py": (
        "_graph_node_ids_from_cards",
        "_protein_hypothesis_opposing_evidence",
        "_pathway_hypothesis_supporting_protein_refs",
        "_pathway_hypothesis_opposing_evidence",
        "_regulator_hypothesis_opposing_evidence",
    ),
    "biological_report_ranking.py": (
        "_build_biological_pathway_ranking_candidates",
        "_build_biological_protein_ranking_candidates",
    ),
    "biological_report_ranking_support.py": (
        "_mean",
        "_tier_score",
        "_biological_result_uncertainty",
    ),
    "biological_report_protein_ranking.py": (
        "_build_biological_protein_ranking_candidates",
    ),
    "biological_report_protein_ranking_scoring.py": (
        "_build_protein_annotation_score",
        "_build_protein_confidence_score",
        "_build_protein_ranking_penalties",
        "_build_protein_reproducibility_score",
        "_build_protein_support_score",
    ),
    "biological_report_pathway_ranking.py": (
        "_build_biological_pathway_ranking_candidates",
    ),
    "biological_report_pathway_member_metrics.py": (
        "BiologicalPathwayMemberMetrics",
        "_build_biological_pathway_abundance",
        "_build_biological_pathway_member_metrics",
        "_build_biological_pathway_ranking_penalties",
        "_build_biological_pathway_reproducibility",
        "_build_biological_pathway_support_strength",
    ),
    "biological_report_activity_exports.py": (
        "BiologicalActivityExportNames",
        "write_biological_activity_exports",
    ),
    "biological_report_compartment_activity_exports.py": (
        "BiologicalCompartmentActivityExportNames",
        "_write_biological_compartment_activity_exports",
    ),
    "biological_report_pathway_activity_exports.py": (
        "BiologicalPathwayActivityExportNames",
        "_write_biological_pathway_activity_exports",
    ),
    "biological_report_complex_activity_exports.py": (
        "BiologicalComplexActivityExportNames",
        "_write_biological_complex_activity_exports",
    ),
    "biological_report_scientific_export_contracts.py": (
        "BiologicalScientificExportNames",
    ),
    "biological_report_scientific_exports.py": (
        "render_biological_report_section_confidence_tsv",
        "render_biological_result_report_summary_tsv",
        "write_biological_scientific_exports",
    ),
    "biological_report_scientific_export_name_building.py": (
        "_build_biological_scientific_export_names",
    ),
    "biological_report_scientific_optional_exports.py": (),
    "biological_report_ranking_exports.py": (
        "BiologicalRankingExportNames",
        "_write_biological_optional_ranking_exports",
    ),
    "biological_report_claim_exports.py": (
        "BiologicalClaimExportNames",
        "_write_biological_optional_claim_exports",
    ),
    "biological_report_hypothesis_exports.py": (
        "BiologicalHypothesisExportNames",
        "_write_biological_optional_hypothesis_exports",
    ),
    "biological_report_regulator_exports.py": (
        "BiologicalRegulatorExportNames",
        "_write_biological_optional_regulator_exports",
    ),
    "biological_report_scientific_required_exports.py": (
        "BiologicalScientificRequiredExportNames",
        "_write_biological_required_scientific_exports",
    ),
    "biological_report_scientific_analysis_exports.py": (
        "BiologicalScientificAnalysisExportNames",
        "_write_biological_analysis_scientific_exports",
    ),
    "biological_report_scientific_interpretation_exports.py": (
        "BiologicalScientificInterpretationExportNames",
        "_write_biological_interpretation_scientific_exports",
    ),
    "biological_report_scientific_summary_tables.py": (
        "render_biological_report_section_confidence_tsv",
        "render_biological_result_report_summary_tsv",
    ),
    "biological_report_visual_export_contracts.py": (
        "BiologicalVisualExportNames",
    ),
    "biological_report_visual_export_naming.py": (
        "_build_biological_visual_export_names",
    ),
    "biological_report_visual_exports.py": (
        "write_biological_visual_exports",
    ),
    "biological_report_contextual_exports.py": (
        "BiologicalContextualExportNames",
        "write_biological_contextual_exports",
    ),
    "biological_report_annotation_context_exports.py": (
        "BiologicalAnnotationContextExportNames",
        "_write_biological_annotation_context_exports",
    ),
    "biological_report_sample_context_exports.py": (
        "BiologicalCohortContextExportNames",
        "BiologicalTissueContextExportNames",
        "_write_biological_cohort_context_exports",
        "_write_biological_tissue_context_exports",
    ),
    "biological_report_molecular_context_exports.py": (
        "BiologicalDrugTargetExportNames",
        "BiologicalDiseasePhenotypeExportNames",
        "_write_biological_drug_target_exports",
        "_write_biological_disease_phenotype_exports",
    ),
    "biological_report_html_scientific_artifact_inventory.py": (
        "_build_biological_scientific_artifact_sections",
    ),
    "biological_report_html_contextual_artifact_inventory.py": (
        "_build_biological_contextual_artifact_sections",
    ),
    "biological_report_html_activity_artifact_inventory.py": (
        "_build_biological_activity_artifact_sections",
    ),
    "biological_report_html_visual_artifact_inventory.py": (
        "_build_biological_visual_artifact_sections",
    ),
    "biological_report_assembly.py": (
        "build_biological_result_report_bundle",
        "build_biological_result_report_bundle_from_quant_table",
    ),
    "biological_report_quant_table_input.py": (
        "build_biological_result_report_bundle_from_quant_table",
    ),
    "biological_report_quant_table_bundle_building.py": (
        "_build_biological_result_report_bundle_from_quant_table_owned",
    ),
    "biological_report_quant_table_build_options.py": (
        "BiologicalReportQuantTableBuildOptions",
        "_build_biological_report_quant_table_build_options",
    ),
    "biological_report_quant_table_bundle_stages.py": (
        "BiologicalQuantTableBundleStages",
        "_build_biological_quant_table_bundle_stages",
    ),
    "biological_report_ms1_feature_quant_table.py": (
        "_build_biological_quant_table_from_ms1_feature_input",
        "_resolve_biological_ms1_feature_mapping",
    ),
    "biological_report_html_support.py": (
        "_format_optional_float",
        "_render_biological_report_section_confidence_table_html",
        "_render_section_heading_html",
    ),
    "biological_report_html_scientific_confidence_tables.py": (
        "_render_experiment_confidence_table_html",
        "_render_foreground_background_model_table_html",
    ),
    "biological_report_html_scientific_claim_tables.py": (
        "_render_biological_claim_validation_table_html",
        "_render_biological_hypothesis_table_html",
    ),
    "biological_report_html_scientific_ranking_tables.py": (
        "_render_protein_mechanism_card_table_html",
        "_render_evidence_aware_ranking_table_html",
    ),
    "biological_report_html_contextual_tables.py": (
        "_render_regulator_inference_table_html",
        "_render_drug_target_table_html",
        "_render_disease_phenotype_table_html",
        "_render_tissue_cell_type_context_table_html",
        "_render_cohort_stratification_table_html",
        "_render_compartment_biology_table_html",
        "_render_pathway_activity_table_html",
        "_render_complex_activity_table_html",
    ),
    "biological_report_html_molecular_interpretation_tables.py": (
        "_render_regulator_inference_table_html",
        "_render_drug_target_table_html",
        "_render_disease_phenotype_table_html",
    ),
    "biological_report_html_regulator_tables.py": (
        "_render_regulator_inference_table_html",
    ),
    "biological_report_html_drug_target_tables.py": (
        "_render_drug_target_table_html",
    ),
    "biological_report_html_disease_phenotype_tables.py": (
        "_render_disease_phenotype_table_html",
    ),
    "biological_report_html_sample_context_tables.py": (
        "_render_tissue_cell_type_context_table_html",
        "_render_cohort_stratification_table_html",
    ),
    "biological_report_html_activity_tables.py": (
        "_render_compartment_biology_table_html",
        "_render_pathway_activity_table_html",
        "_render_complex_activity_table_html",
    ),
    "biological_report_html_compartment_tables.py": (
        "_render_compartment_biology_table_html",
    ),
    "biological_report_html_pathway_activity_tables.py": (
        "_render_pathway_activity_table_html",
    ),
    "biological_report_html_complex_activity_tables.py": (
        "_render_complex_activity_table_html",
    ),
    "biological_report_html_artifact_inventory.py": (
        "_render_biological_report_artifact_inventory_html",
    ),
    "biological_report_html_report_summary.py": (
        "_render_biological_report_summary_html",
    ),
    "biological_report_html_report_sections.py": (
        "_render_biological_report_section_blocks_html",
    ),
    "biological_report_html.py": ("_render_biological_result_report_html",),
    "biological_report_export_writing.py": (
        "BiologicalResultReportExportNames",
        "_write_biological_result_report_export_names",
    ),
    "biological_report_export_finalization.py": (
        "_finalize_biological_result_report_export",
    ),
    "biological_report_rendering.py": (
        "export_biological_result_report_bundle",
        "write_biological_result_report_bundle",
    ),
}


def test_biological_report_modules_stay_under_one_thousand_lines() -> None:
    violations: list[str] = []
    for path in BIOLOGICAL_REPORT_MODULES:
        line_count = sum(1 for _ in path.open(encoding="utf-8"))
        if line_count > BIOLOGICAL_REPORT_LINE_LIMIT:
            violations.append(
                f"{path.relative_to(WORKFLOW_ROOT)} has {line_count} lines"
            )
    assert not violations, "\n".join(violations)


def test_biological_report_submodules_expose_owned_surfaces() -> None:
    missing_symbols: list[str] = []
    for filename, symbols in MODULE_SURFACES.items():
        module = ast.parse((REPORTS_ROOT / filename).read_text(encoding="utf-8"))
        defined_symbols = {
            node.name
            for node in module.body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        }
        defined_symbols.update(
            target.id
            for node in module.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        )
        for symbol in symbols:
            if symbol not in defined_symbols:
                missing_symbols.append(f"{filename} missing {symbol}")
    assert not missing_symbols, "\n".join(missing_symbols)


def test_biological_reporting_facade_delegates_to_split_owners() -> None:
    module = ast.parse(
        (REPORTS_ROOT / "biological_reporting.py").read_text(encoding="utf-8")
    )
    import_map = {
        node.module: {alias.name for alias in node.names}
        for node in module.body
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    exported_names: set[str] = set()
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in node.targets
        ):
            continue
        if isinstance(node.value, ast.List | ast.Tuple):
            exported_names.update(
                element.value
                for element in node.value.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            )

    assert import_map[
        "bijux_proteomics.workflow.reports.biological_report_assembly"
    ] >= {
        "build_biological_result_report_bundle",
        "build_biological_result_report_bundle_from_quant_table",
    }
    assert import_map["bijux_proteomics.workflow.reports.biological_report_models"] >= {
        "BiologicalReportSectionConfidenceEntry",
        "BiologicalReportSectionConfidenceLabel",
        "BiologicalReportSectionKey",
        "BiologicalResultReportArtifactPaths",
        "BiologicalResultReportBundle",
        "BiologicalResultReportExportManifest",
        "BiologicalResultReportSummary",
        "BiologicalResultSelectionPolicy",
    }
    assert import_map[
        "bijux_proteomics.workflow.reports.biological_report_rendering"
    ] >= {
        "export_biological_result_report_bundle",
        "render_biological_report_section_confidence_tsv",
        "render_biological_result_report_summary_tsv",
    }
    assert import_map[
        "bijux_proteomics.review.explanations.volcano_plots"
    ] >= {"VolcanoReviewPolicy"}
    assert exported_names >= {
        "BiologicalReportSectionConfidenceEntry",
        "BiologicalReportSectionConfidenceLabel",
        "BiologicalReportSectionKey",
        "BiologicalResultReportArtifactPaths",
        "BiologicalResultReportBundle",
        "BiologicalResultReportExportManifest",
        "BiologicalResultReportSummary",
        "BiologicalResultSelectionPolicy",
        "VolcanoReviewPolicy",
        "build_biological_result_report_bundle",
        "build_biological_result_report_bundle_from_quant_table",
        "export_biological_result_report_bundle",
        "render_biological_report_section_confidence_tsv",
        "render_biological_result_report_summary_tsv",
    }


def test_biological_report_assembly_forwards_ms1_input_ownership() -> None:
    module = ast.parse(
        (REPORTS_ROOT / "biological_report_assembly.py").read_text(encoding="utf-8")
    )
    wrapper = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "build_biological_result_report_bundle"
    )
    delegated_call = next(
        node.value
        for node in ast.walk(wrapper)
        if isinstance(node, ast.Return)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id
        == "build_biological_result_report_bundle_from_ms1_feature_input"
    )
    forwarded_keywords = {
        keyword.arg
        for keyword in delegated_call.keywords
        if keyword.arg is not None
    }

    assert forwarded_keywords >= {
        "mapping",
        "aggregation_method",
        "top_n",
        "normalization_method",
        "chunk_size_rows",
    }


def test_biological_report_assembly_forwards_quant_table_input_ownership() -> None:
    module = ast.parse(
        (REPORTS_ROOT / "biological_report_assembly.py").read_text(encoding="utf-8")
    )
    wrapper = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "build_biological_result_report_bundle_from_quant_table"
    )
    delegated_call = next(
        node.value
        for node in ast.walk(wrapper)
        if isinstance(node, ast.Return)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "build_from_quant_table_owned"
    )
    forwarded_keywords = {
        keyword.arg
        for keyword in delegated_call.keywords
        if keyword.arg is not None
    }

    assert forwarded_keywords >= {
        "proteins_fasta_path",
        "normalization_method",
        "selection_policy",
        "volcano_policy",
        "run_qc_reports",
        "run_qc_assessments",
    }
