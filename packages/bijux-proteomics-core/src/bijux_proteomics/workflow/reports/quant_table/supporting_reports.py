# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Supporting report assembly for biological quant-table workflows."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.ptm import PtmEvidenceCardReport
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
)
from bijux_proteomics.study import ExperimentDesign
from bijux_proteomics.workflow.reports.biological_report_context_assembly import (
    BiologicalContextAssemblyReports,
)
from bijux_proteomics.workflow.reports.biological_report_enrichment_assembly import (
    BiologicalEnrichmentAssemblyReports,
)
from bijux_proteomics.workflow.reports.biological_report_protein_evidence import (
    BiologicalProteinEvidenceReports,
)
from bijux_proteomics.workflow.reports.biological_report_regulator_analysis import (
    BiologicalRegulatorAnalysisReports,
)
from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
    BiologicalResultSelectionPolicy,
)
from bijux_proteomics.workflow.reports.biological_report_source_data import (
    BiologicalReportSourceData,
)
from bijux_proteomics.workflow.reports.quant_table.evidence_reports import (
    _build_biological_quant_table_evidence_reports,
)
from bijux_proteomics.workflow.reports.quant_table.foundation_reports import (
    _build_biological_quant_table_foundation_reports,
)

if TYPE_CHECKING:
    from bijux_proteomics_lab.handoffs.qc_feedback import LabRunQcFeedbackReport


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
    differential_report: DifferentialAbundanceReport,
    experiment_design: ExperimentDesign,
    design_entries: tuple[ExperimentalDesignEntry, ...],
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
    lab_run_qc_feedback_report: LabRunQcFeedbackReport | None,
) -> BiologicalQuantTableSupportingReports:
    foundation_reports = _build_biological_quant_table_foundation_reports(
        normalized_table=normalized_table,
        differential_report=differential_report,
        experiment_design=experiment_design,
        design_entries=design_entries,
        active_selection_policy=active_selection_policy,
        proteins_fasta_path=proteins_fasta_path,
        variant_proteins_fasta_path=variant_proteins_fasta_path,
        variant_peptide_tsv_path=variant_peptide_tsv_path,
        annotation_tsv_path=annotation_tsv_path,
        context_annotation_tsv_path=context_annotation_tsv_path,
        protein_region_context_tsv_path=protein_region_context_tsv_path,
        go_annotation_tsv_path=go_annotation_tsv_path,
        pathway_membership_tsv_path=pathway_membership_tsv_path,
        complex_membership_tsv_path=complex_membership_tsv_path,
    )
    evidence_reports = _build_biological_quant_table_evidence_reports(
        normalized_table=normalized_table,
        differential_report=differential_report,
        design_entries=design_entries,
        active_selection_policy=active_selection_policy,
        foundation_reports=foundation_reports,
        regulator_evidence_tsv_path=regulator_evidence_tsv_path,
        regulator_site_signal_tsv_path=regulator_site_signal_tsv_path,
        ptm_evidence_card_report=ptm_evidence_card_report,
        lab_run_qc_feedback_report=lab_run_qc_feedback_report,
    )
    return BiologicalQuantTableSupportingReports(
        source_data=foundation_reports.source_data,
        context_reports=foundation_reports.context_reports,
        enrichment_reports=foundation_reports.enrichment_reports,
        regulator_reports=evidence_reports.regulator_reports,
        protein_evidence_reports=evidence_reports.protein_evidence_reports,
    )


__all__ = [
    "BiologicalQuantTableSupportingReports",
    "_build_biological_quant_table_supporting_reports",
]
