# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Structured final-protein evidence cards over biological result bundles."""

from __future__ import annotations

from collections import Counter, defaultdict

from bijux_proteomics.domain.semantic_ids import build_protein_card_id
from bijux_proteomics.interpretation import (
    BiologicalContextKind,
    BiologicalContextMappingReport,
    ComplexEnrichmentEntry,
    ComplexEnrichmentReport,
    PathwayEnrichmentEntry,
    PathwayEnrichmentReport,
    ProteinAnnotationMappingReport,
    ProteinAnnotationResultEntry,
    ProteinAnnotationStatus,
)
from bijux_proteomics.ptm import PtmEvidenceCardReport
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
)
from bijux_proteomics.review import (
    FinalClaimEvidenceTier,
    ProteinEvidenceSummaryReport,
    ProteomicsEvidenceNodeKind,
    query_protein_evidence_summary,
)
from bijux_proteomics.sequences.fasta import NormalizedProteinRecord
from bijux_proteomics.sequences.protein_identity_resolution import (
    ProteinIdentityLevel,
    ProteinIdentityReference,
    ProteinIdentityResolutionEntry,
    build_protein_identity_resolution_report,
)
from bijux_proteomics.sequences.protein_region_context_models import (
    ProteinFunctionalRegionEvidence,
    ProteinFunctionalRegionKind,
    ProteinPeptideRegionReference,
    ProteinPeptideRegionContextReport,
    ProteinRegionContextRecord,
)
from bijux_proteomics.sequences.protein_region_context_workflows import (
    build_protein_peptide_region_context_report,
)
from bijux_proteomics.sequences.proteogenomic_peptide_support import (
    ProteogenomicPeptideReference,
    ProteogenomicPeptideSupportEntry,
    ProteogenomicVariantPeptideRecord,
    build_proteogenomic_peptide_support_report,
)
from bijux_proteomics.workflow.reports.biological_result_graph import (
    BiologicalResultGraphReport,
)
from bijux_proteomics.workflow.cards.protein_evidence.models import (
    ProteinEvidenceCard,
    ProteinEvidenceCardAnnotation,
    ProteinEvidenceCardContextEntry,
    ProteinEvidenceCardCoverage,
    ProteinEvidenceCardDifferentialResult,
    ProteinEvidenceCardPathwayEntry,
    ProteinEvidenceCardPathwayEntryKind,
    ProteinEvidenceCardQuantification,
    ProteinEvidenceCardReport,
    ProteinEvidenceCardSampleValue,
    ProteinEvidenceCardSelectionPolicy,
    ProteinEvidenceCardSummary,
    ProteinEvidenceCardTier,
    ProteinEvidenceCardWarning,
    ProteinEvidenceCardWarningCode,
    _PreparedProteinCard,
)
from bijux_proteomics.workflow.cards.protein_evidence.rendering import (
    export_protein_evidence_card_summary_tsv,
    export_protein_evidence_card_tsv,
    render_protein_evidence_card_summary_tsv,
    render_protein_evidence_card_tsv,
)
from bijux_proteomics.workflow.cards.protein_evidence.quantitative_evidence import (
    build_coverage_by_protein,
    build_differential_payload,
    build_quantification_payload,
    build_warnings,
    entry_is_significant,
    group_values_by_entity,
)


