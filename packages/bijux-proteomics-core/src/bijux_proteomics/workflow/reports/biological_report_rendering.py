# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Biological report artifact coordination and compatibility exports."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow.reports.biological_report_export_finalization import (
    _finalize_biological_result_report_export,
)
from bijux_proteomics.workflow.reports.biological_report_export_writing import (
    _write_biological_result_report_export_names,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
    BiologicalResultReportExportManifest,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_exports import (
    render_biological_report_section_confidence_tsv,
    render_biological_result_report_summary_tsv,
)


def write_biological_result_report_bundle(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalResultReportExportManifest:
    """Write one biological result bundle into a stable output directory."""

    output_dir.mkdir(parents=True, exist_ok=True)
    export_names = _write_biological_result_report_export_names(report, output_dir)
    return _finalize_biological_result_report_export(
        report,
        output_dir,
        export_names,
    )


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
