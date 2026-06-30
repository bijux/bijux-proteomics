# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stage preparation for biological quant-table bundle assembly."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import LabelFreeQuantTable
from bijux_proteomics.study import ExperimentDesign, coerce_experiment_design
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultSelectionPolicy,
)
from bijux_proteomics.workflow.reports.biological_report_quant_table_review_reports import (
    BiologicalQuantTableReviewReports,
    _build_biological_quant_table_review_reports,
)
from bijux_proteomics.workflow.reports.biological_report_quant_table_supporting_reports import (
    BiologicalQuantTableSupportingReports,
    _build_biological_quant_table_supporting_reports,
)
from bijux_proteomics.workflow.reports.biological_report_quantification_analysis import (
    BiologicalQuantificationAnalysis,
    _build_biological_quantification_analysis,
)

if TYPE_CHECKING:
    from bijux_proteomics.workflow.reports.biological_report_quant_table_build_options import (
        BiologicalReportQuantTableBuildOptions,
    )


class BiologicalQuantTableBundleStages(NamedTuple):
    """Prepared stage outputs for one biological quant-table bundle."""

    experiment_design: ExperimentDesign
    design_entries: tuple[ExperimentalDesignEntry, ...]
    active_selection_policy: BiologicalResultSelectionPolicy
    quantification_analysis: BiologicalQuantificationAnalysis
    supporting_reports: BiologicalQuantTableSupportingReports
    review_reports: BiologicalQuantTableReviewReports


def _build_biological_quant_table_bundle_stages(
    quant_table: LabelFreeQuantTable,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    build_options: BiologicalReportQuantTableBuildOptions,
) -> BiologicalQuantTableBundleStages:
    experiment_design = coerce_experiment_design(design_entries)
    quantification_analysis = _build_biological_quantification_analysis(
        quant_table,
        experiment_design,
        normalization_method=build_options.normalization_method,
        condition_a=build_options.condition_a,
        condition_b=build_options.condition_b,
        selection_policy=build_options.selection_policy,
        protocol_context_tsv_path=build_options.protocol_context_tsv_path,
    )
    stage_design_entries = quantification_analysis.design_entries
    active_selection_policy = quantification_analysis.selection_policy
    normalized_table = quantification_analysis.normalized_table
    differential_report = quantification_analysis.differential_report
    supporting_reports = _build_biological_quant_table_supporting_reports(
        normalized_table=normalized_table,
        differential_report=differential_report,
        experiment_design=experiment_design,
        design_entries=stage_design_entries,
        active_selection_policy=active_selection_policy,
        proteins_fasta_path=build_options.proteins_fasta_path,
        variant_proteins_fasta_path=build_options.variant_proteins_fasta_path,
        variant_peptide_tsv_path=build_options.variant_peptide_tsv_path,
        protocol_context_tsv_path=build_options.protocol_context_tsv_path,
        annotation_tsv_path=build_options.annotation_tsv_path,
        context_annotation_tsv_path=build_options.context_annotation_tsv_path,
        protein_region_context_tsv_path=build_options.protein_region_context_tsv_path,
        go_annotation_tsv_path=build_options.go_annotation_tsv_path,
        pathway_membership_tsv_path=build_options.pathway_membership_tsv_path,
        complex_membership_tsv_path=build_options.complex_membership_tsv_path,
        regulator_evidence_tsv_path=build_options.regulator_evidence_tsv_path,
        regulator_site_signal_tsv_path=build_options.regulator_site_signal_tsv_path,
        ptm_evidence_card_report=build_options.ptm_evidence_card_report,
        lab_run_qc_feedback_report=build_options.lab_run_qc_feedback_report,
    )
    review_reports = _build_biological_quant_table_review_reports(
        normalized_table=normalized_table,
        differential_report=differential_report,
        experiment_design=experiment_design,
        design_entries=stage_design_entries,
        active_selection_policy=active_selection_policy,
        protein_cards=supporting_reports.protein_evidence_reports.protein_cards,
        protein_mechanism_cards=(
            supporting_reports.protein_evidence_reports.protein_mechanism_cards
        ),
        pathway_activity_report=supporting_reports.enrichment_reports.pathway_activity_report,
        pathway_enrichment_report=(
            supporting_reports.enrichment_reports.pathway_enrichment_report
        ),
        regulator_inference_report=(
            supporting_reports.regulator_reports.regulator_inference_report
        ),
        resolved_condition_a=quantification_analysis.resolved_condition_a,
        resolved_condition_b=quantification_analysis.resolved_condition_b,
        protocol_context_tsv_path=build_options.protocol_context_tsv_path,
        run_qc_reports=build_options.run_qc_reports,
        run_qc_assessments=build_options.run_qc_assessments,
        volcano_policy=build_options.volcano_policy,
    )
    return BiologicalQuantTableBundleStages(
        experiment_design=experiment_design,
        design_entries=stage_design_entries,
        active_selection_policy=active_selection_policy,
        quantification_analysis=quantification_analysis,
        supporting_reports=supporting_reports,
        review_reports=review_reports,
    )


__all__ = [
    "BiologicalQuantTableBundleStages",
    "_build_biological_quant_table_bundle_stages",
]
