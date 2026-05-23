# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned protein coverage inference over peptide evidence and protein sequences."""

from __future__ import annotations

from collections import defaultdict
import csv
from enum import StrEnum
import hashlib
import io
import json

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    PeptideEvidenceEntry,
    PsmRecord,
    TargetDecoyLabel,
    rollup_peptide_evidence,
)
from bijux_proteomics_foundation import JsonModel


class ProteinCoverageCoordinateStatus(StrEnum):
    """Match state for one peptide-to-protein coordinate row."""

    MATCHED = "matched"
    UNMATCHED = "unmatched"


class ProteinCoverageSummary(JsonModel):
    """Compact summary over sequence-backed protein coverage evidence."""

    model_config = ConfigDict(extra="forbid")

    total_proteins: int = Field(..., ge=0)
    proteins_with_sequence: int = Field(..., ge=0)
    proteins_missing_sequence: int = Field(..., ge=0)
    fully_uncovered_proteins: int = Field(..., ge=0)
    proteins_with_unique_peptides: int = Field(..., ge=0)
    proteins_with_shared_peptides: int = Field(..., ge=0)
    proteins_with_unmatched_peptides: int = Field(..., ge=0)
    total_regions: int = Field(..., ge=0)
    total_residues: int = Field(..., ge=0)
    total_covered_residues: int = Field(..., ge=0)
    mean_coverage_fraction: float = Field(..., ge=0.0, le=1.0)


class ProteinCoverageProteinEntry(JsonModel):
    """One protein coverage row with matched and uncovered interval state."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    residue_count: int = Field(..., ge=1)
    covered_residue_count: int = Field(..., ge=0)
    coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    covered_ranges: tuple[tuple[int, int], ...] = Field(default_factory=tuple)
    uncovered_ranges: tuple[tuple[int, int], ...] = Field(default_factory=tuple)
    covered_region_count: int = Field(..., ge=0)
    uncovered_region_count: int = Field(..., ge=0)
    covered_peptides: tuple[str, ...] = Field(default_factory=tuple)
    unmatched_peptides: tuple[str, ...] = Field(default_factory=tuple)
    unique_peptides: tuple[str, ...] = Field(default_factory=tuple)
    shared_peptides: tuple[str, ...] = Field(default_factory=tuple)
    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    matched_peptide_count: int = Field(..., ge=0)
    unmatched_peptide_count: int = Field(..., ge=0)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel
    contaminant_flag: bool = False


class ProteinCoverageRegionEntry(JsonModel):
    """One contiguous covered protein region."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    region_index: int = Field(..., ge=1)
    start_residue: int = Field(..., ge=1)
    end_residue: int = Field(..., ge=1)
    residue_count: int = Field(..., ge=1)


class ProteinCoverageUncoveredRegionEntry(JsonModel):
    """One contiguous uncovered protein region."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    region_index: int = Field(..., ge=1)
    start_residue: int = Field(..., ge=1)
    end_residue: int = Field(..., ge=1)
    residue_count: int = Field(..., ge=1)


class ProteinCoveragePeptideCoordinateEntry(JsonModel):
    """One peptide-to-protein coordinate row."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    coordinate_status: ProteinCoverageCoordinateStatus
    occurrence_index: int | None = Field(default=None, ge=1)
    start_residue: int | None = Field(default=None, ge=1)
    end_residue: int | None = Field(default=None, ge=1)
    unique_peptide: bool = False
    shared_peptide: bool = False
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel
    contaminant_flag: bool = False


class ProteinCoverageReport(JsonModel):
    """Stable owner report over protein coverage, intervals, and peptide coordinates."""

    model_config = ConfigDict(extra="forbid")

    threshold: float | None = Field(default=None, ge=0.0)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    summary: ProteinCoverageSummary
    missing_sequence_proteins: tuple[str, ...] = Field(default_factory=tuple)
    entries: tuple[ProteinCoverageProteinEntry, ...] = Field(default_factory=tuple)
    regions: tuple[ProteinCoverageRegionEntry, ...] = Field(default_factory=tuple)
    uncovered_regions: tuple[ProteinCoverageUncoveredRegionEntry, ...] = Field(
        default_factory=tuple
    )
    peptide_coordinates: tuple[ProteinCoveragePeptideCoordinateEntry, ...] = Field(
        default_factory=tuple
    )
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)


