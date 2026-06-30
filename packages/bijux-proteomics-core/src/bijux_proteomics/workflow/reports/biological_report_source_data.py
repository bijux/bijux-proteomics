# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Owned parsing and annotation mapping for biological report source inputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics.interpretation.complex_enrichment import (
    ComplexMembershipRecord,
)
from bijux_proteomics.interpretation.pathway_enrichment import (
    PathwayMembershipRecord,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationMappingReport,
    ProteinAnnotationRecord,
    ProteinReferenceEntry,
)
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
)
from bijux_proteomics.sequences.core import NormalizedProteinRecord
from bijux_proteomics.sequences.protein_region_context_models import (
    ProteinRegionContextRecord,
)
from bijux_proteomics.sequences.proteogenomic_peptide_support import (
    ProteogenomicVariantPeptideRecord,
)
from bijux_proteomics.workflow.reports.biological_report_annotation_source_data import (
    _build_biological_annotation_mapping_report,
    _load_biological_complex_membership_records,
    _load_biological_custom_annotation_records,
    _load_biological_pathway_membership_records,
)
from bijux_proteomics.workflow.reports.biological_report_reference_entries import (
    _build_differential_reference_entries,
)
from bijux_proteomics.workflow.reports.biological_report_sequence_source_data import (
    _load_biological_fasta_records,
    _load_biological_protein_region_context_records,
    _load_biological_variant_fasta_records,
    _load_biological_variant_peptide_records,
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
    fasta_records = _load_biological_fasta_records(proteins_fasta_path)
    variant_fasta_records = _load_biological_variant_fasta_records(
        variant_proteins_fasta_path
    )
    variant_peptide_records = _load_biological_variant_peptide_records(
        variant_peptide_tsv_path
    )
    custom_annotation_records = _load_biological_custom_annotation_records(
        annotation_tsv_path
    )
    pathway_records = _load_biological_pathway_membership_records(
        pathway_membership_tsv_path
    )
    complex_records = _load_biological_complex_membership_records(
        complex_membership_tsv_path
    )
    differential_reference_entries = _build_differential_reference_entries(
        differential_report,
        protein_refs_by_entity=normalized_table.entity_protein_refs,
    )
    annotation_report = _build_biological_annotation_mapping_report(
        differential_reference_entries,
        fasta_records,
        custom_annotation_records,
    )
    protein_region_context_records = _load_biological_protein_region_context_records(
        protein_region_context_tsv_path
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
