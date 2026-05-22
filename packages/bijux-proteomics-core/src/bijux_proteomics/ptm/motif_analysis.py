# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned PTM motif-analysis surfaces."""

from __future__ import annotations

from enum import StrEnum

from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.ptm.contracts import (
    PtmEnrichmentInput,
    PtmMotifBackgroundEntry,
    PtmMotifBackgroundReport,
    PtmMotifWindow,
    PtmSiteEntry,
)
from bijux_proteomics.ptm.differential_analysis import (
    PtmDifferentialAnalysisReport,
    PtmProteinCorrectionMode,
    PtmSiteDifferentialEntry,
)
from bijux_proteomics.ptm.site_quantification import PtmSiteQuantRow
from bijux_proteomics_foundation import JsonModel
from pydantic import ConfigDict, Field


class PtmMotifRegulationDirection(StrEnum):
    """Direction filter for regulated phosphosite motif selection."""

    BOTH = "both"
    UPREGULATED = "upregulated"
    DOWNREGULATED = "downregulated"


class PtmPhosphositeSelectionPolicy(JsonModel):
    """Selection policy for regulated phosphosite motif enrichment."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float = Field(default=1.0, ge=0.0)
    direction: PtmMotifRegulationDirection = PtmMotifRegulationDirection.BOTH
    include_ambiguous_regulated_sites: bool = False
    include_ambiguous_background_sites: bool = False


class PtmCenteredMotifWindowEntry(JsonModel):
    """One fixed-width centered motif window from a regulated or background phosphosite."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    direction: PtmMotifRegulationDirection
    window_role: str = Field(..., min_length=1)
    centered_window: str = Field(..., min_length=1)
    flank_size: int = Field(..., ge=0)
    plotted_log2_fold_change: float | None = None
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    ambiguous: bool = False
    protein_correction_mode: PtmProteinCorrectionMode


