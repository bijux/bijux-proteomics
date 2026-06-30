# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein and gene member resolution for complex activity scoring."""

from __future__ import annotations

from collections import defaultdict
import math

import numpy as np

from bijux_proteomics.interpretation.complex_enrichment import (
    ComplexMemberKind,
    ComplexMembershipRecord,
)
from bijux_proteomics.interpretation.complex_activity.models import (
    UnresolvedComplexActivityMemberEntry,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationRecord,
)
from bijux_proteomics.quantification.contracts.matrix_building import (
    _matrix_value_index,
)
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable
from bijux_proteomics.sequences.fasta import canonicalize_protein_reference
from bijux_proteomics.sequences.core import NormalizedProteinRecord

ComplexMemberSpec = tuple[ComplexMemberKind, str, tuple[str, ...]]


def group_complex_records(
    complex_records: tuple[ComplexMembershipRecord, ...],
) -> dict[str, list[ComplexMembershipRecord]]:
    """Group complex membership records by owned complex identifier."""

    grouped: dict[str, list[ComplexMembershipRecord]] = {}
    for record in complex_records:
        grouped.setdefault(record.complex_id, []).append(record)
    return grouped


def protein_refs_in_table(table: LabelFreeQuantTable) -> tuple[str, ...]:
    """Return canonical protein references represented by the quantification table."""

    protein_refs: list[str] = []
    for entity_id in table.entity_ids:
        protein_refs.extend(
            table.entity_protein_refs.get(entity_id, ()) or (entity_id,)
        )
    return tuple(
        dict.fromkeys(canonicalize_protein_reference(ref) for ref in protein_refs)
    )


def standardized_protein_ref_values(
    table: LabelFreeQuantTable,
) -> dict[tuple[str, str], float | None]:
    """Standardize protein abundance values and aggregate them by protein reference."""

    value_lookup = _matrix_value_index(table)
    entity_standardized: dict[tuple[str, str], float | None] = {}
    for entity_id in table.entity_ids:
        observed_values: list[float] = []
        sample_values: dict[str, float | None] = {}
        for sample_id in table.sample_ids:
            abundance = value_lookup[(entity_id, sample_id)].abundance
            if abundance is None:
                sample_values[sample_id] = None
                continue
            log_value = math.log2(float(abundance) + 1.0)
            sample_values[sample_id] = log_value
            observed_values.append(log_value)
        if not observed_values:
            for sample_id in table.sample_ids:
                entity_standardized[(entity_id, sample_id)] = None
            continue
        mean_value = float(np.mean(observed_values))
        std_value = float(np.std(observed_values))
        for sample_id in table.sample_ids:
            value = sample_values[sample_id]
            if value is None:
                entity_standardized[(entity_id, sample_id)] = None
            elif std_value <= 1e-12:
                entity_standardized[(entity_id, sample_id)] = 0.0
            else:
                entity_standardized[(entity_id, sample_id)] = (
                    value - mean_value
                ) / std_value

    protein_ref_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    for entity_id in table.entity_ids:
        protein_refs = table.entity_protein_refs.get(entity_id, ()) or (entity_id,)
        for protein_ref in protein_refs:
            canonical_ref = canonicalize_protein_reference(protein_ref)
            for sample_id in table.sample_ids:
                value = entity_standardized[(entity_id, sample_id)]
                if value is not None:
                    protein_ref_values[(canonical_ref, sample_id)].append(value)

    aggregated: dict[tuple[str, str], float | None] = {}
    for protein_ref in protein_refs_in_table(table):
        for sample_id in table.sample_ids:
            values = protein_ref_values.get((protein_ref, sample_id), [])
            aggregated[(protein_ref, sample_id)] = (
                round(float(np.mean(values)), 6) if values else None
            )
    return aggregated


def protein_gene_annotations(
    *,
    fasta_records: tuple[NormalizedProteinRecord, ...],
    custom_annotations: tuple[ProteinAnnotationRecord, ...],
) -> dict[str, tuple[str, ...]]:
    """Collect canonical protein-to-gene annotations from sequence and custom input."""

    annotations: dict[str, set[str]] = {}
    for fasta_record in fasta_records:
        if fasta_record.gene:
            annotations.setdefault(fasta_record.canonical_accession, set()).add(
                fasta_record.gene
            )
    for annotation_record in custom_annotations:
        if annotation_record.gene_symbol:
            annotations.setdefault(annotation_record.protein_ref, set()).add(
                annotation_record.gene_symbol
            )
    return {
        canonicalize_protein_reference(protein_ref): tuple(sorted(gene_symbols))
        for protein_ref, gene_symbols in annotations.items()
    }


def gene_to_protein_refs(
    *,
    available_protein_refs: set[str],
    gene_annotations: dict[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    """Build the observed protein lookup for each annotated gene symbol."""

    gene_to_proteins: dict[str, set[str]] = {}
    for protein_ref in sorted(available_protein_refs):
        for gene_symbol in gene_annotations.get(protein_ref, ()):
            gene_to_proteins.setdefault(gene_symbol, set()).add(protein_ref)
    return {
        gene_symbol: tuple(sorted(protein_refs))
        for gene_symbol, protein_refs in gene_to_proteins.items()
    }


def build_member_specs(
    records: list[ComplexMembershipRecord],
    *,
    available_protein_refs: set[str],
    gene_to_proteins: dict[str, tuple[str, ...]],
    unresolved_members: list[UnresolvedComplexActivityMemberEntry],
) -> tuple[ComplexMemberSpec, ...]:
    """Resolve each unique complex member onto observed protein references."""

    first = records[0]
    member_specs: list[ComplexMemberSpec] = []
    seen_members: set[tuple[str, str]] = set()
    for record in records:
        member_key = (record.member_kind.value, record.member_id)
        if member_key in seen_members:
            continue
        seen_members.add(member_key)
        resolved_protein_refs: tuple[str, ...]
        if record.member_kind is ComplexMemberKind.PROTEIN:
            canonical_ref = canonicalize_protein_reference(record.member_id)
            resolved_protein_refs = (
                (canonical_ref,) if canonical_ref in available_protein_refs else ()
            )
        else:
            resolved_protein_refs = gene_to_proteins.get(record.member_id, ())
        if not resolved_protein_refs:
            unresolved_members.append(
                UnresolvedComplexActivityMemberEntry(
                    complex_id=record.complex_id,
                    complex_name=first.complex_name,
                    source_name=first.source_name,
                    source_accession=first.source_accession,
                    member_kind=record.member_kind,
                    member_id=record.member_id,
                    reason=(
                        "complex protein member was not present in the quantification table"
                        if record.member_kind is ComplexMemberKind.PROTEIN
                        else "complex gene member could not be resolved onto observed proteins"
                    ),
                )
            )
        member_specs.append(
            (record.member_kind, record.member_id, tuple(sorted(resolved_protein_refs)))
        )
    return tuple(member_specs)


def member_label(member_kind: ComplexMemberKind, member_id: str) -> str:
    """Return the stable rendered label for one complex member."""

    return f"{member_kind.value}:{member_id}"
