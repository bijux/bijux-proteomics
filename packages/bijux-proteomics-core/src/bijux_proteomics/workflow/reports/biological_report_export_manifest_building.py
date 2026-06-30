# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Biological report artifact-path and manifest assembly."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_artifact_path_building import (
    _build_biological_result_report_artifact_paths,
)
from bijux_proteomics.workflow.reports.biological_report_export_manifest_metadata import (
    _build_biological_result_report_export_metadata,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportArtifactPaths,
    BiologicalResultReportBundle,
    BiologicalResultReportExportManifest,
)

def _build_biological_result_report_export_manifest(
    report: BiologicalResultReportBundle,
    artifacts: BiologicalResultReportArtifactPaths,
) -> BiologicalResultReportExportManifest:
    export_metadata = _build_biological_result_report_export_metadata(report)
    return BiologicalResultReportExportManifest(
        summary=report.summary,
        artifacts=artifacts,
        claim_validation_included=export_metadata.claim_validation_included,
        hypothesis_summary_included=export_metadata.hypothesis_summary_included,
        context_summary_included=export_metadata.context_summary_included,
        cohort_stratification_summary_included=(
            export_metadata.cohort_stratification_summary_included
        ),
        tissue_context_summary_included=(
            export_metadata.tissue_context_summary_included
        ),
        drug_target_summary_included=export_metadata.drug_target_summary_included,
        disease_phenotype_summary_included=(
            export_metadata.disease_phenotype_summary_included
        ),
        go_summary_included=export_metadata.go_summary_included,
        pathway_summary_included=export_metadata.pathway_summary_included,
        complex_summary_included=export_metadata.complex_summary_included,
        note=export_metadata.note,
    )


__all__ = [
    "_build_biological_result_report_artifact_paths",
    "_build_biological_result_report_export_manifest",
]