def build_protein_evidence_card_report(
    graph_report: BiologicalResultGraphReport,
    quant_table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    annotation_report: ProteinAnnotationMappingReport,
    *,
    protein_sequences: dict[str, str],
    protein_records: tuple[NormalizedProteinRecord, ...] | None = None,
    variant_protein_records: tuple[NormalizedProteinRecord, ...] | None = None,
    variant_peptide_records: tuple[ProteogenomicVariantPeptideRecord, ...]
    | None = None,
    selection_policy: ProteinEvidenceCardSelectionPolicy,
    sample_conditions: dict[str, str | None] | None = None,
    context_mapping_report: BiologicalContextMappingReport | None = None,
    pathway_enrichment_report: PathwayEnrichmentReport | None = None,
    complex_enrichment_report: ComplexEnrichmentReport | None = None,
    protein_region_context_records: tuple[ProteinRegionContextRecord, ...]
    | None = None,
    ptm_evidence_card_report: PtmEvidenceCardReport | None = None,
) -> ProteinEvidenceCardReport:
    """Build one structured card per final protein result."""

    values_by_entity = group_values_by_entity(quant_table.values)
    protein_peptides = {
        entity_id: tuple(
            sorted(set(quant_table.entity_member_peptides.get(entity_id, ())))
        )
        for entity_id in quant_table.entity_ids
    }
    peptide_membership_counts = Counter(
        peptide for peptides in protein_peptides.values() for peptide in peptides
    )
    coverage_by_protein = build_coverage_by_protein(
        quant_table,
        protein_sequences=protein_sequences,
    )
    annotations_by_entity = _group_annotations_by_entity(annotation_report)
    context_by_protein = _group_context_entries_by_protein(context_mapping_report)
    pathway_by_member = _group_pathway_entries_by_member(
        pathway_enrichment_report,
        complex_enrichment_report,
    )
    functional_regions_by_protein = _group_functional_regions_by_protein(
        _build_peptide_region_context_report(
            quant_table,
            protein_sequences=protein_sequences,
            protein_region_context_records=protein_region_context_records,
        )
    )
    ptm_sites_by_protein = _group_ptm_sites_by_protein(ptm_evidence_card_report)
    differential_by_entity = {
        entry.entity_id: entry for entry in differential_report.entries
    }
    final_entries = tuple(
        entry
        for entry in graph_report.final_results.entries
        if entry.subject_node_kind is ProteomicsEvidenceNodeKind.PROTEIN
    )
    prepared_cards: list[_PreparedProteinCard] = []
    for final_entry in sorted(final_entries, key=lambda entry: entry.subject_node_ref):
        differential_entry = differential_by_entity.get(final_entry.subject_node_ref)
        if differential_entry is None:
            continue
        protein_refs = quant_table.entity_protein_refs.get(
            differential_entry.entity_id,
            (),
        ) or (differential_entry.entity_id,)
        annotation_entries = annotations_by_entity.get(differential_entry.entity_id, ())
        representative_protein_ref = _select_representative_protein_ref(
            protein_refs,
            annotation_entries=annotation_entries,
            protein_sequences=protein_sequences,
        )
        peptides = protein_peptides.get(differential_entry.entity_id, ())
        unique_peptide_count = sum(
            1 for peptide in peptides if peptide_membership_counts.get(peptide, 0) == 1
        )
        shared_peptide_count = len(peptides) - unique_peptide_count
        coverage = coverage_by_protein.get(
            representative_protein_ref,
            ProteinEvidenceCardCoverage(
                coverage_protein_ref=representative_protein_ref,
                residue_count=len(
                    protein_sequences.get(representative_protein_ref, "")
                ),
                covered_residue_count=0,
                coverage_fraction=0.0,
                covered_peptides=(),
            ),
        )
        annotation = _build_annotation_payload(
            representative_protein_ref,
            annotation_entries=annotation_entries,
        )
        quantification = build_quantification_payload(
            values_by_entity.get(differential_entry.entity_id, ()),
            sample_conditions={} if sample_conditions is None else sample_conditions,
        )
        significant = entry_is_significant(
            differential_entry,
            policy=selection_policy,
        )
        contexts = _select_context_entries(
            protein_refs,
            by_protein=context_by_protein,
        )
        pathways = _select_pathway_entries(
            protein_refs,
            annotation_entries=annotation_entries,
            by_member=pathway_by_member,
        )
        functional_regions = _select_functional_regions(
            protein_refs,
            by_protein=functional_regions_by_protein,
        )
        graph_summary = query_protein_evidence_summary(
            graph_report.graph,
            protein_id=final_entry.subject_node_ref,
        )
        warnings = build_warnings(
            annotation=annotation,
            coverage=coverage,
            differential_entry=differential_entry,
            significant=significant,
            unique_peptide_count=unique_peptide_count,
            peptide_count=len(peptides),
        )
        prepared_cards.append(
            {
                "final_entry": final_entry,
                "differential_entry": differential_entry,
                "graph_summary": graph_summary,
                "representative_protein_ref": representative_protein_ref,
                "protein_refs": protein_refs,
                "annotation": annotation,
                "peptides": peptides,
                "unique_peptide_count": unique_peptide_count,
                "shared_peptide_count": shared_peptide_count,
                "coverage": coverage,
                "quantification": quantification,
                "contexts": contexts,
                "pathways": pathways,
                "functional_regions": functional_regions,
                "significant": significant,
                "warnings": warnings,
            }
        )

    identity_by_entity = _build_identity_entries_by_entity(
        prepared_cards,
        protein_records=protein_records,
        protein_sequences=protein_sequences,
    )
    proteogenomic_support_by_entity = _build_proteogenomic_support_by_entity(
        prepared_cards,
        protein_records=protein_records,
        protein_sequences=protein_sequences,
        variant_protein_records=variant_protein_records,
        variant_peptide_records=variant_peptide_records,
    )
    cards: list[ProteinEvidenceCard] = []
    for prepared_card in prepared_cards:
        differential_entry = prepared_card["differential_entry"]
        final_entry = prepared_card["final_entry"]
        identity_entry = identity_by_entity.get(differential_entry.entity_id)
        cards.append(
            ProteinEvidenceCard(
                card_id=_build_card_id(differential_entry.entity_id),
                graph_claim_node_id=final_entry.claim_node_id,
                graph_subject_node_id=final_entry.subject_node_id,
                graph_subject_node_kind=final_entry.subject_node_kind,
                graph_support_node_ids=_graph_support_node_ids(
                    prepared_card["graph_summary"]
                ),
                graph_source_row_refs=final_entry.source_row_refs,
                protein_group_id=differential_entry.entity_id,
                representative_protein_ref=prepared_card["representative_protein_ref"],
                protein_refs=prepared_card["protein_refs"],
                identity_level=(
                    ProteinIdentityLevel.AMBIGUOUS
                    if identity_entry is None
                    else identity_entry.identity_level
                ),
                identity_reason=(
                    "protein identity could not be resolved because no peptide-backed sequence context was available"
                    if identity_entry is None
                    else identity_entry.identity_reason
                ),
                annotation=prepared_card["annotation"],
                peptides=prepared_card["peptides"],
                peptide_count=len(prepared_card["peptides"]),
                unique_peptide_count=prepared_card["unique_peptide_count"],
                shared_peptide_count=prepared_card["shared_peptide_count"],
                coverage=prepared_card["coverage"],
                quantification=prepared_card["quantification"],
                differential_result=build_differential_payload(differential_entry),
                context_terms=prepared_card["contexts"],
                pathways=prepared_card["pathways"],
                functional_regions=prepared_card["functional_regions"],
                proteogenomic_support=proteogenomic_support_by_entity.get(
                    differential_entry.entity_id
                ),
                ptm_sites=_select_ptm_sites(
                    prepared_card["protein_refs"],
                    by_protein=ptm_sites_by_protein,
                ),
                significant=prepared_card["significant"],
                evidence_tier=_graph_evidence_tier(final_entry.evidence_tier),
                warnings=prepared_card["warnings"],
            )
        )

    return ProteinEvidenceCardReport(
        selection_policy=selection_policy,
        summary=ProteinEvidenceCardSummary(
            protein_result_count=len(cards),
            significant_card_count=sum(1 for card in cards if card.significant),
            warning_card_count=sum(1 for card in cards if card.warnings),
            pathway_annotated_card_count=sum(1 for card in cards if card.pathways),
            context_annotated_card_count=sum(1 for card in cards if card.context_terms),
            functional_region_annotated_card_count=sum(
                1 for card in cards if card.functional_regions
            ),
            proteogenomic_annotated_card_count=sum(
                1 for card in cards if card.proteogenomic_support is not None
            ),
            ptm_annotated_card_count=sum(1 for card in cards if card.ptm_sites),
        ),
        cards=tuple(cards),
        note=(
            "protein evidence cards preserve one structured object per final protein result, "
            "derive final claim identity and evidence tiers from the canonical review graph, "
            "carry annotation, peptide membership, coverage, quantification, differential, "
            "context, pathway, functional-region, proteogenomic peptide-support, and warning "
            "evidence together, and give "
            "biological reporting one stable graph-backed table source instead of ad hoc "
            "final-protein summaries"
        ),
    )

