# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned flagship Bijux proteomics run workflow bundles."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._atomic_files import atomic_write_text
from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.dia.run_qc import render_dia_run_qc_summary_tsv
from bijux_proteomics.identification import SearchAdapterKind
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    NormalizationMethod,
)
from bijux_proteomics.quantification.normalization import (
    normalize_label_free_table,
)
from bijux_proteomics.quantification.statistics import (
    render_differential_abundance_tsv,
)
from bijux_proteomics.review.explanations.volcano_plots import VolcanoReviewPolicy
from bijux_proteomics.study import ExperimentDesign, coerce_experiment_design
from bijux_proteomics.workflow.pipelines.comparative.dia_differential_analysis import (
    render_dia_differential_matrix_tsv,
)
from bijux_proteomics.workflow.pipelines.engines.dda_biological_workflow import (
    DdaBiologicalWorkflowBundle,
    DdaBiologicalWorkflowExportManifest,
    DdaPsmAcceptancePolicy,
    build_dda_biological_workflow_bundle,
    build_label_free_quant_table_from_protein_lfq_report,
    write_dda_biological_workflow_bundle,
)
from bijux_proteomics.workflow.pipelines.engines.diann_biological_workflow import (
    DiannBiologicalWorkflowBundle,
    DiannBiologicalWorkflowExportManifest,
    build_diann_biological_workflow_bundle,
    write_diann_biological_workflow_bundle,
)
from bijux_proteomics.workflow.pipelines.engines.maxquant_biological_workflow import (
    MaxquantBiologicalWorkflowBundle,
    MaxquantBiologicalWorkflowExportManifest,
    MaxquantProteinGroupAcceptancePolicy,
    build_maxquant_biological_workflow_bundle,
    render_maxquant_lfq_matrix_tsv,
    write_maxquant_biological_workflow_bundle,
)
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportBundle,
    BiologicalResultReportExportManifest,
    BiologicalResultSelectionPolicy,
)
from bijux_proteomics_foundation import JsonModel


class ProteomicsRunEngine(StrEnum):
    """Supported flagship engine entrypoints."""

    DIANN = "diann"
    MAXQUANT = "maxquant"
    FRAGPIPE = "fragpipe"


class ProteomicsRunSummary(JsonModel):
    """Compact summary over one flagship proteomics run."""

    model_config = ConfigDict(extra="forbid")

    engine: ProteomicsRunEngine
    metadata_row_count: int = Field(..., ge=0)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    protein_count: int = Field(..., ge=0)
    significant_protein_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    qc_issue_count: int = Field(..., ge=0)
    enrichment_entry_count: int = Field(..., ge=0)


class ProteomicsRunBundle(JsonModel):
    """One governed flagship run bundle over common biology workflows."""

    model_config = ConfigDict(extra="forbid")

    engine: ProteomicsRunEngine
    normalization_method: NormalizationMethod
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    summary: ProteomicsRunSummary
    diann_workflow: DiannBiologicalWorkflowBundle | None = None
    maxquant_workflow: MaxquantBiologicalWorkflowBundle | None = None
    fragpipe_workflow: DdaBiologicalWorkflowBundle | None = None
    note: str = Field(..., min_length=1)