def build_protein_coverage_report(
    records: tuple[PsmRecord, ...],
    *,
    protein_sequences: dict[str, str],
    threshold: float | None = None,
    score_orientation: str = "higher_better",
) -> ProteinCoverageReport:
    """Build one direct owner report over sequence-backed protein coverage."""
    peptide_rollups = rollup_peptide_evidence(records)
    peptide_sequences = _build_peptide_sequence_index(records)
    protein_to_peptides: dict[str, list[PeptideEvidenceEntry]] = defaultdict(list)
    for rollup in peptide_rollups:
        for protein_ref in rollup.protein_refs:
            protein_to_peptides[protein_ref].append(rollup)

    missing_sequence_proteins = tuple(
        protein_ref
        for protein_ref in sorted(protein_to_peptides)
        if protein_ref not in protein_sequences
    )
    entries: list[ProteinCoverageProteinEntry] = []
    regions: list[ProteinCoverageRegionEntry] = []
    uncovered_regions: list[ProteinCoverageUncoveredRegionEntry] = []
    peptide_coordinates: list[ProteinCoveragePeptideCoordinateEntry] = []
    for protein_ref in sorted(protein_to_peptides):
        sequence = protein_sequences.get(protein_ref)
        if sequence is None:
            continue
        (
            entry,
            covered_regions,
            uncovered_region_rows,
            coordinate_rows,
        ) = _build_coverage_entry(
            protein_ref,
            sequence=sequence,
            peptide_rollups=protein_to_peptides[protein_ref],
            peptide_sequences=peptide_sequences,
        )
        entries.append(entry)
        regions.extend(covered_regions)
        uncovered_regions.extend(uncovered_region_rows)
        peptide_coordinates.extend(coordinate_rows)

    proteins_with_sequence = len(entries)
    total_covered_residues = sum(entry.covered_residue_count for entry in entries)
    total_residues = sum(entry.residue_count for entry in entries)
    summary = ProteinCoverageSummary(
        total_proteins=len(protein_to_peptides),
        proteins_with_sequence=proteins_with_sequence,
        proteins_missing_sequence=len(missing_sequence_proteins),
        fully_uncovered_proteins=sum(
            1 for entry in entries if entry.covered_residue_count == 0
        ),
        proteins_with_unique_peptides=sum(
            1 for entry in entries if entry.unique_peptide_count > 0
        ),
        proteins_with_shared_peptides=sum(
            1 for entry in entries if entry.shared_peptide_count > 0
        ),
        proteins_with_unmatched_peptides=sum(
            1 for entry in entries if entry.unmatched_peptide_count > 0
        ),
        total_regions=len(regions),
        total_residues=total_residues,
        total_covered_residues=total_covered_residues,
        mean_coverage_fraction=(
            sum(entry.coverage_fraction for entry in entries) / proteins_with_sequence
            if proteins_with_sequence
            else 0.0
        ),
    )
    report = ProteinCoverageReport(
        threshold=threshold,
        score_orientation=score_orientation,
        summary=summary,
        missing_sequence_proteins=missing_sequence_proteins,
        entries=tuple(entries),
        regions=tuple(regions),
        uncovered_regions=tuple(uncovered_regions),
        peptide_coordinates=tuple(peptide_coordinates),
        reproducibility_hash="0" * 64,
    )
    return report.model_copy(
        update={"reproducibility_hash": hashlib.sha256(_raw_payload(report)).hexdigest()}
    )


