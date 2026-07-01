# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Annotation and membership source inputs for biological report bundles."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation.complex_enrichment import (
    ComplexMembershipRecord,
    parse_complex_membership_table,
)
from bijux_proteomics.interpretation.pathway_enrichment import (
    PathwayMembershipRecord,
    parse_pathway_membership_table,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationColumnMapping,
    ProteinAnnotationMappingReport,
    ProteinAnnotationRecord,
    ProteinReferenceEntry,
    build_protein_annotation_mapping_report,
    parse_protein_annotation_table,
)
from bijux_proteomics.sequences.core import NormalizedProteinRecord


def _load_biological_custom_annotation_records(
    annotation_tsv_path: Path | None,
) -> tuple[ProteinAnnotationRecord, ...]:
    if annotation_tsv_path is None:
        return ()
    return parse_protein_annotation_table(
        annotation_tsv_path,
        mapping=ProteinAnnotationColumnMapping(
            protein_ref="protein_ref",
            gene_symbol="gene_symbol",
            description="description",
            organism="organism",
            annotation_identifier="annotation_identifier",
        ),
    ).accepted_records


def _load_biological_pathway_membership_records(
    pathway_membership_tsv_path: Path | None,
) -> tuple[PathwayMembershipRecord, ...]:
    if pathway_membership_tsv_path is None:
        return ()
    return parse_pathway_membership_table(pathway_membership_tsv_path).accepted_records


def _load_biological_complex_membership_records(
    complex_membership_tsv_path: Path | None,
) -> tuple[ComplexMembershipRecord, ...]:
    if complex_membership_tsv_path is None:
        return ()
    return parse_complex_membership_table(complex_membership_tsv_path).accepted_records


def _build_biological_annotation_mapping_report(
    differential_reference_entries: tuple[ProteinReferenceEntry, ...],
    fasta_records: tuple[NormalizedProteinRecord, ...],
    custom_annotation_records: tuple[ProteinAnnotationRecord, ...],
) -> ProteinAnnotationMappingReport:
    return build_protein_annotation_mapping_report(
        differential_reference_entries,
        fasta_records,
        custom_annotations=custom_annotation_records,
    )


__all__ = [
    "_build_biological_annotation_mapping_report",
    "_load_biological_complex_membership_records",
    "_load_biological_custom_annotation_records",
    "_load_biological_pathway_membership_records",
]
