# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Coverage metadata for biological report export manifests."""

from __future__ import annotations

from dataclasses import dataclass

from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


@dataclass(frozen=True)
class BiologicalResultReportExportMetadata:
    """Coverage flags and note text for one biological report export."""

    claim_validation_included: bool
    hypothesis_summary_included: bool
    context_summary_included: bool
    cohort_stratification_summary_included: bool
    tissue_context_summary_included: bool
    drug_target_summary_included: bool
    disease_phenotype_summary_included: bool
    go_summary_included: bool
    pathway_summary_included: bool
    complex_summary_included: bool
    note: str


def _build_biological_result_report_export_metadata(
    report: BiologicalResultReportBundle,
) -> BiologicalResultReportExportMetadata:
    return BiologicalResultReportExportMetadata(
        claim_validation_included=report.claim_validation_report is not None,
        hypothesis_summary_included=report.biological_hypothesis_report is not None,
        context_summary_included=report.context_mapping_report is not None,
        cohort_stratification_summary_included=(
            report.cohort_stratification_report is not None
        ),
        tissue_context_summary_included=(
            report.tissue_cell_type_context_report is not None
        ),
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
    "BiologicalResultReportExportMetadata",
    "_build_biological_result_report_export_metadata",
]
