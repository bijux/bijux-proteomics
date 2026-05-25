# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility facade for split biological report workflow ownership."""

from __future__ import annotations

from bijux_proteomics.review import VolcanoReviewPolicy
from bijux_proteomics.workflow.biological_report_assembly import (
    build_biological_result_report_bundle,
    build_biological_result_report_bundle_from_quant_table,
)
from bijux_proteomics.workflow.biological_report_models import (
    BiologicalReportSectionConfidenceEntry,
    BiologicalReportSectionConfidenceLabel,
    BiologicalReportSectionKey,
    BiologicalResultReportArtifactPaths,
    BiologicalResultReportBundle,
    BiologicalResultReportExportManifest,
    BiologicalResultReportSummary,
    BiologicalResultSelectionPolicy,
)
from bijux_proteomics.workflow.biological_report_rendering import (
    export_biological_result_report_bundle,
    render_biological_report_section_confidence_tsv,
    render_biological_result_report_summary_tsv,
)

__all__ = [
    "BiologicalReportSectionConfidenceEntry",
    "BiologicalReportSectionConfidenceLabel",
    "BiologicalReportSectionKey",
    "BiologicalResultReportArtifactPaths",
    "BiologicalResultReportBundle",
    "BiologicalResultReportExportManifest",
    "BiologicalResultReportSummary",
    "BiologicalResultSelectionPolicy",
    "VolcanoReviewPolicy",
    "build_biological_result_report_bundle",
    "build_biological_result_report_bundle_from_quant_table",
    "export_biological_result_report_bundle",
    "render_biological_report_section_confidence_tsv",
    "render_biological_result_report_summary_tsv",
]
