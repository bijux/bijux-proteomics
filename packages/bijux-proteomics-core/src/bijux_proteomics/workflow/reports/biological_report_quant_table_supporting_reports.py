# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Supporting report assembly for biological quant-table workflows."""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from bijux_proteomics.interpretation.go_enrichment import (
    parse_go_annotation_table,
)
from bijux_proteomics.ptm import PtmEvidenceCardReport
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
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultSelectionPolicy,
)
from bijux_proteomics.workflow.reports.biological_report_protein_evidence import (
    BiologicalProteinEvidenceReports,
    _build_biological_protein_evidence_reports,
)
from bijux_proteomics.workflow.reports.biological_report_regulator_analysis import (
    BiologicalRegulatorAnalysisReports,
    _build_biological_regulator_analysis_reports,
)
from bijux_proteomics.workflow.reports.biological_report_source_data import (
    BiologicalReportSourceData,
    _build_biological_report_source_data,
)


class BiologicalQuantTableSupportingReports(NamedTuple):
    """Supporting reports required before experiment review and claim assembly."""

    source_data: BiologicalReportSourceData
    context_reports: BiologicalContextAssemblyReports
    enrichment_reports: BiologicalEnrichmentAssemblyReports
    regulator_reports: BiologicalRegulatorAnalysisReports
    protein_evidence_reports: BiologicalProteinEvidenceReports


def _build_biological_quant_table_supporting_reports(
    *,
    normalized_table: LabelFreeQuantTable,
    differential_report: object,
    experiment_design: object,
    design_entries: tuple[object, ...],
    active_selection_policy: BiologicalResultSelectionPolicy,
    proteins_fasta_path: Path,
    variant_proteins_fasta_path: Path | None,
    variant_peptide_tsv_path: Path | None,
    protocol_context_tsv_path: Path | None,
    annotation_tsv_path: Path | None,
    context_annotation_tsv_path: Path | None,
    protein_region_context_tsv_path: Path | None,
    go_annotation_tsv_path: Path | None,
    pathway_membership_tsv_path: Path | None,
    complex_membership_tsv_path: Path | None,
    regulator_evidence_tsv_path: Path | None,
    regulator_site_signal_tsv_path: Path | None,
    ptm_evidence_card_report: PtmEvidenceCardReport | None,
    lab_run_qc_feedback_report: object | None,
) -> BiologicalQuantTableSupportingReports:
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
    regulator_reports = _build_biological_regulator_analysis_reports(
        regulator_evidence_tsv_path=regulator_evidence_tsv_path,
        regulator_site_signal_tsv_path=regulator_site_signal_tsv_path,
        ptm_evidence_card_report=ptm_evidence_card_report,
        differential_report=differential_report,
        protein_refs_by_entity=normalized_table.entity_protein_refs,
        annotation_report=source_data.annotation_report,
        pathway_activity_report=enrichment_reports.pathway_activity_report,
    )
    protein_evidence_reports = _build_biological_protein_evidence_reports(
        normalized_table=normalized_table,
        differential_report=differential_report,
        design_entries=design_entries,
        selection_policy=active_selection_policy,
        annotation_report=source_data.annotation_report,
        fasta_records=source_data.fasta_records,
        variant_fasta_records=source_data.variant_fasta_records,
        variant_peptide_records=source_data.variant_peptide_records,
        context_mapping_report=context_reports.context_mapping_report,
        pathway_enrichment_report=enrichment_reports.pathway_enrichment_report,
        complex_enrichment_report=enrichment_reports.complex_enrichment_report,
        protein_region_context_records=source_data.protein_region_context_records,
        ptm_evidence_card_report=ptm_evidence_card_report,
        lab_run_qc_feedback_report=lab_run_qc_feedback_report,
    )
    return BiologicalQuantTableSupportingReports(
        source_data=source_data,
        context_reports=context_reports,
        enrichment_reports=enrichment_reports,
        regulator_reports=regulator_reports,
        protein_evidence_reports=protein_evidence_reports,
    )


__all__ = [
    "BiologicalQuantTableSupportingReports",
    "_build_biological_quant_table_supporting_reports",
]
