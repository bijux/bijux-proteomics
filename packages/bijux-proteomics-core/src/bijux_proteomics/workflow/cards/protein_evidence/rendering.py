# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein-evidence card rendering and export surfaces."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.domain.card_schema import (
    StandardCardEntry,
    StandardCardKind,
    StandardCardSubjectKind,
    render_standard_card_row,
)
from bijux_proteomics.domain.confidence import ConfidenceTier
from bijux_proteomics.workflow.cards.protein_evidence.models import (
    ProteinEvidenceCard,
    ProteinEvidenceCardReport,
    ProteinEvidenceCardTier,
)


def render_protein_evidence_card_summary_tsv(report: ProteinEvidenceCardReport) -> str:
    """Render the protein-card summary ledger as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("protein_result_count", report.summary.protein_result_count))
    writer.writerow(("significant_card_count", report.summary.significant_card_count))
    writer.writerow(("warning_card_count", report.summary.warning_card_count))
    writer.writerow(
        ("pathway_annotated_card_count", report.summary.pathway_annotated_card_count)
    )
    writer.writerow(
        ("context_annotated_card_count", report.summary.context_annotated_card_count)
    )
    writer.writerow(
        (
            "functional_region_annotated_card_count",
            report.summary.functional_region_annotated_card_count,
        )
    )
    writer.writerow(
        (
            "proteogenomic_annotated_card_count",
            report.summary.proteogenomic_annotated_card_count,
        )
    )
    writer.writerow(
        ("ptm_annotated_card_count", report.summary.ptm_annotated_card_count)
    )
    writer.writerow(
        ("max_adjusted_p_value", report.selection_policy.max_adjusted_p_value)
    )
    writer.writerow(
        (
            "min_absolute_log2_fold_change",
            report.selection_policy.min_absolute_log2_fold_change,
        )
    )
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_protein_evidence_card_tsv(report: ProteinEvidenceCardReport) -> str:
    """Render final protein cards as a flat TSV ledger."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "card_id",
            "card_kind",
            "subject_kind",
            "subject_id",
            "subject_label",
            "claim",
            "evidence_for",
            "evidence_against",
            "confidence",
            "warning_codes",
            "source_ids",
            "graph_claim_node_id",
            "graph_subject_node_id",
            "graph_subject_node_kind",
            "graph_support_node_ids",
            "graph_source_row_refs",
            "protein_group_id",
            "representative_protein_ref",
            "protein_refs",
            "identity_level",
            "identity_reason",
            "gene_symbol",
            "annotation_status",
            "peptides",
            "peptide_count",
            "unique_peptide_count",
            "shared_peptide_count",
            "coverage_fraction",
            "covered_residue_count",
            "residue_count",
            "observed_sample_count",
            "missing_sample_count",
            "condition_a",
            "condition_b",
            "log2_fold_change",
            "adjusted_p_value",
            "significant",
            "evidence_tier",
            "pathway_ids",
            "context_ids",
            "functional_regions",
            "proteogenomic_support_class",
            "proteogenomic_support_reason",
            "proteogenomic_reference_only_peptides",
            "proteogenomic_variant_only_peptides",
            "proteogenomic_shared_peptides",
            "proteogenomic_ambiguous_peptides",
            "proteogenomic_variant_protein_refs",
            "ptm_sites",
        )
    )
    for card in report.cards:
        standard_card = _build_standard_card_entry(card)
        writer.writerow(
            (
                *render_standard_card_row(standard_card),
                card.graph_claim_node_id,
                card.graph_subject_node_id,
                card.graph_subject_node_kind.value,
                ";".join(card.graph_support_node_ids),
                ";".join(card.graph_source_row_refs),
                card.protein_group_id,
                card.representative_protein_ref,
                ";".join(card.protein_refs),
                card.identity_level.value,
                card.identity_reason,
                ""
                if card.annotation.gene_symbol is None
                else card.annotation.gene_symbol,
                card.annotation.annotation_status.value,
                ";".join(card.peptides),
                card.peptide_count,
                card.unique_peptide_count,
                card.shared_peptide_count,
                card.coverage.coverage_fraction,
                card.coverage.covered_residue_count,
                card.coverage.residue_count,
                card.quantification.observed_sample_count,
                card.quantification.missing_sample_count,
                card.differential_result.condition_a,
                card.differential_result.condition_b,
                card.differential_result.log2_fold_change,
                ""
                if card.differential_result.adjusted_p_value is None
                else card.differential_result.adjusted_p_value,
                str(card.significant).lower(),
                card.evidence_tier.value,
                ";".join(entry.entry_id for entry in card.pathways),
                ";".join(
                    f"{entry.context_kind.value}:{entry.context_id}"
                    for entry in card.context_terms
                ),
                ";".join(
                    f"{region.region_kind.value}:{region.label}@{region.start}-{region.end}"
                    for region in card.functional_regions
                ),
                ""
                if card.proteogenomic_support is None
                else card.proteogenomic_support.support_class.value,
                ""
                if card.proteogenomic_support is None
                else card.proteogenomic_support.support_reason,
                ""
                if card.proteogenomic_support is None
                else ";".join(card.proteogenomic_support.reference_only_peptides),
                ""
                if card.proteogenomic_support is None
                else ";".join(card.proteogenomic_support.variant_only_peptides),
                ""
                if card.proteogenomic_support is None
                else ";".join(card.proteogenomic_support.shared_peptides),
                ""
                if card.proteogenomic_support is None
                else ";".join(card.proteogenomic_support.ambiguous_peptides),
                ""
                if card.proteogenomic_support is None
                else ";".join(card.proteogenomic_support.matched_variant_protein_refs),
                ";".join(card.ptm_sites),
            )
        )
    return handle.getvalue()


