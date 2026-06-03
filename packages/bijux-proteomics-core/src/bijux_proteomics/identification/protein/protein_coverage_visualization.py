# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Plot-ready protein coverage payloads and static renderers."""

from __future__ import annotations

import csv
from html import escape
import io

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    ConfidenceLabel,
    PsmRecord,
    TargetDecoyLabel,
    build_peptide_protein_trace_report,
    rollup_peptide_evidence,
)
from bijux_proteomics.identification.protein.protein_coverage_review import (
    build_protein_coverage_review_report,
)
from bijux_proteomics_foundation import JsonModel


class ProteinCoveragePlotEntry(JsonModel):
    """One peptide-position row inside a protein coverage plot payload."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    protein_length: int = Field(..., ge=1)
    canonical_peptide: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    modified_peptide: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    start_residue: int = Field(..., ge=1)
    end_residue: int = Field(..., ge=1)
    residue_count: int = Field(..., ge=1)
    shared: bool
    confidence_label: ConfidenceLabel
    peptide_q_value: float | None = Field(default=None, ge=0.0)
    best_score: float
    best_intensity: float | None = Field(default=None, ge=0.0)
    charge_states: tuple[int, ...] = Field(default_factory=tuple)
    spectrum_ids: tuple[str, ...] = Field(default_factory=tuple)
    protein_group_ids: tuple[str, ...] = Field(default_factory=tuple)


class ProteinCoveragePlotTrack(JsonModel):
    """One protein track with explicit peptide-position rows."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    protein_length: int = Field(..., ge=1)
    coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    target_decoy_label: TargetDecoyLabel
    contaminant_flag: bool = False
    positions: tuple[ProteinCoveragePlotEntry, ...] = Field(default_factory=tuple)