class PtmPhosphositeMotifEnrichmentReport(JsonModel):
    """Regulated phosphosite windows prepared for motif comparison and logo output."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    selection_policy: PtmPhosphositeSelectionPolicy
    protein_correction_mode: PtmProteinCorrectionMode
    flank_size: int = Field(..., ge=0)
    regulated_site_count: int = Field(..., ge=0)
    background_site_count: int = Field(..., ge=0)
    regulated_windows: tuple[PtmCenteredMotifWindowEntry, ...] = Field(
        default_factory=tuple
    )
    background_windows: tuple[PtmCenteredMotifWindowEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


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


def build_ptm_phosphosite_motif_enrichment_report(
    differential_analysis: PtmDifferentialAnalysisReport,
    *,
    protein_sequences: dict[str, str],
    flank_size: int = 7,
    selection_policy: PtmPhosphositeSelectionPolicy | None = None,
) -> PtmPhosphositeMotifEnrichmentReport:
    """Select regulated phosphosites and build centered windows for motif enrichment."""

    active_policy = selection_policy or PtmPhosphositeSelectionPolicy()
    site_rows_by_key = {
        row.site_key: row for row in differential_analysis.site_quantification.rows
    }
    regulated_windows: list[PtmCenteredMotifWindowEntry] = []
    regulated_site_keys: set[str] = set()
    for entry in differential_analysis.differential_report.entries:
        row = site_rows_by_key.get(entry.site_key)
        if row is None or not _is_phospho_target_row(row):
            continue
        if row.ambiguous and not active_policy.include_ambiguous_regulated_sites:
            continue
        plotted_log2_fold_change = _plotted_log2_fold_change(entry)
        if not _matches_direction(plotted_log2_fold_change, active_policy.direction):
            continue
        adjusted_p_value = entry.adjusted_p_value or entry.p_value
        if adjusted_p_value > active_policy.max_adjusted_p_value:
            continue
        if abs(plotted_log2_fold_change) < active_policy.min_absolute_log2_fold_change:
            continue
        centered_window = _extract_centered_window(
            row.protein_ref,
            row.position,
            protein_sequences=protein_sequences,
            flank_size=flank_size,
        )
        if centered_window is None:
            continue
        regulated_site_keys.add(row.site_key)
        regulated_windows.append(
            PtmCenteredMotifWindowEntry(
                site_key=row.site_key,
                protein_ref=row.protein_ref,
                residue=row.residue,
                position=row.position,
                modification_name=row.modification_name,
                direction=_direction_for_value(plotted_log2_fold_change),
                window_role="regulated",
                centered_window=centered_window,
                flank_size=flank_size,
                plotted_log2_fold_change=plotted_log2_fold_change,
                adjusted_p_value=adjusted_p_value,
                ambiguous=row.ambiguous,
                protein_correction_mode=differential_analysis.protein_correction_mode,
            )
        )

    background_windows: list[PtmCenteredMotifWindowEntry] = []
    for row in differential_analysis.site_quantification.rows:
        if row.site_key in regulated_site_keys or not _is_phospho_target_row(row):
            continue
        if row.ambiguous and not active_policy.include_ambiguous_background_sites:
            continue
        centered_window = _extract_centered_window(
            row.protein_ref,
            row.position,
            protein_sequences=protein_sequences,
            flank_size=flank_size,
        )
        if centered_window is None:
            continue
        background_windows.append(
            PtmCenteredMotifWindowEntry(
                site_key=row.site_key,
                protein_ref=row.protein_ref,
                residue=row.residue,
                position=row.position,
                modification_name=row.modification_name,
                direction=PtmMotifRegulationDirection.BOTH,
                window_role="background",
                centered_window=centered_window,
                flank_size=flank_size,
                ambiguous=row.ambiguous,
                protein_correction_mode=differential_analysis.protein_correction_mode,
            )
        )

    return PtmPhosphositeMotifEnrichmentReport(
        condition_a=differential_analysis.differential_report.condition_a,
        condition_b=differential_analysis.differential_report.condition_b,
        selection_policy=active_policy,
        protein_correction_mode=differential_analysis.protein_correction_mode,
        flank_size=flank_size,
        regulated_site_count=len(regulated_windows),
        background_site_count=len(background_windows),
        regulated_windows=tuple(
            sorted(regulated_windows, key=lambda entry: (entry.site_key, entry.window_role))
        ),
        background_windows=tuple(
            sorted(background_windows, key=lambda entry: (entry.site_key, entry.window_role))
        ),
        note=(
            "phosphosite motif enrichment preserves centered sequence windows for regulated phosphosites and one explicit phosphosite background set"
        ),
    )


def _is_phospho_target_row(row: PtmSiteQuantRow) -> bool:
    return (
        row.modification_name == "Phospho"
        and row.target_decoy_label is not TargetDecoyLabel.DECOY
    )


def _plotted_log2_fold_change(entry: PtmSiteDifferentialEntry) -> float:
    if entry.corrected_log2_fold_change is not None:
        return entry.corrected_log2_fold_change
    return entry.log2_fold_change


def _matches_direction(
    plotted_log2_fold_change: float,
    direction: PtmMotifRegulationDirection,
) -> bool:
    if direction is PtmMotifRegulationDirection.BOTH:
        return True
    if direction is PtmMotifRegulationDirection.UPREGULATED:
        return plotted_log2_fold_change > 0.0
    return plotted_log2_fold_change < 0.0


def _direction_for_value(value: float) -> PtmMotifRegulationDirection:
    if value < 0.0:
        return PtmMotifRegulationDirection.DOWNREGULATED
    return PtmMotifRegulationDirection.UPREGULATED


def _extract_centered_window(
    protein_ref: str,
    position: int,
    *,
    protein_sequences: dict[str, str],
    flank_size: int,
) -> str | None:
    sequence = protein_sequences.get(protein_ref)
    if sequence is None:
        return None
    residues: list[str] = []
    for offset in range(-flank_size, flank_size + 1):
        index = position + offset
        if index < 1 or index > len(sequence):
            residues.append("-")
        else:
            residues.append(sequence[index - 1])
    return "".join(residues)
