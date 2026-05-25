# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned PTM motif-analysis surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.ptm.contracts import (
    PtmEnrichmentInput,
    PtmMotifBackgroundEntry,
    PtmMotifBackgroundReport,
    PtmMotifWindow,
    PtmSiteEntry,
)
from bijux_proteomics.ptm.quant.differential_analysis import (
    PtmDifferentialAnalysisReport,
    PtmProteinCorrectionMode,
    PtmSiteDifferentialEntry,
)
from bijux_proteomics.ptm.quant.site_quantification import PtmSiteQuantRow
from bijux_proteomics_foundation import JsonModel
from pydantic import ConfigDict, Field


class PtmMotifRegulationDirection(StrEnum):
    """Direction filter for regulated phosphosite motif selection."""

    BOTH = "both"
    UPREGULATED = "upregulated"
    DOWNREGULATED = "downregulated"


class PtmMotifBackgroundMode(StrEnum):
    """Background universe used for PTM motif enrichment comparison."""

    OBSERVED_SITE_BACKGROUND = "observed_site_background"
    WHOLE_PROTEOME_BACKGROUND = "whole_proteome_background"


class PtmPhosphositeSelectionPolicy(JsonModel):
    """Selection policy for regulated phosphosite motif enrichment."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float = Field(default=1.0, ge=0.0)
    direction: PtmMotifRegulationDirection = PtmMotifRegulationDirection.BOTH
    include_ambiguous_regulated_sites: bool = False
    include_ambiguous_background_sites: bool = False


class PtmMotifComparisonPolicy(JsonModel):
    """Comparison policy for phosphosite motif frequency and enrichment review."""

    model_config = ConfigDict(extra="forbid")

    background_mode: PtmMotifBackgroundMode = (
        PtmMotifBackgroundMode.OBSERVED_SITE_BACKGROUND
    )
    min_frequency_difference: float = Field(default=0.1, ge=0.0, le=1.0)
    min_enrichment_ratio: float = Field(default=1.5, ge=0.0)
    max_reported_term_count: int = Field(default=25, ge=1)


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


class PtmMotifFrequencyEntry(JsonModel):
    """One position-by-residue frequency comparison between regulated and background windows."""

    model_config = ConfigDict(extra="forbid")

    position_offset: int
    residue: str = Field(..., min_length=1, max_length=1)
    regulated_window_count: int = Field(..., ge=0)
    background_window_count: int = Field(..., ge=0)
    regulated_frequency: float = Field(..., ge=0.0, le=1.0)
    background_frequency: float = Field(..., ge=0.0, le=1.0)


class PtmMotifEnrichedTermEntry(JsonModel):
    """One enriched motif term derived from regulated-vs-background frequency comparison."""

    model_config = ConfigDict(extra="forbid")

    position_offset: int
    residue: str = Field(..., min_length=1, max_length=1)
    regulated_window_count: int = Field(..., ge=0)
    background_window_count: int = Field(..., ge=0)
    regulated_frequency: float = Field(..., ge=0.0, le=1.0)
    background_frequency: float = Field(..., ge=0.0, le=1.0)
    frequency_difference: float = Field(..., ge=0.0, le=1.0)
    enrichment_ratio: float | None = Field(default=None, ge=0.0)
    exclusive_to_regulated: bool = False


class PtmMotifLogoDatum(JsonModel):
    """One logo-ready residue frequency datum for one window role and motif position."""

    model_config = ConfigDict(extra="forbid")

    window_role: str = Field(..., min_length=1)
    position_offset: int
    residue: str = Field(..., min_length=1, max_length=1)
    residue_count: int = Field(..., ge=0)
    total_window_count: int = Field(..., ge=0)
    frequency: float = Field(..., ge=0.0, le=1.0)


class PtmMotifEnrichmentTermEntry(JsonModel):
    """One residue-level term in PTM motif background-provenance reporting."""

    model_config = ConfigDict(extra="forbid")

    residue: str = Field(..., min_length=1, max_length=1)
    foreground_site_count: int = Field(..., ge=0)
    background_site_count: int = Field(..., ge=0)
    enrichment_ratio: float | None = Field(default=None, ge=0.0)


class PtmMotifEnrichmentBackgroundProvenanceReport(JsonModel):
    """Motif enrichment report with explicit background and test provenance."""

    model_config = ConfigDict(extra="forbid")

    modification_name: str = Field(..., min_length=1)
    background_mode: PtmMotifBackgroundMode
    background_universe: str = Field(..., min_length=1)
    applied_filters: tuple[str, ...] = Field(default_factory=tuple)
    statistical_test: str = Field(..., min_length=1)
    multiple_testing_correction: str = Field(..., min_length=1)
    foreground_site_count: int = Field(..., ge=0)
    background_site_count: int = Field(..., ge=0)
    terms: tuple[PtmMotifEnrichmentTermEntry, ...] = Field(default_factory=tuple)
    caveats: tuple[str, ...] = Field(default_factory=tuple)


class PtmPhosphositeMotifEnrichmentReport(JsonModel):
    """Regulated phosphosite windows prepared for motif comparison and logo output."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    selection_policy: PtmPhosphositeSelectionPolicy
    comparison_policy: PtmMotifComparisonPolicy
    background_mode: PtmMotifBackgroundMode
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
    frequency_entries: tuple[PtmMotifFrequencyEntry, ...] = Field(default_factory=tuple)
    enriched_terms: tuple[PtmMotifEnrichedTermEntry, ...] = Field(default_factory=tuple)
    logo_data: tuple[PtmMotifLogoDatum, ...] = Field(default_factory=tuple)
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
    background_mode: PtmMotifBackgroundMode | str = (
        PtmMotifBackgroundMode.WHOLE_PROTEOME_BACKGROUND
    ),
) -> PtmMotifBackgroundReport:
    """Build a residue background report for PTM motif interpretation."""

    active_background_mode = PtmMotifBackgroundMode(background_mode)
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
    foreground_counts = _count_background_residues(relevant_entries, target_residues)
    if active_background_mode is PtmMotifBackgroundMode.OBSERVED_SITE_BACKGROUND:
        background_counts = foreground_counts
    else:
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
        background_mode=active_background_mode.value,
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
    comparison_policy: PtmMotifComparisonPolicy | None = None,
) -> PtmPhosphositeMotifEnrichmentReport:
    """Select regulated phosphosites and build centered windows for motif enrichment."""

    active_policy = selection_policy or PtmPhosphositeSelectionPolicy()
    active_comparison_policy = comparison_policy or PtmMotifComparisonPolicy()
    site_rows_by_key = {
        row.site_key: row for row in differential_analysis.site_quantification.rows
    }
    regulated_windows: list[PtmCenteredMotifWindowEntry] = []
    regulated_site_keys: set[str] = set()
    regulated_positions: set[tuple[str, str, int]] = set()
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
        regulated_positions.add((row.protein_ref, row.residue, row.position))
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

    background_windows = _build_background_windows(
        differential_analysis=differential_analysis,
        active_policy=active_policy,
        background_mode=active_comparison_policy.background_mode,
        protein_sequences=protein_sequences,
        flank_size=flank_size,
        regulated_site_keys=regulated_site_keys,
        regulated_positions=regulated_positions,
    )

    frequency_entries = _build_position_frequency_entries(
        tuple(regulated_windows),
        tuple(background_windows),
    )
    enriched_terms = _build_enriched_terms(
        frequency_entries,
        comparison_policy=active_comparison_policy,
    )
    logo_data = _build_logo_data(
        tuple(regulated_windows),
        tuple(background_windows),
    )

    return PtmPhosphositeMotifEnrichmentReport(
        condition_a=differential_analysis.differential_report.condition_a,
        condition_b=differential_analysis.differential_report.condition_b,
        selection_policy=active_policy,
        comparison_policy=active_comparison_policy,
        background_mode=active_comparison_policy.background_mode,
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
        frequency_entries=frequency_entries,
        enriched_terms=enriched_terms,
        logo_data=logo_data,
        note=(
            "phosphosite motif enrichment preserves centered sequence windows, position-specific residue frequencies, enriched motif terms, and logo-ready data for one explicit regulated-versus-background phosphosite comparison"
        ),
    )


