# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""FragPipe bundle import over PSM, peptide, and protein evidence tables."""

from __future__ import annotations

from collections.abc import Sequence
import csv
from pathlib import Path

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification.contracts import (
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
    parse_target_decoy_label,
)
from bijux_proteomics.identification.rejected_evidence_table import (
    RejectedEvidenceTableEntry,
    build_rejected_evidence_rows_from_psm_rows,
)
from bijux_proteomics.identification.search_adapters.contracts import (
    SearchAdapterKind,
)
from bijux_proteomics.identification.search_adapters.normalization import (
    normalize_search_results_with_adapter,
)
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.identification.adapters.fragpipe_import.models import (
    FragpipeCanonicalPsmEntry,
    FragpipeImportReport,
    FragpipeImportSummary,
    FragpipeOpenSearchEvidenceEntry,
    FragpipePeptideReviewEntry,
    FragpipeProteinQuantityEntry,
    FragpipeProteinReviewEntry,
    FragpipePsmReviewEntry,
)
from bijux_proteomics.identification.adapters.fragpipe_import.psm_rows import (
    build_fragpipe_canonical_psm_rows,
    build_fragpipe_psm_rows,
)
from bijux_proteomics.identification.adapters.fragpipe_import.rendering import (
    render_fragpipe_canonical_psm_tsv,
    render_fragpipe_open_search_evidence_tsv,
    render_fragpipe_peptide_tsv,
    render_fragpipe_protein_quantity_tsv,
    render_fragpipe_protein_tsv,
    render_fragpipe_psm_tsv,
    render_fragpipe_summary_tsv,
)
from bijux_proteomics.identification.adapters.fragpipe_import.table_support import (
    canonical_modified_peptide,
    fragpipe_peptide_entity_id,
    has_modified_content,
    is_open_search_candidate,
    optional_float,
    optional_int,
    optional_text,
    split_multi_value,
)


def build_fragpipe_import_report(
    psm_tsv_path: Path,
    *,
    peptide_tsv_path: Path,
    protein_tsv_path: Path,
    quant_tsv_path: Path | None = None,
    decoy_policy: TargetDecoyLabelPolicy | None = None,
    open_search_mass_tolerance: float = 0.01,
) -> FragpipeImportReport:
    """Import one FragPipe result bundle with explicit table preservation."""
    if open_search_mass_tolerance < 0:
        raise ValueError("open_search_mass_tolerance must be non-negative")
    active_decoy_policy = decoy_policy or TargetDecoyLabelPolicy(
        protein_prefix="DECOY_"
    )
    psm_normalization = normalize_search_results_with_adapter(
        source_path=psm_tsv_path,
        adapter_kind=SearchAdapterKind.MSFRAGGER,
        dialect_id="fragpipe-psm",
    )
    canonical_psms = build_fragpipe_canonical_psm_rows(
        normalization_report=psm_normalization,
        open_search_mass_tolerance=open_search_mass_tolerance,
    )
    psm_rows = build_fragpipe_psm_rows(
        normalization_report=psm_normalization,
        open_search_mass_tolerance=open_search_mass_tolerance,
    )
    peptide_rows = _parse_fragpipe_peptide_table(
        peptide_tsv_path,
        decoy_policy=active_decoy_policy,
        open_search_mass_tolerance=open_search_mass_tolerance,
    )
    protein_rows = _parse_fragpipe_protein_table(
        protein_tsv_path,
        decoy_policy=active_decoy_policy,
    )
    open_search_evidence = _build_fragpipe_open_search_evidence(
        canonical_psms=canonical_psms,
        peptide_rows=peptide_rows,
    )
    protein_quantity_rows = _parse_fragpipe_quant_table(
        quant_tsv_path,
        decoy_policy=active_decoy_policy,
    )
    protein_refs = {
        protein_ref
        for row in peptide_rows
        for protein_ref in row.protein_refs + row.mapped_protein_refs
    }
    summary = FragpipeImportSummary(
        accepted_psm_count=len(psm_rows),
        rejected_psm_count=len(psm_normalization.parse_report.rejected_rows),
        peptide_row_count=len(peptide_rows),
        protein_row_count=len(protein_rows),
        canonical_psm_count=len(canonical_psms),
        peptide_evidence_count=len(peptide_rows),
        protein_reference_count=len(protein_rows),
        open_search_evidence_count=len(open_search_evidence),
        protein_quantity_count=len(protein_quantity_rows),
        modified_psm_count=sum(1 for row in psm_rows if has_modified_content(row)),
        modified_peptide_row_count=sum(
            1 for row in peptide_rows if has_modified_content(row)
        ),
        open_search_psm_count=sum(1 for row in psm_rows if row.open_search_candidate),
        open_search_peptide_count=sum(
            1 for row in peptide_rows if row.open_search_candidate
        ),
        q_value_psm_count=sum(1 for row in psm_rows if row.q_value is not None),
        q_value_peptide_count=sum(1 for row in peptide_rows if row.q_value is not None),
        mapped_protein_count=len(protein_refs),
        target_protein_count=sum(
            1
            for row in protein_rows
            if row.target_decoy_label is TargetDecoyLabel.TARGET
        ),
        decoy_protein_count=sum(
            1
            for row in protein_rows
            if row.target_decoy_label is TargetDecoyLabel.DECOY
        ),
    )
    return FragpipeImportReport(
        psm_normalization=psm_normalization,
        canonical_psms=canonical_psms,
        psm_rows=psm_rows,
        peptide_evidence=peptide_rows,
        peptide_rows=peptide_rows,
        protein_references=protein_rows,
        protein_rows=protein_rows,
        open_search_evidence=open_search_evidence,
        protein_quantity_rows=protein_quantity_rows,
        rejected_evidence_rows=build_rejected_evidence_rows_from_psm_rows(
            psm_normalization.parse_report.rejected_rows,
            source_file=psm_tsv_path.name,
            entity_type="psm",
            entity_id_columns=("Spectrum", "Modified Peptide", "Peptide"),
        ),
        summary=summary,
    )
def _parse_fragpipe_peptide_table(
    path: Path,
    *,
    decoy_policy: TargetDecoyLabelPolicy,
    open_search_mass_tolerance: float,
) -> tuple[FragpipePeptideReviewEntry, ...]:
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


def _parse_fragpipe_protein_table(
    path: Path,
    *,
    decoy_policy: TargetDecoyLabelPolicy,
) -> tuple[FragpipeProteinReviewEntry, ...]:
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


def _build_fragpipe_open_search_evidence(
    *,
    canonical_psms: tuple[FragpipeCanonicalPsmEntry, ...],
    peptide_rows: tuple[FragpipePeptideReviewEntry, ...],
) -> tuple[FragpipeOpenSearchEvidenceEntry, ...]:
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


def _parse_fragpipe_quant_table(
    path: Path | None,
    *,
    decoy_policy: TargetDecoyLabelPolicy,
) -> tuple[FragpipeProteinQuantityEntry, ...]:
    if path is None:
        return ()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("FragPipe quant table must include a header row")
        if "Protein" not in reader.fieldnames:
            raise ValueError("missing required FragPipe quant column 'Protein'")
        quant_columns = _fragpipe_quant_columns(reader.fieldnames)
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


def _fragpipe_quant_columns(
    fieldnames: Sequence[str],
) -> tuple[tuple[str, str, str], ...]:
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