class ProteomicsRunArtifactPaths(JsonModel):
    """Relative artifact paths written into one flagship run directory."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    qc_summary_tsv: str = Field(..., min_length=1)
    normalized_matrix_tsv: str = Field(..., min_length=1)
    differential_tsv: str = Field(..., min_length=1)
    enrichment_tsv: str = Field(..., min_length=1)
    report_html: str = Field(..., min_length=1)
    workflow_manifest_json: str = Field(..., min_length=1)
    biological_manifest_json: str = Field(..., min_length=1)


class ProteomicsRunExportManifest(JsonModel):
    """Stable manifest over one exported flagship run directory."""

    model_config = ConfigDict(extra="forbid")

    summary: ProteomicsRunSummary
    artifacts: ProteomicsRunArtifactPaths
    workflow_manifest: (
        DiannBiologicalWorkflowExportManifest
        | MaxquantBiologicalWorkflowExportManifest
        | DdaBiologicalWorkflowExportManifest
    )
    biological_report_manifest: BiologicalResultReportExportManifest
    note: str = Field(..., min_length=1)


def build_proteomics_run_bundle(
    *,
    engine: ProteomicsRunEngine,
    metadata_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    proteins_fasta_path: Path,
    report_tsv_path: Path,
    contrast: str | None = None,
    peptides_tsv_path: Path | None = None,
    protein_groups_tsv_path: Path | None = None,
    source_protein_tsv_path: Path | None = None,
    config_path: Path | None = None,
    annotation_tsv_path: Path | None = None,
    go_annotation_tsv_path: Path | None = None,
    pathway_membership_tsv_path: Path | None = None,
    complex_membership_tsv_path: Path | None = None,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    max_q_value: float = 0.01,
    psm_q_value_threshold: float = 0.01,
    selection_policy: BiologicalResultSelectionPolicy | None = None,
    volcano_policy: VolcanoReviewPolicy | None = None,
) -> ProteomicsRunBundle:
    """Build one flagship proteomics run bundle over a supported engine input."""

    experiment_design = coerce_experiment_design(metadata_entries)
    if not experiment_design.entries:
        raise ValueError("flagship proteomics run requires at least one metadata row")
    condition_a, condition_b = _resolve_contrast(experiment_design, contrast=contrast)
    active_selection_policy = selection_policy or BiologicalResultSelectionPolicy()
    if engine is ProteomicsRunEngine.DIANN:
        diann_workflow = build_diann_biological_workflow_bundle(
            report_tsv_path,
            experiment_design,
            proteins_fasta_path=proteins_fasta_path,
            config_path=config_path,
            max_q_value=max_q_value,
            normalization_method=normalization_method,
            condition_a=condition_a,
            condition_b=condition_b,
            annotation_tsv_path=annotation_tsv_path,
            go_annotation_tsv_path=go_annotation_tsv_path,
            pathway_membership_tsv_path=pathway_membership_tsv_path,
            complex_membership_tsv_path=complex_membership_tsv_path,
            selection_policy=active_selection_policy,
            volcano_policy=volcano_policy,
        )
        biological_report = diann_workflow.biological_report
        qc_issue_count = diann_workflow.summary.flagged_run_count
        return ProteomicsRunBundle(
            engine=engine,
            normalization_method=normalization_method,
            condition_a=condition_a,
            condition_b=condition_b,
            summary=_build_summary(
                engine=engine,
                biological_report=biological_report,
                experiment_design=experiment_design,
                condition_a=condition_a,
                condition_b=condition_b,
                qc_issue_count=qc_issue_count,
            ),
            diann_workflow=diann_workflow,
            note=(
                "flagship proteomics run dispatches DIA-NN input through governed import, QC, normalization, differential analysis, enrichment, and final biology reporting"
            ),
        )
    if engine is ProteomicsRunEngine.MAXQUANT:
        if peptides_tsv_path is None or protein_groups_tsv_path is None:
            raise ValueError(
                "MaxQuant flagship runs require peptides_tsv_path and protein_groups_tsv_path"
            )
        maxquant_workflow = build_maxquant_biological_workflow_bundle(
            report_tsv_path,
            experiment_design,
            peptides_txt_path=peptides_tsv_path,
            protein_groups_txt_path=protein_groups_tsv_path,
            proteins_fasta_path=proteins_fasta_path,
            config_path=config_path,
            normalization_method=normalization_method,
            condition_a=condition_a,
            condition_b=condition_b,
            annotation_tsv_path=annotation_tsv_path,
            go_annotation_tsv_path=go_annotation_tsv_path,
            pathway_membership_tsv_path=pathway_membership_tsv_path,
            complex_membership_tsv_path=complex_membership_tsv_path,
            selection_policy=active_selection_policy,
            volcano_policy=volcano_policy,
            acceptance_policy=MaxquantProteinGroupAcceptancePolicy(),
        )
        biological_report = maxquant_workflow.biological_report
        qc_issue_count = biological_report.summary.pca_outlier_sample_count
        return ProteomicsRunBundle(
            engine=engine,
            normalization_method=normalization_method,
            condition_a=condition_a,
            condition_b=condition_b,
            summary=_build_summary(
                engine=engine,
                biological_report=biological_report,
                experiment_design=experiment_design,
                condition_a=condition_a,
                condition_b=condition_b,
                qc_issue_count=qc_issue_count,
            ),
            maxquant_workflow=maxquant_workflow,
            note=(
                "flagship proteomics run dispatches MaxQuant evidence through governed protein-group acceptance, LFQ bridging, differential analysis, enrichment, and final biology reporting"
            ),
        )
    if engine is ProteomicsRunEngine.FRAGPIPE:
        fragpipe_workflow = build_dda_biological_workflow_bundle(
            report_tsv_path,
            experiment_design,
            proteins_fasta_path=proteins_fasta_path,
            adapter_kind=SearchAdapterKind.MSFRAGGER,
            dialect_id="fragpipe-psm",
            acceptance_policy=DdaPsmAcceptancePolicy(max_q_value=psm_q_value_threshold),
            normalization_method=normalization_method,
            condition_a=condition_a,
            condition_b=condition_b,
            source_protein_tsv_path=source_protein_tsv_path,
            annotation_tsv_path=annotation_tsv_path,
            go_annotation_tsv_path=go_annotation_tsv_path,
            pathway_membership_tsv_path=pathway_membership_tsv_path,
            complex_membership_tsv_path=complex_membership_tsv_path,
            selection_policy=active_selection_policy,
            volcano_policy=volcano_policy,
        )
        biological_report = fragpipe_workflow.biological_report
        qc_issue_count = biological_report.summary.pca_outlier_sample_count
        return ProteomicsRunBundle(
            engine=engine,
            normalization_method=normalization_method,
            condition_a=condition_a,
            condition_b=condition_b,
            summary=_build_summary(
                engine=engine,
                biological_report=biological_report,
                experiment_design=experiment_design,
                condition_a=condition_a,
                condition_b=condition_b,
                qc_issue_count=qc_issue_count,
            ),
            fragpipe_workflow=fragpipe_workflow,
            note=(
                "flagship proteomics run dispatches FragPipe PSM export through governed MSFragger normalization, DDA protein inference, LFQ, differential analysis, enrichment, and final biology reporting"
            ),
        )
    raise ValueError(f"unsupported flagship proteomics run engine: {engine.value}")


def render_proteomics_run_summary_tsv(report: ProteomicsRunBundle) -> str:
    """Render one compact flagship run summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("engine", report.summary.engine.value),
        ("metadata_row_count", report.summary.metadata_row_count),
        ("condition_a", report.summary.condition_a),
        ("condition_b", report.summary.condition_b),
        ("protein_count", report.summary.protein_count),
        ("significant_protein_count", report.summary.significant_protein_count),
        ("sample_count", report.summary.sample_count),
        ("qc_issue_count", report.summary.qc_issue_count),
        ("enrichment_entry_count", report.summary.enrichment_entry_count),
        ("normalization_method", report.normalization_method.value),
        ("note", report.note),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def render_proteomics_run_qc_summary_tsv(report: ProteomicsRunBundle) -> str:
    """Render one flagship QC summary as TSV."""

    biological_report = _biological_report(report)
    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("engine", report.engine.value))
    writer.writerow(("condition_a", report.condition_a))
    writer.writerow(("condition_b", report.condition_b))
    writer.writerow(("sample_count", biological_report.summary.sample_count))
    writer.writerow(("protein_count", biological_report.summary.protein_count))
    writer.writerow(
        (
            "significant_protein_count",
            biological_report.summary.significant_protein_count,
        )
    )
    if report.diann_workflow is not None:
        writer.writerow(
            ("flagged_run_count", report.diann_workflow.summary.flagged_run_count)
        )
        writer.writerow(
            (
                "run_qc_summary",
                _single_value_field(
                    render_dia_run_qc_summary_tsv(report.diann_workflow.run_qc_report),
                    "run_count",
                ),
            )
        )
    else:
        writer.writerow(("flagged_run_count", 0))
    writer.writerow(
        (
            "pca_outlier_sample_count",
            biological_report.summary.pca_outlier_sample_count,
        )
    )
    writer.writerow(
        (
            "heatmap_entity_count",
            biological_report.summary.heatmap_entity_count,
        )
    )
    writer.writerow(
        (
            "note",
            "flagship QC preserves engine-native QC when available and otherwise surfaces governed sample exploration review",
        )
    )
    return handle.getvalue()


