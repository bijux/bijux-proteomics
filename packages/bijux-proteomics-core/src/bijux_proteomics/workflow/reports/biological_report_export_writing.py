# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Artifact-writing ownership for biological report exports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics.workflow.reports.biological_report_activity_exports import (
    BiologicalActivityExportNames,
    write_biological_activity_exports,
)
from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.reports.biological_report_contextual_exports import (
    BiologicalContextualExportNames,
    write_biological_contextual_exports,
)
from bijux_proteomics.workflow.reports.biological_report_enrichment_exports import (
    BiologicalEnrichmentExportNames,
    write_biological_enrichment_exports,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_export_contracts import (
    BiologicalScientificExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_exports import (
    write_biological_scientific_exports,
)
from bijux_proteomics.workflow.reports.biological_report_visual_export_contracts import (
    BiologicalVisualExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_visual_exports import (
    write_biological_visual_exports,
)


@dataclass(frozen=True)
class BiologicalResultReportExportNames:
    """Artifact-name bundles written for one biological report export."""

    scientific: BiologicalScientificExportNames
    contextual: BiologicalContextualExportNames
    activity: BiologicalActivityExportNames
    enrichment: BiologicalEnrichmentExportNames
    visual: BiologicalVisualExportNames


def _write_biological_result_report_export_names(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalResultReportExportNames:
    return BiologicalResultReportExportNames(
        scientific=write_biological_scientific_exports(report, output_dir),
        contextual=write_biological_contextual_exports(report.contextual, output_dir),
        activity=write_biological_activity_exports(report.activity, output_dir),
        enrichment=write_biological_enrichment_exports(report.enrichment, output_dir),
        visual=write_biological_visual_exports(report.visual, output_dir),
    )


__all__ = [
    "BiologicalResultReportExportNames",
    "_write_biological_result_report_export_names",
]
