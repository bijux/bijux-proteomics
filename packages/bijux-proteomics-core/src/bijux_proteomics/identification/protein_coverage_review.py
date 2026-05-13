# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Reviewer-facing protein coverage summaries and ledgers."""

from __future__ import annotations

import csv
import io
from collections import defaultdict

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    PsmRecord,
    TargetDecoyLabel,
    rollup_peptide_evidence,
)
from bijux_proteomics_foundation import JsonModel


class ProteinCoverageReviewSummary(JsonModel):
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


class ProteinCoverageReviewEntry(JsonModel):
    """One protein coverage review row."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    residue_count: int = Field(..., ge=1)
    covered_residue_count: int = Field(..., ge=0)
    coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    covered_ranges: tuple[tuple[int, int], ...] = Field(default_factory=tuple)
    covered_region_count: int = Field(..., ge=0)
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


class ProteinCoverageReviewReport(JsonModel):
    """One owned review packet over sequence-backed protein coverage."""

    model_config = ConfigDict(extra="forbid")

    threshold: float | None = Field(default=None, ge=0.0)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    summary: ProteinCoverageReviewSummary
    missing_sequence_proteins: tuple[str, ...] = Field(default_factory=tuple)
    entries: tuple[ProteinCoverageReviewEntry, ...] = Field(default_factory=tuple)
    regions: tuple[ProteinCoverageRegionEntry, ...] = Field(default_factory=tuple)


def build_protein_coverage_review_report(
    records: tuple[PsmRecord, ...],
    *,
    protein_sequences: dict[str, str],
    threshold: float | None = None,
    score_orientation: str = "higher_better",
) -> ProteinCoverageReviewReport:
    """Build one direct review report over sequence-backed protein coverage."""
    peptide_rollups = rollup_peptide_evidence(records)
    peptide_sequences = _build_peptide_sequence_index(records)
    protein_to_peptides: dict[str, list] = defaultdict(list)
    for rollup in peptide_rollups:
        for protein_ref in rollup.protein_refs:
            protein_to_peptides[protein_ref].append(rollup)

    missing_sequence_proteins = tuple(
        protein_ref
        for protein_ref in sorted(protein_to_peptides)
        if protein_ref not in protein_sequences
    )
    entries: list[ProteinCoverageReviewEntry] = []
    regions: list[ProteinCoverageRegionEntry] = []
    for protein_ref in sorted(protein_to_peptides):
        sequence = protein_sequences.get(protein_ref)
        if sequence is None:
            continue
        coverage = _build_coverage_entry(
            protein_ref,
            sequence=sequence,
            peptide_rollups=protein_to_peptides[protein_ref],
            peptide_sequences=peptide_sequences,
        )
        entries.append(coverage)
        for region_index, (start_residue, end_residue) in enumerate(
            coverage.covered_ranges,
            start=1,
        ):
            regions.append(
                ProteinCoverageRegionEntry(
                    protein_ref=protein_ref,
                    region_index=region_index,
                    start_residue=start_residue,
                    end_residue=end_residue,
                    residue_count=end_residue - start_residue + 1,
                )
            )

    proteins_with_sequence = len(entries)
    total_covered_residues = sum(entry.covered_residue_count for entry in entries)
    total_residues = sum(entry.residue_count for entry in entries)
    return ProteinCoverageReviewReport(
        threshold=threshold,
        score_orientation=score_orientation,
        summary=ProteinCoverageReviewSummary(
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
        ),
        missing_sequence_proteins=missing_sequence_proteins,
        entries=tuple(entries),
        regions=tuple(regions),
    )


def render_protein_coverage_summary_tsv(report: ProteinCoverageReviewReport) -> str:
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
    ):
        writer.writerow((metric, value))
    return buffer.getvalue()


def render_protein_coverage_entries_tsv(report: ProteinCoverageReviewReport) -> str:
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


def render_protein_coverage_regions_tsv(report: ProteinCoverageReviewReport) -> str:
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


def _build_coverage_entry(
    protein_ref: str,
    *,
    sequence: str,
    peptide_rollups: list,
    peptide_sequences: dict[str, str],
) -> ProteinCoverageReviewEntry:
    covered_positions: set[int] = set()
    covered_ranges: set[tuple[int, int]] = set()
    covered_peptides: list[str] = []
    unmatched_peptides: list[str] = []
    unique_peptides: list[str] = []
    shared_peptides: list[str] = []
    best_score = float("-inf")
    q_values: list[float] = []

    for rollup in sorted(peptide_rollups, key=lambda entry: entry.canonical_peptide):
        peptide = rollup.canonical_peptide
        peptide_sequence = peptide_sequences[peptide]
        if len(rollup.protein_refs) == 1:
            unique_peptides.append(peptide)
        else:
            shared_peptides.append(peptide)
        matched = False
        start = sequence.find(peptide_sequence)
        while start != -1:
            matched = True
            end = start + len(peptide_sequence)
            covered_ranges.add((start + 1, end))
            covered_positions.update(range(start + 1, end + 1))
            start = sequence.find(peptide_sequence, start + 1)
        if matched:
            covered_peptides.append(peptide)
        else:
            unmatched_peptides.append(peptide)
        best_score = max(best_score, rollup.best_score)
        if rollup.best_q_value is not None:
            q_values.append(rollup.best_q_value)

    return ProteinCoverageReviewEntry(
        protein_ref=protein_ref,
        residue_count=len(sequence),
        covered_residue_count=len(covered_positions),
        coverage_fraction=(
            min(len(covered_positions) / len(sequence), 1.0) if sequence else 0.0
        ),
        covered_ranges=tuple(sorted(covered_ranges)),
        covered_region_count=len(covered_ranges),
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
        target_decoy_label=TargetDecoyLabel.DECOY
        if protein_ref.startswith("DECOY_")
        else TargetDecoyLabel.TARGET,
        contaminant_flag=protein_ref.startswith("CON__"),
    )


def _build_peptide_sequence_index(records: tuple[PsmRecord, ...]) -> dict[str, str]:
    peptide_sequences: dict[str, str] = {}
    for record in records:
        peptide_sequences.setdefault(
            record.canonical_peptide,
            record.peptide_sequence or record.canonical_peptide,
        )
    return peptide_sequences