def render_proteomics_run_enrichment_tsv(report: ProteomicsRunBundle) -> str:
    """Render one combined enrichment table across GO, pathway, and complex review."""

    biological_report = _biological_report(report)
    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "source_kind",
            "source_name",
            "entry_id",
            "entry_name",
            "member_kind",
            "foreground_overlap_count",
            "background_member_count",
            "foreground_size",
            "background_size",
            "expected_overlap_count",
            "enrichment_ratio",
            "p_value",
            "adjusted_p_value",
        )
    )
    enrichment_rows: list[
        tuple[str, str, str, str, str, int, int, int, int, str, str, str, str]
    ] = []
    if biological_report.go_enrichment_report is not None:
        for entry in biological_report.go_enrichment_report.term_entries:
            enrichment_rows.append(
                (
                    "go",
                    "gene_ontology",
                    entry.go_term_id,
                    entry.go_term_name,
                    entry.go_aspect,
                    entry.foreground_overlap_count,
                    entry.background_term_count,
                    entry.foreground_size,
                    entry.background_size,
                    f"{entry.expected_overlap_count:g}",
                    f"{entry.enrichment_ratio:g}",
                    f"{entry.p_value:g}",
                    ""
                    if entry.adjusted_p_value is None
                    else f"{entry.adjusted_p_value:g}",
                )
            )
    if biological_report.pathway_enrichment_report is not None:
        for entry in biological_report.pathway_enrichment_report.entries:
            enrichment_rows.append(
                (
                    "pathway",
                    entry.source_name,
                    entry.pathway_id,
                    entry.pathway_name,
                    str(entry.member_kind.value),
                    entry.foreground_overlap_count,
                    entry.background_member_count,
                    entry.foreground_size,
                    entry.background_size,
                    f"{entry.expected_overlap_count:g}",
                    f"{entry.enrichment_ratio:g}",
                    f"{entry.p_value:g}",
                    ""
                    if entry.adjusted_p_value is None
                    else f"{entry.adjusted_p_value:g}",
                )
            )
    if biological_report.complex_enrichment_report is not None:
        for entry in biological_report.complex_enrichment_report.entries:
            enrichment_rows.append(
                (
                    "complex",
                    entry.source_name,
                    entry.complex_id,
                    entry.complex_name,
                    str(entry.member_kind.value),
                    entry.foreground_overlap_count,
                    entry.background_member_count,
                    entry.foreground_size,
                    entry.background_size,
                    f"{entry.expected_overlap_count:g}",
                    f"{entry.enrichment_ratio:g}",
                    f"{entry.p_value:g}",
                    ""
                    if entry.adjusted_p_value is None
                    else f"{entry.adjusted_p_value:g}",
                )
            )
    for row in sorted(enrichment_rows, key=lambda value: value[:5]):
        writer.writerow(row)
    return handle.getvalue()


