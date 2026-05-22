# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned biological result bundles over governed label-free protein quantification."""

from __future__ import annotations

import csv
from html import escape
from io import StringIO
from pathlib import Path

from bijux_proteomics.interpretation import (
    ComplexEnrichmentCorrectionPolicy,
    ComplexEnrichmentReport,
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
    parse_complex_membership_table,
    parse_go_annotation_table,
    parse_pathway_membership_table,
    parse_protein_annotation_table,
    render_go_enrichment_summary_tsv,
    render_go_enrichment_term_tsv,
    render_go_enrichment_unannotated_tsv,
    render_mapped_protein_annotation_tsv,
    render_pathway_enrichment_entry_tsv,
    render_pathway_enrichment_summary_tsv,
    render_pathway_unresolved_member_tsv,
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
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    SampleExplorationReport,
    build_differential_abundance_report,
    build_heatmap_preparation_report,
    build_label_free_intensity_table,
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
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics_foundation import JsonModel


class BiologicalResultSelectionPolicy(JsonModel):
    """Selection policy for interpretation-focused biological result bundles."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float = Field(default=1.0, ge=0.0)
    heatmap_max_entity_count: int = Field(default=50, ge=1)
    heatmap_min_observed_fraction: float = Field(default=0.5, ge=0.0, le=1.0)


class BiologicalResultReportSummary(JsonModel):
    """Compact summary over one biological result bundle."""

    model_config = ConfigDict(extra="forbid")

    protein_count: int = Field(..., ge=0)
    significant_protein_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    annotation_entry_count: int = Field(..., ge=0)
    annotation_unmapped_count: int = Field(..., ge=0)
    go_enriched_term_count: int = Field(..., ge=0)
    pathway_enriched_entry_count: int = Field(..., ge=0)
    complex_enriched_entry_count: int = Field(..., ge=0)
    heatmap_entity_count: int = Field(..., ge=0)
    pca_outlier_sample_count: int = Field(..., ge=0)


class BiologicalResultReportBundle(JsonModel):
    """Owned workflow bundle over differential proteins and review-ready plots."""

    model_config = ConfigDict(extra="forbid")

    differential_report: DifferentialAbundanceReport
    annotation_report: ProteinAnnotationMappingReport
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
    annotation_summary_tsv: str = Field(..., min_length=1)
    annotation_mapped_tsv: str = Field(..., min_length=1)
    annotation_unmapped_tsv: str = Field(..., min_length=1)
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
    go_summary_included: bool
    pathway_summary_included: bool
    complex_summary_included: bool
    note: str = Field(..., min_length=1)


def build_biological_result_report_bundle(
    input_tsv_path: Path,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    proteins_fasta_path: Path,
    annotation_tsv_path: Path | None = None,
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
) -> BiologicalResultReportBundle:
    """Build a biological result bundle over one governed protein LFQ workflow."""

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
    active_selection_policy = selection_policy or BiologicalResultSelectionPolicy()
    parse_report = parse_ms1_feature_table(input_tsv_path, mapping=active_mapping)
    normalized_table = normalize_label_free_table(
        build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=aggregation_method,
            top_n=top_n,
        ),
        method=normalization_method,
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
        differential_report
    )
    annotation_report = build_protein_annotation_mapping_report(
        differential_reference_entries,
        fasta_report.accepted_records,
        custom_annotations=()
        if custom_annotation_report is None
        else custom_annotation_report.accepted_records,
    )
    background_entries = _build_background_reference_entries(normalized_table)
    foreground_entries = _build_foreground_reference_entries(
        differential_report,
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
    significant_protein_count = len(
        _select_significant_entity_ids(differential_report, policy=active_selection_policy)
    )
    return BiologicalResultReportBundle(
        differential_report=differential_report,
        annotation_report=annotation_report,
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
            annotation_entry_count=len(annotation_report.mapped_entries),
            annotation_unmapped_count=len(annotation_report.unmapped_entries),
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
            "biological reporting assembles governed protein differential analysis, annotation mapping, enrichment, volcano review, heatmap preparation, and sample exploration into one owned workflow bundle"
        ),
    )


def _resolve_contrast(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None,
    condition_b: str | None,
) -> tuple[str, str]:
    if bool(condition_a) ^ bool(condition_b):
        raise ValueError("both condition_a and condition_b are required together")
    if condition_a is not None and condition_b is not None:
        return condition_a, condition_b
    conditions = tuple(
        sorted({entry.condition for entry in design_entries if entry.condition})
    )
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
) -> tuple[ProteinReferenceEntry, ...]:
    return tuple(
        ProteinReferenceEntry(
            row_number=index + 2,
            source_row_id=entry.entity_id,
            input_protein_ref=entry.entity_id,
            protein_ref=entry.entity_id,
        )
        for index, entry in enumerate(report.entries)
    )


def _build_background_reference_entries(
    normalized_table,
) -> tuple[ProteinReferenceEntry, ...]:
    return tuple(
        ProteinReferenceEntry(
            row_number=index + 2,
            source_row_id=entity_id,
            input_protein_ref=entity_id,
            protein_ref=entity_id,
        )
        for index, entity_id in enumerate(normalized_table.entity_ids)
    )


def _build_foreground_reference_entries(
    report: DifferentialAbundanceReport,
    *,
    policy: BiologicalResultSelectionPolicy,
) -> tuple[ProteinReferenceEntry, ...]:
    significant_entity_ids = _select_significant_entity_ids(report, policy=policy)
    return tuple(
        ProteinReferenceEntry(
            row_number=index + 2,
            source_row_id=entity_id,
            input_protein_ref=entity_id,
            protein_ref=entity_id,
        )
        for index, entity_id in enumerate(significant_entity_ids)
    )


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
    annotation_summary_name = "biological_annotation_summary.tsv"
    annotation_mapped_name = "biological_annotations.tsv"
    annotation_unmapped_name = "biological_annotation_unmapped.tsv"
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
    (output_dir / annotation_summary_name).write_text(
        render_protein_annotation_summary_tsv(report.annotation_report),
        encoding="utf-8",
    )
    (output_dir / annotation_mapped_name).write_text(
        render_mapped_protein_annotation_tsv(report.annotation_report),
        encoding="utf-8",
    )
    (output_dir / annotation_unmapped_name).write_text(
        render_unmapped_protein_annotation_tsv(report.annotation_report),
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
        annotation_summary_tsv=annotation_summary_name,
        annotation_mapped_tsv=annotation_mapped_name,
        annotation_unmapped_tsv=annotation_unmapped_name,
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
        go_summary_included=report.go_enrichment_report is not None,
        pathway_summary_included=report.pathway_enrichment_report is not None,
        complex_summary_included=report.complex_enrichment_report is not None,
        note=(
            "biological report export writes stable differential, annotation, enrichment, volcano, heatmap, and sample exploration artifacts into one durable output directory"
        ),
    )


def _render_biological_result_report_html(
    report: BiologicalResultReportBundle,
    artifacts: BiologicalResultReportArtifactPaths,
) -> str:
    sections = [
        ("Differential proteins", artifacts.differential_tsv),
        ("Annotation summary", artifacts.annotation_summary_tsv),
        ("Mapped annotations", artifacts.annotation_mapped_tsv),
        ("Unmapped annotations", artifacts.annotation_unmapped_tsv),
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
    )
    return (
        "<html><head><title>Bijux Proteomics Biological Report</title></head><body>"
        "<h1>Biological result report</h1>"
        f"<p><strong>Contrast</strong>: {escape(report.volcano_review.condition_a)} vs {escape(report.volcano_review.condition_b)}</p>"
        f"<p><strong>Proteins</strong>: {report.summary.protein_count} | "
        f"<strong>Significant</strong>: {report.summary.significant_protein_count} | "
        f"<strong>Annotated</strong>: {report.summary.annotation_entry_count} | "
        f"<strong>Heatmap rows</strong>: {report.summary.heatmap_entity_count}</p>"
        "<h2>Artifacts</h2>"
        f"<ul>{section_html}</ul>"
        f"<p>{escape(report.note)}</p>"
        "</body></html>\n"
    )


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
