# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""TSV rendering for FragPipe adapter import surfaces."""

from __future__ import annotations

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification.adapters.fragpipe_import.models import (
    FragpipeCanonicalPsmEntry,
    FragpipeImportSummary,
    FragpipeOpenSearchEvidenceEntry,
    FragpipePeptideReviewEntry,
    FragpipeProteinQuantityEntry,
    FragpipeProteinReviewEntry,
    FragpipePsmReviewEntry,
)
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings


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
        rows, "spectrum_id", "charge", "canonical_peptide"
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


__all__ = [
    "render_fragpipe_canonical_psm_tsv",
    "render_fragpipe_open_search_evidence_tsv",
    "render_fragpipe_peptide_tsv",
    "render_fragpipe_protein_quantity_tsv",
    "render_fragpipe_protein_tsv",
    "render_fragpipe_psm_tsv",
    "render_fragpipe_summary_tsv",
]
