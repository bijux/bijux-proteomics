# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned biological result bundles over governed label-free protein quantification."""

from __future__ import annotations

import csv
from html import escape
from io import StringIO
from pathlib import Path

from bijux_proteomics.interpretation import (
    BiologicalContextImportReport,
    BiologicalContextMappingReport,
    ComplexEnrichmentCorrectionPolicy,
    ComplexEnrichmentReport,
    build_biological_context_mapping_report,
    render_complex_enrichment_entry_tsv,
    render_complex_enrichment_summary_tsv,
    render_complex_unresolved_member_tsv,
    PathwayEnrichmentCorrectionPolicy,
    PathwayEnrichmentReport,
    GoEnrichmentCorrectionPolicy,
    GoEnrichmentReport,
    ProteinAnnotationColumnMapping,
    ProteinAnnotationMappingReport,
    ProteinReferenceEntry,
    apply_complex_enrichment_multiple_testing,
    apply_go_enrichment_multiple_testing,
    apply_pathway_enrichment_multiple_testing,
    build_complex_enrichment_report,
    build_go_enrichment_report,
    build_pathway_enrichment_report,
    build_protein_annotation_mapping_report,
    parse_biological_context_table,
    parse_complex_membership_table,
    parse_go_annotation_table,
    parse_pathway_membership_table,
    parse_protein_annotation_table,
    render_biological_context_mapping_summary_tsv,
    render_biological_context_mapping_tsv,
    render_biological_context_term_tsv,
    render_rejected_biological_context_tsv,
    render_unmapped_biological_context_tsv,
    render_go_enrichment_summary_tsv,
    render_go_enrichment_term_tsv,
    render_go_enrichment_unannotated_tsv,
    render_pathway_enrichment_entry_tsv,
    render_pathway_enrichment_summary_tsv,
    render_pathway_unresolved_member_tsv,
    render_protein_annotation_tsv,
    render_protein_annotation_summary_tsv,
    render_unmapped_protein_annotation_tsv,
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
    render_differential_abundance_tsv,
)
from bijux_proteomics.quantification.contracts import DifferentialAbundanceReport
from bijux_proteomics.quantification.differential_abundance import (
    apply_benjamini_hochberg,
)
from bijux_proteomics.review import (
    VolcanoReviewPolicy,
    VolcanoReviewReport,
    build_quantification_volcano_review,
    export_volcano_review_html,
    export_volcano_review_json,
    export_volcano_review_svg,
    render_volcano_review_tsv,
)
from bijux_proteomics.sequences import (
    FastaParseMode,
    parse_fasta_document,
    parse_protein_region_context_tsv,
)
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
from bijux_proteomics.study.lab_protocol_context import (
    build_lab_protocol_interpretation_profile,
    parse_lab_protocol_context_table,
    require_single_lab_protocol_context,
)
from bijux_proteomics.workflow.protein_evidence_cards import (
    ProteinEvidenceCardReport,
    ProteinEvidenceCardSelectionPolicy,
    build_protein_evidence_card_report,
    render_protein_evidence_card_summary_tsv,
    render_protein_evidence_card_tsv,
)
from bijux_proteomics.workflow.biological_result_graph import (
    BiologicalResultGraphReport,
    build_biological_result_graph_report,
)
from bijux_proteomics_foundation import JsonModel


