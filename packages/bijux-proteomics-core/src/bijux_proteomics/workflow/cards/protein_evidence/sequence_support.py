# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Sequence-derived support helpers for protein-evidence card assembly."""

from __future__ import annotations

from collections import defaultdict

from bijux_proteomics.ptm import PtmEvidenceCardReport
from bijux_proteomics.quantification.contracts import LabelFreeQuantTable
from bijux_proteomics.sequences.fasta import NormalizedProteinRecord
from bijux_proteomics.sequences.protein_identity_resolution import (
    ProteinIdentityReference,
    ProteinIdentityResolutionEntry,
    build_protein_identity_resolution_report,
)
from bijux_proteomics.sequences.protein_region_context_models import (
    ProteinFunctionalRegionEvidence,
    ProteinFunctionalRegionKind,
    ProteinPeptideRegionContextReport,
    ProteinPeptideRegionReference,
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
from bijux_proteomics.workflow.cards.protein_evidence.models import (
    _PreparedProteinCard,
)


def build_peptide_region_context_report(
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


def build_identity_entries_by_entity(
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


def build_proteogenomic_support_by_entity(
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


def group_functional_regions_by_protein(
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


def group_ptm_sites_by_protein(
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


def select_ptm_sites(
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


def select_functional_regions(
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


__all__ = [
    "build_identity_entries_by_entity",
    "build_peptide_region_context_report",
    "build_proteogenomic_support_by_entity",
    "group_functional_regions_by_protein",
    "group_ptm_sites_by_protein",
    "select_functional_regions",
    "select_ptm_sites",
]
