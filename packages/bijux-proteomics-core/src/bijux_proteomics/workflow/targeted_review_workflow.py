# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Workflow-owned targeted review exports over matrix and assay-QC surfaces."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.targeted import (
    TargetedAssayQcReport,
    TargetedMatrixReport,
    TargetedResultImportReport,
    TargetedResultSourceKind,
    render_targeted_assay_qc_coelution_tsv,
    render_targeted_assay_qc_fragment_ratio_tsv,
    render_targeted_assay_qc_replicate_cv_tsv,
    render_targeted_assay_qc_retention_tsv,
    render_targeted_assay_qc_summary_tsv,
    render_targeted_assay_qc_target_tsv,
    render_targeted_assay_qc_transition_coelution_tsv,
    render_targeted_assay_qc_transition_qc_tsv,
    render_targeted_assay_qc_transition_tsv,
    render_targeted_assay_qc_unreliable_tsv,
    render_targeted_matrix_excluded_transition_tsv,
    render_targeted_matrix_flagged_tsv,
    render_targeted_matrix_missingness_tsv,
    render_targeted_matrix_retained_transition_tsv,
    render_targeted_matrix_sample_tsv,
    render_targeted_matrix_summary_tsv,
    render_targeted_matrix_target_tsv,
    render_targeted_result_observation_tsv,
)
from bijux_proteomics.workflow.exports.artifact_layout import synchronize_workflow_artifact_layout
from bijux_proteomics_foundation import JsonModel


class TargetedMatrixWorkflowArtifactPaths(JsonModel):
    """Relative artifact paths written into one exported targeted matrix directory."""

    model_config = ConfigDict(extra="forbid")

    import_summary_tsv: str = Field(..., min_length=1)
    observations_tsv: str = Field(..., min_length=1)
    matrix_summary_tsv: str = Field(..., min_length=1)
    matrix_targets_tsv: str = Field(..., min_length=1)
    matrix_samples_tsv: str = Field(..., min_length=1)
    matrix_flagged_targets_tsv: str = Field(..., min_length=1)
    matrix_retained_transitions_tsv: str = Field(..., min_length=1)
    matrix_excluded_transitions_tsv: str = Field(..., min_length=1)
    matrix_missingness_tsv: str = Field(..., min_length=1)


class TargetedMatrixWorkflowExportManifest(JsonModel):
    """Stable manifest over one exported targeted matrix workflow directory."""

    model_config = ConfigDict(extra="forbid")

    source_kind: TargetedResultSourceKind
    import_summary: dict[str, int]
    matrix_summary: dict[str, int]
    artifacts: TargetedMatrixWorkflowArtifactPaths
    note: str = Field(..., min_length=1)


class TargetedAssayQcWorkflowArtifactPaths(JsonModel):
    """Relative artifact paths written into one exported targeted assay-QC directory."""

    model_config = ConfigDict(extra="forbid")

    import_summary_tsv: str = Field(..., min_length=1)
    observations_tsv: str = Field(..., min_length=1)
    matrix_summary_tsv: str = Field(..., min_length=1)
    matrix_targets_tsv: str = Field(..., min_length=1)
    matrix_samples_tsv: str = Field(..., min_length=1)
    matrix_flagged_targets_tsv: str = Field(..., min_length=1)
    matrix_retained_transitions_tsv: str = Field(..., min_length=1)
    matrix_excluded_transitions_tsv: str = Field(..., min_length=1)
    matrix_missingness_tsv: str = Field(..., min_length=1)
    assay_qc_summary_tsv: str = Field(..., min_length=1)
    assay_qc_targets_tsv: str = Field(..., min_length=1)
    assay_qc_transitions_tsv: str = Field(..., min_length=1)
    assay_qc_coelution_tsv: str = Field(..., min_length=1)
    assay_qc_transition_coelution_tsv: str = Field(..., min_length=1)
    assay_qc_transition_qc_tsv: str = Field(..., min_length=1)
    assay_qc_fragment_ratios_tsv: str = Field(..., min_length=1)
    assay_qc_retention_tsv: str = Field(..., min_length=1)
    assay_qc_replicate_cv_tsv: str = Field(..., min_length=1)
    assay_qc_unreliable_targets_tsv: str = Field(..., min_length=1)


class TargetedAssayQcWorkflowExportManifest(JsonModel):
    """Stable manifest over one exported targeted assay-QC workflow directory."""

    model_config = ConfigDict(extra="forbid")

    source_kind: TargetedResultSourceKind
    import_summary: dict[str, int]
    matrix_summary: dict[str, int]
    assay_qc_summary: dict[str, int]
    artifacts: TargetedAssayQcWorkflowArtifactPaths
    note: str = Field(..., min_length=1)