def _build_annotation_payload(
    representative_protein_ref: str,
    *,
    annotation_entries: tuple[ProteinAnnotationResultEntry, ...],
) -> ProteinEvidenceCardAnnotation:
    annotated_entries = tuple(
        entry
        for entry in annotation_entries
        if entry.annotation_status is ProteinAnnotationStatus.ANNOTATED
    )
    primary_entry = (
        next(
            (
                entry
                for entry in annotated_entries
                if entry.protein_ref == representative_protein_ref
            ),
            None,
        )
        or (annotated_entries[0] if annotated_entries else None)
        or (annotation_entries[0] if annotation_entries else None)
    )
    if primary_entry is None:
        return ProteinEvidenceCardAnnotation(
            annotation_status=ProteinAnnotationStatus.UNMAPPED,
        )
    return ProteinEvidenceCardAnnotation(
        annotation_status=primary_entry.annotation_status,
        gene_symbol=primary_entry.gene_symbol,
        description=primary_entry.description,
        organism=primary_entry.organism,
        annotation_identifiers=tuple(
            sorted(
                {
                    entry.annotation_identifier
                    for entry in annotated_entries
                    if entry.annotation_identifier
                }
            )
        ),
        accession_aliases=tuple(
            sorted(
                {
                    alias
                    for entry in annotation_entries
                    for alias in entry.accession_aliases
                }
            )
        ),
        custom_annotation=dict(sorted(primary_entry.custom_annotation.items())),
    )

