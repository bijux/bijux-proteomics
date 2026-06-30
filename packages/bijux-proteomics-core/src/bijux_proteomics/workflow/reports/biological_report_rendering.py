# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Biological report artifact coordination and compatibility exports."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics._atomic_files import atomic_write_text
from bijux_proteomics.workflow.exports.artifact_layout import (
    synchronize_workflow_artifact_layout,
)
from bijux_proteomics.workflow.reports.biological_report_activity_exports import (
    write_biological_activity_exports,
)
from bijux_proteomics.workflow.reports.biological_report_contextual_exports import (
    write_biological_contextual_exports,
)
from bijux_proteomics.workflow.reports.biological_report_enrichment_exports import (
    write_biological_enrichment_exports,
)
from bijux_proteomics.workflow.reports.biological_report_export_manifest_building import (
    _build_biological_result_report_artifact_paths,
    _build_biological_result_report_export_manifest,
)
from bijux_proteomics.workflow.reports.biological_report_html import (
    _render_biological_result_report_html,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
    BiologicalResultReportExportManifest,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_exports import (
    render_biological_report_section_confidence_tsv,
    render_biological_result_report_summary_tsv,
    write_biological_scientific_exports,
)
from bijux_proteomics.workflow.reports.biological_report_visual_exports import (
    write_biological_visual_exports,
)


def write_biological_result_report_bundle(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalResultReportExportManifest:
    """Write one biological result bundle into a stable output directory."""

    output_dir.mkdir(parents=True, exist_ok=True)
    scientific_export_names = write_biological_scientific_exports(report, output_dir)
    contextual_export_names = write_biological_contextual_exports(report, output_dir)
    activity_export_names = write_biological_activity_exports(report, output_dir)
    enrichment_export_names = write_biological_enrichment_exports(report, output_dir)
    visual_export_names = write_biological_visual_exports(report, output_dir)

    artifacts = _build_biological_result_report_artifact_paths(
        scientific_export_names,
        contextual_export_names,
        activity_export_names,
        enrichment_export_names,
        visual_export_names,
    )
    atomic_write_text(
        output_dir / visual_export_names.report_html_name,
        _render_biological_result_report_html(report, artifacts),
    )
    synchronize_workflow_artifact_layout(
        output_dir,
        producer_function="export_biological_result_report_bundle",
    )
    return _build_biological_result_report_export_manifest(report, artifacts)


def export_biological_result_report_bundle(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalResultReportExportManifest:
    """Compatibility wrapper for the legacy biological report bundle exporter."""

    return write_biological_result_report_bundle(report, output_dir)


__all__ = [
    "export_biological_result_report_bundle",
    "write_biological_result_report_bundle",
    "render_biological_report_section_confidence_tsv",
    "render_biological_result_report_summary_tsv",
]
