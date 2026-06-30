# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Structured protein mechanism cards over graph-backed protein result evidence."""

from __future__ import annotations

from collections import defaultdict
import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.domain.source_row_lineage import SourceRowLineage
from bijux_proteomics.domain.semantic_ids import build_protein_mechanism_card_id
from bijux_proteomics.ptm import PtmEvidenceCardReport, PtmMechanismClass
from bijux_proteomics.review import (
    EvidenceGraphConfidenceTier,
    EvidenceGraphDowngradeReason,
    FinalClaimEvidenceTier,
    ProteomicsEvidenceNodeKind,
    query_protein_evidence_summary,
)
from bijux_proteomics.sequences import (
    ProteinFunctionalRegionEvidence,
    ProteinFunctionalRegionKind,
    ProteinIdentityLevel,
)
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
    ProteinEvidenceCard,
    ProteinEvidenceCardPathwayEntry,
    ProteinEvidenceCardPathwayEntryKind,
    ProteinEvidenceCardReport,
    ProteinEvidenceCardWarningCode,
)
from bijux_proteomics.workflow.reports.biological_result_graph import (
    BiologicalResultGraphReport,
)
from bijux_proteomics_foundation import JsonModel


class ProteinMechanismDirection(StrEnum):
    """Stable direction labels for protein abundance changes."""

    INCREASED = "increased"
    DECREASED = "decreased"
    UNCHANGED = "unchanged"


class ProteinMechanismCardAbundanceChange(JsonModel):
    """Structured abundance-change summary for one protein mechanism card."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    direction: ProteinMechanismDirection
    significant: bool = False
    log2_fold_change: float
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    effect_size_cohens_d: float | None = None
    uncertainty_note: str | None = None


class ProteinMechanismCardPeptideSupport(JsonModel):
    """Graph-backed peptide support summary for one protein mechanism card."""

    model_config = ConfigDict(extra="forbid")

    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    quantifying_peptide_count: int = Field(..., ge=0)
    quant_value_count: int = Field(..., ge=0)
    graph_support_edge_count: int = Field(..., ge=0)


class ProteinMechanismCardPtmSummary(JsonModel):
    """One PTM site summarized on a protein mechanism card."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    modification_name: str = Field(..., min_length=1)
    position: int = Field(..., ge=1)
    mechanism_class: PtmMechanismClass | None = None
    raw_log2_fold_change: float
    corrected_log2_fold_change: float | None = None
    warning_codes: tuple[str, ...] = Field(default_factory=tuple)
    claim_ids: tuple[str, ...] = Field(default_factory=tuple)


class ProteinMechanismCard(JsonModel):
    """One structured protein mechanism card over a graph-backed protein result."""

    model_config = ConfigDict(extra="forbid")

    card_id: str = Field(..., min_length=1)
    protein_card_id: str = Field(..., min_length=1)
    graph_claim_node_id: str = Field(..., min_length=1)
    graph_subject_node_id: str = Field(..., min_length=1)
    graph_subject_node_kind: ProteomicsEvidenceNodeKind
    protein_group_id: str = Field(..., min_length=1)
    representative_protein_ref: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    identity_level: ProteinIdentityLevel
    identity_reason: str = Field(..., min_length=1)
    abundance_change: ProteinMechanismCardAbundanceChange
    peptide_support: ProteinMechanismCardPeptideSupport
    ptms: tuple[ProteinMechanismCardPtmSummary, ...] = Field(default_factory=tuple)
    domains: tuple[ProteinFunctionalRegionEvidence, ...] = Field(default_factory=tuple)
    pathways: tuple[ProteinEvidenceCardPathwayEntry, ...] = Field(default_factory=tuple)
    complexes: tuple[ProteinEvidenceCardPathwayEntry, ...] = Field(
        default_factory=tuple
    )
    evidence_tier: FinalClaimEvidenceTier
    confidence_tier: EvidenceGraphConfidenceTier
    downgrade_reasons: tuple[EvidenceGraphDowngradeReason, ...] = Field(
        default_factory=tuple
    )
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    derived_no_source_reason: str | None = None
    evidence_rationale: str = Field(..., min_length=1)
    warning_codes: tuple[ProteinEvidenceCardWarningCode, ...] = Field(
        default_factory=tuple
    )

    @model_validator(mode="after")
    def _validate_source_row_lineage(self) -> ProteinMechanismCard:
        SourceRowLineage(
            source_row_refs=self.source_row_refs,
            derived_no_source_reason=self.derived_no_source_reason,
        )
        return self