def write_proteomics_run_bundle(
    report: ProteomicsRunBundle,
    output_dir: Path,
) -> ProteomicsRunExportManifest:
    """Write one flagship proteomics run bundle into a stable output directory."""

    output_dir.mkdir(parents=True, exist_ok=True)
    workflow_manifest = _write_workflow_bundle(report, output_dir)
    biological_manifest = workflow_manifest.biological_report_manifest
    summary_name = "proteomics_run_summary.tsv"
    qc_summary_name = "proteomics_qc_summary.tsv"
    normalized_matrix_name = "proteomics_normalized_matrix.tsv"
    differential_name = "proteomics_differential.tsv"
    enrichment_name = "proteomics_enrichment.tsv"
    report_name = "proteomics_report.html"
    workflow_manifest_name = "proteomics_workflow_manifest.json"
    biological_manifest_name = "biological_report_manifest.json"

    write_output_table_tsv(
        (output_dir / summary_name), render_proteomics_run_summary_tsv(report)
    )
    write_output_table_tsv(
        (output_dir / qc_summary_name), render_proteomics_run_qc_summary_tsv(report)
    )
    write_output_table_tsv(
        (output_dir / normalized_matrix_name), _render_normalized_matrix_tsv(report)
    )
    write_output_table_tsv(
        output_dir / differential_name,
        render_differential_abundance_tsv(
            _biological_report(report).differential_report
        ),
    )
    write_output_table_tsv(
        (output_dir / enrichment_name), render_proteomics_run_enrichment_tsv(report)
    )
    source_report_path = output_dir / biological_manifest.artifacts.report_html
    atomic_write_text(
        output_dir / report_name,
        source_report_path.read_text(encoding="utf-8"),
    )
    atomic_write_text(
        output_dir / workflow_manifest_name,
        workflow_manifest.to_stable_json() + "\n",
    )
    return ProteomicsRunExportManifest(
        summary=report.summary,
        artifacts=ProteomicsRunArtifactPaths(
            summary_tsv=summary_name,
            qc_summary_tsv=qc_summary_name,
            normalized_matrix_tsv=normalized_matrix_name,
            differential_tsv=differential_name,
            enrichment_tsv=enrichment_name,
            report_html=report_name,
            workflow_manifest_json=workflow_manifest_name,
            biological_manifest_json=biological_manifest_name,
        ),
        workflow_manifest=workflow_manifest,
        biological_report_manifest=biological_manifest,
        note=(
            "flagship run export preserves engine-native workflow review, standardized QC, normalized matrix, differential, enrichment, and final HTML reporting in one directory"
        ),
    )