class ProteinCoveragePlotUnmatchedEntry(JsonModel):
    """One peptide assigned to a protein but not found in its supplied sequence."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    modified_peptide: str | None = None
    confidence_label: ConfidenceLabel
    peptide_q_value: float | None = Field(default=None, ge=0.0)
    best_score: float
    best_intensity: float | None = Field(default=None, ge=0.0)


class ProteinCoveragePlotSummary(JsonModel):
    """Compact summary over a protein coverage plot payload."""

    model_config = ConfigDict(extra="forbid")

    total_proteins: int = Field(..., ge=0)
    plotted_proteins: int = Field(..., ge=0)
    total_position_rows: int = Field(..., ge=0)
    modified_position_count: int = Field(..., ge=0)
    shared_position_count: int = Field(..., ge=0)
    intensity_position_count: int = Field(..., ge=0)
    unmatched_peptide_count: int = Field(..., ge=0)


class ProteinCoveragePlotReport(JsonModel):
    """One plot-ready protein coverage packet."""

    model_config = ConfigDict(extra="forbid")

    threshold: float | None = Field(default=None, ge=0.0)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    high_q_value: float = Field(..., ge=0.0)
    medium_q_value: float = Field(..., ge=0.0)
    summary: ProteinCoveragePlotSummary
    tracks: tuple[ProteinCoveragePlotTrack, ...] = Field(default_factory=tuple)
    unmatched_entries: tuple[ProteinCoveragePlotUnmatchedEntry, ...] = Field(
        default_factory=tuple
    )


def build_protein_coverage_plot_report(
    records: tuple[PsmRecord, ...],
    *,
    protein_sequences: dict[str, str],
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    high_q_value: float = 0.01,
    medium_q_value: float = 0.05,
) -> ProteinCoveragePlotReport:
    """Build one plot-ready peptide-to-protein coverage payload."""
    if high_q_value < 0.0 or medium_q_value < 0.0:
        raise ValueError("confidence thresholds must be non-negative")
    if high_q_value > medium_q_value:
        raise ValueError("high_q_value must not exceed medium_q_value")

    coverage = build_protein_coverage_review_report(
        records,
        protein_sequences=protein_sequences,
        threshold=threshold,
        score_orientation=score_orientation,
    )
    trace = build_peptide_protein_trace_report(records)
    trace_by_peptide = {entry.canonical_peptide: entry for entry in trace.entries}
    rollups = {
        entry.canonical_peptide: entry for entry in rollup_peptide_evidence(records)
    }
    peptide_sequences = {
        record.canonical_peptide: record.peptide_sequence or record.canonical_peptide
        for record in records
    }
    intensities_by_peptide = _build_intensity_index(records)

    tracks: list[ProteinCoveragePlotTrack] = []
    unmatched_entries: list[ProteinCoveragePlotUnmatchedEntry] = []
    for coverage_entry in coverage.entries:
        sequence = protein_sequences[coverage_entry.protein_ref]
        positions: list[ProteinCoveragePlotEntry] = []
        for canonical_peptide in coverage_entry.covered_peptides:
            rollup = rollups[canonical_peptide]
            peptide_sequence = peptide_sequences[canonical_peptide]
            start = sequence.find(peptide_sequence)
            while start != -1:
                positions.append(
                    ProteinCoveragePlotEntry(
                        protein_ref=coverage_entry.protein_ref,
                        protein_length=coverage_entry.residue_count,
                        canonical_peptide=canonical_peptide,
                        peptide=rollup.peptide,
                        modified_peptide=(
                            canonical_peptide if "[" in canonical_peptide else None
                        ),
                        peptide_sequence=peptide_sequence,
                        start_residue=start + 1,
                        end_residue=start + len(peptide_sequence),
                        residue_count=len(peptide_sequence),
                        shared=len(rollup.protein_refs) > 1,
                        confidence_label=_label_from_q_value(
                            rollup.best_q_value,
                            target_decoy_label=rollup.target_decoy_label,
                            high_q_value=high_q_value,
                            medium_q_value=medium_q_value,
                            threshold=threshold,
                        ),
                        peptide_q_value=rollup.best_q_value,
                        best_score=rollup.best_score,
                        best_intensity=intensities_by_peptide.get(canonical_peptide),
                        charge_states=rollup.charge_states,
                        spectrum_ids=trace_by_peptide[canonical_peptide].spectrum_ids,
                        protein_group_ids=trace_by_peptide[
                            canonical_peptide
                        ].protein_group_ids,
                    )
                )
                start = sequence.find(peptide_sequence, start + 1)
        for canonical_peptide in coverage_entry.unmatched_peptides:
            rollup = rollups[canonical_peptide]
            unmatched_entries.append(
                ProteinCoveragePlotUnmatchedEntry(
                    protein_ref=coverage_entry.protein_ref,
                    canonical_peptide=canonical_peptide,
                    peptide_sequence=peptide_sequences[canonical_peptide],
                    modified_peptide=(
                        canonical_peptide if "[" in canonical_peptide else None
                    ),
                    confidence_label=_label_from_q_value(
                        rollup.best_q_value,
                        target_decoy_label=rollup.target_decoy_label,
                        high_q_value=high_q_value,
                        medium_q_value=medium_q_value,
                        threshold=threshold,
                    ),
                    peptide_q_value=rollup.best_q_value,
                    best_score=rollup.best_score,
                    best_intensity=intensities_by_peptide.get(canonical_peptide),
                )
            )
        tracks.append(
            ProteinCoveragePlotTrack(
                protein_ref=coverage_entry.protein_ref,
                protein_length=coverage_entry.residue_count,
                coverage_fraction=coverage_entry.coverage_fraction,
                target_decoy_label=coverage_entry.target_decoy_label,
                contaminant_flag=coverage_entry.contaminant_flag,
                positions=tuple(
                    sorted(
                        positions,
                        key=lambda entry: (
                            entry.start_residue,
                            entry.end_residue,
                            entry.canonical_peptide,
                        ),
                    )
                ),
            )
        )

    all_positions = [position for track in tracks for position in track.positions]
    return ProteinCoveragePlotReport(
        threshold=threshold,
        score_orientation=score_orientation,
        high_q_value=high_q_value,
        medium_q_value=medium_q_value,
        summary=ProteinCoveragePlotSummary(
            total_proteins=coverage.summary.total_proteins,
            plotted_proteins=len(tracks),
            total_position_rows=len(all_positions),
            modified_position_count=sum(
                1 for position in all_positions if position.modified_peptide is not None
            ),
            shared_position_count=sum(
                1 for position in all_positions if position.shared
            ),
            intensity_position_count=sum(
                1 for position in all_positions if position.best_intensity is not None
            ),
            unmatched_peptide_count=len(unmatched_entries),
        ),
        tracks=tuple(tracks),
        unmatched_entries=tuple(
            sorted(
                unmatched_entries,
                key=lambda entry: (entry.protein_ref, entry.canonical_peptide),
            )
        ),
    )


def render_protein_coverage_plot_positions_tsv(
    report: ProteinCoveragePlotReport,
) -> str:
    """Render flattened peptide-position rows as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_ref",
            "protein_length",
            "canonical_peptide",
            "peptide",
            "modified_peptide",
            "peptide_sequence",
            "start_residue",
            "end_residue",
            "residue_count",
            "shared",
            "confidence_label",
            "peptide_q_value",
            "best_score",
            "best_intensity",
            "charge_states",
            "spectrum_ids",
            "protein_group_ids",
        )
    )
    for track in report.tracks:
        for position in track.positions:
            writer.writerow(
                (
                    position.protein_ref,
                    position.protein_length,
                    position.canonical_peptide,
                    position.peptide,
                    position.modified_peptide or "",
                    position.peptide_sequence,
                    position.start_residue,
                    position.end_residue,
                    position.residue_count,
                    str(position.shared).lower(),
                    position.confidence_label.value,
                    ""
                    if position.peptide_q_value is None
                    else position.peptide_q_value,
                    position.best_score,
                    "" if position.best_intensity is None else position.best_intensity,
                    ";".join(str(charge) for charge in position.charge_states),
                    ";".join(position.spectrum_ids),
                    ";".join(position.protein_group_ids),
                )
            )
    return buffer.getvalue()