def _group_annotations_by_entity(
    report: ProteinAnnotationMappingReport,
) -> dict[str, tuple[ProteinAnnotationResultEntry, ...]]:
    grouped: dict[str, list[ProteinAnnotationResultEntry]] = defaultdict(list)
    for entry in report.result_entries:
        grouped[(entry.source_row_id or entry.protein_ref)].append(entry)
    return {
        entity_id: tuple(sorted(entries, key=lambda entry: entry.protein_ref))
        for entity_id, entries in grouped.items()
    }


def _group_context_entries_by_protein(
    report: BiologicalContextMappingReport | None,
) -> dict[str, tuple[ProteinEvidenceCardContextEntry, ...]]:
    if report is None:
        return {}
    grouped: dict[str, list[ProteinEvidenceCardContextEntry]] = defaultdict(list)
    for entry in report.term_entries:
        context_entry = ProteinEvidenceCardContextEntry(
            context_kind=entry.context_kind,
            context_id=entry.context_id,
            context_name=entry.context_name,
            source_name=entry.source_name,
            source_accession=entry.source_accession,
        )
        for protein_ref in entry.supporting_protein_refs:
            grouped[protein_ref].append(context_entry)
    return {
        protein_ref: tuple(
            sorted(
                entries,
                key=lambda entry: (entry.context_kind.value, entry.context_id),
            )
        )
        for protein_ref, entries in grouped.items()
    }


def _group_pathway_entries_by_member(
    pathway_report: PathwayEnrichmentReport | None,
    complex_report: ComplexEnrichmentReport | None,
) -> dict[str, tuple[ProteinEvidenceCardPathwayEntry, ...]]:
    grouped: dict[str, list[ProteinEvidenceCardPathwayEntry]] = defaultdict(list)
    if pathway_report is not None:
        for entry in pathway_report.entries:
            card_entry = _pathway_card_entry(entry)
            for member_id in entry.foreground_member_ids:
                grouped[member_id].append(card_entry)
    if complex_report is not None:
        for entry in complex_report.entries:
            card_entry = _complex_card_entry(entry)
            for member_id in entry.foreground_member_ids:
                grouped[member_id].append(card_entry)
    return {
        member_id: tuple(
            sorted(
                entries,
                key=lambda entry: (entry.entry_kind.value, entry.entry_id),
            )
        )
        for member_id, entries in grouped.items()
    }


