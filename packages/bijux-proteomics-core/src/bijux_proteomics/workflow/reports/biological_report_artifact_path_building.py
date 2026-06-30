# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Artifact-path assembly for biological report exports."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_artifact_path_contracts import (
    BiologicalResultReportArtifactPaths,
)
from bijux_proteomics.workflow.reports.biological_report_activity_artifact_paths import (
    _build_biological_activity_artifact_path_fields,
)
from bijux_proteomics.workflow.reports.biological_report_activity_exports import (
    BiologicalActivityExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_contextual_artifact_paths import (
    _build_biological_contextual_artifact_path_fields,
)
from bijux_proteomics.workflow.reports.biological_report_contextual_exports import (
    BiologicalContextualExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_enrichment_exports import (
    BiologicalEnrichmentExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_artifact_paths import (
    _build_biological_scientific_artifact_path_fields,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_export_contracts import (
    BiologicalScientificExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_visual_export_contracts import (
    BiologicalVisualExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_visual_enrichment_artifact_paths import (
    _build_biological_enrichment_artifact_path_fields,
    _build_biological_visual_artifact_path_fields,
)


def _build_biological_result_report_artifact_paths(
    scientific_export_names: BiologicalScientificExportNames,
    contextual_export_names: BiologicalContextualExportNames,
    activity_export_names: BiologicalActivityExportNames,
    enrichment_export_names: BiologicalEnrichmentExportNames,
    visual_export_names: BiologicalVisualExportNames,
) -> BiologicalResultReportArtifactPaths:
    return BiologicalResultReportArtifactPaths(
        **_build_biological_scientific_artifact_path_fields(scientific_export_names),
        **_build_biological_contextual_artifact_path_fields(contextual_export_names),
        **_build_biological_activity_artifact_path_fields(activity_export_names),
        **_build_biological_visual_artifact_path_fields(visual_export_names),
        **_build_biological_enrichment_artifact_path_fields(enrichment_export_names),
    )


__all__ = ["_build_biological_result_report_artifact_paths"]