def render_protein_coverage_plot_svg(report: ProteinCoveragePlotReport) -> str:
    """Render one compact static SVG protein coverage plot."""
    track_count = max(len(report.tracks), 1)
    left_margin = 180
    right_margin = 40
    usable_width = 900
    row_height = 48
    header_height = 52
    footer_height = 24
    height = header_height + track_count * row_height + footer_height
    max_length = max((track.protein_length for track in report.tracks), default=1)
    max_intensity = max(
        (
            position.best_intensity or 0.0
            for track in report.tracks
            for position in track.positions
        ),
        default=0.0,
    )

    rows = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{left_margin + usable_width + right_margin}' height='{height}' viewBox='0 0 {left_margin + usable_width + right_margin} {height}'>",
        "<style>",
        "text { font-family: Helvetica, Arial, sans-serif; fill: #1f2937; }",
        ".axis { stroke: #9ca3af; stroke-width: 2; }",
        ".protein-label { font-size: 13px; font-weight: 700; }",
        ".protein-meta { font-size: 11px; fill: #4b5563; }",
        ".peptide-label { font-size: 10px; fill: #111827; }",
        "</style>",
        "<rect width='100%' height='100%' fill='#ffffff'/>",
        f"<text x='{left_margin}' y='24' font-size='18' font-weight='700'>Protein coverage plot</text>",
        (
            f"<text x='{left_margin}' y='42' font-size='11'>"
            f"proteins={report.summary.plotted_proteins} positions={report.summary.total_position_rows} "
            f"modified={report.summary.modified_position_count} shared={report.summary.shared_position_count}"
            "</text>"
        ),
    ]
    for track_index, track in enumerate(report.tracks):
        y = header_height + track_index * row_height
        baseline_y = y + 18
        rows.append(
            f"<text class='protein-label' x='12' y='{y + 10}'>{escape(track.protein_ref)}</text>"
        )
        rows.append(
            f"<text class='protein-meta' x='12' y='{y + 25}'>length={track.protein_length} coverage={track.coverage_fraction:.3f}</text>"
        )
        rows.append(
            f"<line class='axis' x1='{left_margin}' y1='{baseline_y}' x2='{left_margin + usable_width}' y2='{baseline_y}'/>"
        )
        for position in track.positions:
            start_x = (
                left_margin + (position.start_residue - 1) / max_length * usable_width
            )
            width = max(position.residue_count / max_length * usable_width, 4)
            fill = _confidence_fill(position.confidence_label)
            opacity = _intensity_opacity(
                position.best_intensity, max_intensity=max_intensity
            )
            stroke = "#111827" if position.shared else "#ffffff"
            rows.append(
                f"<rect x='{start_x:.2f}' y='{y + 6}' width='{width:.2f}' height='18' rx='3' fill='{fill}' fill-opacity='{opacity:.3f}' stroke='{stroke}' stroke-width='1'>"
                f"<title>{escape(_position_tooltip(position))}</title>"
                "</rect>"
            )
            if width >= 70:
                rows.append(
                    f"<text class='peptide-label' x='{start_x + 3:.2f}' y='{y + 19}'>{escape(position.canonical_peptide)}</text>"
                )
    rows.append("</svg>\n")
    return "".join(rows)


