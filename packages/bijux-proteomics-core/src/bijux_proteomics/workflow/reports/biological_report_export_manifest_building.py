# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Biological report artifact-path and manifest assembly."""

from __future__ import annotations

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
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportArtifactPaths,
    BiologicalResultReportBundle,
    BiologicalResultReportExportManifest,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_artifact_paths import (
    _build_biological_scientific_artifact_path_fields,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_exports import (
    BiologicalScientificExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_visual_enrichment_artifact_paths import (
    _build_biological_enrichment_artifact_path_fields,
    _build_biological_visual_artifact_path_fields,
)
from bijux_proteomics.workflow.reports.biological_report_visual_exports import (
    BiologicalVisualExportNames,
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


def _build_biological_result_report_export_manifest(
    report: BiologicalResultReportBundle,
    artifacts: BiologicalResultReportArtifactPaths,
) -> BiologicalResultReportExportManifest:
    return BiologicalResultReportExportManifest(
        summary=report.summary,
        artifacts=artifacts,
        claim_validation_included=report.claim_validation_report is not None,
        hypothesis_summary_included=report.biological_hypothesis_report is not None,
        context_summary_included=report.context_mapping_report is not None,
        cohort_stratification_summary_included=(
            report.cohort_stratification_report is not None
        ),
        tissue_context_summary_included=report.tissue_cell_type_context_report
        is not None,
        drug_target_summary_included=report.drug_target_report is not None,
        disease_phenotype_summary_included=report.disease_phenotype_report is not None,
        go_summary_included=report.go_enrichment_report is not None,
        pathway_summary_included=report.pathway_enrichment_report is not None,
        complex_summary_included=report.complex_enrichment_report is not None,
        note=(
            "biological report export writes stable differential, explicit "
            "foreground/background enrichment inputs, protein-card, "
            "protein-mechanism-card, annotation, optional biological hypotheses, "
            "optional biological context, optional cohort stratification, "
            "optional tissue and cell-type context, enrichment, volcano, heatmap, "
            "and sample exploration artifacts into one durable output directory"
        ),
    )


__all__ = [
    "_build_biological_result_report_artifact_paths",
    "_build_biological_result_report_export_manifest",
]