class BiologicalResultSelectionPolicy(JsonModel):
    """Selection policy for interpretation-focused biological result bundles."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float = Field(default=1.0, ge=0.0)
    heatmap_max_entity_count: int = Field(default=50, ge=1)
    heatmap_min_observed_fraction: float = Field(default=0.5, ge=0.0, le=1.0)


def _resolve_biological_result_selection_policy(
    selection_policy: BiologicalResultSelectionPolicy | None,
    *,
    protocol_context_tsv_path: Path | None,
) -> BiologicalResultSelectionPolicy:
    if selection_policy is not None:
        return selection_policy
    if protocol_context_tsv_path is None:
        return BiologicalResultSelectionPolicy()
    protocol_context = require_single_lab_protocol_context(
        parse_lab_protocol_context_table(protocol_context_tsv_path)
    )
    profile = build_lab_protocol_interpretation_profile(protocol_context)
    return BiologicalResultSelectionPolicy(
        max_adjusted_p_value=profile.max_adjusted_p_value,
        min_absolute_log2_fold_change=profile.min_absolute_log2_fold_change,
        heatmap_max_entity_count=profile.heatmap_max_entity_count,
        heatmap_min_observed_fraction=BiologicalResultSelectionPolicy().heatmap_min_observed_fraction,
    )


class BiologicalResultReportSummary(JsonModel):
    """Compact summary over one biological result bundle."""

    model_config = ConfigDict(extra="forbid")

    protein_count: int = Field(..., ge=0)
    significant_protein_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    annotation_entry_count: int = Field(..., ge=0)
    annotation_unmapped_count: int = Field(..., ge=0)
    protein_card_count: int = Field(..., ge=0)
    warning_card_count: int = Field(..., ge=0)
    experiment_confidence_score: float = Field(..., ge=0.0, le=1.0)
    experiment_confidence_tier: str = Field(..., min_length=1)
    low_confidence_component_count: int = Field(..., ge=0)
    context_entry_count: int = Field(..., ge=0)
    context_unmapped_count: int = Field(..., ge=0)
    context_term_count: int = Field(..., ge=0)
    go_enriched_term_count: int = Field(..., ge=0)
    pathway_enriched_entry_count: int = Field(..., ge=0)
    complex_enriched_entry_count: int = Field(..., ge=0)
    heatmap_entity_count: int = Field(..., ge=0)
    pca_outlier_sample_count: int = Field(..., ge=0)


class BiologicalResultReportBundle(JsonModel):
    """Owned workflow bundle over differential proteins and review-ready plots."""

    model_config = ConfigDict(extra="forbid")

    differential_report: DifferentialAbundanceReport
    graph_report: BiologicalResultGraphReport
    annotation_report: ProteinAnnotationMappingReport
    protein_cards: ProteinEvidenceCardReport
    experiment_confidence_report: ExperimentConfidenceReport
    context_import_report: BiologicalContextImportReport | None = None
    context_mapping_report: BiologicalContextMappingReport | None = None
    go_enrichment_report: GoEnrichmentReport | None = None
    pathway_enrichment_report: PathwayEnrichmentReport | None = None
    complex_enrichment_report: ComplexEnrichmentReport | None = None
    volcano_review: VolcanoReviewReport
    heatmap_report: HeatmapPreparationReport
    sample_exploration_report: SampleExplorationReport
    selection_policy: BiologicalResultSelectionPolicy
    summary: BiologicalResultReportSummary
    note: str = Field(..., min_length=1)


class BiologicalResultReportArtifactPaths(JsonModel):
    """Relative artifact paths written into one biological result report directory."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    differential_tsv: str = Field(..., min_length=1)
    protein_card_summary_tsv: str = Field(..., min_length=1)
    protein_card_tsv: str = Field(..., min_length=1)
    experiment_confidence_summary_tsv: str = Field(..., min_length=1)
    experiment_confidence_components_tsv: str = Field(..., min_length=1)
    annotation_summary_tsv: str = Field(..., min_length=1)
    annotation_tsv: str = Field(..., min_length=1)
    annotation_unmapped_tsv: str = Field(..., min_length=1)
    context_summary_tsv: str | None = None
    context_mapping_tsv: str | None = None
    context_term_tsv: str | None = None
    context_unmapped_tsv: str | None = None
    context_rejected_tsv: str | None = None
    volcano_tsv: str = Field(..., min_length=1)
    volcano_json: str = Field(..., min_length=1)
    volcano_svg: str = Field(..., min_length=1)
    volcano_html: str = Field(..., min_length=1)
    heatmap_summary_tsv: str = Field(..., min_length=1)
    heatmap_matrix_tsv: str = Field(..., min_length=1)
    heatmap_row_metadata_tsv: str = Field(..., min_length=1)
    heatmap_column_metadata_tsv: str = Field(..., min_length=1)
    sample_exploration_summary_tsv: str = Field(..., min_length=1)
    sample_pca_scores_tsv: str = Field(..., min_length=1)
    sample_pca_variance_tsv: str = Field(..., min_length=1)
    sample_distance_tsv: str = Field(..., min_length=1)
    sample_cluster_tsv: str = Field(..., min_length=1)
    report_html: str = Field(..., min_length=1)
    go_summary_tsv: str | None = None
    go_term_tsv: str | None = None
    go_unannotated_tsv: str | None = None
    pathway_summary_tsv: str | None = None
    pathway_entry_tsv: str | None = None
    pathway_unresolved_tsv: str | None = None
    complex_summary_tsv: str | None = None
    complex_entry_tsv: str | None = None
    complex_unresolved_tsv: str | None = None


class BiologicalResultReportExportManifest(JsonModel):
    """Stable manifest over one exported biological result report directory."""

    model_config = ConfigDict(extra="forbid")

    summary: BiologicalResultReportSummary
    artifacts: BiologicalResultReportArtifactPaths
    context_summary_included: bool
    go_summary_included: bool
    pathway_summary_included: bool
    complex_summary_included: bool
    note: str = Field(..., min_length=1)