def render_protein_coverage_summary_tsv(report: ProteinCoverageReport) -> str:
    """Render the protein coverage summary ledger as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("metric", "value"))
    for metric, value in (
        ("threshold", "" if report.threshold is None else report.threshold),
        ("score_orientation", report.score_orientation),
        ("total_proteins", report.summary.total_proteins),
        ("proteins_with_sequence", report.summary.proteins_with_sequence),
        ("proteins_missing_sequence", report.summary.proteins_missing_sequence),
        ("fully_uncovered_proteins", report.summary.fully_uncovered_proteins),
        ("proteins_with_unique_peptides", report.summary.proteins_with_unique_peptides),
        ("proteins_with_shared_peptides", report.summary.proteins_with_shared_peptides),
        (
            "proteins_with_unmatched_peptides",
            report.summary.proteins_with_unmatched_peptides,
        ),
        ("total_regions", report.summary.total_regions),
        ("total_residues", report.summary.total_residues),
        ("total_covered_residues", report.summary.total_covered_residues),
        ("mean_coverage_fraction", report.summary.mean_coverage_fraction),
        ("missing_sequence_proteins", ";".join(report.missing_sequence_proteins)),
        ("reproducibility_hash", report.reproducibility_hash),
    ):
        writer.writerow((metric, value))
    return buffer.getvalue()


def render_protein_coverage_entries_tsv(report: ProteinCoverageReport) -> str:
    """Render the protein coverage table as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_ref",
            "residue_count",
            "covered_residue_count",
            "coverage_fraction",
            "covered_ranges",
            "covered_region_count",
            "covered_peptides",
            "unmatched_peptides",
            "unique_peptides",
            "shared_peptides",
            "peptide_count",
            "unique_peptide_count",
            "shared_peptide_count",
            "matched_peptide_count",
            "unmatched_peptide_count",
            "best_score",
            "best_q_value",
            "target_decoy_label",
            "contaminant_flag",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.protein_ref,
                entry.residue_count,
                entry.covered_residue_count,
                entry.coverage_fraction,
                ";".join(
                    f"{start_residue}-{end_residue}"
                    for start_residue, end_residue in entry.covered_ranges
                ),
                entry.covered_region_count,
                ";".join(entry.covered_peptides),
                ";".join(entry.unmatched_peptides),
                ";".join(entry.unique_peptides),
                ";".join(entry.shared_peptides),
                entry.peptide_count,
                entry.unique_peptide_count,
                entry.shared_peptide_count,
                entry.matched_peptide_count,
                entry.unmatched_peptide_count,
                entry.best_score,
                "" if entry.best_q_value is None else entry.best_q_value,
                entry.target_decoy_label.value,
                str(entry.contaminant_flag).lower(),
            )
        )
    return buffer.getvalue()


def render_protein_coverage_regions_tsv(report: ProteinCoverageReport) -> str:
    """Render covered protein regions as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_ref",
            "region_index",
            "start_residue",
            "end_residue",
            "residue_count",
        )
    )
    for entry in report.regions:
        writer.writerow(
            (
                entry.protein_ref,
                entry.region_index,
                entry.start_residue,
                entry.end_residue,
                entry.residue_count,
            )
        )
    return buffer.getvalue()


def render_protein_coverage_uncovered_regions_tsv(report: ProteinCoverageReport) -> str:
    """Render uncovered protein regions as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_ref",
            "region_index",
            "start_residue",
            "end_residue",
            "residue_count",
        )
    )
    for entry in report.uncovered_regions:
        writer.writerow(
            (
                entry.protein_ref,
                entry.region_index,
                entry.start_residue,
                entry.end_residue,
                entry.residue_count,
            )
        )
    return buffer.getvalue()


