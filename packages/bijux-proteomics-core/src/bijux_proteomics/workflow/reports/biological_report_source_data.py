# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Owned parsing and annotation mapping for biological report source inputs."""

from __future__ import annotations

from dataclasses import dataclass
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
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
)
from bijux_proteomics.sequences.core import NormalizedProteinRecord
from bijux_proteomics.sequences.fasta import FastaParseMode, parse_fasta_document
from bijux_proteomics.sequences.protein_region_context_models import (
    ProteinRegionContextRecord,
)
from bijux_proteomics.sequences.protein_region_context_workflows import (
    parse_protein_region_context_tsv,
)
from bijux_proteomics.sequences.proteogenomic_peptide_support import (
    ProteogenomicVariantPeptideRecord,
    parse_proteogenomic_variant_peptide_table,
)
from bijux_proteomics.workflow.reports.biological_report_selection import (
    _build_differential_reference_entries,
)


@dataclass(frozen=True, slots=True)
class BiologicalReportSourceData:
    """Parsed source inputs and annotation mapping for one biological report bundle."""

    fasta_records: tuple[NormalizedProteinRecord, ...]
    variant_fasta_records: tuple[NormalizedProteinRecord, ...]
    variant_peptide_records: tuple[ProteogenomicVariantPeptideRecord, ...]
    custom_annotation_records: tuple[ProteinAnnotationRecord, ...]
    pathway_records: tuple[PathwayMembershipRecord, ...]
    complex_records: tuple[ComplexMembershipRecord, ...]
    differential_reference_entries: tuple[ProteinReferenceEntry, ...]
    annotation_report: ProteinAnnotationMappingReport
    protein_region_context_records: tuple[ProteinRegionContextRecord, ...] | None


def _build_biological_report_source_data(
    *,
    normalized_table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    proteins_fasta_path: Path,
    variant_proteins_fasta_path: Path | None,
    variant_peptide_tsv_path: Path | None,
    annotation_tsv_path: Path | None,
    pathway_membership_tsv_path: Path | None,
    complex_membership_tsv_path: Path | None,
    protein_region_context_tsv_path: Path | None,
) -> BiologicalReportSourceData:
    fasta_records = _parse_strict_fasta_records(
        proteins_fasta_path,
        rejected_message_prefix="FASTA input contains rejected records under strict mode",
    )
    variant_fasta_records: tuple[NormalizedProteinRecord, ...] = ()
    if variant_proteins_fasta_path is not None:
        variant_fasta_records = _parse_strict_fasta_records(
            variant_proteins_fasta_path,
            rejected_message_prefix=(
                "variant FASTA input contains rejected records under strict mode"
            ),
        )

    variant_peptide_records: tuple[ProteogenomicVariantPeptideRecord, ...] = ()
    if variant_peptide_tsv_path is not None:
        variant_peptide_report = parse_proteogenomic_variant_peptide_table(
            variant_peptide_tsv_path
        )
        if variant_peptide_report.rejected_rows:
            rejected = "; ".join(
                row.reason for row in variant_peptide_report.rejected_rows[:3]
            )
            raise ValueError(
                "variant peptide table contains rejected rows: " + rejected
            )
        variant_peptide_records = variant_peptide_report.accepted_records

    custom_annotation_records: tuple[ProteinAnnotationRecord, ...] = ()
    if annotation_tsv_path is not None:
        custom_annotation_records = parse_protein_annotation_table(
            annotation_tsv_path,
            mapping=ProteinAnnotationColumnMapping(
                protein_ref="protein_ref",
                gene_symbol="gene_symbol",
                description="description",
                organism="organism",
                annotation_identifier="annotation_identifier",
            ),
        ).accepted_records

    pathway_records = (
        ()
        if pathway_membership_tsv_path is None
        else parse_pathway_membership_table(pathway_membership_tsv_path).accepted_records
    )
    complex_records = (
        ()
        if complex_membership_tsv_path is None
        else parse_complex_membership_table(complex_membership_tsv_path).accepted_records
    )
    differential_reference_entries = _build_differential_reference_entries(
        differential_report,
        protein_refs_by_entity=normalized_table.entity_protein_refs,
    )
    annotation_report = build_protein_annotation_mapping_report(
        differential_reference_entries,
        fasta_records,
        custom_annotations=custom_annotation_records,
    )
    protein_region_context_records = (
        None
        if protein_region_context_tsv_path is None
        else parse_protein_region_context_tsv(protein_region_context_tsv_path).accepted_records
    )

    return BiologicalReportSourceData(
        fasta_records=fasta_records,
        variant_fasta_records=variant_fasta_records,
        variant_peptide_records=variant_peptide_records,
        custom_annotation_records=custom_annotation_records,
        pathway_records=pathway_records,
        complex_records=complex_records,
        differential_reference_entries=differential_reference_entries,
        annotation_report=annotation_report,
        protein_region_context_records=protein_region_context_records,
    )


def _parse_strict_fasta_records(
    fasta_path: Path, *, rejected_message_prefix: str
) -> tuple[NormalizedProteinRecord, ...]:
    fasta_report = parse_fasta_document(
        fasta_path.read_text(encoding="utf-8"),
        mode=FastaParseMode.STRICT,
    )
    if fasta_report.rejected_records:
        rejected = ", ".join(
            record.source_identifier for record in fasta_report.rejected_records
        )
        raise ValueError(f"{rejected_message_prefix}: {rejected}")
    return fasta_report.accepted_records