def build_biological_result_report_bundle(
    input_tsv_path: Path,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    proteins_fasta_path: Path,
    protocol_context_tsv_path: Path | None = None,
    annotation_tsv_path: Path | None = None,
    context_annotation_tsv_path: Path | None = None,
    protein_region_context_tsv_path: Path | None = None,
    go_annotation_tsv_path: Path | None = None,
    pathway_membership_tsv_path: Path | None = None,
    complex_membership_tsv_path: Path | None = None,
    mapping: Ms1FeatureColumnMapping | None = None,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    top_n: int = 3,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    selection_policy: BiologicalResultSelectionPolicy | None = None,
    volcano_policy: VolcanoReviewPolicy | None = None,
    run_qc_reports: tuple[LcmsRunQcReport, ...] = (),
    run_qc_assessments: tuple[QcRunAssessmentReport, ...] = (),
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
    parse_report = parse_ms1_feature_table(input_tsv_path, mapping=active_mapping)
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
        protocol_context_tsv_path=protocol_context_tsv_path,
        annotation_tsv_path=annotation_tsv_path,
        context_annotation_tsv_path=context_annotation_tsv_path,
        protein_region_context_tsv_path=protein_region_context_tsv_path,
        go_annotation_tsv_path=go_annotation_tsv_path,
        pathway_membership_tsv_path=pathway_membership_tsv_path,
        complex_membership_tsv_path=complex_membership_tsv_path,
        normalization_method=normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
        selection_policy=active_selection_policy,
        volcano_policy=volcano_policy,
        run_qc_reports=run_qc_reports,
        run_qc_assessments=run_qc_assessments,
    )


