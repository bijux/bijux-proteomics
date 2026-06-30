# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Quant-table biological report bundle building over governed workflow stages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.ptm import PtmEvidenceCardReport
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    NormalizationMethod,
)
from bijux_proteomics.review.explanations.volcano_plots import VolcanoReviewPolicy
from bijux_proteomics.study import (
    ExperimentDesign,
    LcmsRunQcReport,
    QcRunAssessmentReport,
)
from bijux_proteomics.workflow.reports.biological_report_bundle_assembly import (
    _assemble_biological_result_report_bundle,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
    BiologicalResultSelectionPolicy,
)
from bijux_proteomics.workflow.reports.biological_report_quant_table_bundle_stages import (
    _build_biological_quant_table_bundle_stages,
)


@dataclass(frozen=True)
class BiologicalReportQuantTableBuildOptions:
    """Governed options and supporting sources for quant-table report building."""

    proteins_fasta_path: Path
    variant_proteins_fasta_path: Path | None = None
    variant_peptide_tsv_path: Path | None = None
    protocol_context_tsv_path: Path | None = None
    annotation_tsv_path: Path | None = None
    context_annotation_tsv_path: Path | None = None
    protein_region_context_tsv_path: Path | None = None
    go_annotation_tsv_path: Path | None = None
    pathway_membership_tsv_path: Path | None = None
    complex_membership_tsv_path: Path | None = None
    regulator_evidence_tsv_path: Path | None = None
    regulator_site_signal_tsv_path: Path | None = None
    ptm_evidence_card_report: PtmEvidenceCardReport | None = None
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN
    condition_a: str | None = None
    condition_b: str | None = None
    selection_policy: BiologicalResultSelectionPolicy | None = None
    volcano_policy: VolcanoReviewPolicy | None = None
    lab_run_qc_feedback_report: object | None = None
    run_qc_reports: tuple[LcmsRunQcReport, ...] = ()
    run_qc_assessments: tuple[QcRunAssessmentReport, ...] = ()


def _build_biological_result_report_bundle_from_quant_table_owned(
    quant_table: LabelFreeQuantTable,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    build_options: BiologicalReportQuantTableBuildOptions,
) -> BiologicalResultReportBundle:
    bundle_stages = _build_biological_quant_table_bundle_stages(
        quant_table,
        design_entries,
        build_options=build_options,
    )
    quantification_analysis = bundle_stages.quantification_analysis
    supporting_reports = bundle_stages.supporting_reports
    review_reports = bundle_stages.review_reports
    source_data = supporting_reports.source_data
    context_reports = supporting_reports.context_reports
    enrichment_reports = supporting_reports.enrichment_reports
    regulator_reports = supporting_reports.regulator_reports
    protein_evidence_reports = supporting_reports.protein_evidence_reports
    return _assemble_biological_result_report_bundle(
        normalized_table=quantification_analysis.normalized_table,
        differential_report=quantification_analysis.differential_report,
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
        selection_policy=bundle_stages.active_selection_policy,
    )
