# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Biological report assembly over governed quantification and review surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from bijux_proteomics.interpretation.go_enrichment import (
    parse_go_annotation_table,
)
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.lab.protocol_context import (
    parse_lab_protocol_context_table,
    require_single_lab_protocol_context,
)
from bijux_proteomics.ptm import PtmEvidenceCardReport
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
)
from bijux_proteomics.quantification.missingness import (
    build_missingness_condition_summary_report,
)
from bijux_proteomics.quantification.normalization import (
    normalize_label_free_table,
)
from bijux_proteomics.quantification.provenance import (
    HeatmapMissingValuePolicy,
    HeatmapPreparationPolicy,
    build_heatmap_preparation_report,
    build_sample_exploration_report,
)
from bijux_proteomics.quantification.statistics import (
    apply_benjamini_hochberg,
    build_differential_abundance_report,
    build_power_estimation_report,
)
from bijux_proteomics.review.explanations.volcano_plots import (
    VolcanoReviewPolicy,
    build_quantification_volcano_review,
)
from bijux_proteomics.study import (
    ExperimentDesign,
    LcmsRunQcReport,
    QcRunAssessmentReport,
    build_experiment_confidence_report,
    build_experiment_feasibility_report,
    build_protocol_consistency_report,
    coerce_experiment_design,
)
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
    ProteinEvidenceCardSelectionPolicy,
    build_protein_evidence_card_report,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    build_protein_mechanism_card_report,
)
from bijux_proteomics.workflow.studies.cohort_stratification import (
    CohortStratificationReport,
    build_cohort_stratification_report,
)
from bijux_proteomics.workflow.reports.biological_result_graph import (
    build_biological_result_graph_report,
)

if TYPE_CHECKING:
    from bijux_proteomics_lab.handoffs.qc_feedback import LabRunQcFeedbackReport