def export_targeted_matrix_workflow_artifacts(
    import_report: TargetedResultImportReport,
    matrix_report: TargetedMatrixReport,
    output_dir: Path,
) -> TargetedMatrixWorkflowExportManifest:
    """Export one targeted matrix workflow directory from governed owners."""

    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = TargetedMatrixWorkflowArtifactPaths(
        import_summary_tsv="targeted_import_summary.tsv",
        observations_tsv="targeted_import_observations.tsv",
        matrix_summary_tsv="targeted_matrix_summary.tsv",
        matrix_targets_tsv="targeted_matrix_targets.tsv",
        matrix_samples_tsv="targeted_matrix_samples.tsv",
        matrix_flagged_targets_tsv="targeted_matrix_flagged_targets.tsv",
        matrix_retained_transitions_tsv="targeted_matrix_retained_transitions.tsv",
        matrix_excluded_transitions_tsv="targeted_matrix_excluded_transitions.tsv",
        matrix_missingness_tsv="targeted_matrix_missingness.tsv",
    )
    _write_text(
        output_dir / artifacts.import_summary_tsv,
        _render_import_summary_tsv(import_report),
    )
    _write_text(
        output_dir / artifacts.observations_tsv,
        render_targeted_result_observation_tsv(import_report),
    )
    _write_text(
        output_dir / artifacts.matrix_summary_tsv,
        render_targeted_matrix_summary_tsv(matrix_report),
    )
    _write_text(
        output_dir / artifacts.matrix_targets_tsv,
        render_targeted_matrix_target_tsv(matrix_report),
    )
    _write_text(
        output_dir / artifacts.matrix_samples_tsv,
        render_targeted_matrix_sample_tsv(matrix_report),
    )
    _write_text(
        output_dir / artifacts.matrix_flagged_targets_tsv,
        render_targeted_matrix_flagged_tsv(matrix_report),
    )
    _write_text(
        output_dir / artifacts.matrix_retained_transitions_tsv,
        render_targeted_matrix_retained_transition_tsv(matrix_report),
    )
    _write_text(
        output_dir / artifacts.matrix_excluded_transitions_tsv,
        render_targeted_matrix_excluded_transition_tsv(matrix_report),
    )
    _write_text(
        output_dir / artifacts.matrix_missingness_tsv,
        render_targeted_matrix_missingness_tsv(matrix_report),
    )
    synchronize_workflow_artifact_layout(
        output_dir,
        producer_function="export_targeted_matrix_workflow_artifacts",
    )
    return TargetedMatrixWorkflowExportManifest(
        source_kind=import_report.source_kind,
        import_summary=_int_summary(import_report.summary.to_dict()),
        matrix_summary=_int_summary(matrix_report.summary.to_dict()),
        artifacts=artifacts,
        note=(
            "targeted matrix workflow export keeps import observations and "
            "target-matrix review ledgers together for one governed targeted run"
        ),
    )


