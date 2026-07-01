# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Manifest and layout finalization for biological report exports."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics._atomic_files import atomic_write_text
from bijux_proteomics.workflow.exports.artifact_layout import (
    synchronize_workflow_artifact_layout,
)
from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.reports.biological_report_export_contracts import (
    BiologicalResultReportExportManifest,
)
from bijux_proteomics.workflow.reports.biological_report_export_manifest_building import (
    _build_biological_result_report_artifact_paths,
    _build_biological_result_report_export_manifest,
)
from bijux_proteomics.workflow.reports.biological_report_export_writing import (
    BiologicalResultReportExportNames,
)
from bijux_proteomics.workflow.reports.html import (
    _render_biological_result_report_html,
)


def _finalize_biological_result_report_export(
    report: BiologicalResultReportBundle,
    output_dir: Path,
    export_names: BiologicalResultReportExportNames,
) -> BiologicalResultReportExportManifest:
    artifacts = _build_biological_result_report_artifact_paths(
        export_names.scientific,
        export_names.contextual,
        export_names.activity,
        export_names.enrichment,
        export_names.visual,
    )
    atomic_write_text(
        output_dir / export_names.visual.report_html_name,
        _render_biological_result_report_html(report, artifacts),
    )
    synchronize_workflow_artifact_layout(
        output_dir,
        producer_function="export_biological_result_report_bundle",
    )
    return _build_biological_result_report_export_manifest(report, artifacts)


__all__ = ["_finalize_biological_result_report_export"]
