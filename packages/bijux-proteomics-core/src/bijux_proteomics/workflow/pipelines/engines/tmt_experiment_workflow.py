# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned TMT workflow bundles from search output to report-ready differential results."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._atomic_files import atomic_write_text
from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.io.formats import (
    ExperimentalDesignReport,
    parse_experimental_design_table,
)
from bijux_proteomics.multiplex import (
    MultiplexMetadataValidationReport,
    TmtInterferenceReport,
    TmtNormalizationMethod,
    TmtReporterChannelColumn,
    TmtReporterColumnMapping,
    TmtSearchResultSourceKind,
    build_multiplex_metadata_validation_report,
    build_tmt_interference_report,
    export_multiplex_channel_assignment_tsv,
    export_multiplex_duplicate_assignment_tsv,
    export_multiplex_metadata_summary_tsv,
    export_multiplex_missing_condition_tsv,
    export_tmt_filtered_interference_tsv,
    export_tmt_interference_channel_summary_tsv,
    export_tmt_interference_observation_tsv,
    export_tmt_interference_summary_tsv,
)
from bijux_proteomics.multiplex.reporter_ion_import import TmtReporterImportReport
from bijux_proteomics.quantification.contracts import NormalizationMethod
from bijux_proteomics.study import build_experiment_design
from bijux_proteomics.workflow.exports.artifact_layout import (
    synchronize_workflow_artifact_layout,
)
from bijux_proteomics.workflow.pipelines.comparative.label_based_differential import (
    LabelBasedDifferentialSourceKind,
)
from bijux_proteomics.workflow.pipelines.label_based_reporting import (
    LabelBasedReportBundle,
    LabelBasedReportExportManifest,
    build_tmt_label_based_report_bundle,
    write_label_based_report_bundle,
)
from bijux_proteomics.workflow.result_types import (
    build_rejected_evidence_entries_from_issue_rows,
    render_result_rejected_evidence_tsv,
)
from bijux_proteomics_foundation import JsonModel


class TmtExperimentWorkflowSummary(JsonModel):
    """Compact summary over one TMT search-result workflow bundle."""

    model_config = ConfigDict(extra="forbid")

    accepted_input_row_count: int = Field(..., ge=0)
    rejected_input_row_count: int = Field(..., ge=0)
    design_row_count: int = Field(..., ge=0)
    multiplex_group_count: int = Field(..., ge=0)
    mapped_channel_count: int = Field(..., ge=0)
    missing_source_channel_count: int = Field(..., ge=0)
    protein_row_count: int = Field(..., ge=0)
    protein_ratio_count: int = Field(..., ge=0)
    differential_result_count: int = Field(..., ge=0)
    sample_qc_entry_count: int = Field(..., ge=0)
    interference_observation_count: int = Field(..., ge=0)
    flagged_interference_count: int = Field(..., ge=0)


class TmtExperimentWorkflowBundle(JsonModel):
    """Owned TMT workflow from search-result reporter rows to report-ready outputs."""

    model_config = ConfigDict(extra="forbid")

    source_kind: TmtSearchResultSourceKind
    design_report: ExperimentalDesignReport
    metadata_validation_report: MultiplexMetadataValidationReport
    interference_report: TmtInterferenceReport
    report: LabelBasedReportBundle
    summary: TmtExperimentWorkflowSummary
    note: str = Field(..., min_length=1)