class ProteinMechanismCardSummary(JsonModel):
    """Stable summary over one protein mechanism-card pass."""

    model_config = ConfigDict(extra="forbid")

    card_count: int = Field(..., ge=0)
    significant_card_count: int = Field(..., ge=0)
    ptm_annotated_card_count: int = Field(..., ge=0)
    domain_annotated_card_count: int = Field(..., ge=0)
    pathway_annotated_card_count: int = Field(..., ge=0)
    complex_annotated_card_count: int = Field(..., ge=0)
    warning_card_count: int = Field(..., ge=0)
    weak_evidence_card_count: int = Field(..., ge=0)
    evidence_tier_counts: dict[str, int] = Field(default_factory=dict)


class ProteinMechanismCardReport(JsonModel):
    """Stable report over graph-backed protein mechanism cards."""

    model_config = ConfigDict(extra="forbid")

    cards: tuple[ProteinMechanismCard, ...] = Field(default_factory=tuple)
    summary: ProteinMechanismCardSummary
    note: str = Field(..., min_length=1)


def build_protein_mechanism_card_report(
    graph_report: BiologicalResultGraphReport,
    protein_card_report: ProteinEvidenceCardReport,
    *,
    ptm_evidence_card_report: PtmEvidenceCardReport | None = None,
) -> ProteinMechanismCardReport:
    """Build structured protein mechanism cards from the canonical evidence graph."""

    final_entries_by_subject_ref = {
        entry.subject_node_ref: entry
        for entry in graph_report.final_results.entries
        if entry.subject_node_kind is ProteomicsEvidenceNodeKind.PROTEIN
    }
    ptms_by_protein = _group_ptm_cards_by_protein(ptm_evidence_card_report)
    cards: list[ProteinMechanismCard] = []
    for protein_card in sorted(
        protein_card_report.cards,
        key=lambda card: (
            card.representative_protein_ref,
            card.protein_group_id,
            card.card_id,
        ),
    ):
        final_entry = final_entries_by_subject_ref.get(protein_card.protein_group_id)
        if final_entry is None:
            raise ValueError(
                "protein mechanism cards require one graph final-result entry per protein card"
            )
        graph_summary = query_protein_evidence_summary(
            graph_report.graph,
            protein_id=protein_card.protein_group_id,
        )
        source_row_lineage = (
            SourceRowLineage.from_source_row_refs(protein_card.graph_source_row_refs)
            if protein_card.graph_source_row_refs
            else SourceRowLineage.from_derived_reason(
                "protein mechanism cards inherit governed protein evidence but the upstream protein card did not preserve concrete source-row refs"
            )
        )
        pathways, complexes = _split_pathway_entries(protein_card.pathways)
        cards.append(
            ProteinMechanismCard(
                card_id=_build_card_id(protein_card),
                protein_card_id=protein_card.card_id,
                graph_claim_node_id=protein_card.graph_claim_node_id,
                graph_subject_node_id=protein_card.graph_subject_node_id,
                graph_subject_node_kind=protein_card.graph_subject_node_kind,
                protein_group_id=protein_card.protein_group_id,
                representative_protein_ref=protein_card.representative_protein_ref,
                gene_symbol=protein_card.annotation.gene_symbol,
                identity_level=protein_card.identity_level,
                identity_reason=protein_card.identity_reason,
                abundance_change=ProteinMechanismCardAbundanceChange(
                    condition_a=protein_card.differential_result.condition_a,
                    condition_b=protein_card.differential_result.condition_b,
                    direction=_mechanism_direction(
                        protein_card.differential_result.log2_fold_change
                    ),
                    significant=protein_card.significant,
                    log2_fold_change=protein_card.differential_result.log2_fold_change,
                    adjusted_p_value=protein_card.differential_result.adjusted_p_value,
                    effect_size_cohens_d=protein_card.differential_result.effect_size_cohens_d,
                    uncertainty_note=protein_card.differential_result.uncertainty_note,
                ),
                peptide_support=ProteinMechanismCardPeptideSupport(
                    peptide_count=protein_card.peptide_count,
                    unique_peptide_count=protein_card.unique_peptide_count,
                    shared_peptide_count=protein_card.shared_peptide_count,
                    coverage_fraction=protein_card.coverage.coverage_fraction,
                    quantifying_peptide_count=len(graph_summary.quantifying_peptides),
                    quant_value_count=len(graph_summary.quant_values),
                    graph_support_edge_count=graph_summary.support_edge_count,
                ),
                ptms=_select_ptm_summaries(
                    protein_card,
                    by_protein=ptms_by_protein,
                ),
                domains=tuple(
                    region
                    for region in protein_card.functional_regions
                    if region.region_kind is ProteinFunctionalRegionKind.DOMAIN
                ),
                pathways=pathways,
                complexes=complexes,
                evidence_tier=final_entry.evidence_tier,
                confidence_tier=final_entry.confidence_tier,
                downgrade_reasons=final_entry.downgrade_reasons,
                source_row_refs=source_row_lineage.source_row_refs,
                derived_no_source_reason=source_row_lineage.derived_no_source_reason,
                evidence_rationale=final_entry.rationale,
                warning_codes=tuple(
                    sorted(
                        (warning.code for warning in protein_card.warnings),
                        key=lambda code: code.value,
                    )
                ),
            )
        )

    tier_counts: dict[str, int] = {}
    for card in cards:
        tier_counts[card.evidence_tier.value] = (
            tier_counts.get(card.evidence_tier.value, 0) + 1
        )
    return ProteinMechanismCardReport(
        cards=tuple(cards),
        summary=ProteinMechanismCardSummary(
            card_count=len(cards),
            significant_card_count=sum(
                1 for card in cards if card.abundance_change.significant
            ),
            ptm_annotated_card_count=sum(1 for card in cards if card.ptms),
            domain_annotated_card_count=sum(1 for card in cards if card.domains),
            pathway_annotated_card_count=sum(1 for card in cards if card.pathways),
            complex_annotated_card_count=sum(1 for card in cards if card.complexes),
            warning_card_count=sum(1 for card in cards if card.warning_codes),
            weak_evidence_card_count=sum(
                1
                for card in cards
                if card.evidence_tier
                in {
                    FinalClaimEvidenceTier.WEAK,
                    FinalClaimEvidenceTier.AMBIGUOUS,
                }
            ),
            evidence_tier_counts=dict(sorted(tier_counts.items())),
        ),
        note=(
            "protein mechanism cards summarize graph-backed abundance change, peptide "
            "support, PTM support, protein domains, pathway and complex context, and "
            "graph-derived evidence tiers so strong and weak protein claims stay visibly "
            "different without relying on prose templates"
        ),
    )


