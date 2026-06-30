# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Biological report assembly over governed quantification and review surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.ptm import PtmEvidenceCardReport
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantRollupMethod,
)
from bijux_proteomics.review.explanations.volcano_plots import VolcanoReviewPolicy
from bijux_proteomics.study import (
    ExperimentDesign,
    LcmsRunQcReport,
    QcRunAssessmentReport,
    coerce_experiment_design,
)

if TYPE_CHECKING:
    from bijux_proteomics_lab.handoffs.qc_feedback import LabRunQcFeedbackReport

from bijux_proteomics.workflow.reports.biological_report_bundle_assembly import (
    _assemble_biological_result_report_bundle,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
    BiologicalResultSelectionPolicy,
)
from bijux_proteomics.workflow.reports.biological_report_quant_table_review_reports import (
    _build_biological_quant_table_review_reports,
)
from bijux_proteomics.workflow.reports.biological_report_quantification_analysis import (
    _build_biological_quantification_analysis,
)
from bijux_proteomics.workflow.reports.biological_report_quant_table_supporting_reports import (
    _build_biological_quant_table_supporting_reports,
)


def build_biological_result_report_bundle(
    input_tsv_path: Path,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    proteins_fasta_path: Path,
    variant_proteins_fasta_path: Path | None = None,
    variant_peptide_tsv_path: Path | None = None,
    protocol_context_tsv_path: Path | None = None,
    annotation_tsv_path: Path | None = None,
    context_annotation_tsv_path: Path | None = None,
    protein_region_context_tsv_path: Path | None = None,
    go_annotation_tsv_path: Path | None = None,
    pathway_membership_tsv_path: Path | None = None,
    complex_membership_tsv_path: Path | None = None,
    regulator_evidence_tsv_path: Path | None = None,
    regulator_site_signal_tsv_path: Path | None = None,
    ptm_evidence_card_report: PtmEvidenceCardReport | None = None,
    mapping: Ms1FeatureColumnMapping | None = None,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    top_n: int = 3,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    selection_policy: BiologicalResultSelectionPolicy | None = None,
    volcano_policy: VolcanoReviewPolicy | None = None,
    lab_run_qc_feedback_report: LabRunQcFeedbackReport | None = None,
    run_qc_reports: tuple[LcmsRunQcReport, ...] = (),
    run_qc_assessments: tuple[QcRunAssessmentReport, ...] = (),
    chunk_size_rows: int | None = None,
) -> BiologicalResultReportBundle:
    """Build a biological result bundle over one governed protein LFQ workflow."""

    from bijux_proteomics.workflow.reports.biological_report_ms1_feature_input import (
        build_biological_result_report_bundle_from_ms1_feature_input,
    )

    return build_biological_result_report_bundle_from_ms1_feature_input(
        input_tsv_path,
        design_entries,
        proteins_fasta_path=proteins_fasta_path,
        variant_proteins_fasta_path=variant_proteins_fasta_path,
        variant_peptide_tsv_path=variant_peptide_tsv_path,
        protocol_context_tsv_path=protocol_context_tsv_path,
        annotation_tsv_path=annotation_tsv_path,
        context_annotation_tsv_path=context_annotation_tsv_path,
        protein_region_context_tsv_path=protein_region_context_tsv_path,
        go_annotation_tsv_path=go_annotation_tsv_path,
        pathway_membership_tsv_path=pathway_membership_tsv_path,
        complex_membership_tsv_path=complex_membership_tsv_path,
        regulator_evidence_tsv_path=regulator_evidence_tsv_path,
        regulator_site_signal_tsv_path=regulator_site_signal_tsv_path,
        ptm_evidence_card_report=ptm_evidence_card_report,
        mapping=mapping,
        aggregation_method=aggregation_method,
        top_n=top_n,
        normalization_method=normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
        selection_policy=selection_policy,
        volcano_policy=volcano_policy,
        lab_run_qc_feedback_report=lab_run_qc_feedback_report,
        run_qc_reports=run_qc_reports,
        run_qc_assessments=run_qc_assessments,
        chunk_size_rows=chunk_size_rows,
    )