class TmtExperimentWorkflowArtifactPaths(JsonModel):
    """Relative artifact paths written into one exported TMT workflow directory."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    reporter_import_summary_tsv: str = Field(..., min_length=1)
    accepted_reporter_rows_tsv: str = Field(..., min_length=1)
    rejected_reporter_rows_tsv: str = Field(..., min_length=1)
    rejected_evidence_tsv: str = Field(..., min_length=1)
    metadata_summary_tsv: str = Field(..., min_length=1)
    channel_assignments_tsv: str = Field(..., min_length=1)
    duplicate_assignments_tsv: str = Field(..., min_length=1)
    missing_conditions_tsv: str = Field(..., min_length=1)
    interference_summary_tsv: str = Field(..., min_length=1)
    interference_observations_tsv: str = Field(..., min_length=1)
    filtered_interference_tsv: str = Field(..., min_length=1)
    interference_channel_summary_tsv: str = Field(..., min_length=1)
    label_based_report_manifest_json: str = Field(..., min_length=1)


class TmtExperimentWorkflowExportManifest(JsonModel):
    """Stable manifest over one exported TMT workflow directory."""

    model_config = ConfigDict(extra="forbid")

    source_kind: TmtSearchResultSourceKind
    summary: TmtExperimentWorkflowSummary
    artifacts: TmtExperimentWorkflowArtifactPaths
    label_based_report_manifest: LabelBasedReportExportManifest
    note: str = Field(..., min_length=1)


def build_tmt_experiment_workflow_bundle(
    result_tsv_path: Path,
    design_path: Path,
    *,
    control_channel: str,
    source_kind: TmtSearchResultSourceKind = TmtSearchResultSourceKind.MAXQUANT,
    mapping: TmtReporterColumnMapping | None = None,
    channel_columns: tuple[TmtReporterChannelColumn, ...] = (),
    channel_normalization_method: TmtNormalizationMethod = TmtNormalizationMethod.MEDIAN,
    differential_normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
) -> TmtExperimentWorkflowBundle:
    """Build one governed TMT workflow bundle from search output plus design metadata."""

    design_report = parse_experimental_design_table(design_path)
    if design_report.rejected_rows:
        raise ValueError("design table contains rejected rows")
    experiment_design = build_experiment_design(design_report.accepted_entries)
    metadata_validation_report = build_multiplex_metadata_validation_report(
        design_report
    )
    _require_workflow_ready_metadata(metadata_validation_report)
    report = build_tmt_label_based_report_bundle(
        result_tsv_path,
        experiment_design,
        control_channel=control_channel,
        source_kind=source_kind,
        mapping=mapping,
        channel_columns=channel_columns,
        channel_normalization_method=channel_normalization_method,
        differential_normalization_method=differential_normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
        batch_field=batch_field,
        covariate_fields=tuple(dict.fromkeys(covariate_fields)),
        pairing_field=pairing_field,
    )
    if report.source_kind is not LabelBasedDifferentialSourceKind.TMT:
        raise ValueError("tmt workflow requires a TMT labeled report bundle")
    if report.tmt_matrix_report is None:
        raise ValueError("tmt workflow requires reporter-matrix review in the report")
    if report.tmt_ratio_report is None:
        raise ValueError("tmt workflow requires protein-ratio review in the report")
    matrix_report = report.tmt_matrix_report
    interference_report = build_tmt_interference_report(
        matrix_report.source_report,
        design_entries=tuple(design_report.accepted_entries),
    )
    return TmtExperimentWorkflowBundle(
        source_kind=source_kind,
        design_report=design_report,
        metadata_validation_report=metadata_validation_report,
        interference_report=interference_report,
        report=report,
        summary=TmtExperimentWorkflowSummary(
            accepted_input_row_count=(
                matrix_report.source_report.summary.accepted_row_count
            ),
            rejected_input_row_count=(
                matrix_report.source_report.summary.rejected_row_count
            ),
            design_row_count=len(design_report.accepted_entries),
            multiplex_group_count=matrix_report.feature_bundle.summary.multiplex_group_count,
            mapped_channel_count=matrix_report.feature_bundle.summary.mapped_channel_count,
            missing_source_channel_count=(
                matrix_report.feature_bundle.summary.missing_channel_count
            ),
            protein_row_count=matrix_report.summary.protein_row_count,
            protein_ratio_count=report.summary.protein_ratio_count,
            differential_result_count=report.summary.differential_result_count,
            sample_qc_entry_count=report.summary.sample_qc_entry_count,
            interference_observation_count=(
                interference_report.summary.observed_channel_row_count
            ),
            flagged_interference_count=(
                interference_report.summary.threshold_exceeded_count
            ),
        ),
        note=(
            "TMT workflow parses reporter-ion search output, requires workflow-ready multiplex design metadata, preserves interference review, and routes accepted channel evidence through the owned labeled report bundle for normalization, protein ratios, differential analysis, and report export"
        ),
    )


def render_tmt_experiment_workflow_summary_tsv(
    report: TmtExperimentWorkflowBundle,
) -> str:
    """Render one compact TMT workflow summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("source_kind", report.source_kind.value),
        ("accepted_input_row_count", report.summary.accepted_input_row_count),
        ("rejected_input_row_count", report.summary.rejected_input_row_count),
        ("design_row_count", report.summary.design_row_count),
        ("multiplex_group_count", report.summary.multiplex_group_count),
        ("mapped_channel_count", report.summary.mapped_channel_count),
        ("missing_source_channel_count", report.summary.missing_source_channel_count),
        ("protein_row_count", report.summary.protein_row_count),
        ("protein_ratio_count", report.summary.protein_ratio_count),
        ("differential_result_count", report.summary.differential_result_count),
        ("sample_qc_entry_count", report.summary.sample_qc_entry_count),
        (
            "interference_observation_count",
            report.summary.interference_observation_count,
        ),
        ("flagged_interference_count", report.summary.flagged_interference_count),
        ("note", report.note),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def render_tmt_workflow_import_summary_tsv(report: TmtExperimentWorkflowBundle) -> str:
    """Render the governed reporter-ion import summary used by the TMT workflow."""

    source_report = _source_report(report)
    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("source_kind", source_report.source_kind.value),
        ("total_rows", source_report.summary.total_rows),
        ("accepted_row_count", source_report.summary.accepted_row_count),
        ("rejected_row_count", source_report.summary.rejected_row_count),
        ("multiplex_group_count", source_report.summary.multiplex_group_count),
        ("reporter_channel_count", source_report.summary.reporter_channel_count),
        ("note", source_report.note),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def render_tmt_workflow_accepted_reporter_rows_tsv(
    report: TmtExperimentWorkflowBundle,
) -> str:
    """Render accepted reporter-ion rows carried into the TMT workflow."""

    source_report = _source_report(report)
    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "source_row_id",
            "multiplex_group",
            "modified_peptide",
            "canonical_peptide",
            "protein_refs",
            "isolation_interference_fraction",
            "channel_intensities",
        )
    )
    for row in source_report.accepted_rows:
        writer.writerow(
            (
                row.source_row_id,
                row.multiplex_group,
                row.modified_peptide,
                row.canonical_peptide,
                ";".join(row.protein_refs),
                (
                    ""
                    if row.isolation_interference_fraction is None
                    else f"{row.isolation_interference_fraction:g}"
                ),
                ";".join(
                    f"{entry.multiplex_channel}="
                    f"{'' if entry.intensity is None else f'{entry.intensity:g}'}"
                    for entry in row.channel_intensities
                ),
            )
        )
    return handle.getvalue()