def render_protein_coverage_peptide_coordinates_tsv(
    report: ProteinCoverageReport,
) -> str:
    """Render peptide-to-protein coordinate rows as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_ref",
            "canonical_peptide",
            "peptide_sequence",
            "coordinate_status",
            "occurrence_index",
            "start_residue",
            "end_residue",
            "unique_peptide",
            "shared_peptide",
            "best_score",
            "best_q_value",
            "target_decoy_label",
            "contaminant_flag",
        )
    )
    for entry in report.peptide_coordinates:
        writer.writerow(
            (
                entry.protein_ref,
                entry.canonical_peptide,
                entry.peptide_sequence,
                entry.coordinate_status.value,
                "" if entry.occurrence_index is None else entry.occurrence_index,
                "" if entry.start_residue is None else entry.start_residue,
                "" if entry.end_residue is None else entry.end_residue,
                str(entry.unique_peptide).lower(),
                str(entry.shared_peptide).lower(),
                entry.best_score,
                "" if entry.best_q_value is None else entry.best_q_value,
                entry.target_decoy_label.value,
                str(entry.contaminant_flag).lower(),
            )
        )
    return buffer.getvalue()


def _build_coverage_entry(
    protein_ref: str,
    *,
    sequence: str,
    peptide_rollups: list[PeptideEvidenceEntry],
    peptide_sequences: dict[str, str],
) -> tuple[
    ProteinCoverageProteinEntry,
    tuple[ProteinCoverageRegionEntry, ...],
    tuple[ProteinCoverageUncoveredRegionEntry, ...],
    tuple[ProteinCoveragePeptideCoordinateEntry, ...],
]:
    covered_positions: set[int] = set()
    covered_peptides: list[str] = []
    unmatched_peptides: list[str] = []
    unique_peptides: list[str] = []
    shared_peptides: list[str] = []
    coordinate_rows: list[ProteinCoveragePeptideCoordinateEntry] = []
    best_score = float("-inf")
    q_values: list[float] = []

    for rollup in sorted(peptide_rollups, key=lambda entry: entry.canonical_peptide):
        peptide = rollup.canonical_peptide
        peptide_sequence = peptide_sequences[peptide]
        unique_peptide = len(rollup.protein_refs) == 1
        shared_peptide = not unique_peptide
        if unique_peptide:
            unique_peptides.append(peptide)
        else:
            shared_peptides.append(peptide)
        matched_ranges = _find_peptide_ranges(sequence, peptide_sequence)
        if matched_ranges:
            covered_peptides.append(peptide)
            for occurrence_index, (start_residue, end_residue) in enumerate(
                matched_ranges,
                start=1,
            ):
                covered_positions.update(range(start_residue, end_residue + 1))
                coordinate_rows.append(
                    ProteinCoveragePeptideCoordinateEntry(
                        protein_ref=protein_ref,
                        canonical_peptide=peptide,
                        peptide_sequence=peptide_sequence,
                        coordinate_status=ProteinCoverageCoordinateStatus.MATCHED,
                        occurrence_index=occurrence_index,
                        start_residue=start_residue,
                        end_residue=end_residue,
                        unique_peptide=unique_peptide,
                        shared_peptide=shared_peptide,
                        best_score=rollup.best_score,
                        best_q_value=rollup.best_q_value,
                        target_decoy_label=_protein_target_decoy_label(protein_ref),
                        contaminant_flag=_protein_contaminant_flag(protein_ref),
                    )
                )
        else:
            unmatched_peptides.append(peptide)
            coordinate_rows.append(
                ProteinCoveragePeptideCoordinateEntry(
                    protein_ref=protein_ref,
                    canonical_peptide=peptide,
                    peptide_sequence=peptide_sequence,
                    coordinate_status=ProteinCoverageCoordinateStatus.UNMATCHED,
                    occurrence_index=None,
                    start_residue=None,
                    end_residue=None,
                    unique_peptide=unique_peptide,
                    shared_peptide=shared_peptide,
                    best_score=rollup.best_score,
                    best_q_value=rollup.best_q_value,
                    target_decoy_label=_protein_target_decoy_label(protein_ref),
                    contaminant_flag=_protein_contaminant_flag(protein_ref),
                )
            )
        best_score = max(best_score, rollup.best_score)
        if rollup.best_q_value is not None:
            q_values.append(rollup.best_q_value)

    covered_ranges = _ranges_from_positions(covered_positions)
    uncovered_ranges = _uncovered_ranges(
        sequence_length=len(sequence),
        covered_ranges=covered_ranges,
    )
    entry = ProteinCoverageProteinEntry(
        protein_ref=protein_ref,
        residue_count=len(sequence),
        covered_residue_count=len(covered_positions),
        coverage_fraction=(
            min(len(covered_positions) / len(sequence), 1.0) if sequence else 0.0
        ),
        covered_ranges=covered_ranges,
        uncovered_ranges=uncovered_ranges,
        covered_region_count=len(covered_ranges),
        uncovered_region_count=len(uncovered_ranges),
        covered_peptides=tuple(covered_peptides),
        unmatched_peptides=tuple(unmatched_peptides),
        unique_peptides=tuple(unique_peptides),
        shared_peptides=tuple(shared_peptides),
        peptide_count=len(peptide_rollups),
        unique_peptide_count=len(unique_peptides),
        shared_peptide_count=len(shared_peptides),
        matched_peptide_count=len(covered_peptides),
        unmatched_peptide_count=len(unmatched_peptides),
        best_score=best_score,
        best_q_value=min(q_values) if q_values else None,
        target_decoy_label=_protein_target_decoy_label(protein_ref),
        contaminant_flag=_protein_contaminant_flag(protein_ref),
    )
    covered_region_rows = tuple(
        ProteinCoverageRegionEntry(
            protein_ref=protein_ref,
            region_index=region_index,
            start_residue=start_residue,
            end_residue=end_residue,
            residue_count=end_residue - start_residue + 1,
        )
        for region_index, (start_residue, end_residue) in enumerate(
            covered_ranges,
            start=1,
        )
    )
    uncovered_region_rows = tuple(
        ProteinCoverageUncoveredRegionEntry(
            protein_ref=protein_ref,
            region_index=region_index,
            start_residue=start_residue,
            end_residue=end_residue,
            residue_count=end_residue - start_residue + 1,
        )
        for region_index, (start_residue, end_residue) in enumerate(
            uncovered_ranges,
            start=1,
        )
    )
    return (
        entry,
        covered_region_rows,
        uncovered_region_rows,
        tuple(coordinate_rows),
    )


def _build_peptide_sequence_index(records: tuple[PsmRecord, ...]) -> dict[str, str]:
    peptide_sequences: dict[str, str] = {}
    for record in records:
        peptide_sequences.setdefault(
            record.canonical_peptide,
            record.peptide_sequence or record.peptide,
        )
    return peptide_sequences


def _find_peptide_ranges(
    sequence: str,
    peptide_sequence: str,
) -> tuple[tuple[int, int], ...]:
    ranges: list[tuple[int, int]] = []
    start = sequence.find(peptide_sequence)
    while start != -1:
        end = start + len(peptide_sequence)
        ranges.append((start + 1, end))
        start = sequence.find(peptide_sequence, start + 1)
    return tuple(ranges)


def _ranges_from_positions(
    covered_positions: set[int],
) -> tuple[tuple[int, int], ...]:
    if not covered_positions:
        return ()
    sorted_positions = sorted(covered_positions)
    ranges: list[tuple[int, int]] = []
    start_residue = sorted_positions[0]
    previous_residue = sorted_positions[0]
    for residue in sorted_positions[1:]:
        if residue == previous_residue + 1:
            previous_residue = residue
            continue
        ranges.append((start_residue, previous_residue))
        start_residue = residue
        previous_residue = residue
    ranges.append((start_residue, previous_residue))
    return tuple(ranges)


def _uncovered_ranges(
    *,
    sequence_length: int,
    covered_ranges: tuple[tuple[int, int], ...],
) -> tuple[tuple[int, int], ...]:
    if sequence_length <= 0:
        return ()
    if not covered_ranges:
        return ((1, sequence_length),)
    uncovered: list[tuple[int, int]] = []
    next_start = 1
    for start_residue, end_residue in covered_ranges:
        if next_start < start_residue:
            uncovered.append((next_start, start_residue - 1))
        next_start = end_residue + 1
    if next_start <= sequence_length:
        uncovered.append((next_start, sequence_length))
    return tuple(uncovered)


def _protein_target_decoy_label(protein_ref: str) -> TargetDecoyLabel:
    return (
        TargetDecoyLabel.DECOY
        if protein_ref.startswith("DECOY_")
        else TargetDecoyLabel.TARGET
    )


def _protein_contaminant_flag(protein_ref: str) -> bool:
    return protein_ref.startswith("CON__")


def _raw_payload(report: ProteinCoverageReport) -> bytes:
    payload = {
        "threshold": report.threshold,
        "score_orientation": report.score_orientation,
        "summary": report.summary.to_dict(),
        "missing_sequence_proteins": list(report.missing_sequence_proteins),
        "entries": [entry.to_dict() for entry in report.entries],
        "regions": [entry.to_dict() for entry in report.regions],
        "uncovered_regions": [entry.to_dict() for entry in report.uncovered_regions],
        "peptide_coordinates": [
            entry.to_dict() for entry in report.peptide_coordinates
        ],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