def _build_background_windows(
    *,
    differential_analysis: PtmDifferentialAnalysisReport,
    active_policy: PtmPhosphositeSelectionPolicy,
    background_mode: PtmMotifBackgroundMode,
    protein_sequences: dict[str, str],
    flank_size: int,
    regulated_site_keys: set[str],
    regulated_positions: set[tuple[str, str, int]],
) -> list[PtmCenteredMotifWindowEntry]:
    if background_mode is PtmMotifBackgroundMode.OBSERVED_SITE_BACKGROUND:
        return _build_observed_site_background_windows(
            differential_analysis=differential_analysis,
            active_policy=active_policy,
            protein_sequences=protein_sequences,
            flank_size=flank_size,
            regulated_site_keys=regulated_site_keys,
        )
    return _build_whole_proteome_background_windows(
        protein_correction_mode=differential_analysis.protein_correction_mode,
        protein_sequences=protein_sequences,
        flank_size=flank_size,
        regulated_positions=regulated_positions,
    )


def _build_observed_site_background_windows(
    *,
    differential_analysis: PtmDifferentialAnalysisReport,
    active_policy: PtmPhosphositeSelectionPolicy,
    protein_sequences: dict[str, str],
    flank_size: int,
    regulated_site_keys: set[str],
) -> list[PtmCenteredMotifWindowEntry]:
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
    return background_windows