def build_biological_result_report_bundle_from_quant_table(
    quant_table: LabelFreeQuantTable,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    proteins_fasta_path: Path,
    protocol_context_tsv_path: Path | None = None,
    annotation_tsv_path: Path | None = None,
    context_annotation_tsv_path: Path | None = None,
    protein_region_context_tsv_path: Path | None = None,
    go_annotation_tsv_path: Path | None = None,
    pathway_membership_tsv_path: Path | None = None,
    complex_membership_tsv_path: Path | None = None,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    selection_policy: BiologicalResultSelectionPolicy | None = None,
    volcano_policy: VolcanoReviewPolicy | None = None,
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
    if context_annotation_tsv_path is not None:
        context_import_report = parse_biological_context_table(context_annotation_tsv_path)
        context_mapping_report = build_biological_context_mapping_report(
            differential_reference_entries,
            context_import_report.accepted_records,
        )
    protein_region_context_records = None
    if protein_region_context_tsv_path is not None:
        protein_region_context_records = parse_protein_region_context_tsv(
            protein_region_context_tsv_path
        ).accepted_records
    background_entries = _build_background_reference_entries(normalized_table)
    foreground_entries = _build_foreground_reference_entries(
        differential_report,
        protein_refs_by_entity=normalized_table.entity_protein_refs,
        policy=active_selection_policy,
    )
    go_enrichment_report = None
    if go_annotation_tsv_path is not None:
        go_enrichment_report = apply_go_enrichment_multiple_testing(
            build_go_enrichment_report(
                foreground_entries,
                background_entries,
                parse_go_annotation_table(go_annotation_tsv_path).accepted_records,
            ),
            policy=GoEnrichmentCorrectionPolicy(
                max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
                min_enrichment_ratio=1.0,
            ),
        )
    pathway_enrichment_report = None
    if pathway_membership_tsv_path is not None:
        pathway_enrichment_report = apply_pathway_enrichment_multiple_testing(
            build_pathway_enrichment_report(
                foreground_entries,
                background_entries,
                parse_pathway_membership_table(
                    pathway_membership_tsv_path
                ).accepted_records,
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
    complex_enrichment_report = None
    if complex_membership_tsv_path is not None:
        complex_enrichment_report = apply_complex_enrichment_multiple_testing(
            build_complex_enrichment_report(
                foreground_entries,
                background_entries,
                parse_complex_membership_table(
                    complex_membership_tsv_path
                ).accepted_records,
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
    protein_cards = build_protein_evidence_card_report(
        graph_report := build_biological_result_graph_report(
            normalized_table,
            differential_report,
            design_entries,
            max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
            min_absolute_log2_fold_change=active_selection_policy.min_absolute_log2_fold_change,
        ),
        normalized_table,
        differential_report,
        annotation_report,
        protein_sequences={
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        },
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
    significant_protein_count = len(
        _select_significant_entity_ids(differential_report, policy=active_selection_policy)
    )
    return BiologicalResultReportBundle(
        differential_report=differential_report,
        graph_report=graph_report,
        annotation_report=annotation_report,
        protein_cards=protein_cards,
        experiment_confidence_report=experiment_confidence_report,
        context_import_report=context_import_report,
        context_mapping_report=context_mapping_report,
        go_enrichment_report=go_enrichment_report,
        pathway_enrichment_report=pathway_enrichment_report,
        complex_enrichment_report=complex_enrichment_report,
        volcano_review=volcano_review,
        heatmap_report=heatmap_report,
        sample_exploration_report=sample_exploration_report,
        selection_policy=active_selection_policy,
        summary=BiologicalResultReportSummary(
            protein_count=len(normalized_table.entity_ids),
            significant_protein_count=significant_protein_count,
            sample_count=len(normalized_table.sample_ids),
            annotation_entry_count=len(annotation_report.result_entries),
            annotation_unmapped_count=len(annotation_report.unmapped_entries),
            protein_card_count=protein_cards.summary.protein_result_count,
            warning_card_count=protein_cards.summary.warning_card_count,
            experiment_confidence_score=experiment_confidence_report.summary.overall_score,
            experiment_confidence_tier=(
                experiment_confidence_report.summary.overall_tier.value
            ),
            low_confidence_component_count=(
                experiment_confidence_report.summary.low_confidence_component_count
            ),
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
            " with experiment-level confidence scoring and explicit component reasons"
        ),
    )


def _resolve_contrast(
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None,
    condition_b: str | None,
) -> tuple[str, str]:
    experiment_design = coerce_experiment_design(design_entries)
    if bool(condition_a) ^ bool(condition_b):
        raise ValueError("both condition_a and condition_b are required together")
    if condition_a is not None and condition_b is not None:
        return condition_a, condition_b
    conditions = experiment_design.conditions
    if len(conditions) != 2:
        raise ValueError(
            "biological result reporting requires exactly two conditions or an explicit contrast"
        )
    return conditions[0], conditions[1]


def _select_significant_entity_ids(
    report: DifferentialAbundanceReport,
    *,
    policy: BiologicalResultSelectionPolicy,
) -> tuple[str, ...]:
    return tuple(
        entry.entity_id
        for entry in report.entries
        if entry.adjusted_p_value is not None
        and entry.adjusted_p_value <= policy.max_adjusted_p_value
        and abs(entry.log2_fold_change) >= policy.min_absolute_log2_fold_change
    )


def _select_heatmap_entity_ids(
    report: DifferentialAbundanceReport,
    *,
    policy: BiologicalResultSelectionPolicy,
) -> tuple[str, ...]:
    significant_entity_ids = _select_significant_entity_ids(report, policy=policy)
    if significant_entity_ids:
        return significant_entity_ids
    ranked_entries = sorted(
        report.entries,
        key=lambda entry: (
            -(abs(entry.log2_fold_change)),
            entry.adjusted_p_value if entry.adjusted_p_value is not None else 1.0,
            entry.entity_id,
        ),
    )
    return tuple(
        entry.entity_id for entry in ranked_entries[: policy.heatmap_max_entity_count]
    )


def _build_differential_reference_entries(
    report: DifferentialAbundanceReport,
    *,
    protein_refs_by_entity: dict[str, tuple[str, ...]] | None = None,
) -> tuple[ProteinReferenceEntry, ...]:
    return _build_protein_reference_entries(
        (
            (entry.entity_id, protein_refs_by_entity or {})
            for entry in report.entries
        )
    )


def _build_background_reference_entries(
    normalized_table,
) -> tuple[ProteinReferenceEntry, ...]:
    return _build_protein_reference_entries(
        (
            (entity_id, normalized_table.entity_protein_refs)
            for entity_id in normalized_table.entity_ids
        )
    )


def _build_foreground_reference_entries(
    report: DifferentialAbundanceReport,
    *,
    protein_refs_by_entity: dict[str, tuple[str, ...]] | None = None,
    policy: BiologicalResultSelectionPolicy,
) -> tuple[ProteinReferenceEntry, ...]:
    significant_entity_ids = _select_significant_entity_ids(report, policy=policy)
    return _build_protein_reference_entries(
        (
            (entity_id, protein_refs_by_entity or {})
            for entity_id in significant_entity_ids
        )
    )


def _build_protein_reference_entries(
    entity_rows: tuple[tuple[str, dict[str, tuple[str, ...]]], ...]
    | list[tuple[str, dict[str, tuple[str, ...]]]]
    | object,
) -> tuple[ProteinReferenceEntry, ...]:
    entries: list[ProteinReferenceEntry] = []
    row_number = 2
    for entity_id, protein_refs_by_entity in entity_rows:
        protein_refs = protein_refs_by_entity.get(entity_id, ()) or (entity_id,)
        for protein_ref in protein_refs:
            entries.append(
                ProteinReferenceEntry(
                    row_number=row_number,
                    source_row_id=entity_id,
                    input_protein_ref=protein_ref,
                    protein_ref=protein_ref,
                )
            )
            row_number += 1
    return tuple(entries)


def render_biological_result_report_summary_tsv(
    report: BiologicalResultReportBundle,
) -> str:
    """Render one biological result report summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("condition_a", report.volcano_review.condition_a))
    writer.writerow(("condition_b", report.volcano_review.condition_b))
    writer.writerow(("protein_count", report.summary.protein_count))
    writer.writerow(
        ("significant_protein_count", report.summary.significant_protein_count)
    )
    writer.writerow(("sample_count", report.summary.sample_count))
    writer.writerow(("annotation_entry_count", report.summary.annotation_entry_count))
    writer.writerow(
        ("annotation_unmapped_count", report.summary.annotation_unmapped_count)
    )
    writer.writerow(("protein_card_count", report.summary.protein_card_count))
    writer.writerow(("warning_card_count", report.summary.warning_card_count))
    writer.writerow(
        (
            "experiment_confidence_score",
            f"{report.summary.experiment_confidence_score:.4f}",
        )
    )
    writer.writerow(
        ("experiment_confidence_tier", report.summary.experiment_confidence_tier)
    )
    writer.writerow(
        (
            "low_confidence_component_count",
            report.summary.low_confidence_component_count,
        )
    )
    writer.writerow(("context_entry_count", report.summary.context_entry_count))
    writer.writerow(("context_unmapped_count", report.summary.context_unmapped_count))
    writer.writerow(("context_term_count", report.summary.context_term_count))
    writer.writerow(("go_enriched_term_count", report.summary.go_enriched_term_count))
    writer.writerow(
        ("pathway_enriched_entry_count", report.summary.pathway_enriched_entry_count)
    )
    writer.writerow(
        ("complex_enriched_entry_count", report.summary.complex_enriched_entry_count)
    )
    writer.writerow(("heatmap_entity_count", report.summary.heatmap_entity_count))
    writer.writerow(
        ("pca_outlier_sample_count", report.summary.pca_outlier_sample_count)
    )
    writer.writerow(("note", report.note))
    return handle.getvalue()


def export_biological_result_report_bundle(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalResultReportExportManifest:
    """Write one biological result bundle into a stable output directory."""

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_name = "biological_report_summary.tsv"
    differential_name = "biological_differential.tsv"
    protein_card_summary_name = "biological_protein_card_summary.tsv"
    protein_card_name = "biological_protein_cards.tsv"
    experiment_confidence_summary_name = "biological_experiment_confidence_summary.tsv"
    experiment_confidence_components_name = (
        "biological_experiment_confidence_components.tsv"
    )
    annotation_summary_name = "biological_annotation_summary.tsv"
    annotation_name = "biological_annotations.tsv"
    annotation_unmapped_name = "biological_annotation_unmapped.tsv"
    context_summary_name = None
    context_mapping_name = None
    context_term_name = None
    context_unmapped_name = None
    context_rejected_name = None
    volcano_tsv_name = "biological_volcano.tsv"
    volcano_json_name = "biological_volcano.json"
    volcano_svg_name = "biological_volcano.svg"
    volcano_html_name = "biological_volcano.html"
    heatmap_summary_name = "biological_heatmap_summary.tsv"
    heatmap_matrix_name = "biological_heatmap_matrix.tsv"
    heatmap_row_name = "biological_heatmap_rows.tsv"
    heatmap_column_name = "biological_heatmap_columns.tsv"
    sample_summary_name = "biological_sample_exploration_summary.tsv"
    sample_scores_name = "biological_sample_pca_scores.tsv"
    sample_variance_name = "biological_sample_pca_variance.tsv"
    sample_distance_name = "biological_sample_distances.tsv"
    sample_cluster_name = "biological_sample_clusters.tsv"
    report_html_name = "biological_report.html"

    (output_dir / summary_name).write_text(
        render_biological_result_report_summary_tsv(report),
        encoding="utf-8",
    )
    (output_dir / differential_name).write_text(
        render_differential_abundance_tsv(report.differential_report),
        encoding="utf-8",
    )
    (output_dir / protein_card_summary_name).write_text(
        render_protein_evidence_card_summary_tsv(report.protein_cards),
        encoding="utf-8",
    )
    (output_dir / protein_card_name).write_text(
        render_protein_evidence_card_tsv(report.protein_cards),
        encoding="utf-8",
    )
    (output_dir / experiment_confidence_summary_name).write_text(
        render_experiment_confidence_summary_tsv(report.experiment_confidence_report),
        encoding="utf-8",
    )
    (output_dir / experiment_confidence_components_name).write_text(
        render_experiment_confidence_component_tsv(report.experiment_confidence_report),
        encoding="utf-8",
    )
    (output_dir / annotation_summary_name).write_text(
        render_protein_annotation_summary_tsv(report.annotation_report),
        encoding="utf-8",
    )
    (output_dir / annotation_name).write_text(
        render_protein_annotation_tsv(report.annotation_report),
        encoding="utf-8",
    )
    (output_dir / annotation_unmapped_name).write_text(
        render_unmapped_protein_annotation_tsv(report.annotation_report),
        encoding="utf-8",
    )
    if (
        report.context_import_report is not None
        and report.context_mapping_report is not None
    ):
        context_summary_name = "biological_context_summary.tsv"
        context_mapping_name = "biological_context_mappings.tsv"
        context_term_name = "biological_context_terms.tsv"
        context_unmapped_name = "biological_context_unmapped.tsv"
        context_rejected_name = "biological_context_rejected.tsv"
        (output_dir / context_summary_name).write_text(
            render_biological_context_mapping_summary_tsv(report.context_mapping_report),
            encoding="utf-8",
        )
        (output_dir / context_mapping_name).write_text(
            render_biological_context_mapping_tsv(report.context_mapping_report),
            encoding="utf-8",
        )
        (output_dir / context_term_name).write_text(
            render_biological_context_term_tsv(report.context_mapping_report),
            encoding="utf-8",
        )
        (output_dir / context_unmapped_name).write_text(
            render_unmapped_biological_context_tsv(report.context_mapping_report),
            encoding="utf-8",
        )
        (output_dir / context_rejected_name).write_text(
            render_rejected_biological_context_tsv(report.context_import_report),
            encoding="utf-8",
        )
    (output_dir / volcano_tsv_name).write_text(
        render_volcano_review_tsv(report.volcano_review),
        encoding="utf-8",
    )
    export_volcano_review_json(report.volcano_review, output_dir / volcano_json_name)
    export_volcano_review_svg(report.volcano_review, output_dir / volcano_svg_name)
    export_volcano_review_html(report.volcano_review, output_dir / volcano_html_name)
    export_heatmap_summary_tsv(report.heatmap_report, output_dir / heatmap_summary_name)
    export_heatmap_matrix_tsv(report.heatmap_report, output_dir / heatmap_matrix_name)
    export_heatmap_row_metadata_tsv(report.heatmap_report, output_dir / heatmap_row_name)
    export_heatmap_column_metadata_tsv(
        report.heatmap_report,
        output_dir / heatmap_column_name,
    )
    export_sample_exploration_summary_tsv(
        report.sample_exploration_report,
        output_dir / sample_summary_name,
    )
    export_sample_pca_scores_tsv(
        report.sample_exploration_report,
        output_dir / sample_scores_name,
    )
    export_sample_pca_variance_tsv(
        report.sample_exploration_report,
        output_dir / sample_variance_name,
    )
    export_sample_distance_tsv(
        report.sample_exploration_report,
        output_dir / sample_distance_name,
    )
    export_sample_cluster_tsv(
        report.sample_exploration_report,
        output_dir / sample_cluster_name,
    )

    go_summary_name = None
    go_term_name = None
    go_unannotated_name = None
    if report.go_enrichment_report is not None:
        go_summary_name = "biological_go_summary.tsv"
        go_term_name = "biological_go_terms.tsv"
        go_unannotated_name = "biological_go_unannotated.tsv"
        (output_dir / go_summary_name).write_text(
            render_go_enrichment_summary_tsv(report.go_enrichment_report),
            encoding="utf-8",
        )
        (output_dir / go_term_name).write_text(
            render_go_enrichment_term_tsv(report.go_enrichment_report),
            encoding="utf-8",
        )
        (output_dir / go_unannotated_name).write_text(
            render_go_enrichment_unannotated_tsv(report.go_enrichment_report),
            encoding="utf-8",
        )

    pathway_summary_name = None
    pathway_entry_name = None
    pathway_unresolved_name = None
    if report.pathway_enrichment_report is not None:
        pathway_summary_name = "biological_pathway_summary.tsv"
        pathway_entry_name = "biological_pathway_entries.tsv"
        pathway_unresolved_name = "biological_pathway_unresolved.tsv"
        (output_dir / pathway_summary_name).write_text(
            render_pathway_enrichment_summary_tsv(report.pathway_enrichment_report),
            encoding="utf-8",
        )
        (output_dir / pathway_entry_name).write_text(
            render_pathway_enrichment_entry_tsv(report.pathway_enrichment_report),
            encoding="utf-8",
        )
        (output_dir / pathway_unresolved_name).write_text(
            render_pathway_unresolved_member_tsv(report.pathway_enrichment_report),
            encoding="utf-8",
        )

    complex_summary_name = None
    complex_entry_name = None
    complex_unresolved_name = None
    if report.complex_enrichment_report is not None:
        complex_summary_name = "biological_complex_summary.tsv"
        complex_entry_name = "biological_complex_entries.tsv"
        complex_unresolved_name = "biological_complex_unresolved.tsv"
        (output_dir / complex_summary_name).write_text(
            render_complex_enrichment_summary_tsv(report.complex_enrichment_report),
            encoding="utf-8",
        )
        (output_dir / complex_entry_name).write_text(
            render_complex_enrichment_entry_tsv(report.complex_enrichment_report),
            encoding="utf-8",
        )
        (output_dir / complex_unresolved_name).write_text(
            render_complex_unresolved_member_tsv(report.complex_enrichment_report),
            encoding="utf-8",
        )

    artifacts = BiologicalResultReportArtifactPaths(
        summary_tsv=summary_name,
        differential_tsv=differential_name,
        protein_card_summary_tsv=protein_card_summary_name,
        protein_card_tsv=protein_card_name,
        experiment_confidence_summary_tsv=experiment_confidence_summary_name,
        experiment_confidence_components_tsv=experiment_confidence_components_name,
        annotation_summary_tsv=annotation_summary_name,
        annotation_tsv=annotation_name,
        annotation_unmapped_tsv=annotation_unmapped_name,
        context_summary_tsv=context_summary_name,
        context_mapping_tsv=context_mapping_name,
        context_term_tsv=context_term_name,
        context_unmapped_tsv=context_unmapped_name,
        context_rejected_tsv=context_rejected_name,
        volcano_tsv=volcano_tsv_name,
        volcano_json=volcano_json_name,
        volcano_svg=volcano_svg_name,
        volcano_html=volcano_html_name,
        heatmap_summary_tsv=heatmap_summary_name,
        heatmap_matrix_tsv=heatmap_matrix_name,
        heatmap_row_metadata_tsv=heatmap_row_name,
        heatmap_column_metadata_tsv=heatmap_column_name,
        sample_exploration_summary_tsv=sample_summary_name,
        sample_pca_scores_tsv=sample_scores_name,
        sample_pca_variance_tsv=sample_variance_name,
        sample_distance_tsv=sample_distance_name,
        sample_cluster_tsv=sample_cluster_name,
        report_html=report_html_name,
        go_summary_tsv=go_summary_name,
        go_term_tsv=go_term_name,
        go_unannotated_tsv=go_unannotated_name,
        pathway_summary_tsv=pathway_summary_name,
        pathway_entry_tsv=pathway_entry_name,
        pathway_unresolved_tsv=pathway_unresolved_name,
        complex_summary_tsv=complex_summary_name,
        complex_entry_tsv=complex_entry_name,
        complex_unresolved_tsv=complex_unresolved_name,
    )
    (output_dir / report_html_name).write_text(
        _render_biological_result_report_html(report, artifacts),
        encoding="utf-8",
    )
    return BiologicalResultReportExportManifest(
        summary=report.summary,
        artifacts=artifacts,
        context_summary_included=report.context_mapping_report is not None,
        go_summary_included=report.go_enrichment_report is not None,
        pathway_summary_included=report.pathway_enrichment_report is not None,
        complex_summary_included=report.complex_enrichment_report is not None,
        note=(
            "biological report export writes stable differential, protein-card, annotation, optional biological context, enrichment, volcano, heatmap, and sample exploration artifacts into one durable output directory"
        ),
    )


def _render_biological_result_report_html(
    report: BiologicalResultReportBundle,
    artifacts: BiologicalResultReportArtifactPaths,
) -> str:
    sections = [
        ("Differential proteins", artifacts.differential_tsv),
        ("Protein card summary", artifacts.protein_card_summary_tsv),
        ("Protein cards", artifacts.protein_card_tsv),
        (
            "Experiment confidence summary",
            artifacts.experiment_confidence_summary_tsv,
        ),
        (
            "Experiment confidence components",
            artifacts.experiment_confidence_components_tsv,
        ),
        ("Annotation summary", artifacts.annotation_summary_tsv),
        ("Annotated proteins", artifacts.annotation_tsv),
        ("Unmapped annotations", artifacts.annotation_unmapped_tsv),
        (
            "Biological context summary",
            artifacts.context_summary_tsv,
        ),
        (
            "Biological context mappings",
            artifacts.context_mapping_tsv,
        ),
        (
            "Biological context terms",
            artifacts.context_term_tsv,
        ),
        (
            "Biological context unmapped",
            artifacts.context_unmapped_tsv,
        ),
        (
            "Biological context rejected rows",
            artifacts.context_rejected_tsv,
        ),
        ("Volcano TSV", artifacts.volcano_tsv),
        ("Volcano JSON", artifacts.volcano_json),
        ("Volcano SVG", artifacts.volcano_svg),
        ("Volcano HTML", artifacts.volcano_html),
        ("Heatmap summary", artifacts.heatmap_summary_tsv),
        ("Heatmap matrix", artifacts.heatmap_matrix_tsv),
        ("Sample PCA scores", artifacts.sample_pca_scores_tsv),
        ("Sample distances", artifacts.sample_distance_tsv),
        ("Sample clusters", artifacts.sample_cluster_tsv),
    ]
    if artifacts.go_term_tsv is not None:
        sections.append(("GO enrichment", artifacts.go_term_tsv))
    if artifacts.pathway_entry_tsv is not None:
        sections.append(("Pathway enrichment", artifacts.pathway_entry_tsv))
    if artifacts.complex_entry_tsv is not None:
        sections.append(("Complex enrichment", artifacts.complex_entry_tsv))
    section_html = "".join(
        f"<li><strong>{escape(label)}</strong>: <code>{escape(path)}</code></li>"
        for label, path in sections
        if path is not None
    )
    confidence_table_html = _render_experiment_confidence_table_html(report)
    card_table_html = _render_protein_card_table_html(report)
    return (
        "<html><head><title>Bijux Proteomics Biological Report</title></head><body>"
        "<h1>Biological result report</h1>"
        f"<p><strong>Contrast</strong>: {escape(report.volcano_review.condition_a)} vs {escape(report.volcano_review.condition_b)}</p>"
        f"<p><strong>Proteins</strong>: {report.summary.protein_count} | "
        f"<strong>Significant</strong>: {report.summary.significant_protein_count} | "
        f"<strong>Protein cards</strong>: {report.summary.protein_card_count} | "
        f"<strong>Experiment confidence</strong>: {report.summary.experiment_confidence_score:.2f} "
        f"({escape(report.summary.experiment_confidence_tier)}) | "
        f"<strong>Annotated</strong>: {report.summary.annotation_entry_count} | "
        f"<strong>Heatmap rows</strong>: {report.summary.heatmap_entity_count}</p>"
        "<h2>Experiment confidence</h2>"
        f"{confidence_table_html}"
        "<h2>Final protein cards</h2>"
        f"{card_table_html}"
        "<h2>Artifacts</h2>"
        f"<ul>{section_html}</ul>"
        f"<p>{escape(report.note)}</p>"
        "</body></html>\n"
    )


def _render_experiment_confidence_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    headers = ("Component", "Score", "Tier", "Reason codes", "Message")
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(component.component.value)}</td>"
            f"<td>{component.score:.3f}</td>"
            f"<td>{escape(component.tier.value)}</td>"
            f"<td>{escape('; '.join(component.reason_codes))}</td>"
            f"<td>{escape(component.message)}</td>"
            "</tr>"
        )
        for component in report.experiment_confidence_report.components
    )
    summary = report.experiment_confidence_report.summary
    return (
        "<p>"
        f"<strong>Overall score</strong>: {summary.overall_score:.3f} | "
        f"<strong>Tier</strong>: {escape(summary.overall_tier.value)} | "
        f"<strong>Low-confidence components</strong>: "
        f"{summary.low_confidence_component_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


def _render_protein_card_table_html(report: BiologicalResultReportBundle) -> str:
    headers = (
        "Protein group",
        "Representative protein",
        "Graph claim",
        "Gene",
        "Evidence tier",
        "Peptides",
        "Functional regions",
        "Coverage",
        "log2FC",
        "Adjusted p-value",
        "Warnings",
        "Pathways",
        "Card ID",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(card.protein_group_id)}</td>"
            f"<td>{escape(card.representative_protein_ref)}</td>"
            f"<td><code>{escape(card.graph_claim_node_id)}</code></td>"
            f"<td>{escape(card.annotation.gene_symbol or '')}</td>"
            f"<td>{escape(card.evidence_tier.value)}</td>"
            f"<td>{card.peptide_count}</td>"
            f"<td>{escape('; '.join(f'{region.region_kind.value}:{region.label}' for region in card.functional_regions))}</td>"
            f"<td>{card.coverage.coverage_fraction:.2%}</td>"
            f"<td>{card.differential_result.log2_fold_change:.3f}</td>"
            f"<td>{_format_optional_float(card.differential_result.adjusted_p_value)}</td>"
            f"<td>{escape('; '.join(warning.code.value for warning in card.warnings))}</td>"
            f"<td>{escape('; '.join(entry.entry_id for entry in card.pathways))}</td>"
            f"<td><code>{escape(card.card_id)}</code></td>"
            "</tr>"
        )
        for card in report.protein_cards.cards
    )
    return (
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


def _format_optional_float(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4g}"


__all__ = [
    "BiologicalResultReportArtifactPaths",
    "BiologicalResultReportBundle",
    "BiologicalResultReportExportManifest",
    "BiologicalResultReportSummary",
    "BiologicalResultSelectionPolicy",
    "build_biological_result_report_bundle",
    "export_biological_result_report_bundle",
    "render_biological_result_report_summary_tsv",
]