def _build_peptide_region_context_report(
    quant_table: LabelFreeQuantTable,
    *,
    protein_sequences: dict[str, str],
    protein_region_context_records: tuple[ProteinRegionContextRecord, ...] | None,
) -> ProteinPeptideRegionContextReport | None:
    if not protein_region_context_records:
        return None
    references = tuple(
        ProteinPeptideRegionReference(
            peptide_key=f"{protein_ref}:{peptide}",
            protein_ref=protein_ref,
            peptide_sequence=peptide,
        )
        for entity_id, peptides in quant_table.entity_member_peptides.items()
        for protein_ref in (
            quant_table.entity_protein_refs.get(entity_id, ()) or (entity_id,)
        )
        for peptide in sorted(set(peptides))
    )
    return build_protein_peptide_region_context_report(
        references,
        protein_sequences=protein_sequences,
        context_records=protein_region_context_records,
    )


def _build_identity_entries_by_entity(
    prepared_cards: list[_PreparedProteinCard],
    *,
    protein_records: tuple[NormalizedProteinRecord, ...] | None,
    protein_sequences: dict[str, str],
) -> dict[str, ProteinIdentityResolutionEntry]:
    if not prepared_cards:
        return {}
    report = build_protein_identity_resolution_report(
        tuple(
            ProteinIdentityReference(
                evidence_key=prepared_card["differential_entry"].entity_id,
                target_protein_ref=prepared_card["representative_protein_ref"],
                candidate_protein_refs=prepared_card["protein_refs"],
                peptide_sequences=prepared_card["peptides"],
            )
            for prepared_card in prepared_cards
        ),
        protein_records=() if protein_records is None else protein_records,
        protein_sequences=protein_sequences,
    )
    return {entry.evidence_key: entry for entry in report.entries}


def _build_proteogenomic_support_by_entity(
    prepared_cards: list[_PreparedProteinCard],
    *,
    protein_records: tuple[NormalizedProteinRecord, ...] | None,
    protein_sequences: dict[str, str],
    variant_protein_records: tuple[NormalizedProteinRecord, ...] | None,
    variant_peptide_records: tuple[ProteogenomicVariantPeptideRecord, ...] | None,
) -> dict[str, ProteogenomicPeptideSupportEntry]:
    if not prepared_cards or (
        not variant_protein_records and not variant_peptide_records
    ):
        return {}
    report = build_proteogenomic_peptide_support_report(
        tuple(
            ProteogenomicPeptideReference(
                evidence_key=prepared_card["differential_entry"].entity_id,
                peptide_sequences=prepared_card["peptides"],
                target_protein_refs=prepared_card["protein_refs"],
            )
            for prepared_card in prepared_cards
        ),
        reference_protein_records=() if protein_records is None else protein_records,
        reference_protein_sequences=protein_sequences,
        variant_protein_records=()
        if variant_protein_records is None
        else variant_protein_records,
        variant_peptide_records=()
        if variant_peptide_records is None
        else variant_peptide_records,
    )
    return {entry.evidence_key: entry for entry in report.entries}


