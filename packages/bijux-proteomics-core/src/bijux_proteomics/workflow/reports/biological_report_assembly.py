# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
# ruff: noqa: F401

"""Biological report assembly over governed quantification and review surfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

import csv
from enum import StrEnum
from html import escape
from io import StringIO
from pathlib import Path

from bijux_proteomics.interpretation import (
    BiologicalContextKind,
    BiologicalContextImportReport,
    BiologicalContextMappingReport,
    BiologicalForegroundBackgroundModel,
    BiologicalSetEntry,
    BiologicalSetFilteringPolicy,
    BiologicalSetSourceKind,
    ComplexActivityReport,
    ComplexEnrichmentCorrectionPolicy,
    ComplexEnrichmentReport,
    DrugTargetInterpretationPolicy,
    DrugTargetInterpretationReport,
    DiseasePhenotypeInterpretationPolicy,
    DiseasePhenotypeInterpretationReport,
    build_complex_activity_report,
    build_biological_context_mapping_report,
    build_biological_foreground_background_model,
    build_drug_target_interpretation_report,
    build_disease_phenotype_interpretation_report,
    render_complex_activity_condition_comparison_tsv,
    render_complex_activity_condition_score_tsv,
    render_complex_activity_matrix_tsv,
    render_complex_activity_sample_score_tsv,
    render_complex_activity_summary_tsv,
    render_complex_activity_unresolved_member_tsv,
    render_complex_member_contribution_tsv,
    render_complex_enrichment_entry_tsv,
    render_complex_enrichment_summary_tsv,
    render_complex_unresolved_member_tsv,
    render_drug_target_interpretation_summary_tsv,
    render_drug_target_interpretation_tsv,
    render_disease_phenotype_interpretation_summary_tsv,
    render_disease_phenotype_interpretation_tsv,
    render_unknown_disease_phenotype_annotation_tsv,
    PathwayEnrichmentCorrectionPolicy,
    PathwayEnrichmentReport,
    PathwayActivityReport,
    GoEnrichmentCorrectionPolicy,
    GoEnrichmentReport,
    ProteinAnnotationColumnMapping,
    ProteinAnnotationMappingReport,
    ProteinReferenceEntry,
    RegulatorEvidenceImportReport,
    RegulatorInferenceReport,
    apply_complex_enrichment_multiple_testing,
    apply_go_enrichment_multiple_testing,
    apply_pathway_enrichment_multiple_testing,
    build_complex_enrichment_report,
    build_go_enrichment_report,
    build_pathway_activity_report,
    build_pathway_enrichment_report,
    build_protein_annotation_mapping_report,
    build_regulator_inference_report,
    build_regulator_site_signal_entries_from_ptm_evidence_cards,
    parse_biological_context_table,
    parse_complex_membership_table,
    parse_go_annotation_table,
    parse_pathway_membership_table,
    parse_protein_annotation_table,
    parse_regulator_evidence_table,
    parse_regulator_site_signal_table,
    render_biological_context_mapping_summary_tsv,
    render_biological_context_mapping_tsv,
    render_biological_context_term_tsv,
    render_biological_foreground_background_entry_tsv,
    render_biological_foreground_background_issue_tsv,
    render_biological_foreground_background_summary_tsv,
    render_rejected_biological_context_tsv,
    render_unmapped_biological_context_tsv,
    render_go_enrichment_summary_tsv,
    render_go_enrichment_term_tsv,
    render_go_enrichment_unannotated_tsv,
    render_pathway_activity_condition_comparison_tsv,
    render_pathway_activity_condition_score_tsv,
    render_pathway_activity_matrix_tsv,
    render_pathway_activity_sample_score_tsv,
    render_pathway_activity_summary_tsv,
    render_pathway_activity_unresolved_member_tsv,
    render_pathway_enrichment_entry_tsv,
    render_pathway_enrichment_summary_tsv,
    render_pathway_member_contribution_tsv,
    render_pathway_unresolved_member_tsv,
    render_protein_annotation_tsv,
    render_protein_annotation_summary_tsv,
    render_rejected_regulator_evidence_tsv,
    render_regulator_inference_summary_tsv,
    render_regulator_inference_tsv,
    render_tissue_cell_type_context_summary_tsv,
    render_tissue_cell_type_interpretation_tsv,
    render_tissue_cell_type_sample_consistency_tsv,
    render_tissue_cell_type_unexpected_signal_tsv,
    render_unresolved_regulator_target_tsv,
    render_unmapped_protein_annotation_tsv,
    require_valid_biological_foreground_background_model,
    TissueCellTypeContextReport,
    build_tissue_cell_type_context_report,
)
from bijux_proteomics.interpretation.compartment_biology import (
    CompartmentBiologyPolicy,
    CompartmentBiologyReport,
    build_compartment_biology_report,
    render_compartment_activity_condition_comparison_tsv,
    render_compartment_activity_condition_score_tsv,
    render_compartment_activity_matrix_tsv,
    render_compartment_activity_sample_score_tsv,
    render_compartment_activity_unresolved_member_tsv,
    render_compartment_biology_summary_tsv,
    render_compartment_enrichment_tsv,
    render_unknown_compartment_localization_tsv,
)
from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    export_heatmap_column_metadata_tsv,
    export_heatmap_matrix_tsv,
    export_heatmap_row_metadata_tsv,
    export_heatmap_summary_tsv,
    export_sample_cluster_tsv,
    export_sample_distance_tsv,
    export_sample_exploration_summary_tsv,
    export_sample_pca_scores_tsv,
    export_sample_pca_variance_tsv,
    HeatmapMissingValuePolicy,
    HeatmapPreparationPolicy,
    HeatmapPreparationReport,
    Ms1FeatureColumnMapping,
    LabelFreeQuantTable,
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    SampleExplorationReport,
    build_differential_abundance_report,
    build_heatmap_preparation_report,
    build_label_free_intensity_table,
    build_missingness_condition_summary_report,
    build_power_estimation_report,
    build_sample_exploration_report,
    normalize_label_free_table,
    parse_ms1_feature_table,
    parse_ms1_feature_table_chunked,
    render_differential_abundance_tsv,
)
from bijux_proteomics.quantification.contracts import DifferentialAbundanceReport
from bijux_proteomics.quantification.differential_abundance import (
    apply_benjamini_hochberg,
)
from bijux_proteomics.review import (
    BiologicalClaimCandidate,
    BiologicalClaimDirection,
    BiologicalClaimKind,
    BiologicalClaimValidationPolicy,
    BiologicalClaimValidationReport,
    BiologicalHypothesisCandidate,
    BiologicalHypothesisKind,
    BiologicalHypothesisReport,
    EvidenceAwareRankingCandidate,
    EvidenceAwareRankingEntityKind,
    EvidenceAwareRankingReport,
    VolcanoReviewPolicy,
    VolcanoReviewReport,
    build_biological_claim_validation_report,
    build_biological_hypothesis_report,
    build_evidence_aware_ranking_report,
    build_quantification_volcano_review,
    export_proteomics_evidence_graph,
    export_volcano_review_html,
    normalize_linear_range,
    export_volcano_review_json,
    export_volcano_review_svg,
    render_proteomics_evidence_graph_edges_tsv,
    render_proteomics_evidence_graph_nodes_tsv,
    render_biological_claim_validation_summary_tsv,
    render_biological_hypothesis_summary_tsv,
    render_biological_hypothesis_tsv,
    render_rejected_biological_hypothesis_candidate_tsv,
    render_rejected_biological_claim_tsv,
    render_supported_biological_claim_tsv,
    render_volcano_review_tsv,
    render_evidence_aware_ranking_tsv,
    score_adjusted_p_value,
    score_effect_size,
    score_support_count,
)
from bijux_proteomics.sequences import (
    FastaParseMode,
    parse_fasta_document,
    parse_proteogenomic_variant_peptide_table,
    parse_protein_region_context_tsv,
)
from bijux_proteomics.ptm import PtmEvidenceCardReport
from bijux_proteomics.study import (
    ExperimentConfidenceReport,
    ExperimentDesign,
    LcmsRunQcReport,
    QcRunAssessmentReport,
    build_experiment_confidence_report,
    build_experiment_feasibility_report,
    build_protocol_consistency_report,
    coerce_experiment_design,
    render_experiment_confidence_component_tsv,
    render_experiment_confidence_summary_tsv,
)
from bijux_proteomics.lab.protocol_context import (
    build_lab_protocol_interpretation_profile,
    parse_lab_protocol_context_table,
    require_single_lab_protocol_context,
)
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
    ProteinEvidenceCardReport,
    ProteinEvidenceCardSelectionPolicy,
    build_protein_evidence_card_report,
    render_protein_evidence_card_summary_tsv,
    render_protein_evidence_card_tsv,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCard,
    ProteinMechanismCardReport,
    build_protein_mechanism_card_report,
    render_protein_mechanism_card_summary_tsv,
    render_protein_mechanism_card_tsv,
)
from bijux_proteomics.workflow.reports.biological_result_graph import (
    BiologicalResultGraphReport,
    build_biological_result_graph_report,
)
from bijux_proteomics.workflow.cohort_stratification import (
    CohortStratificationReport,
    build_cohort_stratification_report,
    render_cohort_interaction_candidate_tsv,
    render_cohort_stratification_summary_tsv,
    render_cohort_stratum_tsv,
    render_cohort_subgroup_effect_tsv,
)
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics_lab.handoffs.qc_feedback import LabRunQcFeedbackReport

from bijux_proteomics.workflow.reports.biological_report_claims import (
    _build_biological_claim_validation_report,
    _build_biological_evidence_aware_ranking_report,
    _build_biological_hypothesis_report,
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
    _build_background_reference_entries,
    _build_biological_background_filtering_policy,
    _build_biological_foreground_filtering_policy,
    _build_differential_reference_entries,
    _build_foreground_reference_entries,
    _build_protein_reference_entries_from_biological_set,
    _resolve_contrast,
    _select_heatmap_entity_ids,
    _select_significant_entity_ids,
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

    experiment_design = coerce_experiment_design(design_entries)
    active_mapping = mapping or Ms1FeatureColumnMapping(
        sample_id="sample_id",
        feature_id="feature_id",
        peptide="peptide",
        intensity="intensity",
        protein_refs="proteins",
        charge="charge",
        mz="mz",
        retention_time_seconds="retention_time_seconds",
        missing_reason="missing_reason",
        protein_separator=";",
    )
    active_selection_policy = _resolve_biological_result_selection_policy(
        selection_policy,
        protocol_context_tsv_path=protocol_context_tsv_path,
    )
    parse_report = (
        parse_ms1_feature_table_chunked(
            input_tsv_path,
            mapping=active_mapping,
            chunk_size_rows=chunk_size_rows,
        )
        if chunk_size_rows is not None
        else parse_ms1_feature_table(input_tsv_path, mapping=active_mapping)
    )
    quant_table = build_label_free_intensity_table(
        parse_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    return build_biological_result_report_bundle_from_quant_table(
        quant_table,
        experiment_design,
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
        normalization_method=normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
        selection_policy=active_selection_policy,
        volcano_policy=volcano_policy,
        lab_run_qc_feedback_report=lab_run_qc_feedback_report,
        run_qc_reports=run_qc_reports,
        run_qc_assessments=run_qc_assessments,
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
    fasta_report = parse_fasta_document(
        proteins_fasta_path.read_text(encoding="utf-8"),
        mode=FastaParseMode.STRICT,
    )
    if fasta_report.rejected_records:
        rejected = ", ".join(
            record.source_identifier for record in fasta_report.rejected_records
        )
        raise ValueError(
            "FASTA input contains rejected records under strict mode: " + rejected
        )
    variant_fasta_records = ()
    if variant_proteins_fasta_path is not None:
        variant_fasta_report = parse_fasta_document(
            variant_proteins_fasta_path.read_text(encoding="utf-8"),
            mode=FastaParseMode.STRICT,
        )
        if variant_fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in variant_fasta_report.rejected_records
            )
            raise ValueError(
                "variant FASTA input contains rejected records under strict mode: "
                + rejected
            )
        variant_fasta_records = variant_fasta_report.accepted_records
    variant_peptide_records = ()
    if variant_peptide_tsv_path is not None:
        variant_peptide_report = parse_proteogenomic_variant_peptide_table(
            variant_peptide_tsv_path
        )
        if variant_peptide_report.rejected_rows:
            rejected = "; ".join(
                row.reason for row in variant_peptide_report.rejected_rows[:3]
            )
            raise ValueError(
                "variant peptide table contains rejected rows: " + rejected
            )
        variant_peptide_records = variant_peptide_report.accepted_records
    custom_annotation_report = (
        None
        if annotation_tsv_path is None
        else parse_protein_annotation_table(
            annotation_tsv_path,
            mapping=ProteinAnnotationColumnMapping(
                protein_ref="protein_ref",
                gene_symbol="gene_symbol",
                description="description",
                organism="organism",
                annotation_identifier="annotation_identifier",
            ),
        )
    )
    pathway_membership_report = (
        None
        if pathway_membership_tsv_path is None
        else parse_pathway_membership_table(pathway_membership_tsv_path)
    )
    complex_membership_report = (
        None
        if complex_membership_tsv_path is None
        else parse_complex_membership_table(complex_membership_tsv_path)
    )
    differential_reference_entries = _build_differential_reference_entries(
        differential_report,
        protein_refs_by_entity=normalized_table.entity_protein_refs,
    )
    annotation_report = build_protein_annotation_mapping_report(
        differential_reference_entries,
        fasta_report.accepted_records,
        custom_annotations=()
        if custom_annotation_report is None
        else custom_annotation_report.accepted_records,
    )
    context_import_report = None
    context_mapping_report = None
    tissue_cell_type_context_report = None
    if context_annotation_tsv_path is not None:
        context_import_report = parse_biological_context_table(context_annotation_tsv_path)
        context_mapping_report = build_biological_context_mapping_report(
            differential_reference_entries,
            context_import_report.accepted_records,
        )
        if any(
            record.context_kind
            in {
                BiologicalContextKind.TISSUE_MARKER,
                BiologicalContextKind.CELL_TYPE_MARKER,
            }
            for record in context_import_report.accepted_records
        ):
            tissue_cell_type_context_report = build_tissue_cell_type_context_report(
                normalized_table,
                experiment_design,
                context_import_report.accepted_records,
            )
    drug_target_report = None
    if (
        context_import_report is not None
        and any(
            record.context_kind is BiologicalContextKind.DRUG_TARGET
            for record in context_import_report.accepted_records
        )
    ):
        drug_target_report = build_drug_target_interpretation_report(
            normalized_table,
            differential_report,
            context_import_report.accepted_records,
            pathway_records=()
            if pathway_membership_report is None
            else pathway_membership_report.accepted_records,
            annotation_report=annotation_report,
            policy=DrugTargetInterpretationPolicy(
                max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
                min_absolute_log2_fold_change=(
                    active_selection_policy.min_absolute_log2_fold_change
                ),
            ),
        )
    disease_phenotype_report = None
    if (
        context_import_report is not None
        and any(
            record.context_kind in {
                BiologicalContextKind.DISEASE_TERM,
                BiologicalContextKind.PHENOTYPE_TERM,
            }
            for record in context_import_report.accepted_records
        )
    ):
        disease_phenotype_report = build_disease_phenotype_interpretation_report(
            normalized_table,
            differential_report,
            context_import_report.accepted_records,
            policy=DiseasePhenotypeInterpretationPolicy(
                max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
                min_absolute_log2_fold_change=(
                    active_selection_policy.min_absolute_log2_fold_change
                ),
                min_enrichment_ratio=1.0,
            ),
        )
    compartment_biology_report = None
    if (
        context_import_report is not None
        and any(
            record.context_kind is BiologicalContextKind.SUBCELLULAR_COMPARTMENT
            for record in context_import_report.accepted_records
        )
    ):
        compartment_biology_report = build_compartment_biology_report(
            normalized_table,
            differential_report,
            context_import_report.accepted_records,
            design_entries=design_entries,
            policy=CompartmentBiologyPolicy(
                max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
                min_absolute_log2_fold_change=(
                    active_selection_policy.min_absolute_log2_fold_change
                ),
            ),
        )
    protein_region_context_records = None
    if protein_region_context_tsv_path is not None:
        protein_region_context_records = parse_protein_region_context_tsv(
            protein_region_context_tsv_path
        ).accepted_records
    foreground_background_model = build_biological_foreground_background_model(
        _build_foreground_reference_entries(
            differential_report,
            protein_refs_by_entity=normalized_table.entity_protein_refs,
            policy=active_selection_policy,
        ),
        _build_background_reference_entries(normalized_table),
        foreground_source_kind=BiologicalSetSourceKind.DIFFERENTIAL_SIGNIFICANT_RESULTS,
        background_source_kind=BiologicalSetSourceKind.MEASURED_QUANT_MATRIX,
        foreground_policy=_build_biological_foreground_filtering_policy(
            active_selection_policy
        ),
        background_policy=_build_biological_background_filtering_policy(),
    )
    enrichment_input_requested = any(
        path is not None
        for path in (
            go_annotation_tsv_path,
            pathway_membership_tsv_path,
            complex_membership_tsv_path,
        )
    )
    validated_foreground_background_model = (
        require_valid_biological_foreground_background_model(foreground_background_model)
        if enrichment_input_requested
        else foreground_background_model
    )
    enrichment_foreground_entries = _build_protein_reference_entries_from_biological_set(
        validated_foreground_background_model.foreground_entries
    )
    enrichment_background_entries = _build_protein_reference_entries_from_biological_set(
        validated_foreground_background_model.background_entries
    )
    go_enrichment_report = None
    if go_annotation_tsv_path is not None:
        go_enrichment_report = apply_go_enrichment_multiple_testing(
            build_go_enrichment_report(
                enrichment_foreground_entries,
                enrichment_background_entries,
                parse_go_annotation_table(go_annotation_tsv_path).accepted_records,
            ),
            policy=GoEnrichmentCorrectionPolicy(
                max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
                min_enrichment_ratio=1.0,
            ),
        )
    pathway_activity_report = None
    if pathway_membership_report is not None:
        pathway_activity_report = build_pathway_activity_report(
            normalized_table,
            pathway_membership_report.accepted_records,
            design_entries=design_entries,
            fasta_records=fasta_report.accepted_records,
            custom_annotations=()
            if custom_annotation_report is None
            else custom_annotation_report.accepted_records,
        )
    pathway_enrichment_report = None
    if pathway_membership_report is not None:
        pathway_enrichment_report = apply_pathway_enrichment_multiple_testing(
            build_pathway_enrichment_report(
                enrichment_foreground_entries,
                enrichment_background_entries,
                pathway_membership_report.accepted_records,
                fasta_records=fasta_report.accepted_records,
                custom_annotations=()
                if custom_annotation_report is None
                else custom_annotation_report.accepted_records,
            ),
            policy=PathwayEnrichmentCorrectionPolicy(
                max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
                min_enrichment_ratio=1.0,
            ),
        )
    complex_activity_report = None
    if complex_membership_report is not None:
        complex_activity_report = build_complex_activity_report(
            normalized_table,
            complex_membership_report.accepted_records,
            design_entries=design_entries,
            fasta_records=fasta_report.accepted_records,
            custom_annotations=()
            if custom_annotation_report is None
            else custom_annotation_report.accepted_records,
        )
    complex_enrichment_report = None
    if complex_membership_report is not None:
        complex_enrichment_report = apply_complex_enrichment_multiple_testing(
            build_complex_enrichment_report(
                enrichment_foreground_entries,
                enrichment_background_entries,
                complex_membership_report.accepted_records,
                fasta_records=fasta_report.accepted_records,
                custom_annotations=()
                if custom_annotation_report is None
                else custom_annotation_report.accepted_records,
            ),
            policy=ComplexEnrichmentCorrectionPolicy(
                max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
                min_enrichment_ratio=1.0,
            ),
        )
    regulator_evidence_import_report = (
        None
        if regulator_evidence_tsv_path is None
        else parse_regulator_evidence_table(regulator_evidence_tsv_path)
    )
    regulator_inference_report = None
    if regulator_evidence_import_report is not None:
        if regulator_site_signal_tsv_path is not None:
            site_signal_entries = parse_regulator_site_signal_table(
                regulator_site_signal_tsv_path
            ).accepted_entries
        elif ptm_evidence_card_report is not None:
            site_signal_entries = (
                build_regulator_site_signal_entries_from_ptm_evidence_cards(
                    ptm_evidence_card_report
                )
            )
        else:
            site_signal_entries = ()
        regulator_inference_report = build_regulator_inference_report(
            regulator_evidence_import_report.accepted_records,
            differential_report,
            protein_refs_by_entity=normalized_table.entity_protein_refs,
            annotation_report=annotation_report,
            pathway_activity_report=pathway_activity_report,
            site_signal_entries=site_signal_entries,
        )
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
            for record in fasta_report.accepted_records
        },
        protein_records=fasta_report.accepted_records,
        variant_protein_records=variant_fasta_records,
        variant_peptide_records=variant_peptide_records,
        selection_policy=ProteinEvidenceCardSelectionPolicy(
            max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
            min_absolute_log2_fold_change=(
                active_selection_policy.min_absolute_log2_fold_change
            ),
        ),
        sample_conditions={
            entry.sample_id: entry.condition
            for entry in design_entries
        },
        context_mapping_report=context_mapping_report,
        pathway_enrichment_report=pathway_enrichment_report,
        complex_enrichment_report=complex_enrichment_report,
        protein_region_context_records=protein_region_context_records,
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
    cohort_stratification_report = build_cohort_stratification_report(
        normalized_table,
        experiment_design,
        condition_a=resolved_condition_a,
        condition_b=resolved_condition_b,
    )
    if cohort_stratification_report.summary.field_count == 0:
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
        _select_significant_entity_ids(differential_report, policy=active_selection_policy)
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
                1 for entry in sample_exploration_report.sample_pca_report.entries if entry.outlier
            ),
        ),
        note=(
            "biological reporting assembles governed protein differential analysis, protein evidence cards, annotation mapping, optional user-supplied biological context mapping, enrichment, volcano review, heatmap preparation, and sample exploration into one owned workflow bundle"
            " with experiment-level confidence scoring, tissue and cell-type context review, claim validation, biological hypotheses, and explicit component reasons"
        ),
    )
