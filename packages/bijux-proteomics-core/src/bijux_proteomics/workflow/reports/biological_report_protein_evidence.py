# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned graph-backed protein evidence analysis for biological reports."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from bijux_proteomics.interpretation import (
    BiologicalContextMappingReport,
    ComplexEnrichmentReport,
    PathwayEnrichmentReport,
    ProteinAnnotationMappingReport,
)
from bijux_proteomics.ptm import PtmEvidenceCardReport
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
)
from bijux_proteomics.sequences.fasta import NormalizedProteinRecord
from bijux_proteomics.sequences.protein_region_context_models import (
    ProteinRegionContextRecord,
)
from bijux_proteomics.sequences.proteogenomic_peptide_support import (
    ProteogenomicVariantPeptideRecord,
)
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
    ProteinEvidenceCardReport,
    ProteinEvidenceCardSelectionPolicy,
    build_protein_evidence_card_report,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
    build_protein_mechanism_card_report,
)
from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
    BiologicalResultSelectionPolicy,
)
from bijux_proteomics.workflow.reports.biological_result_graph import (
    BiologicalResultGraphReport,
    build_biological_result_graph_report,
)

if TYPE_CHECKING:
    from bijux_proteomics_lab.handoffs.qc_feedback import LabRunQcFeedbackReport


class BiologicalProteinEvidenceReports(NamedTuple):
    """Graph-backed protein evidence outputs for one biological report bundle."""

    graph_report: BiologicalResultGraphReport
    protein_cards: ProteinEvidenceCardReport
    protein_mechanism_cards: ProteinMechanismCardReport


def _build_biological_protein_evidence_reports(
    *,
    normalized_table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    selection_policy: BiologicalResultSelectionPolicy,
    annotation_report: ProteinAnnotationMappingReport,
    fasta_records: tuple[NormalizedProteinRecord, ...],
    variant_fasta_records: tuple[NormalizedProteinRecord, ...],
    variant_peptide_records: tuple[ProteogenomicVariantPeptideRecord, ...],
    context_mapping_report: BiologicalContextMappingReport | None,
    pathway_enrichment_report: PathwayEnrichmentReport | None,
    complex_enrichment_report: ComplexEnrichmentReport | None,
    protein_region_context_records: tuple[ProteinRegionContextRecord, ...] | None,
    ptm_evidence_card_report: PtmEvidenceCardReport | None,
    lab_run_qc_feedback_report: LabRunQcFeedbackReport | None,
) -> BiologicalProteinEvidenceReports:
    graph_report = build_biological_result_graph_report(
        normalized_table,
        differential_report,
        design_entries,
        max_adjusted_p_value=selection_policy.max_adjusted_p_value,
        min_absolute_log2_fold_change=selection_policy.min_absolute_log2_fold_change,
        lab_run_qc_feedback_report=lab_run_qc_feedback_report,
    )
    protein_cards = build_protein_evidence_card_report(
        graph_report,
        normalized_table,
        differential_report,
        annotation_report,
        protein_sequences={
            record.canonical_accession: record.residues for record in fasta_records
        },
        protein_records=fasta_records,
        variant_protein_records=variant_fasta_records,
        variant_peptide_records=variant_peptide_records,
        selection_policy=ProteinEvidenceCardSelectionPolicy(
            max_adjusted_p_value=selection_policy.max_adjusted_p_value,
            min_absolute_log2_fold_change=(
                selection_policy.min_absolute_log2_fold_change
            ),
        ),
        sample_conditions={
            entry.sample_id: entry.condition for entry in design_entries
        },
        context_mapping_report=context_mapping_report,
        pathway_enrichment_report=pathway_enrichment_report,
        complex_enrichment_report=complex_enrichment_report,
        protein_region_context_records=protein_region_context_records,
        ptm_evidence_card_report=ptm_evidence_card_report,
    )
    protein_mechanism_cards = build_protein_mechanism_card_report(
        graph_report,
        protein_cards,
        ptm_evidence_card_report=ptm_evidence_card_report,
    )
    return BiologicalProteinEvidenceReports(
        graph_report=graph_report,
        protein_cards=protein_cards,
        protein_mechanism_cards=protein_mechanism_cards,
    )