def render_tmt_workflow_rejected_reporter_rows_tsv(
    report: TmtExperimentWorkflowBundle,
) -> str:
    """Render rejected reporter-ion rows as TSV."""

    source_report = _source_report(report)
    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("row_number", "issue_codes", "issue_messages", "raw_fields"))
    for row in source_report.rejected_rows:
        writer.writerow(
            (
                row.row_number,
                ";".join(issue.code for issue in row.issues),
                ";".join(issue.message for issue in row.issues),
                ";".join(
                    f"{key}={value}"
                    for key, value in sorted(
                        row.raw_fields.items(), key=lambda item: item[0]
                    )
                ),
            )
        )
    return handle.getvalue()


def write_tmt_experiment_workflow_bundle(
    report: TmtExperimentWorkflowBundle,
    output_dir: Path,
) -> TmtExperimentWorkflowExportManifest:
    """Export one TMT workflow bundle into a stable directory."""

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_name = "tmt_workflow_summary.tsv"
    import_summary_name = "tmt_reporter_import_summary.tsv"
    accepted_rows_name = "tmt_reporter_rows.tsv"
    rejected_rows_name = "tmt_reporter_rejected_rows.tsv"
    rejected_evidence_name = "rejected_evidence.tsv"
    metadata_summary_name = "tmt_metadata_summary.tsv"
    channel_assignments_name = "tmt_channel_assignments.tsv"
    duplicate_assignments_name = "tmt_duplicate_assignments.tsv"
    missing_conditions_name = "tmt_missing_conditions.tsv"
    interference_summary_name = "tmt_interference_summary.tsv"
    interference_observations_name = "tmt_interference_observations.tsv"
    filtered_interference_name = "tmt_filtered_interference.tsv"
    interference_channel_summary_name = "tmt_interference_channel_summary.tsv"
    report_manifest_name = "label_based_report_manifest.json"
    rejected_evidence_entries = build_rejected_evidence_entries_from_issue_rows(
        _source_report(report).rejected_rows,
        source_surface="tmt_import",
        related_artifact=rejected_evidence_name,
        entity_prefix="reporter_row",
        entity_type="reporter_row",
    )

    write_output_table_tsv(
        (output_dir / summary_name), render_tmt_experiment_workflow_summary_tsv(report)
    )
    write_output_table_tsv(
        (output_dir / import_summary_name),
        render_tmt_workflow_import_summary_tsv(report),
    )
    write_output_table_tsv(
        (output_dir / accepted_rows_name),
        render_tmt_workflow_accepted_reporter_rows_tsv(report),
    )
    write_output_table_tsv(
        (output_dir / rejected_rows_name),
        render_tmt_workflow_rejected_reporter_rows_tsv(report),
    )
    write_output_table_tsv(
        (output_dir / rejected_evidence_name),
        render_result_rejected_evidence_tsv(rejected_evidence_entries),
    )
    export_multiplex_metadata_summary_tsv(
        report.metadata_validation_report,
        output_dir / metadata_summary_name,
    )
    export_multiplex_channel_assignment_tsv(
        report.metadata_validation_report,
        output_dir / channel_assignments_name,
    )
    export_multiplex_duplicate_assignment_tsv(
        report.metadata_validation_report,
        output_dir / duplicate_assignments_name,
    )
    export_multiplex_missing_condition_tsv(
        report.metadata_validation_report,
        output_dir / missing_conditions_name,
    )
    export_tmt_interference_summary_tsv(
        report.interference_report,
        output_dir / interference_summary_name,
    )
    export_tmt_interference_observation_tsv(
        report.interference_report,
        output_dir / interference_observations_name,
    )
    export_tmt_filtered_interference_tsv(
        report.interference_report,
        output_dir / filtered_interference_name,
    )
    export_tmt_interference_channel_summary_tsv(
        report.interference_report,
        output_dir / interference_channel_summary_name,
    )
    label_based_report_manifest = write_label_based_report_bundle(
        report.report,
        output_dir,
    )
    atomic_write_text(
        output_dir / report_manifest_name,
        label_based_report_manifest.to_stable_json() + "\n",
    )
    synchronize_workflow_artifact_layout(
        output_dir,
        producer_function="write_tmt_experiment_workflow_bundle",
    )
    return TmtExperimentWorkflowExportManifest(
        source_kind=report.source_kind,
        summary=report.summary,
        artifacts=TmtExperimentWorkflowArtifactPaths(
            summary_tsv=summary_name,
            reporter_import_summary_tsv=import_summary_name,
            accepted_reporter_rows_tsv=accepted_rows_name,
            rejected_reporter_rows_tsv=rejected_rows_name,
            rejected_evidence_tsv=rejected_evidence_name,
            metadata_summary_tsv=metadata_summary_name,
            channel_assignments_tsv=channel_assignments_name,
            duplicate_assignments_tsv=duplicate_assignments_name,
            missing_conditions_tsv=missing_conditions_name,
            interference_summary_tsv=interference_summary_name,
            interference_observations_tsv=interference_observations_name,
            filtered_interference_tsv=filtered_interference_name,
            interference_channel_summary_tsv=interference_channel_summary_name,
            label_based_report_manifest_json=report_manifest_name,
        ),
        label_based_report_manifest=label_based_report_manifest,
        note=(
            "TMT workflow export preserves reporter-ion import review, multiplex metadata review, interference review, and the downstream labeled report bundle in one durable directory"
        ),
    )


def export_tmt_experiment_workflow_bundle(
    report: TmtExperimentWorkflowBundle,
    output_dir: Path,
) -> TmtExperimentWorkflowExportManifest:
    """Compatibility wrapper for the legacy TMT workflow bundle export name."""

    return write_tmt_experiment_workflow_bundle(report, output_dir)


def _source_report(report: TmtExperimentWorkflowBundle) -> TmtReporterImportReport:
    matrix_report = report.report.tmt_matrix_report
    if matrix_report is None:
        raise ValueError("tmt workflow requires reporter-matrix review in the report")
    return matrix_report.source_report


def _require_workflow_ready_metadata(
    report: MultiplexMetadataValidationReport,
) -> None:
    if report.summary.missing_channel_assignment_count > 0:
        raise ValueError(
            "tmt workflow requires complete multiplex channel coverage in the design table"
        )
    if report.summary.duplicate_assignment_count > 0:
        raise ValueError(
            "tmt workflow requires unique multiplex channel and sample assignments in the design table"
        )
    if report.summary.missing_condition_count > 0:
        raise ValueError(
            "tmt workflow requires explicit conditions for multiplex design entries"
        )