def _group_functional_regions_by_protein(
    report: ProteinPeptideRegionContextReport | None,
) -> dict[str, tuple[ProteinFunctionalRegionEvidence, ...]]:
    if report is None:
        return {}
    grouped: dict[
        str,
        dict[tuple[str, str, int, int, str | None, str | None], set[str]],
    ] = defaultdict(dict)
    for entry in report.entries:
        for region in entry.functional_regions:
            key = (
                region.region_kind.value,
                region.label,
                region.start,
                region.end,
                region.source_name,
                region.source_accession,
            )
            grouped[entry.protein_ref].setdefault(key, set()).update(
                region.supporting_evidence_refs
            )
    return {
        protein_ref: tuple(
            ProteinFunctionalRegionEvidence(
                region_kind=ProteinFunctionalRegionKind(region_kind_value),
                label=label,
                start=start,
                end=end,
                source_name=source_name,
                source_accession=source_accession,
                supporting_evidence_refs=tuple(sorted(refs)),
            )
            for (
                region_kind_value,
                label,
                start,
                end,
                source_name,
                source_accession,
            ), refs in sorted(
                region_entries.items(),
                key=lambda item: (
                    item[0][0],
                    item[0][2],
                    item[0][3],
                    item[0][1],
                    item[0][4] or "",
                    item[0][5] or "",
                ),
            )
        )
        for protein_ref, region_entries in grouped.items()
    }


def _group_ptm_sites_by_protein(
    report: PtmEvidenceCardReport | None,
) -> dict[str, tuple[str, ...]]:
    if report is None:
        return {}
    grouped: dict[str, set[str]] = defaultdict(set)
    for card in report.cards:
        grouped[card.protein_ref].add(card.site_key)
    return {
        protein_ref: tuple(sorted(site_keys))
        for protein_ref, site_keys in grouped.items()
    }


def _select_ptm_sites(
    protein_refs: tuple[str, ...],
    *,
    by_protein: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                site_key
                for protein_ref in protein_refs
                for site_key in by_protein.get(protein_ref, ())
            }
        )
    )


def _select_functional_regions(
    protein_refs: tuple[str, ...],
    *,
    by_protein: dict[str, tuple[ProteinFunctionalRegionEvidence, ...]],
) -> tuple[ProteinFunctionalRegionEvidence, ...]:
    merged: dict[tuple[str, str, int, int, str | None, str | None], set[str]] = {}
    for protein_ref in protein_refs:
        for region in by_protein.get(protein_ref, ()):
            key = (
                region.region_kind.value,
                region.label,
                region.start,
                region.end,
                region.source_name,
                region.source_accession,
            )
            merged.setdefault(key, set()).update(region.supporting_evidence_refs)
    return tuple(
        ProteinFunctionalRegionEvidence(
            region_kind=ProteinFunctionalRegionKind(region_kind_value),
            label=label,
            start=start,
            end=end,
            source_name=source_name,
            source_accession=source_accession,
            supporting_evidence_refs=tuple(sorted(refs)),
        )
        for (
            region_kind_value,
            label,
            start,
            end,
            source_name,
            source_accession,
        ), refs in sorted(
            merged.items(),
            key=lambda item: (
                item[0][0],
                item[0][2],
                item[0][3],
                item[0][1],
                item[0][4] or "",
                item[0][5] or "",
            ),
        )
    )


def _pathway_card_entry(
    entry: PathwayEnrichmentEntry,
) -> ProteinEvidenceCardPathwayEntry:
    return ProteinEvidenceCardPathwayEntry(
        entry_kind=ProteinEvidenceCardPathwayEntryKind.PATHWAY,
        entry_id=entry.pathway_id,
        entry_name=entry.pathway_name,
        source_name=entry.source_name,
        source_accession=entry.source_accession,
        adjusted_p_value=entry.adjusted_p_value,
        enrichment_ratio=entry.enrichment_ratio,
    )


def _complex_card_entry(
    entry: ComplexEnrichmentEntry,
) -> ProteinEvidenceCardPathwayEntry:
    return ProteinEvidenceCardPathwayEntry(
        entry_kind=ProteinEvidenceCardPathwayEntryKind.COMPLEX,
        entry_id=entry.complex_id,
        entry_name=entry.complex_name,
        source_name=entry.source_name,
        source_accession=entry.source_accession,
        adjusted_p_value=entry.adjusted_p_value,
        enrichment_ratio=entry.enrichment_ratio,
    )