def build_biological_result_report_bundle_from_quant_table(
    quant_table: LabelFreeQuantTable,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    proteins_fasta_path: Path,
    variant_proteins_fasta_path: Path | None = None,
    variant_peptide_tsv_path: Path | None = None,
    protocol_context_tsv_path: Path | None = None,
    annotation_tsv_path: Path | None = None,
    context_annotation_tsv_path: Path | None = None,
    protein_region_context_tsv_path: Path | None = None,
    go_annotation_tsv_path: Path | None = None,
    pathway_membership_tsv_path: Path | None = None,
    complex_membership_tsv_path: Path | None = None,
    regulator_evidence_tsv_path: Path | None = None,
    regulator_site_signal_tsv_path: Path | None = None,
    ptm_evidence_card_report: PtmEvidenceCardReport | None = None,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    selection_policy: BiologicalResultSelectionPolicy | None = None,
    volcano_policy: VolcanoReviewPolicy | None = None,
    lab_run_qc_feedback_report: LabRunQcFeedbackReport | None = None,
    run_qc_reports: tuple[LcmsRunQcReport, ...] = (),
    run_qc_assessments: tuple[QcRunAssessmentReport, ...] = (),
) -> BiologicalResultReportBundle:
    """Build a biological result bundle from one governed protein quant table."""

    experiment_design = coerce_experiment_design(design_entries)
    quantification_analysis = _build_biological_quantification_analysis(
        quant_table,
        experiment_design,
        normalization_method=normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
        selection_policy=selection_policy,
        protocol_context_tsv_path=protocol_context_tsv_path,
    )
    design_entries = quantification_analysis.design_entries
    active_selection_policy = quantification_analysis.selection_policy
    normalized_table = quantification_analysis.normalized_table
    resolved_condition_a = quantification_analysis.resolved_condition_a
    resolved_condition_b = quantification_analysis.resolved_condition_b
    differential_report = quantification_analysis.differential_report
    supporting_reports = _build_biological_quant_table_supporting_reports(
        normalized_table=normalized_table,
        differential_report=differential_report,
        experiment_design=experiment_design,
        design_entries=design_entries,
        active_selection_policy=active_selection_policy,
        proteins_fasta_path=proteins_fasta_path,
        variant_proteins_fasta_path=variant_proteins_fasta_path,
        variant_peptide_tsv_path=variant_peptide_tsv_path,
        protocol_context_tsv_path=protocol_context_tsv_path,
        annotation_tsv_path=annotation_tsv_path,
        context_annotation_tsv_path=context_annotation_tsv_path,
        protein_region_context_tsv_path=protein_region_context_tsv_path,
        go_annotation_tsv_path=go_annotation_tsv_path,
        pathway_membership_tsv_path=pathway_membership_tsv_path,
        complex_membership_tsv_path=complex_membership_tsv_path,
        regulator_evidence_tsv_path=regulator_evidence_tsv_path,
        regulator_site_signal_tsv_path=regulator_site_signal_tsv_path,
        ptm_evidence_card_report=ptm_evidence_card_report,
        lab_run_qc_feedback_report=lab_run_qc_feedback_report,
    )
    source_data = supporting_reports.source_data
    context_reports = supporting_reports.context_reports
    enrichment_reports = supporting_reports.enrichment_reports
    regulator_reports = supporting_reports.regulator_reports
    protein_evidence_reports = supporting_reports.protein_evidence_reports
    review_reports = _build_biological_quant_table_review_reports(
        normalized_table=normalized_table,
        differential_report=differential_report,
        experiment_design=experiment_design,
        design_entries=design_entries,
        active_selection_policy=active_selection_policy,
        protein_cards=protein_evidence_reports.protein_cards,
        protein_mechanism_cards=protein_evidence_reports.protein_mechanism_cards,
        pathway_activity_report=enrichment_reports.pathway_activity_report,
        pathway_enrichment_report=enrichment_reports.pathway_enrichment_report,
        regulator_inference_report=regulator_reports.regulator_inference_report,
        resolved_condition_a=resolved_condition_a,
        resolved_condition_b=resolved_condition_b,
        protocol_context_tsv_path=protocol_context_tsv_path,
        run_qc_reports=run_qc_reports,
        run_qc_assessments=run_qc_assessments,
        volcano_policy=volcano_policy,
    )
    return _assemble_biological_result_report_bundle(
        normalized_table=normalized_table,
        differential_report=differential_report,
        graph_report=protein_evidence_reports.graph_report,
        annotation_report=source_data.annotation_report,
        protein_cards=protein_evidence_reports.protein_cards,
        protein_mechanism_cards=protein_evidence_reports.protein_mechanism_cards,
        experiment_confidence_report=review_reports.experiment_confidence_report,
        evidence_aware_ranking_report=review_reports.evidence_aware_ranking_report,
        claim_validation_report=review_reports.claim_validation_report,
        biological_hypothesis_report=review_reports.biological_hypothesis_report,
        foreground_background_model=enrichment_reports.foreground_background_model,
        regulator_evidence_import_report=(
            regulator_reports.regulator_evidence_import_report
        ),
        regulator_inference_report=regulator_reports.regulator_inference_report,
        context_import_report=context_reports.context_import_report,
        context_mapping_report=context_reports.context_mapping_report,
        cohort_stratification_report=review_reports.cohort_stratification_report,
        tissue_cell_type_context_report=context_reports.tissue_cell_type_context_report,
        drug_target_report=context_reports.drug_target_report,
        disease_phenotype_report=context_reports.disease_phenotype_report,
        compartment_biology_report=context_reports.compartment_biology_report,
        pathway_activity_report=enrichment_reports.pathway_activity_report,
        complex_activity_report=enrichment_reports.complex_activity_report,
        go_enrichment_report=enrichment_reports.go_enrichment_report,
        pathway_enrichment_report=enrichment_reports.pathway_enrichment_report,
        complex_enrichment_report=enrichment_reports.complex_enrichment_report,
        volcano_review=review_reports.volcano_review,
        heatmap_report=review_reports.heatmap_report,
        sample_exploration_report=review_reports.sample_exploration_report,
        selection_policy=active_selection_policy,
    )