def _build_whole_proteome_background_windows(
    *,
    protein_correction_mode: PtmProteinCorrectionMode,
    protein_sequences: dict[str, str],
    flank_size: int,
    regulated_positions: set[tuple[str, str, int]],
) -> list[PtmCenteredMotifWindowEntry]:
    background_windows: list[PtmCenteredMotifWindowEntry] = []
    for protein_ref, sequence in sorted(protein_sequences.items()):
        for position, residue in enumerate(sequence, start=1):
            if residue not in {"S", "T", "Y"}:
                continue
            if (protein_ref, residue, position) in regulated_positions:
                continue
            centered_window = _extract_centered_window(
                protein_ref,
                position,
                protein_sequences=protein_sequences,
                flank_size=flank_size,
            )
            if centered_window is None:
                continue
            background_windows.append(
                PtmCenteredMotifWindowEntry(
                    site_key=f"{protein_ref}:{residue}{position}:background",
                    protein_ref=protein_ref,
                    residue=residue,
                    position=position,
                    modification_name="Phospho",
                    direction=PtmMotifRegulationDirection.BOTH,
                    window_role="background",
                    centered_window=centered_window,
                    flank_size=flank_size,
                    ambiguous=False,
                    protein_correction_mode=protein_correction_mode,
                )
            )
    return background_windows


