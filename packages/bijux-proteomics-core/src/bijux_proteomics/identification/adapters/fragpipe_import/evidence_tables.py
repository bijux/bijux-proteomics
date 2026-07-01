# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Peptide, protein, and quantity table parsing for FragPipe imports."""

from __future__ import annotations

from collections.abc import Sequence
import csv
from pathlib import Path

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification.adapters.fragpipe_import.models import (
    FragpipeCanonicalPsmEntry,
    FragpipeOpenSearchEvidenceEntry,
    FragpipePeptideReviewEntry,
    FragpipeProteinQuantityEntry,
    FragpipeProteinReviewEntry,
)
from bijux_proteomics.identification.adapters.fragpipe_import.table_support import (
    canonical_modified_peptide,
    fragpipe_peptide_entity_id,
    is_open_search_candidate,
    optional_float,
    optional_int,
    optional_text,
    split_multi_value,
)
from bijux_proteomics.identification.contracts import (
    TargetDecoyLabelPolicy,
    parse_target_decoy_label,
)


def parse_fragpipe_peptide_table(
    path: Path,
    *,
    decoy_policy: TargetDecoyLabelPolicy,
    open_search_mass_tolerance: float,
) -> tuple[FragpipePeptideReviewEntry, ...]:
    """Parse the FragPipe peptide table into reviewer-facing peptide evidence rows."""
    del decoy_policy
    required = ("Peptide", "Modified Peptide", "Protein")
    rows: list[FragpipePeptideReviewEntry] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("FragPipe peptide table must include a header row")
        for column in required:
            if column not in reader.fieldnames:
                raise ValueError(f"missing required FragPipe peptide column {column!r}")
        for row_number, row in enumerate(reader, start=2):
            peptide = str(row.get("Peptide", "")).strip()
            modified_peptide = str(row.get("Modified Peptide", "")).strip() or None
            mass_difference = optional_float(row.get("Mass Difference"))
            proteins = split_multi_value(row.get("Protein"))
            mapped_proteins = split_multi_value(row.get("Mapped Proteins"))
            rows.append(
                FragpipePeptideReviewEntry(
                    peptide=peptide,
                    modified_peptide=modified_peptide,
                    canonical_modified_peptide=canonical_modified_peptide(
                        modified_peptide
                    ),
                    charge=optional_int(row.get("Charge")),
                    protein_refs=proteins,
                    mapped_protein_refs=mapped_proteins,
                    assigned_modifications=split_multi_value(
                        row.get("Assigned Modifications")
                    ),
                    observed_modifications=split_multi_value(
                        row.get("Observed Modifications")
                    ),
                    hyperscore=optional_float(row.get("Hyperscore")),
                    probability=optional_float(row.get("Probability")),
                    q_value=optional_float(row.get("QValue")),
                    spectral_count=optional_int(row.get("Spectral Count")),
                    mass_difference=mass_difference,
                    open_search_candidate=is_open_search_candidate(
                        mass_difference,
                        tolerance=open_search_mass_tolerance,
                    ),
                    provenance=ImportedEvidenceProvenance.from_single_row(
                        source_engine="fragpipe-peptide",
                        source_file=str(path),
                        source_row_number=row_number,
                        original_identifiers={
                            "peptide": peptide,
                            "modified_peptide": modified_peptide or peptide,
                        },
                    ),
                )
            )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.q_value if row.q_value is not None else float("inf"),
                -(row.hyperscore or 0.0),
                row.peptide,
            ),
        )
    )


def parse_fragpipe_protein_table(
    path: Path,
    *,
    decoy_policy: TargetDecoyLabelPolicy,
) -> tuple[FragpipeProteinReviewEntry, ...]:
    """Parse the FragPipe protein table into reviewer-facing protein rows."""
    required = ("Protein",)
    rows: list[FragpipeProteinReviewEntry] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("FragPipe protein table must include a header row")
        for column in required:
            if column not in reader.fieldnames:
                raise ValueError(f"missing required FragPipe protein column {column!r}")
        for row_number, row in enumerate(reader, start=2):
            protein_ref = str(row.get("Protein", "")).strip()
            rows.append(
                FragpipeProteinReviewEntry(
                    protein_ref=protein_ref,
                    entry_name=optional_text(row.get("Entry Name")),
                    gene_name=optional_text(row.get("Gene")),
                    description=optional_text(row.get("Protein Description")),
                    coverage_fraction=optional_float(row.get("Coverage")),
                    total_peptides=optional_int(row.get("Total Peptides")),
                    unique_peptides=optional_int(row.get("Unique Peptides")),
                    spectral_count=optional_int(row.get("Spectral Count")),
                    probability=optional_float(row.get("Probability")),
                    target_decoy_label=parse_target_decoy_label(
                        protein_refs=(protein_ref,),
                        explicit_label=None,
                        policy=decoy_policy,
                    ),
                    provenance=ImportedEvidenceProvenance.from_single_row(
                        source_engine="fragpipe-protein",
                        source_file=str(path),
                        source_row_number=row_number,
                        original_identifiers={"protein_ref": protein_ref},
                    ),
                )
            )
    return tuple(sorted(rows, key=lambda row: row.protein_ref))