def render_protein_coverage_plot_html(report: ProteinCoveragePlotReport) -> str:
    """Render one compact static HTML wrapper around the SVG protein coverage plot."""
    svg = render_protein_coverage_plot_svg(report)
    return (
        "<html><head><title>Bijux Proteomics Protein Coverage Plot</title></head><body>"
        "<h1>Protein coverage plot</h1>"
        f"<p><strong>Proteins</strong>: {report.summary.plotted_proteins} | "
        f"<strong>Position rows</strong>: {report.summary.total_position_rows} | "
        f"<strong>Modified rows</strong>: {report.summary.modified_position_count} | "
        f"<strong>Shared rows</strong>: {report.summary.shared_position_count} | "
        f"<strong>Intensity rows</strong>: {report.summary.intensity_position_count}</p>"
        "<p><strong>Legend</strong>: high = green, medium = amber, low = red, rejected = pale red, decoy = gray.</p>"
        f"{svg}"
        "</body></html>\n"
    )


def _build_intensity_index(records: tuple[PsmRecord, ...]) -> dict[str, float]:
    intensity_by_peptide: dict[str, float] = {}
    for record in records:
        if record.intensity is None:
            continue
        previous = intensity_by_peptide.get(record.canonical_peptide)
        if previous is None or record.intensity > previous:
            intensity_by_peptide[record.canonical_peptide] = record.intensity
    return intensity_by_peptide


def _label_from_q_value(
    q_value: float | None,
    *,
    target_decoy_label: TargetDecoyLabel,
    high_q_value: float,
    medium_q_value: float,
    threshold: float | None,
) -> ConfidenceLabel:
    if target_decoy_label is TargetDecoyLabel.DECOY:
        return ConfidenceLabel.DECOY
    if q_value is None:
        return ConfidenceLabel.LOW
    if q_value <= high_q_value:
        return ConfidenceLabel.HIGH
    if q_value <= medium_q_value:
        return ConfidenceLabel.MODERATE
    if threshold is not None and q_value > threshold:
        return ConfidenceLabel.REJECTED
    return ConfidenceLabel.LOW


def _confidence_fill(label: ConfidenceLabel) -> str:
    if label is ConfidenceLabel.HIGH:
        return "#16a34a"
    if label is ConfidenceLabel.MODERATE:
        return "#f59e0b"
    if label is ConfidenceLabel.LOW:
        return "#ef4444"
    if label is ConfidenceLabel.REJECTED:
        return "#fecaca"
    return "#9ca3af"


def _intensity_opacity(intensity: float | None, *, max_intensity: float) -> float:
    if intensity is None or max_intensity <= 0.0:
        return 0.75
    return 0.35 + 0.6 * min(intensity / max_intensity, 1.0)


def _position_tooltip(position: ProteinCoveragePlotEntry) -> str:
    shared = "shared" if position.shared else "unique"
    intensity = (
        "n/a" if position.best_intensity is None else f"{position.best_intensity:.6g}"
    )
    return (
        f"{position.protein_ref}: {position.canonical_peptide} "
        f"({position.start_residue}-{position.end_residue}, {shared}, "
        f"{position.confidence_label.value}, q={position.peptide_q_value}, "
        f"intensity={intensity})"
    )