from bijux_proteomics.workflow.reports.biological_report_claims import (
    _build_biological_claim_validation_report,
    _build_biological_evidence_aware_ranking_report,
    _build_biological_hypothesis_report,
)
from bijux_proteomics.workflow.reports.biological_report_context_assembly import (
    _build_biological_context_reports,
)
from bijux_proteomics.workflow.reports.biological_report_enrichment_assembly import (
    _build_biological_enrichment_reports,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalReportSectionConfidenceLabel,
    BiologicalResultReportBundle,
    BiologicalResultReportSummary,
    BiologicalResultSelectionPolicy,
    _resolve_biological_result_selection_policy,
)
from bijux_proteomics.workflow.reports.biological_report_section_confidence import (
    _build_biological_report_section_confidence_entries,
    _count_section_confidence_labels,
)
from bijux_proteomics.workflow.reports.biological_report_selection import (
    _resolve_contrast,
    _select_heatmap_entity_ids,
    _select_significant_entity_ids,
)
from bijux_proteomics.workflow.reports.biological_report_regulator_analysis import (
    _build_biological_regulator_analysis_reports,
)
from bijux_proteomics.workflow.reports.biological_report_source_data import (
    _build_biological_report_source_data,
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
    design_entries = experiment_design.entries
    active_selection_policy = _resolve_biological_result_selection_policy(
        selection_policy,
        protocol_context_tsv_path=protocol_context_tsv_path,
    )
    normalized_table = normalize_label_free_table(
        quant_table,
        method=normalization_method,
    )
    if normalized_table.entity_level != QuantEntityLevel.PROTEIN:
        raise ValueError(
            "biological result reporting requires a protein-level quantification table"
        )
    if normalized_table.measure_kind != QuantMeasureKind.INTENSITY:
        raise ValueError(
            "biological result reporting requires intensity-based protein quantification"
        )
    resolved_condition_a, resolved_condition_b = _resolve_contrast(
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    differential_report = apply_benjamini_hochberg(
        build_differential_abundance_report(
            normalized_table,
            design_entries,
            condition_a=resolved_condition_a,
            condition_b=resolved_condition_b,
        )
    )
    source_data = _build_biological_report_source_data(
        normalized_table=normalized_table,
        differential_report=differential_report,
        proteins_fasta_path=proteins_fasta_path,
        variant_proteins_fasta_path=variant_proteins_fasta_path,
        variant_peptide_tsv_path=variant_peptide_tsv_path,
        annotation_tsv_path=annotation_tsv_path,
        pathway_membership_tsv_path=pathway_membership_tsv_path,
        complex_membership_tsv_path=complex_membership_tsv_path,
        protein_region_context_tsv_path=protein_region_context_tsv_path,
    )
    annotation_report = source_data.annotation_report
    context_reports = _build_biological_context_reports(
        normalized_table=normalized_table,
        experiment_design=experiment_design,
        design_entries=design_entries,
        differential_report=differential_report,
        differential_reference_entries=source_data.differential_reference_entries,
        annotation_report=annotation_report,
        pathway_records=source_data.pathway_records,
        active_selection_policy=active_selection_policy,
        context_annotation_tsv_path=context_annotation_tsv_path,
    )
    context_import_report = context_reports.context_import_report
    context_mapping_report = context_reports.context_mapping_report
    tissue_cell_type_context_report = context_reports.tissue_cell_type_context_report
    drug_target_report = context_reports.drug_target_report
    disease_phenotype_report = context_reports.disease_phenotype_report
    compartment_biology_report = context_reports.compartment_biology_report
    enrichment_reports = _build_biological_enrichment_reports(
        normalized_table=normalized_table,
        differential_report=differential_report,
        design_entries=design_entries,
        fasta_records=source_data.fasta_records,
        custom_annotations=source_data.custom_annotation_records,
        go_annotation_records=()
        if go_annotation_tsv_path is None
        else parse_go_annotation_table(go_annotation_tsv_path).accepted_records,
        pathway_records=source_data.pathway_records,
        complex_records=source_data.complex_records,
        active_selection_policy=active_selection_policy,
    )
    foreground_background_model = enrichment_reports.foreground_background_model
    go_enrichment_report = enrichment_reports.go_enrichment_report
    pathway_activity_report = enrichment_reports.pathway_activity_report
    pathway_enrichment_report = enrichment_reports.pathway_enrichment_report
    complex_activity_report = enrichment_reports.complex_activity_report
    complex_enrichment_report = enrichment_reports.complex_enrichment_report
    regulator_reports = _build_biological_regulator_analysis_reports(
        regulator_evidence_tsv_path=regulator_evidence_tsv_path,
        regulator_site_signal_tsv_path=regulator_site_signal_tsv_path,
        ptm_evidence_card_report=ptm_evidence_card_report,
        differential_report=differential_report,
        protein_refs_by_entity=normalized_table.entity_protein_refs,
        annotation_report=annotation_report,
        pathway_activity_report=pathway_activity_report,
    )
    regulator_evidence_import_report = (
        regulator_reports.regulator_evidence_import_report
    )
    regulator_inference_report = regulator_reports.regulator_inference_report
    protein_cards = build_protein_evidence_card_report(
        graph_report := build_biological_result_graph_report(
            normalized_table,
            differential_report,
            design_entries,
            max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
            min_absolute_log2_fold_change=active_selection_policy.min_absolute_log2_fold_change,
            lab_run_qc_feedback_report=lab_run_qc_feedback_report,
        ),
        normalized_table,
        differential_report,
        annotation_report,
        protein_sequences={
            record.canonical_accession: record.residues
            for record in source_data.fasta_records
        },
        protein_records=source_data.fasta_records,
        variant_protein_records=source_data.variant_fasta_records,
        variant_peptide_records=source_data.variant_peptide_records,
        selection_policy=ProteinEvidenceCardSelectionPolicy(
            max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
            min_absolute_log2_fold_change=(
                active_selection_policy.min_absolute_log2_fold_change
            ),
        ),
        sample_conditions={
            entry.sample_id: entry.condition for entry in design_entries
        },
        context_mapping_report=context_mapping_report,
        pathway_enrichment_report=pathway_enrichment_report,
        complex_enrichment_report=complex_enrichment_report,
        protein_region_context_records=source_data.protein_region_context_records,
        ptm_evidence_card_report=ptm_evidence_card_report,
    )
    protein_mechanism_cards = build_protein_mechanism_card_report(
        graph_report,
        protein_cards,
        ptm_evidence_card_report=ptm_evidence_card_report,
    )
    volcano_review = build_quantification_volcano_review(
        differential_report,
        protein_refs_by_entity=normalized_table.entity_protein_refs,
        policy=volcano_policy,
    )
    selected_entity_ids = _select_heatmap_entity_ids(
        differential_report,
        policy=active_selection_policy,
    )
    heatmap_report = build_heatmap_preparation_report(
        normalized_table,
        design_entries=design_entries,
        policy=HeatmapPreparationPolicy(
            entity_ids=selected_entity_ids,
            min_observed_fraction=active_selection_policy.heatmap_min_observed_fraction,
            max_entity_count=active_selection_policy.heatmap_max_entity_count,
            z_score_rows=True,
            missing_value_policy=HeatmapMissingValuePolicy.FILL_ROW_MEDIAN,
        ),
    )
    sample_exploration_report = build_sample_exploration_report(
        normalized_table,
        design_entries,
    )
    cohort_stratification_report: CohortStratificationReport | None = (
        build_cohort_stratification_report(
            normalized_table,
            experiment_design,
            condition_a=resolved_condition_a,
            condition_b=resolved_condition_b,
        )
    )
    if (
        cohort_stratification_report is not None
        and cohort_stratification_report.summary.field_count == 0
    ):
        cohort_stratification_report = None
    feasibility_report = build_experiment_feasibility_report(
        experiment_design,
        condition_a=resolved_condition_a,
        condition_b=resolved_condition_b,
    )
    protocol_consistency_report = None
    if protocol_context_tsv_path is not None:
        protocol_consistency_report = build_protocol_consistency_report(
            require_single_lab_protocol_context(
                parse_lab_protocol_context_table(protocol_context_tsv_path)
            ),
            run_qc_report=run_qc_reports[0] if len(run_qc_reports) == 1 else None,
        )
    experiment_confidence_report = build_experiment_confidence_report(
        experiment_design,
        validity_report=feasibility_report.validity_report,
        feasibility_report=feasibility_report,
        missingness_condition_summary_report=build_missingness_condition_summary_report(
            normalized_table,
            design_entries=design_entries,
        ),
        power_estimation_report=build_power_estimation_report(
            normalized_table,
            design_entries,
        ),
        run_qc_reports=run_qc_reports,
        run_qc_assessments=run_qc_assessments,
        protocol_consistency_report=protocol_consistency_report,
        warning_card_count=protein_cards.summary.warning_card_count,
        protein_card_count=protein_cards.summary.protein_result_count,
    )
    evidence_aware_ranking_report = _build_biological_evidence_aware_ranking_report(
        differential_report,
        protein_cards=protein_cards,
        protein_mechanism_cards=protein_mechanism_cards,
        experiment_confidence_report=experiment_confidence_report,
        pathway_enrichment_report=pathway_enrichment_report,
    )
    claim_validation_report = _build_biological_claim_validation_report(
        differential_report,
        protein_mechanism_cards=protein_mechanism_cards,
        pathway_activity_report=pathway_activity_report,
        regulator_inference_report=regulator_inference_report,
        selection_policy=active_selection_policy,
    )
    biological_hypothesis_report = _build_biological_hypothesis_report(
        claim_validation_report,
        protein_mechanism_cards=protein_mechanism_cards,
        pathway_activity_report=pathway_activity_report,
        regulator_inference_report=regulator_inference_report,
    )
    significant_protein_count = len(
        _select_significant_entity_ids(
            differential_report, policy=active_selection_policy
        )
    )
    section_confidence_entries = _build_biological_report_section_confidence_entries(
        experiment_confidence_report=experiment_confidence_report,
        evidence_aware_ranking_report=evidence_aware_ranking_report,
        claim_validation_report=claim_validation_report,
        biological_hypothesis_report=biological_hypothesis_report,
        foreground_background_model=foreground_background_model,
        regulator_inference_report=regulator_inference_report,
        drug_target_report=drug_target_report,
        disease_phenotype_report=disease_phenotype_report,
        cohort_stratification_report=cohort_stratification_report,
        tissue_cell_type_context_report=tissue_cell_type_context_report,
        compartment_biology_report=compartment_biology_report,
        pathway_activity_report=pathway_activity_report,
        complex_activity_report=complex_activity_report,
        protein_mechanism_cards=protein_mechanism_cards,
    )
    section_confidence_counts = _count_section_confidence_labels(
        section_confidence_entries
    )
    return BiologicalResultReportBundle(
        differential_report=differential_report,
        graph_report=graph_report,
        annotation_report=annotation_report,
        protein_cards=protein_cards,
        protein_mechanism_cards=protein_mechanism_cards,
        experiment_confidence_report=experiment_confidence_report,
        evidence_aware_ranking_report=evidence_aware_ranking_report,
        claim_validation_report=claim_validation_report,
        biological_hypothesis_report=biological_hypothesis_report,
        foreground_background_model=foreground_background_model,
        regulator_evidence_import_report=regulator_evidence_import_report,
        regulator_inference_report=regulator_inference_report,
        context_import_report=context_import_report,
        context_mapping_report=context_mapping_report,
        cohort_stratification_report=cohort_stratification_report,
        tissue_cell_type_context_report=tissue_cell_type_context_report,
        drug_target_report=drug_target_report,
        disease_phenotype_report=disease_phenotype_report,
        compartment_biology_report=compartment_biology_report,
        pathway_activity_report=pathway_activity_report,
        complex_activity_report=complex_activity_report,
        go_enrichment_report=go_enrichment_report,
        pathway_enrichment_report=pathway_enrichment_report,
        complex_enrichment_report=complex_enrichment_report,
        volcano_review=volcano_review,
        heatmap_report=heatmap_report,
        sample_exploration_report=sample_exploration_report,
        selection_policy=active_selection_policy,
        section_confidence_entries=section_confidence_entries,
        summary=BiologicalResultReportSummary(
            protein_count=len(normalized_table.entity_ids),
            significant_protein_count=significant_protein_count,
            sample_count=len(normalized_table.sample_ids),
            annotation_entry_count=len(annotation_report.result_entries),
            annotation_unmapped_count=len(annotation_report.unmapped_entries),
            protein_card_count=protein_cards.summary.protein_result_count,
            warning_card_count=protein_cards.summary.warning_card_count,
            tissue_mismatch_warning_count=(
                0
                if tissue_cell_type_context_report is None
                else tissue_cell_type_context_report.summary.mismatch_warning_count
            ),
            cohort_blocked_stratum_count=(
                0
                if cohort_stratification_report is None
                else cohort_stratification_report.summary.blocked_stratum_count
            ),
            cohort_subgroup_effect_count=(
                0
                if cohort_stratification_report is None
                else cohort_stratification_report.summary.subgroup_effect_count
            ),
            cohort_interaction_candidate_count=(
                0
                if cohort_stratification_report is None
                else cohort_stratification_report.summary.interaction_candidate_count
            ),
            experiment_confidence_score=experiment_confidence_report.summary.overall_score,
            experiment_confidence_tier=experiment_confidence_report.summary.overall_tier,
            low_confidence_component_count=(
                experiment_confidence_report.summary.low_confidence_component_count
            ),
            high_confidence_section_count=section_confidence_counts[
                BiologicalReportSectionConfidenceLabel.HIGH
            ],
            moderate_confidence_section_count=section_confidence_counts[
                BiologicalReportSectionConfidenceLabel.MODERATE
            ],
            weak_confidence_section_count=section_confidence_counts[
                BiologicalReportSectionConfidenceLabel.WEAK
            ],
            exploratory_section_count=section_confidence_counts[
                BiologicalReportSectionConfidenceLabel.EXPLORATORY
            ],
            invalid_section_count=section_confidence_counts[
                BiologicalReportSectionConfidenceLabel.INVALID
            ],
            context_entry_count=(
                0
                if context_mapping_report is None
                else len(context_mapping_report.mapped_entries)
            ),
            context_unmapped_count=(
                0
                if context_mapping_report is None
                else len(context_mapping_report.unmapped_entries)
            ),
            context_term_count=(
                0
                if context_mapping_report is None
                else len(context_mapping_report.term_entries)
            ),
            go_enriched_term_count=(
                0
                if go_enrichment_report is None
                else go_enrichment_report.summary.enriched_term_count
            ),
            pathway_enriched_entry_count=(
                0
                if pathway_enrichment_report is None
                else pathway_enrichment_report.summary.enriched_entry_count
            ),
            complex_enriched_entry_count=(
                0
                if complex_enrichment_report is None
                else complex_enrichment_report.summary.enriched_entry_count
            ),
            heatmap_entity_count=len(heatmap_report.rows),
            pca_outlier_sample_count=sum(
                1
                for entry in sample_exploration_report.sample_pca_report.entries
                if entry.outlier
            ),
        ),
        note=(
            "biological reporting assembles governed protein differential analysis, protein evidence cards, annotation mapping, optional user-supplied biological context mapping, enrichment, volcano review, heatmap preparation, and sample exploration into one owned workflow bundle"
            " with experiment-level confidence scoring, tissue and cell-type context review, claim validation, biological hypotheses, and explicit component reasons"
        ),
    )
