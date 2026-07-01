# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Sequence-derived source inputs for biological report bundles."""

from __future__ import annotations

from pathlib import Path

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


def _load_biological_fasta_records(
    proteins_fasta_path: Path,
) -> tuple[NormalizedProteinRecord, ...]:
    return _parse_strict_fasta_records(
        proteins_fasta_path,
        rejected_message_prefix="FASTA input contains rejected records under strict mode",
    )


def _load_biological_variant_fasta_records(
    variant_proteins_fasta_path: Path | None,
) -> tuple[NormalizedProteinRecord, ...]:
    if variant_proteins_fasta_path is None:
        return ()
    return _parse_strict_fasta_records(
        variant_proteins_fasta_path,
        rejected_message_prefix=(
            "variant FASTA input contains rejected records under strict mode"
        ),
    )


def _load_biological_variant_peptide_records(
    variant_peptide_tsv_path: Path | None,
) -> tuple[ProteogenomicVariantPeptideRecord, ...]:
    if variant_peptide_tsv_path is None:
        return ()

    variant_peptide_report = parse_proteogenomic_variant_peptide_table(
        variant_peptide_tsv_path
    )
    if variant_peptide_report.rejected_rows:
        rejected = "; ".join(
            row.reason for row in variant_peptide_report.rejected_rows[:3]
        )
        raise ValueError("variant peptide table contains rejected rows: " + rejected)
    return variant_peptide_report.accepted_records


def _load_biological_protein_region_context_records(
    protein_region_context_tsv_path: Path | None,
) -> tuple[ProteinRegionContextRecord, ...] | None:
    if protein_region_context_tsv_path is None:
        return None
    return parse_protein_region_context_tsv(
        protein_region_context_tsv_path
    ).accepted_records


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


__all__ = [
    "_load_biological_fasta_records",
    "_load_biological_protein_region_context_records",
    "_load_biological_variant_fasta_records",
    "_load_biological_variant_peptide_records",
]