def export_targeted_assay_qc_workflow_artifacts(
    import_report: TargetedResultImportReport,
    matrix_report: TargetedMatrixReport,
    assay_qc_report: TargetedAssayQcReport,
    output_dir: Path,
) -> TargetedAssayQcWorkflowExportManifest:
    """Export one targeted assay-QC workflow directory from governed owners."""

    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = TargetedAssayQcWorkflowArtifactPaths(
        import_summary_tsv="targeted_import_summary.tsv",
        observations_tsv="targeted_import_observations.tsv",
        matrix_summary_tsv="targeted_matrix_summary.tsv",
        matrix_targets_tsv="targeted_matrix_targets.tsv",
        matrix_samples_tsv="targeted_matrix_samples.tsv",
        matrix_flagged_targets_tsv="targeted_matrix_flagged_targets.tsv",
        matrix_retained_transitions_tsv="targeted_matrix_retained_transitions.tsv",
        matrix_excluded_transitions_tsv="targeted_matrix_excluded_transitions.tsv",
        matrix_missingness_tsv="targeted_matrix_missingness.tsv",
        assay_qc_summary_tsv="targeted_assay_qc_summary.tsv",
        assay_qc_targets_tsv="targeted_assay_qc_targets.tsv",
        assay_qc_transitions_tsv="targeted_assay_qc_transitions.tsv",
        assay_qc_coelution_tsv="targeted_assay_qc_coelution.tsv",
        assay_qc_transition_coelution_tsv="targeted_assay_qc_transition_coelution.tsv",
        assay_qc_transition_qc_tsv="targeted_assay_qc_transition_qc.tsv",
        assay_qc_fragment_ratios_tsv="targeted_assay_qc_fragment_ratios.tsv",
        assay_qc_retention_tsv="targeted_assay_qc_retention.tsv",
        assay_qc_replicate_cv_tsv="targeted_assay_qc_replicate_cv.tsv",
        assay_qc_unreliable_targets_tsv="targeted_assay_qc_unreliable_targets.tsv",
    )
    _write_text(
        output_dir / artifacts.import_summary_tsv,
        _render_import_summary_tsv(import_report),
    )
    _write_text(
        output_dir / artifacts.observations_tsv,
        render_targeted_result_observation_tsv(import_report),
    )
    _write_text(
        output_dir / artifacts.matrix_summary_tsv,
        render_targeted_matrix_summary_tsv(matrix_report),
    )
    _write_text(
        output_dir / artifacts.matrix_targets_tsv,
        render_targeted_matrix_target_tsv(matrix_report),
    )
    _write_text(
        output_dir / artifacts.matrix_samples_tsv,
        render_targeted_matrix_sample_tsv(matrix_report),
    )
    _write_text(
        output_dir / artifacts.matrix_flagged_targets_tsv,
        render_targeted_matrix_flagged_tsv(matrix_report),
    )
    _write_text(
        output_dir / artifacts.matrix_retained_transitions_tsv,
        render_targeted_matrix_retained_transition_tsv(matrix_report),
    )
    _write_text(
        output_dir / artifacts.matrix_excluded_transitions_tsv,
        render_targeted_matrix_excluded_transition_tsv(matrix_report),
    )
    _write_text(
        output_dir / artifacts.matrix_missingness_tsv,
        render_targeted_matrix_missingness_tsv(matrix_report),
    )
    _write_text(
        output_dir / artifacts.assay_qc_summary_tsv,
        render_targeted_assay_qc_summary_tsv(assay_qc_report),
    )
    _write_text(
        output_dir / artifacts.assay_qc_targets_tsv,
        render_targeted_assay_qc_target_tsv(assay_qc_report),
    )
    _write_text(
        output_dir / artifacts.assay_qc_transitions_tsv,
        render_targeted_assay_qc_transition_tsv(assay_qc_report),
    )
    _write_text(
        output_dir / artifacts.assay_qc_coelution_tsv,
        render_targeted_assay_qc_coelution_tsv(assay_qc_report),
    )
    _write_text(
        output_dir / artifacts.assay_qc_transition_coelution_tsv,
        render_targeted_assay_qc_transition_coelution_tsv(assay_qc_report),
    )
    _write_text(
        output_dir / artifacts.assay_qc_transition_qc_tsv,
        render_targeted_assay_qc_transition_qc_tsv(assay_qc_report),
    )
    _write_text(
        output_dir / artifacts.assay_qc_fragment_ratios_tsv,
        render_targeted_assay_qc_fragment_ratio_tsv(assay_qc_report),
    )
    _write_text(
        output_dir / artifacts.assay_qc_retention_tsv,
        render_targeted_assay_qc_retention_tsv(assay_qc_report),
    )
    _write_text(
        output_dir / artifacts.assay_qc_replicate_cv_tsv,
        render_targeted_assay_qc_replicate_cv_tsv(assay_qc_report),
    )
    _write_text(
        output_dir / artifacts.assay_qc_unreliable_targets_tsv,
        render_targeted_assay_qc_unreliable_tsv(assay_qc_report),
    )
    synchronize_workflow_artifact_layout(
        output_dir,
        producer_function="export_targeted_assay_qc_workflow_artifacts",
    )
    return TargetedAssayQcWorkflowExportManifest(
        source_kind=import_report.source_kind,
        import_summary=_int_summary(import_report.summary.to_dict()),
        matrix_summary=_int_summary(matrix_report.summary.to_dict()),
        assay_qc_summary=_int_summary(assay_qc_report.summary.to_dict()),
        artifacts=artifacts,
        note=(
            "targeted assay-qc workflow export keeps import, matrix, coelution, "
            "fragment-ratio, retention, replicate-cv, and unreliable-target ledgers "
            "together for one governed targeted run"
        ),
    )


def _render_import_summary_tsv(report: TargetedResultImportReport) -> str:
    row = {"source_kind": report.source_kind.value, "source_name": report.source_name}
    row.update(report.summary.to_dict())
    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=list(row.keys()), delimiter="\t")
    writer.writeheader()
    writer.writerow(row)
    return handle.getvalue()


def _int_summary(summary: dict[str, object]) -> dict[str, int]:
    return {
        key: value
        for key, value in summary.items()
        if isinstance(value, int) and not isinstance(value, bool)
    }


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


__all__ = [
    "TargetedAssayQcWorkflowArtifactPaths",
    "TargetedAssayQcWorkflowExportManifest",
    "TargetedMatrixWorkflowArtifactPaths",
    "TargetedMatrixWorkflowExportManifest",
    "export_targeted_assay_qc_workflow_artifacts",
    "export_targeted_matrix_workflow_artifacts",
]