def export_protein_evidence_card_summary_tsv(
    report: ProteinEvidenceCardReport,
    path: Path,
) -> None:
    """Write the protein-card summary ledger to one stable TSV artifact."""

    write_output_table_tsv(path, render_protein_evidence_card_summary_tsv(report))


def export_protein_evidence_card_tsv(
    report: ProteinEvidenceCardReport,
    path: Path,
) -> None:
    """Write final protein cards to one stable TSV artifact."""

    write_output_table_tsv(path, render_protein_evidence_card_tsv(report))


def _build_standard_card_entry(card: ProteinEvidenceCard) -> StandardCardEntry:
    return StandardCardEntry(
        card_id=card.card_id,
        card_kind=StandardCardKind.PROTEIN,
        subject_kind=StandardCardSubjectKind.PROTEIN,
        subject_id=card.representative_protein_ref,
        subject_label=card.annotation.gene_symbol or card.representative_protein_ref,
        claim=(
            f"Protein {card.representative_protein_ref} has log2 fold change "
            f"{card.differential_result.log2_fold_change:g} between "
            f"{card.differential_result.condition_a} and {card.differential_result.condition_b}."
        ),
        evidence_for=(
            f"{card.unique_peptide_count} unique peptides and "
            f"{card.coverage.coverage_fraction:.0%} sequence coverage support this protein."
        ),
        evidence_against=(
            "no explicit weakening evidence was preserved on this protein card."
            if not card.warnings
            else "warnings remained attached: "
            + ", ".join(warning.code.value for warning in card.warnings)
            + "."
        ),
        confidence=_standard_card_confidence(card.evidence_tier),
        warning_codes=tuple(warning.code.value for warning in card.warnings),
        source_ids=card.graph_source_row_refs,
    )


def _standard_card_confidence(tier: ProteinEvidenceCardTier) -> ConfidenceTier:
    if tier is ProteinEvidenceCardTier.HIGH_SUPPORT:
        return ConfidenceTier.HIGH
    if tier is ProteinEvidenceCardTier.MODERATE_SUPPORT:
        return ConfidenceTier.MODERATE
    return ConfidenceTier.LOW


__all__ = [
    "export_protein_evidence_card_summary_tsv",
    "export_protein_evidence_card_tsv",
    "render_protein_evidence_card_summary_tsv",
    "render_protein_evidence_card_tsv",
]
