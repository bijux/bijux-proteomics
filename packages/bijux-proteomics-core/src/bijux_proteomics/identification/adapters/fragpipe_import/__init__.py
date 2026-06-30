# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""FragPipe bundle import over PSM, peptide, and protein evidence tables."""

from __future__ import annotations

from collections.abc import Sequence
import csv
from pathlib import Path

from bijux_proteomics.chemistry.modified_peptide_parser import (
    SearchEngineModifiedPeptideDialect,
    build_search_engine_modified_peptide_report,
)
from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification.contracts import (
    PsmRecord,
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
    SearchAdapterNormalizationReport,
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
    canonical_psms = _build_fragpipe_canonical_psm_rows(
        normalization_report=psm_normalization,
        open_search_mass_tolerance=open_search_mass_tolerance,
    )
    psm_rows = _build_fragpipe_psm_rows(
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
        modified_psm_count=sum(1 for row in psm_rows if _has_modified_content(row)),
        modified_peptide_row_count=sum(
            1 for row in peptide_rows if _has_modified_content(row)
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


def render_fragpipe_summary_tsv(summary: FragpipeImportSummary) -> str:
    """Render the one-row FragPipe bundle summary as TSV."""
    header = (
        "accepted_psm_count",
        "rejected_psm_count",
        "peptide_row_count",
        "protein_row_count",
        "canonical_psm_count",
        "peptide_evidence_count",
        "protein_reference_count",
        "open_search_evidence_count",
        "protein_quantity_count",
        "modified_psm_count",
        "modified_peptide_row_count",
        "open_search_psm_count",
        "open_search_peptide_count",
        "q_value_psm_count",
        "q_value_peptide_count",
        "mapped_protein_count",
        "target_protein_count",
        "decoy_protein_count",
    )
    row = (
        str(summary.accepted_psm_count),
        str(summary.rejected_psm_count),
        str(summary.peptide_row_count),
        str(summary.protein_row_count),
        str(summary.canonical_psm_count),
        str(summary.peptide_evidence_count),
        str(summary.protein_reference_count),
        str(summary.open_search_evidence_count),
        str(summary.protein_quantity_count),
        str(summary.modified_psm_count),
        str(summary.modified_peptide_row_count),
        str(summary.open_search_psm_count),
        str(summary.open_search_peptide_count),
        str(summary.q_value_psm_count),
        str(summary.q_value_peptide_count),
        str(summary.mapped_protein_count),
        str(summary.target_protein_count),
        str(summary.decoy_protein_count),
    )
    return "\t".join(header) + "\n" + "\t".join(row) + "\n"


def render_fragpipe_canonical_psm_tsv(
    rows: tuple[FragpipeCanonicalPsmEntry, ...],
) -> str:
    """Render canonical FragPipe PSM rows as TSV."""

    ordered_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                row.record.spectrum_id,
                row.record.charge,
                row.record.canonical_peptide,
            ),
        )
    )
    lines = [
        "\t".join(
            (
                "run_id",
                "spectrum_id",
                "peptide",
                "peptide_sequence",
                "modified_peptide",
                "canonical_peptide",
                "charge",
                "score",
                "q_value",
                "protein_refs",
                "target_decoy_label",
                "contaminant_flag",
                "assigned_modifications",
                "observed_modifications",
                "mass_difference",
                "open_search_candidate",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.record.run_id or "",
                    row.record.spectrum_id,
                    row.record.peptide,
                    row.record.peptide_sequence or "",
                    row.record.modified_peptide or "",
                    row.record.canonical_peptide,
                    str(row.record.charge),
                    f"{row.record.score:.6g}",
                    "" if row.record.q_value is None else f"{row.record.q_value:.6g}",
                    ";".join(sort_strings(row.record.protein_refs)),
                    row.record.target_decoy_label.value,
                    "1" if row.record.contaminant_flag else "0",
                    ";".join(sort_strings(row.assigned_modifications)),
                    ";".join(sort_strings(row.observed_modifications)),
                    "" if row.mass_difference is None else f"{row.mass_difference:.6g}",
                    "1" if row.open_search_candidate else "0",
                    *(
                        row.record.provenance.to_tsv_cells()
                        if row.record.provenance
                        else ("", "", "", "")
                    ),
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_fragpipe_psm_tsv(rows: tuple[FragpipePsmReviewEntry, ...]) -> str:
    """Render reviewer-facing FragPipe PSM rows as TSV."""
    ordered_rows = sort_rows_by_fields(
        rows,
        "spectrum_id",
        "charge",
        "canonical_peptide",
    )
    lines = [
        "\t".join(
            (
                "spectrum_id",
                "peptide",
                "canonical_peptide",
                "modified_peptide",
                "canonical_modified_peptide",
                "charge",
                "hyperscore",
                "q_value",
                "protein_refs",
                "target_decoy_label",
                "assigned_modifications",
                "observed_modifications",
                "mass_difference",
                "open_search_candidate",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.spectrum_id,
                    row.peptide,
                    row.canonical_peptide,
                    row.modified_peptide or "",
                    row.canonical_modified_peptide or "",
                    str(row.charge),
                    f"{row.hyperscore:.6g}",
                    "" if row.q_value is None else f"{row.q_value:.6g}",
                    ";".join(sort_strings(row.protein_refs)),
                    row.target_decoy_label.value,
                    ";".join(sort_strings(row.assigned_modifications)),
                    ";".join(sort_strings(row.observed_modifications)),
                    "" if row.mass_difference is None else f"{row.mass_difference:.6g}",
                    "1" if row.open_search_candidate else "0",
                    *row.provenance.to_tsv_cells(),
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_fragpipe_peptide_tsv(rows: tuple[FragpipePeptideReviewEntry, ...]) -> str:
    """Render reviewer-facing FragPipe peptide rows as TSV."""
    ordered_rows = sort_rows_by_fields(
        rows,
        "peptide",
        "canonical_modified_peptide",
        "charge",
    )
    lines = [
        "\t".join(
            (
                "peptide",
                "modified_peptide",
                "canonical_modified_peptide",
                "charge",
                "protein_refs",
                "mapped_protein_refs",
                "assigned_modifications",
                "observed_modifications",
                "hyperscore",
                "probability",
                "q_value",
                "spectral_count",
                "mass_difference",
                "open_search_candidate",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.peptide,
                    row.modified_peptide or "",
                    row.canonical_modified_peptide or "",
                    "" if row.charge is None else str(row.charge),
                    ";".join(sort_strings(row.protein_refs)),
                    ";".join(sort_strings(row.mapped_protein_refs)),
                    ";".join(sort_strings(row.assigned_modifications)),
                    ";".join(sort_strings(row.observed_modifications)),
                    "" if row.hyperscore is None else f"{row.hyperscore:.6g}",
                    "" if row.probability is None else f"{row.probability:.6g}",
                    "" if row.q_value is None else f"{row.q_value:.6g}",
                    "" if row.spectral_count is None else str(row.spectral_count),
                    "" if row.mass_difference is None else f"{row.mass_difference:.6g}",
                    "1" if row.open_search_candidate else "0",
                    *row.provenance.to_tsv_cells(),
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_fragpipe_protein_tsv(rows: tuple[FragpipeProteinReviewEntry, ...]) -> str:
    """Render reviewer-facing FragPipe protein rows as TSV."""
    ordered_rows = sort_rows_by_fields(rows, "protein_ref")
    lines = [
        "\t".join(
            (
                "protein_ref",
                "entry_name",
                "gene_name",
                "description",
                "coverage_fraction",
                "total_peptides",
                "unique_peptides",
                "spectral_count",
                "probability",
                "target_decoy_label",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.protein_ref,
                    row.entry_name or "",
                    row.gene_name or "",
                    row.description or "",
                    ""
                    if row.coverage_fraction is None
                    else f"{row.coverage_fraction:.6g}",
                    "" if row.total_peptides is None else str(row.total_peptides),
                    "" if row.unique_peptides is None else str(row.unique_peptides),
                    "" if row.spectral_count is None else str(row.spectral_count),
                    "" if row.probability is None else f"{row.probability:.6g}",
                    row.target_decoy_label.value,
                    *row.provenance.to_tsv_cells(),
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_fragpipe_open_search_evidence_tsv(
    rows: tuple[FragpipeOpenSearchEvidenceEntry, ...],
) -> str:
    """Render preserved FragPipe open-search evidence rows as TSV."""

    ordered_rows = sort_rows_by_fields(rows, "entity_kind", "entity_id")
    lines = [
        "\t".join(
            (
                "entity_kind",
                "entity_id",
                "peptide",
                "canonical_peptide",
                "modified_peptide",
                "canonical_modified_peptide",
                "mass_difference",
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.entity_kind,
                    row.entity_id,
                    row.peptide,
                    row.canonical_peptide,
                    row.modified_peptide or "",
                    row.canonical_modified_peptide or "",
                    f"{row.mass_difference:.6g}",
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_fragpipe_protein_quantity_tsv(
    rows: tuple[FragpipeProteinQuantityEntry, ...],
) -> str:
    """Render optional FragPipe protein-quantity rows as TSV."""

    ordered_rows = sort_rows_by_fields(rows, "protein_ref", "sample_id")
    lines = [
        "\t".join(
            (
                "protein_ref",
                "sample_id",
                "abundance",
                "quantity_kind",
                "target_decoy_label",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.protein_ref,
                    row.sample_id,
                    f"{row.abundance:.6g}",
                    row.quantity_kind,
                    row.target_decoy_label.value,
                    *row.provenance.to_tsv_cells(),
                )
            )
        )
    return "\n".join(lines) + "\n"


def _build_fragpipe_canonical_psm_rows(
    *,
    normalization_report: SearchAdapterNormalizationReport,
    open_search_mass_tolerance: float,
) -> tuple[FragpipeCanonicalPsmEntry, ...]:
    accepted_rows = tuple(
        row
        for row in normalization_report.evidence_rows
        if row.accepted and row.normalized_record
    )
    rows: list[FragpipeCanonicalPsmEntry] = []
    for row in accepted_rows:
        record = row.normalized_record
        if record is None:
            continue
        raw = row.raw_fields
        mass_difference = _optional_float(raw.get("Mass Difference"))
        rows.append(
            FragpipeCanonicalPsmEntry(
                record=record,
                assigned_modifications=_split_multi_value(
                    raw.get("Assigned Modifications")
                ),
                observed_modifications=_split_multi_value(
                    raw.get("Observed Modifications")
                ),
                mass_difference=mass_difference,
                open_search_candidate=_is_open_search_candidate(
                    mass_difference,
                    tolerance=open_search_mass_tolerance,
                ),
            )
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.record.spectrum_id,
                row.record.q_value if row.record.q_value is not None else float("inf"),
                -row.record.score,
            ),
        )
    )


def _build_fragpipe_psm_rows(
    *,
    normalization_report: SearchAdapterNormalizationReport,
    open_search_mass_tolerance: float,
) -> tuple[FragpipePsmReviewEntry, ...]:
    accepted_rows = tuple(
        row
        for row in normalization_report.evidence_rows
        if row.accepted and row.normalized_record
    )
    rows: list[FragpipePsmReviewEntry] = []
    for row in accepted_rows:
        record = row.normalized_record
        if record is None:
            continue
        provenance = record.provenance
        if provenance is None:
            raise ValueError(
                "normalized FragPipe PSM rows must preserve row provenance"
            )
        raw = row.raw_fields
        modified_peptide = raw.get("Modified Peptide", "").strip() or None
        canonical_modified = _canonical_modified_peptide(modified_peptide)
        mass_difference = _optional_float(raw.get("Mass Difference"))
        rows.append(
            FragpipePsmReviewEntry(
                spectrum_id=record.spectrum_id,
                peptide=record.peptide,
                canonical_peptide=record.canonical_peptide,
                modified_peptide=modified_peptide,
                canonical_modified_peptide=canonical_modified,
                charge=record.charge,
                hyperscore=record.score,
                q_value=record.q_value,
                protein_refs=record.protein_refs,
                target_decoy_label=record.target_decoy_label,
                assigned_modifications=_split_multi_value(
                    raw.get("Assigned Modifications")
                ),
                observed_modifications=_split_multi_value(
                    raw.get("Observed Modifications")
                ),
                mass_difference=mass_difference,
                open_search_candidate=_is_open_search_candidate(
                    mass_difference,
                    tolerance=open_search_mass_tolerance,
                ),
                provenance=provenance,
            )
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.spectrum_id,
                row.q_value if row.q_value is not None else float("inf"),
                -row.hyperscore,
            ),
        )
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
            mass_difference = _optional_float(row.get("Mass Difference"))
            proteins = _split_multi_value(row.get("Protein"))
            mapped_proteins = _split_multi_value(row.get("Mapped Proteins"))
            rows.append(
                FragpipePeptideReviewEntry(
                    peptide=peptide,
                    modified_peptide=modified_peptide,
                    canonical_modified_peptide=_canonical_modified_peptide(
                        modified_peptide
                    ),
                    charge=_optional_int(row.get("Charge")),
                    protein_refs=proteins,
                    mapped_protein_refs=mapped_proteins,
                    assigned_modifications=_split_multi_value(
                        row.get("Assigned Modifications")
                    ),
                    observed_modifications=_split_multi_value(
                        row.get("Observed Modifications")
                    ),
                    hyperscore=_optional_float(row.get("Hyperscore")),
                    probability=_optional_float(row.get("Probability")),
                    q_value=_optional_float(row.get("QValue")),
                    spectral_count=_optional_int(row.get("Spectral Count")),
                    mass_difference=mass_difference,
                    open_search_candidate=_is_open_search_candidate(
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
                    entry_name=_optional_text(row.get("Entry Name")),
                    gene_name=_optional_text(row.get("Gene")),
                    description=_optional_text(row.get("Protein Description")),
                    coverage_fraction=_optional_float(row.get("Coverage")),
                    total_peptides=_optional_int(row.get("Total Peptides")),
                    unique_peptides=_optional_int(row.get("Unique Peptides")),
                    spectral_count=_optional_int(row.get("Spectral Count")),
                    probability=_optional_float(row.get("Probability")),
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
                entity_id=_fragpipe_peptide_entity_id(
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
                abundance = _optional_float(raw_row.get(column_name))
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


def _canonical_modified_peptide(notation: str | None) -> str | None:
    if notation is None:
        return None
    try:
        return build_search_engine_modified_peptide_report(
            notation,
            dialect=SearchEngineModifiedPeptideDialect.FRAGPIPE,
        ).canonical_notation
    except ValueError:
        return None


def _split_multi_value(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    text = str(value).strip()
    if not text:
        return ()
    separators = (";", ",")
    tokens = [text]
    for separator in separators:
        expanded: list[str] = []
        for token in tokens:
            expanded.extend(token.split(separator))
        tokens = expanded
    normalized = tuple(token.strip() for token in tokens if token.strip())
    return tuple(dict.fromkeys(normalized))


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return float(text)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return int(text)


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _is_open_search_candidate(
    mass_difference: float | None, *, tolerance: float
) -> bool:
    if mass_difference is None:
        return False
    return abs(mass_difference) > tolerance


def _has_modified_content(
    row: FragpipePsmReviewEntry | FragpipePeptideReviewEntry,
) -> bool:
    if row.canonical_modified_peptide is None:
        return False
    return row.canonical_modified_peptide != row.peptide


def _fragpipe_peptide_entity_id(
    *, peptide: str, modified_peptide: str | None, charge: int | None
) -> str:
    modified_key = modified_peptide or peptide
    if charge is None:
        return f"{modified_key}|unassigned"
    return f"{modified_key}|z{charge}"