def build_fragpipe_open_search_evidence(
    *,
    canonical_psms: tuple[FragpipeCanonicalPsmEntry, ...],
    peptide_rows: tuple[FragpipePeptideReviewEntry, ...],
) -> tuple[FragpipeOpenSearchEvidenceEntry, ...]:
    """Build preserved open-search evidence from FragPipe PSM and peptide rows."""
    rows: list[FragpipeOpenSearchEvidenceEntry] = []
    for row in canonical_psms:
        if not row.open_search_candidate or row.mass_difference is None:
            continue
        rows.append(
            FragpipeOpenSearchEvidenceEntry(
                entity_kind="psm",
                entity_id=row.record.spectrum_id,
                peptide=row.record.peptide,
                canonical_peptide=row.record.canonical_peptide,
                modified_peptide=row.record.modified_peptide,
                canonical_modified_peptide=row.record.modified_peptide,
                mass_difference=row.mass_difference,
            )
        )
    for peptide_row in peptide_rows:
        if not peptide_row.open_search_candidate or peptide_row.mass_difference is None:
            continue
        rows.append(
            FragpipeOpenSearchEvidenceEntry(
                entity_kind="peptide",
                entity_id=fragpipe_peptide_entity_id(
                    peptide=peptide_row.peptide,
                    modified_peptide=peptide_row.modified_peptide,
                    charge=peptide_row.charge,
                ),
                peptide=peptide_row.peptide,
                canonical_peptide=peptide_row.peptide,
                modified_peptide=peptide_row.modified_peptide,
                canonical_modified_peptide=peptide_row.canonical_modified_peptide,
                mass_difference=peptide_row.mass_difference,
            )
        )
    return tuple(sorted(rows, key=lambda row: (row.entity_kind, row.entity_id)))


def parse_fragpipe_quant_table(
    path: Path | None,
    *,
    decoy_policy: TargetDecoyLabelPolicy,
) -> tuple[FragpipeProteinQuantityEntry, ...]:
    """Parse the optional FragPipe protein-quantity table into quantity rows."""
    if path is None:
        return ()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("FragPipe quant table must include a header row")
        if "Protein" not in reader.fieldnames:
            raise ValueError("missing required FragPipe quant column 'Protein'")
        quant_columns = fragpipe_quant_columns(reader.fieldnames)
        if not quant_columns:
            raise ValueError(
                "FragPipe quant table must include at least one supported abundance column"
            )
        rows: list[FragpipeProteinQuantityEntry] = []
        for row_number, raw_row in enumerate(reader, start=2):
            protein_ref = str(raw_row.get("Protein", "")).strip()
            label = parse_target_decoy_label(
                protein_refs=(protein_ref,),
                explicit_label=None,
                policy=decoy_policy,
            )
            for column_name, quantity_kind, sample_id in quant_columns:
                abundance = optional_float(raw_row.get(column_name))
                if abundance is None:
                    continue
                rows.append(
                    FragpipeProteinQuantityEntry(
                        protein_ref=protein_ref,
                        sample_id=sample_id,
                        abundance=abundance,
                        quantity_kind=quantity_kind,
                        target_decoy_label=label,
                        provenance=ImportedEvidenceProvenance.from_single_row(
                            source_engine="fragpipe-quant",
                            source_file=str(path),
                            source_row_number=row_number,
                            original_identifiers={
                                "protein_ref": protein_ref,
                                "sample_id": sample_id,
                                "quantity_kind": quantity_kind,
                            },
                        ),
                    )
                )
    return tuple(sorted(rows, key=lambda row: (row.protein_ref, row.sample_id)))


def fragpipe_quant_columns(
    fieldnames: Sequence[str],
) -> tuple[tuple[str, str, str], ...]:
    """Discover supported quantity columns from a FragPipe quant table header."""
    prefix_map = (
        ("MaxLFQ Intensity ", "maxlfq_intensity"),
        ("Intensity ", "intensity"),
        ("Abundance ", "abundance"),
    )
    columns: list[tuple[str, str, str]] = []
    for field_name in fieldnames:
        for prefix, quantity_kind in prefix_map:
            if field_name.startswith(prefix):
                sample_id = field_name.removeprefix(prefix).strip()
                if sample_id:
                    columns.append((field_name, quantity_kind, sample_id))
                break
    return tuple(columns)


__all__ = [
    "build_fragpipe_open_search_evidence",
    "fragpipe_quant_columns",
    "parse_fragpipe_peptide_table",
    "parse_fragpipe_protein_table",
    "parse_fragpipe_quant_table",
]
