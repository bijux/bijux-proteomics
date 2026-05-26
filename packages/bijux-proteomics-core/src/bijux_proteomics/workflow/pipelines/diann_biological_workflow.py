# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned DIA-NN-to-biology workflow bundles."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.dia import (
    DiaPeptideRollupMethod,
    DiaPeptideMatrixReport,
    DiaPrecursorMatrixPolicy,
    DiaPrecursorMatrixReport,
    DiaProteinMatrixReport,
    DiaProteinMatrixTargetKind,
    DiaProteinRollupMethod,
    DiaRunQcReport,
    DiaSharedPeptidePolicy,
    build_dia_peptide_matrix_report,
    build_dia_precursor_matrix_report,
    build_dia_protein_matrix_report,
    build_dia_run_qc_report,
    render_dia_peptide_missingness_tsv,
    render_dia_peptide_quantity_matrix_tsv,
    render_dia_precursor_missingness_tsv,
    render_dia_precursor_matrix_summary_tsv,
    render_dia_precursor_metadata_tsv,
    render_dia_precursor_q_value_matrix_tsv,
    render_dia_precursor_quantity_matrix_tsv,
    render_dia_protein_missingness_tsv,
    render_dia_protein_matrix_summary_tsv,
    render_dia_protein_quantity_matrix_tsv,
    render_dia_protein_rollup_evidence_tsv,
    render_dia_run_qc_correlation_tsv,
    render_dia_run_qc_intensity_distribution_tsv,
    render_dia_run_qc_outlier_tsv,
    render_dia_run_qc_run_table_tsv,
    render_dia_run_qc_summary_tsv,
)
from bijux_proteomics.identification.diann_import import (
    DiaNnBundleImportReport,
    build_diann_import_report,
    render_diann_rejected_row_tsv,
    render_diann_summary_tsv,
)
from bijux_proteomics.identification.rejected_evidence_table import (
    render_rejected_evidence_tsv,
)
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import NormalizationMethod
from bijux_proteomics.study import ExperimentDesign, coerce_experiment_design
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportBundle,
    BiologicalResultReportExportManifest,
    BiologicalResultSelectionPolicy,
    VolcanoReviewPolicy,
    build_biological_result_report_bundle_from_quant_table,
    write_biological_result_report_bundle,
)
from bijux_proteomics.workflow.pipelines.dia_differential_analysis import (
    DiaDifferentialAnalysisReport,
    DiaDifferentialSourceKind,
    build_dia_differential_analysis_report,
    build_dia_differential_input_report,
    render_dia_differential_matrix_tsv,
    render_dia_differential_missingness_tsv,
    render_dia_differential_qc_summary_tsv,
    render_dia_differential_results_tsv,
    render_dia_normalization_balance_plot_tsv,
)
from bijux_proteomics.workflow.exports.artifact_layout import synchronize_workflow_artifact_layout
from bijux_proteomics_foundation import JsonModel


class DiannBiologicalWorkflowSummary(JsonModel):
    """Compact summary over one DIA-NN-to-biology workflow bundle."""

    model_config = ConfigDict(extra="forbid")

    imported_precursor_count: int = Field(..., ge=0)
    rejected_precursor_count: int = Field(..., ge=0)
    rejected_evidence_count: int = Field(..., ge=0)
    imported_protein_group_row_count: int = Field(..., ge=0)
    filtered_q_value_row_count: int = Field(..., ge=0)
    precursor_matrix_row_count: int = Field(..., ge=0)
    protein_matrix_row_count: int = Field(..., ge=0)
    run_count: int = Field(..., ge=0)
    flagged_run_count: int = Field(..., ge=0)
    significant_protein_count: int = Field(..., ge=0)
    annotation_entry_count: int = Field(..., ge=0)
    protein_card_count: int = Field(..., ge=0)
    context_term_count: int = Field(..., ge=0)
    go_enriched_term_count: int = Field(..., ge=0)
    pathway_enriched_entry_count: int = Field(..., ge=0)
    complex_enriched_entry_count: int = Field(..., ge=0)