def build_ptm_motif_enrichment_background_provenance_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    protein_sequences: dict[str, str],
    modification_name: str,
    background_mode: PtmMotifBackgroundMode | str,
    applied_filters: tuple[str, ...],
    statistical_test: str = "fisher_exact",
    multiple_testing_correction: str = "benjamini_hochberg",
) -> PtmMotifEnrichmentBackgroundProvenanceReport:
    """Build a provenance-aware motif background report from one PTM site table."""

    active_background_mode = PtmMotifBackgroundMode(background_mode)
    relevant = tuple(
        entry for entry in site_entries if entry.modification_name == modification_name
    )
    residues = tuple(sorted({entry.residue for entry in relevant})) or ("S", "T", "Y")
    residue_foreground_counts = _count_background_residues(relevant, residues)
    if active_background_mode is PtmMotifBackgroundMode.OBSERVED_SITE_BACKGROUND:
        residue_background_counts = residue_foreground_counts
        background_universe = "observed_phosphosite_background"
    else:
        residue_background_counts = {
            residue: sum(sequence.count(residue) for sequence in protein_sequences.values())
            for residue in residues
        }
        background_universe = "whole_proteome_background"
    term_entries: list[PtmMotifEnrichmentTermEntry] = []
    background_total = sum(residue_background_counts.values())
    foreground_total = len(relevant)
    for residue in residues:
        foreground_count = residue_foreground_counts[residue]
        background_count = residue_background_counts[residue]
        ratio = (
            (foreground_count / foreground_total)
            / (background_count / max(background_total, 1))
            if foreground_total > 0 and background_count > 0
            else None
        )
        term_entries.append(
            PtmMotifEnrichmentTermEntry(
                residue=residue,
                foreground_site_count=foreground_count,
                background_site_count=background_count,
                enrichment_ratio=round(ratio, 6) if ratio is not None else None,
            )
        )
    caveats: list[str] = []
    if any(entry.ambiguous for entry in relevant):
        caveats.append("foreground contains ambiguous site assignments")
    if not relevant:
        caveats.append("foreground is empty for requested PTM class")
    return PtmMotifEnrichmentBackgroundProvenanceReport(
        modification_name=modification_name,
        background_mode=active_background_mode,
        background_universe=background_universe,
        applied_filters=applied_filters,
        statistical_test=statistical_test,
        multiple_testing_correction=multiple_testing_correction,
        foreground_site_count=foreground_total,
        background_site_count=background_total,
        terms=tuple(term_entries),
        caveats=tuple(caveats),
    )


def render_ptm_phosphosite_motif_window_tsv(
    report: PtmPhosphositeMotifEnrichmentReport,
) -> str:
    """Render regulated and background phosphosite motif windows as a stable TSV ledger."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "site_key",
            "protein_ref",
            "residue",
            "position",
            "modification_name",
            "background_mode",
            "window_role",
            "direction",
            "centered_window",
            "flank_size",
            "plotted_log2_fold_change",
            "adjusted_p_value",
            "ambiguous",
            "protein_correction_mode",
        )
    )
    for entry in (*report.regulated_windows, *report.background_windows):
        writer.writerow(
            (
                entry.site_key,
                entry.protein_ref,
                entry.residue,
                entry.position,
                entry.modification_name,
                report.background_mode.value,
                entry.window_role,
                entry.direction.value,
                entry.centered_window,
                entry.flank_size,
                ""
                if entry.plotted_log2_fold_change is None
                else f"{entry.plotted_log2_fold_change:g}",
                "" if entry.adjusted_p_value is None else f"{entry.adjusted_p_value:g}",
                str(entry.ambiguous).lower(),
                entry.protein_correction_mode.value,
            )
        )
    return handle.getvalue()


def export_ptm_phosphosite_motif_window_tsv(
    report: PtmPhosphositeMotifEnrichmentReport,
    path: Path,
) -> None:
    """Write phosphosite motif windows to a stable TSV artifact."""

    path.write_text(render_ptm_phosphosite_motif_window_tsv(report), encoding="utf-8")


def render_ptm_phosphosite_motif_frequency_tsv(
    report: PtmPhosphositeMotifEnrichmentReport,
) -> str:
    """Render position-specific phosphosite motif frequencies as a stable TSV ledger."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "position_offset",
            "residue",
            "background_mode",
            "regulated_window_count",
            "background_window_count",
            "regulated_frequency",
            "background_frequency",
        )
    )
    for entry in report.frequency_entries:
        writer.writerow(
            (
                entry.position_offset,
                entry.residue,
                report.background_mode.value,
                entry.regulated_window_count,
                entry.background_window_count,
                f"{entry.regulated_frequency:g}",
                f"{entry.background_frequency:g}",
            )
        )
    return handle.getvalue()


