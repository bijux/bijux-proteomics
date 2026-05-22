# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned PTM motif-analysis surfaces."""

from __future__ import annotations

from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.ptm.contracts import (
    PtmEnrichmentInput,
    PtmMotifBackgroundEntry,
    PtmMotifBackgroundReport,
    PtmMotifWindow,
    PtmSiteEntry,
)


def build_ptm_enrichment_input(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    protein_sequences: dict[str, str],
    modification_name: str = "Phospho",
) -> PtmEnrichmentInput:
    """Build foreground and background site lists for PTM enrichment."""

    site_ids = tuple(
        entry.site_key
        for entry in site_entries
        if entry.modification_name == modification_name
        and entry.target_decoy_label is not TargetDecoyLabel.DECOY
    )
    background: list[str] = []
    for protein_ref, sequence in sorted(protein_sequences.items()):
        for index, residue in enumerate(sequence, start=1):
            if residue in {"S", "T", "Y"}:
                background.append(f"{protein_ref}:{residue}{index}")
    return PtmEnrichmentInput(
        modification_name=modification_name,
        site_ids=tuple(site_ids),
        background_ids=tuple(background),
    )


def build_ptm_motif_background_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    protein_sequences: dict[str, str],
    modification_name: str = "Phospho",
) -> PtmMotifBackgroundReport:
    """Build a residue background report for PTM motif interpretation."""

    relevant_entries = tuple(
        entry
        for entry in site_entries
        if entry.modification_name == modification_name
        and entry.target_decoy_label is not TargetDecoyLabel.DECOY
    )
    target_residues = tuple(sorted({entry.residue for entry in relevant_entries})) or (
        "S",
        "T",
        "Y",
    )
    foreground_counts = {
        residue: sum(1 for entry in relevant_entries if entry.residue == residue)
        for residue in target_residues
    }
    background_counts = {
        residue: sum(sequence.count(residue) for sequence in protein_sequences.values())
        for residue in target_residues
    }
    entries = tuple(
        PtmMotifBackgroundEntry(
            residue=residue,
            foreground_site_count=foreground_counts[residue],
            background_site_count=background_counts[residue],
        )
        for residue in target_residues
    )
    return PtmMotifBackgroundReport(
        modification_name=modification_name,
        total_foreground_sites=sum(foreground_counts.values()),
        total_background_sites=sum(background_counts.values()),
        entries=entries,
    )


def build_ptm_motif_windows(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    protein_sequences: dict[str, str],
    flank_size: int = 7,
) -> tuple[PtmMotifWindow, ...]:
    """Extract +/- N residue motif windows around PTM sites."""

    windows: list[PtmMotifWindow] = []
    for entry in site_entries:
        sequence = protein_sequences.get(entry.protein_ref)
        if sequence is None:
            continue
        start = max(1, entry.position - flank_size)
        end = min(len(sequence), entry.position + flank_size)
        window = sequence[start - 1 : end]
        windows.append(
            PtmMotifWindow(
                site_key=entry.site_key,
                protein_ref=entry.protein_ref,
                window=window,
                center_index=entry.position - start + 1,
                flank_size=flank_size,
            )
        )
    return tuple(windows)