class DiannBiologicalWorkflowBundle(JsonModel):
    """Owned bundle from one DIA-NN report to final biological report surfaces."""

    model_config = ConfigDict(extra="forbid")

    import_report: DiaNnBundleImportReport
    precursor_matrix_report: DiaPrecursorMatrixReport
    peptide_matrix_report: DiaPeptideMatrixReport
    protein_matrix_report: DiaProteinMatrixReport
    run_qc_report: DiaRunQcReport
    differential_analysis_report: DiaDifferentialAnalysisReport
    biological_report: BiologicalResultReportBundle
    summary: DiannBiologicalWorkflowSummary
    note: str = Field(..., min_length=1)


class DiannBiologicalWorkflowArtifactPaths(JsonModel):
    """Relative artifact paths written into one DIA-NN biology output directory."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    import_summary_tsv: str = Field(..., min_length=1)
    import_rejected_rows_tsv: str = Field(..., min_length=1)
    import_rejected_evidence_tsv: str = Field(..., min_length=1)
    precursor_summary_tsv: str = Field(..., min_length=1)
    precursor_quantity_matrix_tsv: str = Field(..., min_length=1)
    precursor_q_value_matrix_tsv: str = Field(..., min_length=1)
    precursor_missingness_tsv: str = Field(..., min_length=1)
    precursor_metadata_tsv: str = Field(..., min_length=1)
    peptide_quantity_matrix_tsv: str = Field(..., min_length=1)
    peptide_missingness_tsv: str = Field(..., min_length=1)
    protein_summary_tsv: str = Field(..., min_length=1)
    protein_quantity_matrix_tsv: str = Field(..., min_length=1)
    protein_missingness_tsv: str = Field(..., min_length=1)
    protein_rollup_evidence_tsv: str = Field(..., min_length=1)
    run_qc_summary_tsv: str = Field(..., min_length=1)
    run_qc_runs_tsv: str = Field(..., min_length=1)
    run_qc_intensity_tsv: str = Field(..., min_length=1)
    run_qc_correlation_tsv: str = Field(..., min_length=1)
    run_qc_outliers_tsv: str = Field(..., min_length=1)
    differential_raw_matrix_tsv: str = Field(..., min_length=1)
    differential_normalized_matrix_tsv: str = Field(..., min_length=1)
    differential_raw_missingness_tsv: str = Field(..., min_length=1)
    differential_normalized_missingness_tsv: str = Field(..., min_length=1)
    differential_results_tsv: str = Field(..., min_length=1)
    differential_qc_summary_tsv: str = Field(..., min_length=1)
    differential_balance_tsv: str = Field(..., min_length=1)
    biological_manifest_json: str = Field(..., min_length=1)
    protein_card_summary_tsv: str = Field(..., min_length=1)
    protein_card_tsv: str = Field(..., min_length=1)
    annotation_tsv: str = Field(..., min_length=1)
    annotation_unmapped_tsv: str = Field(..., min_length=1)
    context_mapping_tsv: str | None = None
    context_term_tsv: str | None = None
    context_unmapped_tsv: str | None = None
    context_rejected_tsv: str | None = None
    report_html: str = Field(..., min_length=1)


class DiannBiologicalWorkflowExportManifest(JsonModel):
    """Stable manifest over one exported DIA-NN-to-biology directory."""

    model_config = ConfigDict(extra="forbid")

    summary: DiannBiologicalWorkflowSummary
    artifacts: DiannBiologicalWorkflowArtifactPaths
    biological_report_manifest: BiologicalResultReportExportManifest
    note: str = Field(..., min_length=1)


def build_diann_biological_workflow_bundle(
    result_tsv_path: Path,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    proteins_fasta_path: Path,
    protocol_context_tsv_path: Path | None = None,
    config_path: Path | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = 0.01,
    peptide_rollup_method: DiaPeptideRollupMethod = DiaPeptideRollupMethod.MAX,
    target_kind: DiaProteinMatrixTargetKind = DiaProteinMatrixTargetKind.PROTEIN_GROUP,
    shared_peptide_policy: DiaSharedPeptidePolicy = DiaSharedPeptidePolicy.INCLUDE,
    protein_rollup_method: DiaProteinRollupMethod = DiaProteinRollupMethod.SUM,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    annotation_tsv_path: Path | None = None,
    context_annotation_tsv_path: Path | None = None,
    go_annotation_tsv_path: Path | None = None,
    pathway_membership_tsv_path: Path | None = None,
    complex_membership_tsv_path: Path | None = None,
    selection_policy: BiologicalResultSelectionPolicy | None = None,
    volcano_policy: VolcanoReviewPolicy | None = None,
) -> DiannBiologicalWorkflowBundle:
    """Build one governed DIA-NN-to-biology workflow bundle."""

    experiment_design = coerce_experiment_design(design_entries)
    import_report = build_diann_import_report(
        result_tsv_path,
        config_path=config_path,
    )
    precursor_matrix_report = build_dia_precursor_matrix_report(
        import_report.precursor_rows,
        source_name="DIA-NN",
        policy=DiaPrecursorMatrixPolicy(
            include_decoys=include_decoys,
            max_q_value=max_q_value,
        ),
    )
    peptide_matrix_report = build_dia_peptide_matrix_report(
        precursor_matrix_report,
        rollup_method=peptide_rollup_method,
    )
    protein_matrix_report = build_dia_protein_matrix_report(
        peptide_matrix_report,
        target_kind=target_kind,
        shared_peptide_policy=shared_peptide_policy,
        rollup_method=protein_rollup_method,
    )
    differential_input = build_dia_differential_input_report(
        protein_matrix_report,
        source_kind=DiaDifferentialSourceKind.DIANN,
        note=(
            "dia differential input preserves one protein-level sample matrix over governed DIA-NN rollup evidence"
        ),
    )
    differential_analysis_report = build_dia_differential_analysis_report(
        differential_input,
        experiment_design,
        normalization_method=normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    run_qc_report = build_dia_run_qc_report(
        import_report,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
        low_correlation_threshold=-1.0,
    )
    biological_report = build_biological_result_report_bundle_from_quant_table(
        differential_analysis_report.normalized_table,
        experiment_design,
        proteins_fasta_path=proteins_fasta_path,
        protocol_context_tsv_path=protocol_context_tsv_path,
        annotation_tsv_path=annotation_tsv_path,
        context_annotation_tsv_path=context_annotation_tsv_path,
        go_annotation_tsv_path=go_annotation_tsv_path,
        pathway_membership_tsv_path=pathway_membership_tsv_path,
        complex_membership_tsv_path=complex_membership_tsv_path,
        normalization_method=NormalizationMethod.NONE,
        condition_a=condition_a,
        condition_b=condition_b,
        selection_policy=selection_policy,
        volcano_policy=volcano_policy,
    )
    return DiannBiologicalWorkflowBundle(
        import_report=import_report,
        precursor_matrix_report=precursor_matrix_report,
        peptide_matrix_report=peptide_matrix_report,
        protein_matrix_report=protein_matrix_report,
        run_qc_report=run_qc_report,
        differential_analysis_report=differential_analysis_report,
        biological_report=biological_report,
        summary=DiannBiologicalWorkflowSummary(
            imported_precursor_count=import_report.summary.accepted_precursor_count,
            rejected_precursor_count=import_report.summary.rejected_precursor_count,
            rejected_evidence_count=len(import_report.rejected_evidence_rows),
            imported_protein_group_row_count=import_report.summary.protein_group_row_count,
            filtered_q_value_row_count=precursor_matrix_report.summary.excluded_q_value_count,
            precursor_matrix_row_count=precursor_matrix_report.summary.precursor_row_count,
            protein_matrix_row_count=protein_matrix_report.summary.protein_row_count,
            run_count=run_qc_report.summary.run_count,
            flagged_run_count=run_qc_report.summary.flagged_run_count,
            significant_protein_count=biological_report.summary.significant_protein_count,
            annotation_entry_count=biological_report.summary.annotation_entry_count,
            protein_card_count=biological_report.summary.protein_card_count,
            context_term_count=biological_report.summary.context_term_count,
            go_enriched_term_count=biological_report.summary.go_enriched_term_count,
            pathway_enriched_entry_count=biological_report.summary.pathway_enriched_entry_count,
            complex_enriched_entry_count=biological_report.summary.complex_enriched_entry_count,
        ),
        note=(
            "DIA-NN biological workflow preserves precursor, peptide, and protein matrices, explicit DIA rollup evidence, run QC, normalized differential analysis, and final biology reporting in one owned bundle"
        ),
    )


def render_diann_biological_workflow_summary_tsv(
    report: DiannBiologicalWorkflowBundle,
) -> str:
    """Render one compact DIA-NN biology workflow summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("imported_precursor_count", report.summary.imported_precursor_count),
        ("rejected_precursor_count", report.summary.rejected_precursor_count),
        ("rejected_evidence_count", report.summary.rejected_evidence_count),
        ("imported_protein_group_row_count", report.summary.imported_protein_group_row_count),
        ("filtered_q_value_row_count", report.summary.filtered_q_value_row_count),
        ("precursor_matrix_row_count", report.summary.precursor_matrix_row_count),
        ("protein_matrix_row_count", report.summary.protein_matrix_row_count),
        ("run_count", report.summary.run_count),
        ("flagged_run_count", report.summary.flagged_run_count),
        ("significant_protein_count", report.summary.significant_protein_count),
        ("annotation_entry_count", report.summary.annotation_entry_count),
        ("protein_card_count", report.summary.protein_card_count),
        ("context_term_count", report.summary.context_term_count),
        ("go_enriched_term_count", report.summary.go_enriched_term_count),
        ("pathway_enriched_entry_count", report.summary.pathway_enriched_entry_count),
        ("complex_enriched_entry_count", report.summary.complex_enriched_entry_count),
        ("note", report.note),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def write_diann_biological_workflow_bundle(
    report: DiannBiologicalWorkflowBundle,
    output_dir: Path,
) -> DiannBiologicalWorkflowExportManifest:
    """Write one DIA-NN biology workflow bundle into a stable output directory."""

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_name = "diann_biological_summary.tsv"
    import_summary_name = "diann_import_summary.tsv"
    import_rejected_rows_name = "diann_import_rejected_rows.tsv"
    import_rejected_evidence_name = "diann_import_rejected_evidence.tsv"
    precursor_summary_name = "diann_precursor_matrix_summary.tsv"
    precursor_matrix_name = "diann_precursor_quantity_matrix.tsv"
    precursor_q_value_name = "diann_precursor_q_values.tsv"
    precursor_missingness_name = "diann_precursor_missingness.tsv"
    precursor_metadata_name = "diann_precursor_metadata.tsv"
    peptide_matrix_name = "diann_peptide_quantity_matrix.tsv"
    peptide_missingness_name = "diann_peptide_missingness.tsv"
    protein_summary_name = "diann_protein_matrix_summary.tsv"
    protein_matrix_name = "diann_protein_quantity_matrix.tsv"
    protein_missingness_name = "diann_protein_missingness.tsv"
    protein_rollup_evidence_name = "diann_protein_rollup_evidence.tsv"
    run_qc_summary_name = "diann_run_qc_summary.tsv"
    run_qc_runs_name = "diann_run_qc_runs.tsv"
    run_qc_intensity_name = "diann_run_qc_intensity.tsv"
    run_qc_correlation_name = "diann_run_qc_correlation.tsv"
    run_qc_outliers_name = "diann_run_qc_outliers.tsv"
    differential_raw_name = "diann_differential_raw_matrix.tsv"
    differential_normalized_name = "diann_differential_normalized_matrix.tsv"
    differential_raw_missingness_name = "diann_differential_raw_missingness.tsv"
    differential_normalized_missingness_name = "diann_differential_normalized_missingness.tsv"
    differential_results_name = "diann_differential_results.tsv"
    differential_qc_summary_name = "diann_differential_qc_summary.tsv"
    differential_balance_name = "diann_differential_balance.tsv"
    biological_manifest_name = "biological_report_manifest.json"

    write_output_table_tsv((output_dir / summary_name), render_diann_biological_workflow_summary_tsv(report))
    write_output_table_tsv((output_dir / import_summary_name), render_diann_summary_tsv(report.import_report.summary))
    write_output_table_tsv((output_dir / import_rejected_rows_name), render_diann_rejected_row_tsv(report.import_report.rejected_rows))
    write_output_table_tsv((output_dir / import_rejected_evidence_name), render_rejected_evidence_tsv(report.import_report.rejected_evidence_rows))
    write_output_table_tsv((output_dir / precursor_summary_name), render_dia_precursor_matrix_summary_tsv(report.precursor_matrix_report))
    write_output_table_tsv((output_dir / precursor_matrix_name), render_dia_precursor_quantity_matrix_tsv(report.precursor_matrix_report))
    write_output_table_tsv((output_dir / precursor_q_value_name), render_dia_precursor_q_value_matrix_tsv(report.precursor_matrix_report))
    write_output_table_tsv((output_dir / precursor_missingness_name), render_dia_precursor_missingness_tsv(report.precursor_matrix_report))
    write_output_table_tsv((output_dir / precursor_metadata_name), render_dia_precursor_metadata_tsv(report.precursor_matrix_report))
    write_output_table_tsv((output_dir / peptide_matrix_name), render_dia_peptide_quantity_matrix_tsv(report.peptide_matrix_report))
    write_output_table_tsv((output_dir / peptide_missingness_name), render_dia_peptide_missingness_tsv(report.peptide_matrix_report))
    write_output_table_tsv((output_dir / protein_summary_name), render_dia_protein_matrix_summary_tsv(report.protein_matrix_report))
    write_output_table_tsv((output_dir / protein_matrix_name), render_dia_protein_quantity_matrix_tsv(report.protein_matrix_report))
    write_output_table_tsv((output_dir / protein_missingness_name), render_dia_protein_missingness_tsv(report.protein_matrix_report))
    write_output_table_tsv((output_dir / protein_rollup_evidence_name), render_dia_protein_rollup_evidence_tsv(report.protein_matrix_report))
    write_output_table_tsv((output_dir / run_qc_summary_name), render_dia_run_qc_summary_tsv(report.run_qc_report))
    write_output_table_tsv((output_dir / run_qc_runs_name), render_dia_run_qc_run_table_tsv(report.run_qc_report))
    write_output_table_tsv((output_dir / run_qc_intensity_name), render_dia_run_qc_intensity_distribution_tsv(report.run_qc_report))
    write_output_table_tsv((output_dir / run_qc_correlation_name), render_dia_run_qc_correlation_tsv(report.run_qc_report))
    write_output_table_tsv((output_dir / run_qc_outliers_name), render_dia_run_qc_outlier_tsv(report.run_qc_report))
    write_output_table_tsv((output_dir / differential_raw_name), render_dia_differential_matrix_tsv(
            report.differential_analysis_report.input_report.table
        ))
    write_output_table_tsv((output_dir / differential_normalized_name), render_dia_differential_matrix_tsv(
            report.differential_analysis_report.normalized_table
        ))
    write_output_table_tsv((output_dir / differential_raw_missingness_name), render_dia_differential_missingness_tsv(
            report.differential_analysis_report.input_report.table
        ))
    write_output_table_tsv((output_dir / differential_normalized_missingness_name), render_dia_differential_missingness_tsv(
            report.differential_analysis_report.normalized_table
        ))
    write_output_table_tsv((output_dir / differential_results_name), render_dia_differential_results_tsv(report.differential_analysis_report))
    write_output_table_tsv((output_dir / differential_qc_summary_name), render_dia_differential_qc_summary_tsv(report.differential_analysis_report))
    write_output_table_tsv((output_dir / differential_balance_name), render_dia_normalization_balance_plot_tsv(
            report.differential_analysis_report.normalization_balance_plot
        ))
    biological_manifest = write_biological_result_report_bundle(
        report.biological_report,
        output_dir,
    )
    (output_dir / biological_manifest_name).write_text(
        biological_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )
    synchronize_workflow_artifact_layout(
        output_dir,
        producer_function="write_diann_biological_workflow_bundle",
    )
    return DiannBiologicalWorkflowExportManifest(
        summary=report.summary,
        artifacts=DiannBiologicalWorkflowArtifactPaths(
            summary_tsv=summary_name,
            import_summary_tsv=import_summary_name,
            import_rejected_rows_tsv=import_rejected_rows_name,
            import_rejected_evidence_tsv=import_rejected_evidence_name,
            precursor_summary_tsv=precursor_summary_name,
            precursor_quantity_matrix_tsv=precursor_matrix_name,
            precursor_q_value_matrix_tsv=precursor_q_value_name,
            precursor_missingness_tsv=precursor_missingness_name,
            precursor_metadata_tsv=precursor_metadata_name,
            peptide_quantity_matrix_tsv=peptide_matrix_name,
            peptide_missingness_tsv=peptide_missingness_name,
            protein_summary_tsv=protein_summary_name,
            protein_quantity_matrix_tsv=protein_matrix_name,
            protein_missingness_tsv=protein_missingness_name,
            protein_rollup_evidence_tsv=protein_rollup_evidence_name,
            run_qc_summary_tsv=run_qc_summary_name,
            run_qc_runs_tsv=run_qc_runs_name,
            run_qc_intensity_tsv=run_qc_intensity_name,
            run_qc_correlation_tsv=run_qc_correlation_name,
            run_qc_outliers_tsv=run_qc_outliers_name,
            differential_raw_matrix_tsv=differential_raw_name,
            differential_normalized_matrix_tsv=differential_normalized_name,
            differential_raw_missingness_tsv=differential_raw_missingness_name,
            differential_normalized_missingness_tsv=differential_normalized_missingness_name,
            differential_results_tsv=differential_results_name,
            differential_qc_summary_tsv=differential_qc_summary_name,
            differential_balance_tsv=differential_balance_name,
            biological_manifest_json=biological_manifest_name,
            protein_card_summary_tsv=biological_manifest.artifacts.protein_card_summary_tsv,
            protein_card_tsv=biological_manifest.artifacts.protein_card_tsv,
            annotation_tsv=biological_manifest.artifacts.annotation_tsv,
            annotation_unmapped_tsv=biological_manifest.artifacts.annotation_unmapped_tsv,
            context_mapping_tsv=biological_manifest.artifacts.context_mapping_tsv,
            context_term_tsv=biological_manifest.artifacts.context_term_tsv,
            context_unmapped_tsv=biological_manifest.artifacts.context_unmapped_tsv,
            context_rejected_tsv=biological_manifest.artifacts.context_rejected_tsv,
            report_html=biological_manifest.artifacts.report_html,
        ),
        biological_report_manifest=biological_manifest,
        note=(
            "DIA-NN biology export preserves import, matrix, QC, differential, and final biological report surfaces in one directory"
        ),
    )


def export_diann_biological_workflow_bundle(
    report: DiannBiologicalWorkflowBundle,
    output_dir: Path,
) -> DiannBiologicalWorkflowExportManifest:
    """Compatibility wrapper for the legacy DIA-NN workflow bundle export name."""

    return write_diann_biological_workflow_bundle(report, output_dir)