def export_proteomics_run_bundle(
    report: ProteomicsRunBundle,
    output_dir: Path,
) -> ProteomicsRunExportManifest:
    """Compatibility wrapper for the legacy flagship run bundle export name."""

    return write_proteomics_run_bundle(report, output_dir)


def _resolve_contrast(
    experiment_design: ExperimentDesign,
    *,
    contrast: str | None,
) -> tuple[str, str]:
    from bijux_proteomics.study.contrasts import resolve_pairwise_study_contrast

    study_samples = tuple(
        entry.to_domain_record() for entry in experiment_design.entries
    )
    conditions = experiment_design.conditions
    if contrast is None:
        if len(conditions) != 2:
            raise ValueError(
                "flagship proteomics run requires --contrast unless metadata resolves exactly two conditions"
            )
        contrast = f"{conditions[0]}-{conditions[1]}"
    resolved = resolve_pairwise_study_contrast(
        contrast,
        sample_metadata=study_samples,
    )
    return resolved.left_condition, resolved.right_condition


def _build_summary(
    *,
    engine: ProteomicsRunEngine,
    biological_report: BiologicalResultReportBundle,
    experiment_design: ExperimentDesign,
    condition_a: str,
    condition_b: str,
    qc_issue_count: int,
) -> ProteomicsRunSummary:
    return ProteomicsRunSummary(
        engine=engine,
        metadata_row_count=len(experiment_design.entries),
        condition_a=condition_a,
        condition_b=condition_b,
        protein_count=biological_report.summary.protein_count,
        significant_protein_count=biological_report.summary.significant_protein_count,
        sample_count=biological_report.summary.sample_count,
        qc_issue_count=qc_issue_count,
        enrichment_entry_count=_count_enrichment_entries(biological_report),
    )