def export_ptm_phosphosite_motif_frequency_tsv(
    report: PtmPhosphositeMotifEnrichmentReport,
    path: Path,
) -> None:
    """Write position-specific phosphosite motif frequencies to a stable TSV artifact."""

    path.write_text(
        render_ptm_phosphosite_motif_frequency_tsv(report),
        encoding="utf-8",
    )


def render_ptm_phosphosite_motif_enriched_term_tsv(
    report: PtmPhosphositeMotifEnrichmentReport,
) -> str:
    """Render enriched phosphosite motif terms as a stable TSV ledger."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "position_offset",
            "residue",
            "background_mode",
            "regulated_window_count",
            "background_window_count",
            "regulated_frequency",
            "background_frequency",
            "frequency_difference",
            "enrichment_ratio",
            "exclusive_to_regulated",
        )
    )
    for entry in report.enriched_terms:
        writer.writerow(
            (
                entry.position_offset,
                entry.residue,
                report.background_mode.value,
                entry.regulated_window_count,
                entry.background_window_count,
                f"{entry.regulated_frequency:g}",
                f"{entry.background_frequency:g}",
                f"{entry.frequency_difference:g}",
                "" if entry.enrichment_ratio is None else f"{entry.enrichment_ratio:g}",
                str(entry.exclusive_to_regulated).lower(),
            )
        )
    return handle.getvalue()


def export_ptm_phosphosite_motif_enriched_term_tsv(
    report: PtmPhosphositeMotifEnrichmentReport,
    path: Path,
) -> None:
    """Write enriched phosphosite motif terms to a stable TSV artifact."""

    path.write_text(
        render_ptm_phosphosite_motif_enriched_term_tsv(report),
        encoding="utf-8",
    )


def render_ptm_phosphosite_motif_logo_tsv(
    report: PtmPhosphositeMotifEnrichmentReport,
) -> str:
    """Render logo-ready phosphosite motif residue frequencies as a stable TSV ledger."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "window_role",
            "position_offset",
            "residue",
            "background_mode",
            "residue_count",
            "total_window_count",
            "frequency",
        )
    )
    for entry in report.logo_data:
        writer.writerow(
            (
                entry.window_role,
                entry.position_offset,
                entry.residue,
                report.background_mode.value,
                entry.residue_count,
                entry.total_window_count,
                f"{entry.frequency:g}",
            )
        )
    return handle.getvalue()


def export_ptm_phosphosite_motif_logo_tsv(
    report: PtmPhosphositeMotifEnrichmentReport,
    path: Path,
) -> None:
    """Write logo-ready phosphosite motif residue frequencies to a stable TSV artifact."""

    path.write_text(render_ptm_phosphosite_motif_logo_tsv(report), encoding="utf-8")


def _count_background_residues(
    relevant_entries: tuple[PtmSiteEntry, ...],
    residues: tuple[str, ...],
) -> dict[str, int]:
    return {
        residue: sum(1 for entry in relevant_entries if entry.residue == residue)
        for residue in residues
    }


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


def _build_position_frequency_entries(
    regulated_windows: tuple[PtmCenteredMotifWindowEntry, ...],
    background_windows: tuple[PtmCenteredMotifWindowEntry, ...],
) -> tuple[PtmMotifFrequencyEntry, ...]:
    regulated_counts, regulated_totals = _count_position_residues(regulated_windows)
    background_counts, background_totals = _count_position_residues(background_windows)
    keys = tuple(sorted(set(regulated_counts) | set(background_counts)))
    entries: list[PtmMotifFrequencyEntry] = []
    for position_offset, residue in keys:
        regulated_total = regulated_totals.get(position_offset, 0)
        background_total = background_totals.get(position_offset, 0)
        regulated_count = regulated_counts.get((position_offset, residue), 0)
        background_count = background_counts.get((position_offset, residue), 0)
        entries.append(
            PtmMotifFrequencyEntry(
                position_offset=position_offset,
                residue=residue,
                regulated_window_count=regulated_count,
                background_window_count=background_count,
                regulated_frequency=round(
                    regulated_count / regulated_total, 6
                )
                if regulated_total
                else 0.0,
                background_frequency=round(
                    background_count / background_total, 6
                )
                if background_total
                else 0.0,
            )
        )
    return tuple(entries)


