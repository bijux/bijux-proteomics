# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PSM row assembly for FragPipe adapter imports."""

from __future__ import annotations

from bijux_proteomics.identification.adapters.fragpipe_import.models import (
    FragpipeCanonicalPsmEntry,
    FragpipePsmReviewEntry,
)
from bijux_proteomics.identification.adapters.fragpipe_import.table_support import (
    canonical_modified_peptide,
    is_open_search_candidate,
    optional_float,
    split_multi_value,
)
from bijux_proteomics.identification.search_adapters.contracts import (
    SearchAdapterNormalizationReport,
)


def build_fragpipe_canonical_psm_rows(
    *,
    normalization_report: SearchAdapterNormalizationReport,
    open_search_mass_tolerance: float,
) -> tuple[FragpipeCanonicalPsmEntry, ...]:
    """Build canonical FragPipe PSM rows from normalized adapter evidence."""
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
        mass_difference = optional_float(raw.get("Mass Difference"))
        rows.append(
            FragpipeCanonicalPsmEntry(
                record=record,
                assigned_modifications=split_multi_value(
                    raw.get("Assigned Modifications")
                ),
                observed_modifications=split_multi_value(
                    raw.get("Observed Modifications")
                ),
                mass_difference=mass_difference,
                open_search_candidate=is_open_search_candidate(
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


def build_fragpipe_psm_rows(
    *,
    normalization_report: SearchAdapterNormalizationReport,
    open_search_mass_tolerance: float,
) -> tuple[FragpipePsmReviewEntry, ...]:
    """Build reviewer-facing FragPipe PSM rows from normalized adapter evidence."""
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
        mass_difference = optional_float(raw.get("Mass Difference"))
        rows.append(
            FragpipePsmReviewEntry(
                spectrum_id=record.spectrum_id,
                peptide=record.peptide,
                canonical_peptide=record.canonical_peptide,
                modified_peptide=modified_peptide,
                canonical_modified_peptide=canonical_modified_peptide(modified_peptide),
                charge=record.charge,
                hyperscore=record.score,
                q_value=record.q_value,
                protein_refs=record.protein_refs,
                target_decoy_label=record.target_decoy_label,
                assigned_modifications=split_multi_value(
                    raw.get("Assigned Modifications")
                ),
                observed_modifications=split_multi_value(
                    raw.get("Observed Modifications")
                ),
                mass_difference=mass_difference,
                open_search_candidate=is_open_search_candidate(
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


__all__ = [
    "build_fragpipe_canonical_psm_rows",
    "build_fragpipe_psm_rows",
]