def render_protein_mechanism_card_summary_tsv(
    report: ProteinMechanismCardReport,
) -> str:
    """Render a compact protein mechanism-card summary ledger as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("card_count", report.summary.card_count))
    writer.writerow(("significant_card_count", report.summary.significant_card_count))
    writer.writerow(
        ("ptm_annotated_card_count", report.summary.ptm_annotated_card_count)
    )
    writer.writerow(
        ("domain_annotated_card_count", report.summary.domain_annotated_card_count)
    )
    writer.writerow(
        ("pathway_annotated_card_count", report.summary.pathway_annotated_card_count)
    )
    writer.writerow(
        ("complex_annotated_card_count", report.summary.complex_annotated_card_count)
    )
    writer.writerow(("warning_card_count", report.summary.warning_card_count))
    writer.writerow(
        ("weak_evidence_card_count", report.summary.weak_evidence_card_count)
    )
    writer.writerow(
        (
            "evidence_tier_counts",
            ";".join(
                f"{tier}:{count}"
                for tier, count in report.summary.evidence_tier_counts.items()
            ),
        )
    )
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_protein_mechanism_card_tsv(report: ProteinMechanismCardReport) -> str:
    """Render protein mechanism cards as a flat TSV ledger."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "card_id",
            "protein_card_id",
            "graph_claim_node_id",
            "protein_group_id",
            "representative_protein_ref",
            "gene_symbol",
            "identity_level",
            "condition_a",
            "condition_b",
            "direction",
            "significant",
            "log2_fold_change",
            "adjusted_p_value",
            "peptide_count",
            "unique_peptide_count",
            "shared_peptide_count",
            "coverage_fraction",
            "quantifying_peptide_count",
            "quant_value_count",
            "graph_support_edge_count",
            "ptm_site_keys",
            "ptm_mechanism_classes",
            "domain_labels",
            "pathway_ids",
            "complex_ids",
            "confidence_tier",
            "evidence_tier",
            "downgrade_reasons",
            "source_row_refs",
            "derived_no_source_reason",
            "warning_codes",
            "evidence_rationale",
        )
    )
    for card in report.cards:
        writer.writerow(
            (
                card.card_id,
                card.protein_card_id,
                card.graph_claim_node_id,
                card.protein_group_id,
                card.representative_protein_ref,
                "" if card.gene_symbol is None else card.gene_symbol,
                card.identity_level.value,
                card.abundance_change.condition_a,
                card.abundance_change.condition_b,
                card.abundance_change.direction.value,
                str(card.abundance_change.significant).lower(),
                card.abundance_change.log2_fold_change,
                ""
                if card.abundance_change.adjusted_p_value is None
                else card.abundance_change.adjusted_p_value,
                card.peptide_support.peptide_count,
                card.peptide_support.unique_peptide_count,
                card.peptide_support.shared_peptide_count,
                card.peptide_support.coverage_fraction,
                card.peptide_support.quantifying_peptide_count,
                card.peptide_support.quant_value_count,
                card.peptide_support.graph_support_edge_count,
                ";".join(ptm.site_key for ptm in card.ptms),
                ";".join(
                    "" if ptm.mechanism_class is None else ptm.mechanism_class.value
                    for ptm in card.ptms
                ),
                ";".join(domain.label for domain in card.domains),
                ";".join(entry.entry_id for entry in card.pathways),
                ";".join(entry.entry_id for entry in card.complexes),
                card.confidence_tier.value,
                card.evidence_tier.value,
                ";".join(reason.value for reason in card.downgrade_reasons),
                ";".join(card.source_row_refs),
                ""
                if card.derived_no_source_reason is None
                else card.derived_no_source_reason,
                ";".join(code.value for code in card.warning_codes),
                card.evidence_rationale,
            )
        )
    return handle.getvalue()


