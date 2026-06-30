# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Foundation report assembly for biological quant-table workflows."""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from bijux_proteomics.interpretation.go_enrichment import (
    parse_go_annotation_table,
)
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
)
from bijux_proteomics.workflow.reports.biological_report_context_assembly import (
    BiologicalContextAssemblyReports,
    _build_biological_context_reports,
)
from bijux_proteomics.workflow.reports.biological_report_enrichment_assembly import (
    BiologicalEnrichmentAssemblyReports,
    _build_biological_enrichment_reports,
)
from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
    BiologicalResultSelectionPolicy,
)
from bijux_proteomics.workflow.reports.biological_report_source_data import (
    BiologicalReportSourceData,
    _build_biological_report_source_data,
)


class BiologicalQuantTableFoundationReports(NamedTuple):
    """Foundational reports prepared before evidence and regulator analysis."""

    source_data: BiologicalReportSourceData
    context_reports: BiologicalContextAssemblyReports
    enrichment_reports: BiologicalEnrichmentAssemblyReports


def _build_biological_quant_table_foundation_reports(
    *,
    normalized_table: LabelFreeQuantTable,
    differential_report: object,
    experiment_design: object,
    design_entries: tuple[object, ...],
    active_selection_policy: BiologicalResultSelectionPolicy,
    proteins_fasta_path: Path,
    variant_proteins_fasta_path: Path | None,
    variant_peptide_tsv_path: Path | None,
    annotation_tsv_path: Path | None,
    context_annotation_tsv_path: Path | None,
    protein_region_context_tsv_path: Path | None,
    go_annotation_tsv_path: Path | None,
    pathway_membership_tsv_path: Path | None,
    complex_membership_tsv_path: Path | None,
) -> BiologicalQuantTableFoundationReports:
    source_data = _build_biological_report_source_data(
        normalized_table=normalized_table,
        differential_report=differential_report,
        proteins_fasta_path=proteins_fasta_path,
        variant_proteins_fasta_path=variant_proteins_fasta_path,
        variant_peptide_tsv_path=variant_peptide_tsv_path,
        annotation_tsv_path=annotation_tsv_path,
        pathway_membership_tsv_path=pathway_membership_tsv_path,
        complex_membership_tsv_path=complex_membership_tsv_path,
        protein_region_context_tsv_path=protein_region_context_tsv_path,
    )
    context_reports = _build_biological_context_reports(
        normalized_table=normalized_table,
        experiment_design=experiment_design,
        design_entries=design_entries,
        differential_report=differential_report,
        differential_reference_entries=source_data.differential_reference_entries,
        annotation_report=source_data.annotation_report,
        pathway_records=source_data.pathway_records,
        active_selection_policy=active_selection_policy,
        context_annotation_tsv_path=context_annotation_tsv_path,
    )
    enrichment_reports = _build_biological_enrichment_reports(
        normalized_table=normalized_table,
        differential_report=differential_report,
        design_entries=design_entries,
        fasta_records=source_data.fasta_records,
        custom_annotations=source_data.custom_annotation_records,
        go_annotation_records=()
        if go_annotation_tsv_path is None
        else parse_go_annotation_table(go_annotation_tsv_path).accepted_records,
        pathway_records=source_data.pathway_records,
        complex_records=source_data.complex_records,
        active_selection_policy=active_selection_policy,
    )
    return BiologicalQuantTableFoundationReports(
        source_data=source_data,
        context_reports=context_reports,
        enrichment_reports=enrichment_reports,
    )


__all__ = [
    "BiologicalQuantTableFoundationReports",
    "_build_biological_quant_table_foundation_reports",
]