def _select_representative_protein_ref(
    protein_refs: tuple[str, ...],
    *,
    annotation_entries: tuple[ProteinAnnotationResultEntry, ...],
    protein_sequences: dict[str, str],
) -> str:
    annotated_refs = {
        entry.protein_ref
        for entry in annotation_entries
        if entry.annotation_status is ProteinAnnotationStatus.ANNOTATED
    }
    for protein_ref in protein_refs:
        if protein_ref in annotated_refs and protein_ref in protein_sequences:
            return protein_ref
    for protein_ref in protein_refs:
        if protein_ref in annotated_refs:
            return protein_ref
    for protein_ref in protein_refs:
        if protein_ref in protein_sequences:
            return protein_ref
    return protein_refs[0]

def _select_context_entries(
    protein_refs: tuple[str, ...],
    *,
    by_protein: dict[str, tuple[ProteinEvidenceCardContextEntry, ...]],
) -> tuple[ProteinEvidenceCardContextEntry, ...]:
    entries = {
        (
            entry.context_kind.value,
            entry.context_id,
            entry.source_accession or "",
        ): entry
        for protein_ref in protein_refs
        for entry in by_protein.get(protein_ref, ())
    }
    return tuple(
        sorted(
            entries.values(),
            key=lambda entry: (entry.context_kind.value, entry.context_id),
        )
    )


def _select_pathway_entries(
    protein_refs: tuple[str, ...],
    *,
    annotation_entries: tuple[ProteinAnnotationResultEntry, ...],
    by_member: dict[str, tuple[ProteinEvidenceCardPathwayEntry, ...]],
) -> tuple[ProteinEvidenceCardPathwayEntry, ...]:
    gene_symbols = {
        entry.gene_symbol for entry in annotation_entries if entry.gene_symbol
    }
    entries = {
        (
            entry.entry_kind.value,
            entry.entry_id,
            entry.source_accession or "",
        ): entry
        for member_id in (*protein_refs, *sorted(gene_symbols))
        for entry in by_member.get(member_id, ())
    }
    return tuple(
        sorted(
            entries.values(),
            key=lambda entry: (entry.entry_kind.value, entry.entry_id),
        )
    )

def _graph_evidence_tier(
    evidence_tier: FinalClaimEvidenceTier,
) -> ProteinEvidenceCardTier:
    if evidence_tier is FinalClaimEvidenceTier.HIGH_CONFIDENCE:
        return ProteinEvidenceCardTier.HIGH_SUPPORT
    if evidence_tier is FinalClaimEvidenceTier.MODERATE:
        return ProteinEvidenceCardTier.MODERATE_SUPPORT
    return ProteinEvidenceCardTier.REVIEW


def _graph_support_node_ids(report: ProteinEvidenceSummaryReport) -> tuple[str, ...]:
    node_ids = {
        report.protein.node_id,
        *(node.node_id for node in report.mapped_peptides),
        *(node.node_id for node in report.quantifying_peptides),
        *(node.node_id for node in report.protein_groups),
        *(node.node_id for node in report.quant_values),
    }
    return tuple(sorted(node_ids))


def _build_card_id(entity_id: str) -> str:
    return build_protein_card_id(entity_id)


__all__ = [
    "ProteinEvidenceCard",
    "ProteinEvidenceCardAnnotation",
    "ProteinEvidenceCardContextEntry",
    "ProteinEvidenceCardCoverage",
    "ProteinEvidenceCardDifferentialResult",
    "ProteinEvidenceCardPathwayEntry",
    "ProteinEvidenceCardPathwayEntryKind",
    "ProteinEvidenceCardQuantification",
    "ProteinEvidenceCardReport",
    "ProteinEvidenceCardSampleValue",
    "ProteinEvidenceCardSelectionPolicy",
    "ProteinEvidenceCardSummary",
    "ProteinEvidenceCardTier",
    "ProteinEvidenceCardWarning",
    "ProteinEvidenceCardWarningCode",
    "build_protein_evidence_card_report",
    "export_protein_evidence_card_summary_tsv",
    "export_protein_evidence_card_tsv",
    "render_protein_evidence_card_summary_tsv",
    "render_protein_evidence_card_tsv",
]