def _count_enrichment_entries(report: BiologicalResultReportBundle) -> int:
    return sum(
        (
            0
            if report.go_enrichment_report is None
            else len(report.go_enrichment_report.term_entries),
            0
            if report.pathway_enrichment_report is None
            else len(report.pathway_enrichment_report.entries),
            0
            if report.complex_enrichment_report is None
            else len(report.complex_enrichment_report.entries),
        )
    )


def _biological_report(report: ProteomicsRunBundle) -> BiologicalResultReportBundle:
    if report.diann_workflow is not None:
        return report.diann_workflow.biological_report
    if report.maxquant_workflow is not None:
        return report.maxquant_workflow.biological_report
    if report.fragpipe_workflow is not None:
        return report.fragpipe_workflow.biological_report
    raise ValueError("flagship run bundle is missing an engine workflow")


def _write_workflow_bundle(
    report: ProteomicsRunBundle,
    output_dir: Path,
) -> (
    DiannBiologicalWorkflowExportManifest
    | MaxquantBiologicalWorkflowExportManifest
    | DdaBiologicalWorkflowExportManifest
):
    if report.diann_workflow is not None:
        return write_diann_biological_workflow_bundle(report.diann_workflow, output_dir)
    if report.maxquant_workflow is not None:
        return write_maxquant_biological_workflow_bundle(
            report.maxquant_workflow,
            output_dir,
        )
    if report.fragpipe_workflow is not None:
        return write_dda_biological_workflow_bundle(
            report.fragpipe_workflow, output_dir
        )
    raise ValueError("flagship run bundle is missing an engine workflow")


def _render_normalized_matrix_tsv(report: ProteomicsRunBundle) -> str:
    if report.diann_workflow is not None:
        return render_dia_differential_matrix_tsv(
            report.diann_workflow.differential_analysis_report.normalized_table
        )
    if report.maxquant_workflow is not None:
        normalized_table = normalize_label_free_table(
            report.maxquant_workflow.lfq_table,
            method=report.normalization_method,
        )
        return render_maxquant_lfq_matrix_tsv(normalized_table)
    if report.fragpipe_workflow is not None:
        raw_table = build_label_free_quant_table_from_protein_lfq_report(
            report.fragpipe_workflow.protein_lfq_report
        )
        normalized_table = normalize_label_free_table(
            raw_table,
            method=report.normalization_method,
        )
        return render_maxquant_lfq_matrix_tsv(normalized_table)
    raise ValueError("flagship run bundle is missing an engine workflow")


def _single_value_field(tsv_text: str, field_name: str) -> str:
    reader = csv.reader(StringIO(tsv_text), delimiter="\t")
    next(reader, None)
    for row in reader:
        if len(row) >= 2 and row[0] == field_name:
            return row[1]
    return ""


__all__ = [
    "ProteomicsRunArtifactPaths",
    "ProteomicsRunBundle",
    "ProteomicsRunEngine",
    "ProteomicsRunExportManifest",
    "ProteomicsRunSummary",
    "build_proteomics_run_bundle",
    "export_proteomics_run_bundle",
    "write_proteomics_run_bundle",
    "render_proteomics_run_enrichment_tsv",
    "render_proteomics_run_qc_summary_tsv",
    "render_proteomics_run_summary_tsv",
]