def _build_enriched_terms(
    frequency_entries: tuple[PtmMotifFrequencyEntry, ...],
    *,
    comparison_policy: PtmMotifComparisonPolicy,
) -> tuple[PtmMotifEnrichedTermEntry, ...]:
    terms: list[PtmMotifEnrichedTermEntry] = []
    for entry in frequency_entries:
        frequency_difference = round(
            entry.regulated_frequency - entry.background_frequency,
            6,
        )
        if frequency_difference < comparison_policy.min_frequency_difference:
            continue
        exclusive_to_regulated = (
            entry.regulated_window_count > 0 and entry.background_window_count == 0
        )
        enrichment_ratio = None
        if entry.background_frequency > 0.0:
            enrichment_ratio = round(
                entry.regulated_frequency / entry.background_frequency,
                6,
            )
        if not exclusive_to_regulated and (
            enrichment_ratio is None
            or enrichment_ratio < comparison_policy.min_enrichment_ratio
        ):
            continue
        terms.append(
            PtmMotifEnrichedTermEntry(
                position_offset=entry.position_offset,
                residue=entry.residue,
                regulated_window_count=entry.regulated_window_count,
                background_window_count=entry.background_window_count,
                regulated_frequency=entry.regulated_frequency,
                background_frequency=entry.background_frequency,
                frequency_difference=frequency_difference,
                enrichment_ratio=enrichment_ratio,
                exclusive_to_regulated=exclusive_to_regulated,
            )
        )
    return tuple(
        sorted(
            terms,
            key=lambda entry: (
                not entry.exclusive_to_regulated,
                -(entry.enrichment_ratio or 0.0),
                -entry.frequency_difference,
                entry.position_offset,
                entry.residue,
            ),
        )[: comparison_policy.max_reported_term_count]
    )


def _build_logo_data(
    regulated_windows: tuple[PtmCenteredMotifWindowEntry, ...],
    background_windows: tuple[PtmCenteredMotifWindowEntry, ...],
) -> tuple[PtmMotifLogoDatum, ...]:
    entries: list[PtmMotifLogoDatum] = []
    for window_role, windows in (
        ("regulated", regulated_windows),
        ("background", background_windows),
    ):
        counts, totals = _count_position_residues(windows)
        for position_offset, residue in sorted(counts):
            total_window_count = totals[position_offset]
            residue_count = counts[(position_offset, residue)]
            entries.append(
                PtmMotifLogoDatum(
                    window_role=window_role,
                    position_offset=position_offset,
                    residue=residue,
                    residue_count=residue_count,
                    total_window_count=total_window_count,
                    frequency=round(residue_count / total_window_count, 6),
                )
            )
    return tuple(entries)


def _count_position_residues(
    windows: tuple[PtmCenteredMotifWindowEntry, ...],
) -> tuple[dict[tuple[int, str], int], dict[int, int]]:
    counts: dict[tuple[int, str], int] = {}
    totals: dict[int, int] = {}
    if not windows:
        return counts, totals
    flank_size = windows[0].flank_size
    for entry in windows:
        for index, residue in enumerate(entry.centered_window):
            if residue == "-":
                continue
            position_offset = index - flank_size
            key = (position_offset, residue)
            counts[key] = counts.get(key, 0) + 1
            totals[position_offset] = totals.get(position_offset, 0) + 1
    return counts, totals
