# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Scientific support helpers for targeted assay interference analysis."""

from __future__ import annotations

from bijux_proteomics.chemistry import (
    FragmentIonSeries,
    calculate_fragment_ions,
    calculate_peptide_mz,
)
from bijux_proteomics.io import SpectralLibraryEntry
from bijux_proteomics.sequences.digestion import DigestedPeptide
from bijux_proteomics.targeted.discovery_peptide_selection import (
    DiscoveryTargetedPeptideSelectionEntry,
)
from bijux_proteomics.targeted.transition_selection import (
    TargetedTransitionSelectionPeptideEntry,
)


def _selected_peptide_key(
    entry: DiscoveryTargetedPeptideSelectionEntry,
) -> tuple[str, str, int]:
    return (entry.target_protein_ref, entry.canonical_peptide, entry.rank)


def _group_digested_peptides(
    peptides: tuple[DigestedPeptide, ...],
) -> dict[str, tuple[DigestedPeptide, ...]]:
    grouped: dict[str, list[DigestedPeptide]] = {}
    for peptide in peptides:
        grouped.setdefault(peptide.sequence, []).append(peptide)
    return {key: tuple(value) for key, value in grouped.items()}


def _background_competitor_peptides(
    assay_entry: TargetedTransitionSelectionPeptideEntry,
    *,
    digested_by_sequence: dict[str, tuple[DigestedPeptide, ...]],
    precursor_tolerance_da: float,
) -> tuple[str, ...]:
    competing_sequences: list[str] = []
    for sequence in sorted(digested_by_sequence):
        if sequence == assay_entry.peptide_sequence:
            continue
        competitor_precursor_mz = calculate_peptide_mz(
            sequence,
            charge=assay_entry.precursor_charge,
        )
        if (
            abs(competitor_precursor_mz - assay_entry.precursor_mz)
            <= precursor_tolerance_da
        ):
            competing_sequences.append(sequence)
    return tuple(competing_sequences)


def _library_competitor_entries(
    assay_entry: TargetedTransitionSelectionPeptideEntry,
    *,
    source_library_entry: SpectralLibraryEntry | None,
    spectral_library_entries: tuple[SpectralLibraryEntry, ...],
    precursor_tolerance_da: float,
) -> tuple[SpectralLibraryEntry, ...]:
    competitors = [
        entry
        for entry in spectral_library_entries
        if entry.canonical_peptide != assay_entry.canonical_peptide
        and abs(entry.precursor_mz - assay_entry.precursor_mz) <= precursor_tolerance_da
        and (
            source_library_entry is None
            or entry.library_entry_id != source_library_entry.library_entry_id
        )
    ]
    return tuple(
        sorted(
            competitors,
            key=lambda entry: (
                abs(entry.precursor_mz - assay_entry.precursor_mz),
                entry.canonical_peptide,
                entry.library_entry_id,
            ),
        )
    )


def _count_panel_fragment_overlaps(
    *,
    assay_entry_id: str,
    precursor_mz: float,
    fragment_mz: float,
    all_transition_entries: tuple[TargetedTransitionSelectionPeptideEntry, ...],
    precursor_tolerance_da: float,
    fragment_tolerance_da: float,
) -> int:
    overlap_count = 0
    for assay_entry in all_transition_entries:
        if assay_entry.assay_entry_id == assay_entry_id:
            continue
        if abs(assay_entry.precursor_mz - precursor_mz) > precursor_tolerance_da:
            continue
        overlap_count += sum(
            1
            for transition in assay_entry.selected_transitions
            if abs(transition.fragment_mz - fragment_mz) <= fragment_tolerance_da
        )
    return overlap_count


def _count_background_fragment_overlaps(
    background_sequences: tuple[str, ...],
    *,
    fragment_mz: float,
    fragment_charge: int,
    fragment_tolerance_da: float,
) -> int:
    overlap_count = 0
    for sequence in background_sequences:
        fragments = calculate_fragment_ions(
            sequence,
            charges=(fragment_charge,),
            series=(FragmentIonSeries.B, FragmentIonSeries.Y),
            include_neutral_losses=False,
        )
        if any(
            abs(candidate.mz_monoisotopic - fragment_mz) <= fragment_tolerance_da
            for candidate in fragments
        ):
            overlap_count += 1
    return overlap_count


def _count_library_fragment_overlaps(
    library_entries: tuple[SpectralLibraryEntry, ...],
    *,
    source_library_entry: SpectralLibraryEntry | None,
    fragment_mz: float,
    fragment_charge: int,
    fragment_tolerance_da: float,
    coelution_rt_window_minutes: float,
) -> tuple[int, int]:
    overlap_count = 0
    coeluting_count = 0
    for entry in library_entries:
        fragments = calculate_fragment_ions(
            entry.canonical_peptide,
            charges=(fragment_charge,),
            series=(FragmentIonSeries.B, FragmentIonSeries.Y),
            include_neutral_losses=False,
        )
        if not any(
            abs(candidate.mz_monoisotopic - fragment_mz) <= fragment_tolerance_da
            for candidate in fragments
        ):
            continue
        overlap_count += 1
        if (
            source_library_entry is not None
            and source_library_entry.spectrum.retention_time_seconds is not None
            and entry.spectrum.retention_time_seconds is not None
            and abs(
                source_library_entry.spectrum.retention_time_seconds
                - entry.spectrum.retention_time_seconds
            )
            / 60.0
            <= coelution_rt_window_minutes
        ):
            coeluting_count += 1
    return overlap_count, coeluting_count


__all__ = [
    "_background_competitor_peptides",
    "_count_background_fragment_overlaps",
    "_count_library_fragment_overlaps",
    "_count_panel_fragment_overlaps",
    "_group_digested_peptides",
    "_library_competitor_entries",
    "_selected_peptide_key",
]