def export_protein_mechanism_card_summary_tsv(
    report: ProteinMechanismCardReport,
    path: Path,
) -> None:
    """Write the protein mechanism-card summary ledger to one stable TSV artifact."""

    write_output_table_tsv(path, render_protein_mechanism_card_summary_tsv(report))


def export_protein_mechanism_card_tsv(
    report: ProteinMechanismCardReport,
    path: Path,
) -> None:
    """Write protein mechanism cards to one stable TSV artifact."""

    write_output_table_tsv(path, render_protein_mechanism_card_tsv(report))


def _build_card_id(card: ProteinEvidenceCard) -> str:
    return build_protein_mechanism_card_id(card.protein_group_id)


def _group_ptm_cards_by_protein(
    report: PtmEvidenceCardReport | None,
) -> dict[str, tuple[ProteinMechanismCardPtmSummary, ...]]:
    if report is None:
        return {}
    grouped: dict[str, list[ProteinMechanismCardPtmSummary]] = defaultdict(list)
    for card in report.cards:
        grouped[card.protein_ref].append(
            ProteinMechanismCardPtmSummary(
                site_key=card.site_key,
                protein_ref=card.protein_ref,
                modification_name=card.modification_name,
                position=card.position,
                mechanism_class=(
                    None
                    if card.mechanism_classification is None
                    else card.mechanism_classification.mechanism_class
                ),
                raw_log2_fold_change=card.differential_result.log2_fold_change,
                corrected_log2_fold_change=card.protein_correction.corrected_log2_fold_change,
                warning_codes=tuple(
                    sorted(
                        (warning.code.value for warning in card.warnings),
                        key=str,
                    )
                ),
                claim_ids=card.claim_ids,
            )
        )
    return {
        protein_ref: tuple(
            sorted(
                summaries,
                key=lambda summary: (
                    summary.position,
                    summary.modification_name,
                    summary.site_key,
                ),
            )
        )
        for protein_ref, summaries in grouped.items()
    }


def _select_ptm_summaries(
    protein_card: ProteinEvidenceCard,
    *,
    by_protein: dict[str, tuple[ProteinMechanismCardPtmSummary, ...]],
) -> tuple[ProteinMechanismCardPtmSummary, ...]:
    deduplicated: dict[str, ProteinMechanismCardPtmSummary] = {}
    for protein_ref in protein_card.protein_refs:
        for summary in by_protein.get(protein_ref, ()):
            deduplicated.setdefault(summary.site_key, summary)
    return tuple(
        sorted(
            deduplicated.values(),
            key=lambda summary: (
                summary.position,
                summary.modification_name,
                summary.site_key,
            ),
        )
    )


def _split_pathway_entries(
    entries: tuple[ProteinEvidenceCardPathwayEntry, ...],
) -> tuple[
    tuple[ProteinEvidenceCardPathwayEntry, ...],
    tuple[ProteinEvidenceCardPathwayEntry, ...],
]:
    pathways = tuple(
        entry
        for entry in entries
        if entry.entry_kind is ProteinEvidenceCardPathwayEntryKind.PATHWAY
    )
    complexes = tuple(
        entry
        for entry in entries
        if entry.entry_kind is ProteinEvidenceCardPathwayEntryKind.COMPLEX
    )
    return pathways, complexes


def _mechanism_direction(log2_fold_change: float) -> ProteinMechanismDirection:
    if log2_fold_change > 0.0:
        return ProteinMechanismDirection.INCREASED
    if log2_fold_change < 0.0:
        return ProteinMechanismDirection.DECREASED
    return ProteinMechanismDirection.UNCHANGED


__all__ = [
    "ProteinMechanismCard",
    "ProteinMechanismCardAbundanceChange",
    "ProteinMechanismDirection",
    "ProteinMechanismCardPeptideSupport",
    "ProteinMechanismCardPtmSummary",
    "ProteinMechanismCardReport",
    "ProteinMechanismCardSummary",
    "build_protein_mechanism_card_report",
    "export_protein_mechanism_card_summary_tsv",
    "export_protein_mechanism_card_tsv",
    "render_protein_mechanism_card_summary_tsv",
    "render_protein_mechanism_card_tsv",
]
