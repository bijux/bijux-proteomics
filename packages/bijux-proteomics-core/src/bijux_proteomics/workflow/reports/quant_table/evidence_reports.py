# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Evidence and regulator report assembly for biological quant-table workflows."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.ptm import PtmEvidenceCardReport
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
)
from bijux_proteomics.workflow.reports.biological_report_protein_evidence import (
    BiologicalProteinEvidenceReports,
    _build_biological_protein_evidence_reports,
)
from bijux_proteomics.workflow.reports.biological_report_regulator_analysis import (
    BiologicalRegulatorAnalysisReports,
    _build_biological_regulator_analysis_reports,
)
from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
    BiologicalResultSelectionPolicy,
)
from bijux_proteomics.workflow.reports.quant_table.foundation_reports import (
    BiologicalQuantTableFoundationReports,
)

if TYPE_CHECKING:
    from bijux_proteomics_lab.handoffs.qc_feedback import LabRunQcFeedbackReport


class BiologicalQuantTableEvidenceReports(NamedTuple):
    """Evidence and regulator reports derived from foundational analyses."""

    regulator_reports: BiologicalRegulatorAnalysisReports
    protein_evidence_reports: BiologicalProteinEvidenceReports


def _build_biological_quant_table_evidence_reports(
    *,
    normalized_table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    active_selection_policy: BiologicalResultSelectionPolicy,
    foundation_reports: BiologicalQuantTableFoundationReports,
    regulator_evidence_tsv_path: Path | None,
    regulator_site_signal_tsv_path: Path | None,
    ptm_evidence_card_report: PtmEvidenceCardReport | None,
    lab_run_qc_feedback_report: LabRunQcFeedbackReport | None,
) -> BiologicalQuantTableEvidenceReports:
    regulator_reports = _build_biological_regulator_analysis_reports(
        regulator_evidence_tsv_path=regulator_evidence_tsv_path,
        regulator_site_signal_tsv_path=regulator_site_signal_tsv_path,
        ptm_evidence_card_report=ptm_evidence_card_report,
        differential_report=differential_report,
        protein_refs_by_entity=normalized_table.entity_protein_refs,
        annotation_report=foundation_reports.source_data.annotation_report,
        pathway_activity_report=foundation_reports.enrichment_reports.pathway_activity_report,
    )
    protein_evidence_reports = _build_biological_protein_evidence_reports(
        normalized_table=normalized_table,
        differential_report=differential_report,
        design_entries=design_entries,
        selection_policy=active_selection_policy,
        annotation_report=foundation_reports.source_data.annotation_report,
        fasta_records=foundation_reports.source_data.fasta_records,
        variant_fasta_records=foundation_reports.source_data.variant_fasta_records,
        variant_peptide_records=foundation_reports.source_data.variant_peptide_records,
        context_mapping_report=foundation_reports.context_reports.context_mapping_report,
        pathway_enrichment_report=(
            foundation_reports.enrichment_reports.pathway_enrichment_report
        ),
        complex_enrichment_report=(
            foundation_reports.enrichment_reports.complex_enrichment_report
        ),
        protein_region_context_records=(
            foundation_reports.source_data.protein_region_context_records
        ),
        ptm_evidence_card_report=ptm_evidence_card_report,
        lab_run_qc_feedback_report=lab_run_qc_feedback_report,
    )
    return BiologicalQuantTableEvidenceReports(
        regulator_reports=regulator_reports,
        protein_evidence_reports=protein_evidence_reports,
    )


__all__ = [
    "BiologicalQuantTableEvidenceReports",
    "_build_biological_quant_table_evidence_reports",
]
