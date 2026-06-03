# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned protein grouping engine over observed peptide evidence."""

from __future__ import annotations

from collections import defaultdict
import csv
import hashlib
import io
import json

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    PeptideEvidenceEntry,
    PsmRecord,
    TargetDecoyLabel,
    parse_target_decoy_label,
    rollup_peptide_evidence,
)
from bijux_proteomics_foundation import JsonModel


class ProteinGroupingSummary(JsonModel):
    """Compact summary over grouped protein evidence."""

    model_config = ConfigDict(extra="forbid")

    total_groups: int = Field(..., ge=0)
    total_proteins: int = Field(..., ge=0)
    singleton_group_count: int = Field(..., ge=0)
    ambiguous_group_count: int = Field(..., ge=0)
    grouped_protein_count: int = Field(..., ge=0)
    target_group_count: int = Field(..., ge=0)
    decoy_group_count: int = Field(..., ge=0)
    mixed_group_count: int = Field(..., ge=0)
    unknown_group_count: int = Field(..., ge=0)
    contaminant_group_count: int = Field(..., ge=0)


class ProteinGroupingEntry(JsonModel):
    """One grouped protein entity with leading-protein and peptide ledgers."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., min_length=1)
    representative_protein: str = Field(..., min_length=1)
    leading_protein: str = Field(..., min_length=1)
    leading_rationale: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    peptides: tuple[str, ...] = Field(default_factory=tuple)
    unique_peptides: tuple[str, ...] = Field(default_factory=tuple)
    shared_peptides: tuple[str, ...] = Field(default_factory=tuple)
    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel
    contaminant_flag: bool = False


class ProteinGroupingReport(JsonModel):
    """Stable owned report over grouped protein evidence."""

    model_config = ConfigDict(extra="forbid")

    summary: ProteinGroupingSummary
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)
    groups: tuple[ProteinGroupingEntry, ...] = Field(default_factory=tuple)


def build_protein_grouping_report(
    records: tuple[PsmRecord, ...],
) -> ProteinGroupingReport:
    """Group proteins by the exact peptide evidence set they explain."""
    peptide_rollups = {
        rollup.canonical_peptide: rollup for rollup in rollup_peptide_evidence(records)
    }
    protein_to_peptides: dict[str, set[str]] = defaultdict(set)
    protein_to_scores: dict[str, list[float]] = defaultdict(list)
    protein_to_q_values: dict[str, list[float]] = defaultdict(list)

    for peptide_rollup in peptide_rollups.values():
        for protein_ref in peptide_rollup.protein_refs:
            protein_to_peptides[protein_ref].add(peptide_rollup.canonical_peptide)
            protein_to_scores[protein_ref].append(peptide_rollup.best_score)
            if peptide_rollup.best_q_value is not None:
                protein_to_q_values[protein_ref].append(peptide_rollup.best_q_value)

    grouped: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for protein_ref, peptides in protein_to_peptides.items():
        grouped[tuple(sorted(peptides))].append(protein_ref)

    unique_counts, best_scores = _build_protein_ranking_context(peptide_rollups)
    groups: list[ProteinGroupingEntry] = []
    for index, (peptide_set, protein_refs) in enumerate(
        sorted(grouped.items()),
        start=1,
    ):
        sorted_proteins = tuple(sorted(protein_refs))
        representative_protein = sorted_proteins[0]
        unique_peptides = tuple(
            peptide
            for peptide in peptide_set
            if len(peptide_rollups[peptide].protein_refs) == 1
        )
        shared_peptides = tuple(
            peptide
            for peptide in peptide_set
            if len(peptide_rollups[peptide].protein_refs) > 1
        )
        leading_protein, leading_rationale = _pick_leading_protein(
            sorted_proteins,
            unique_counts=unique_counts,
            best_scores=best_scores,
        )
        groups.append(
            ProteinGroupingEntry(
                group_id=f"pg-{index:03d}",
                representative_protein=representative_protein,
                leading_protein=leading_protein,
                leading_rationale=leading_rationale,
                protein_refs=sorted_proteins,
                peptides=tuple(peptide_set),
                unique_peptides=unique_peptides,
                shared_peptides=shared_peptides,
                peptide_count=len(peptide_set),
                unique_peptide_count=len(unique_peptides),
                shared_peptide_count=len(shared_peptides),
                best_score=max(
                    max(protein_to_scores[protein_ref])
                    for protein_ref in sorted_proteins
                ),
                best_q_value=min(
                    (
                        q_value
                        for protein_ref in sorted_proteins
                        for q_value in protein_to_q_values[protein_ref]
                    ),
                    default=None,
                ),
                target_decoy_label=parse_target_decoy_label(
                    protein_refs=sorted_proteins
                ),
                contaminant_flag=any(
                    protein_ref.startswith("CON__") for protein_ref in sorted_proteins
                ),
            )
        )

    summary = ProteinGroupingSummary(
        total_groups=len(groups),
        total_proteins=sum(len(group.protein_refs) for group in groups),
        singleton_group_count=sum(
            1 for group in groups if len(group.protein_refs) == 1
        ),
        ambiguous_group_count=sum(1 for group in groups if len(group.protein_refs) > 1),
        grouped_protein_count=sum(
            len(group.protein_refs) for group in groups if len(group.protein_refs) > 1
        ),
        target_group_count=_label_count(groups, TargetDecoyLabel.TARGET),
        decoy_group_count=_label_count(groups, TargetDecoyLabel.DECOY),
        mixed_group_count=_label_count(groups, TargetDecoyLabel.MIXED),
        unknown_group_count=_label_count(groups, TargetDecoyLabel.UNKNOWN),
        contaminant_group_count=sum(1 for group in groups if group.contaminant_flag),
    )
    grouped_entries = tuple(groups)
    return ProteinGroupingReport(
        summary=summary,
        reproducibility_hash=hashlib.sha256(_raw_payload(grouped_entries)).hexdigest(),
        groups=grouped_entries,
    )


def render_protein_grouping_summary_tsv(report: ProteinGroupingReport) -> str:
    """Render the protein grouping summary ledger as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("metric", "value"))
    for metric, value in (
        ("total_groups", report.summary.total_groups),
        ("total_proteins", report.summary.total_proteins),
        ("singleton_group_count", report.summary.singleton_group_count),
        ("ambiguous_group_count", report.summary.ambiguous_group_count),
        ("grouped_protein_count", report.summary.grouped_protein_count),
        ("target_group_count", report.summary.target_group_count),
        ("decoy_group_count", report.summary.decoy_group_count),
        ("mixed_group_count", report.summary.mixed_group_count),
        ("unknown_group_count", report.summary.unknown_group_count),
        ("contaminant_group_count", report.summary.contaminant_group_count),
        ("reproducibility_hash", report.reproducibility_hash),
    ):
        writer.writerow((metric, value))
    return buffer.getvalue()


def render_protein_grouping_entries_tsv(report: ProteinGroupingReport) -> str:
    """Render the protein group table as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "group_id",
            "representative_protein",
            "leading_protein",
            "leading_rationale",
            "protein_refs",
            "peptides",
            "unique_peptides",
            "shared_peptides",
            "peptide_count",
            "unique_peptide_count",
            "shared_peptide_count",
            "best_score",
            "best_q_value",
            "target_decoy_label",
            "contaminant_flag",
        )
    )
    for group in report.groups:
        writer.writerow(
            (
                group.group_id,
                group.representative_protein,
                group.leading_protein,
                group.leading_rationale,
                ";".join(group.protein_refs),
                ";".join(group.peptides),
                ";".join(group.unique_peptides),
                ";".join(group.shared_peptides),
                group.peptide_count,
                group.unique_peptide_count,
                group.shared_peptide_count,
                group.best_score,
                "" if group.best_q_value is None else group.best_q_value,
                group.target_decoy_label.value,
                str(group.contaminant_flag).lower(),
            )
        )
    return buffer.getvalue()


def _build_protein_ranking_context(
    peptide_rollups: dict[str, PeptideEvidenceEntry],
) -> tuple[dict[str, int], dict[str, float]]:
    unique_counts: dict[str, int] = defaultdict(int)
    best_scores: dict[str, float] = defaultdict(float)
    for rollup in peptide_rollups.values():
        for protein_ref in rollup.protein_refs:
            best_scores[protein_ref] = max(best_scores[protein_ref], rollup.best_score)
        if len(rollup.protein_refs) == 1:
            unique_counts[rollup.protein_refs[0]] += 1
    return dict(unique_counts), dict(best_scores)


def _pick_leading_protein(
    protein_refs: tuple[str, ...],
    *,
    unique_counts: dict[str, int],
    best_scores: dict[str, float],
) -> tuple[str, str]:
    if len(protein_refs) == 1:
        return protein_refs[0], "singleton_group"

    ranked = sorted(
        protein_refs,
        key=lambda protein_ref: (
            -unique_counts.get(protein_ref, 0),
            -best_scores.get(protein_ref, float("-inf")),
            protein_ref,
        ),
    )
    leading = ranked[0]
    if unique_counts.get(ranked[0], 0) != unique_counts.get(ranked[-1], 0):
        return leading, "unique_evidence_priority"
    if best_scores.get(ranked[0], 0.0) != best_scores.get(ranked[-1], 0.0):
        return leading, "best_score_tiebreak"
    return leading, "lexicographic_tiebreak"


def _label_count(
    groups: list[ProteinGroupingEntry],
    label: TargetDecoyLabel,
) -> int:
    return sum(1 for group in groups if group.target_decoy_label is label)


def _raw_payload(groups: tuple[ProteinGroupingEntry, ...]) -> bytes:
    payload = [
        {
            "group_id": group.group_id,
            "representative_protein": group.representative_protein,
            "leading_protein": group.leading_protein,
            "leading_rationale": group.leading_rationale,
            "protein_refs": group.protein_refs,
            "peptides": group.peptides,
            "unique_peptides": group.unique_peptides,
            "shared_peptides": group.shared_peptides,
            "peptide_count": group.peptide_count,
            "unique_peptide_count": group.unique_peptide_count,
            "shared_peptide_count": group.shared_peptide_count,
            "best_score": group.best_score,
            "best_q_value": group.best_q_value,
            "target_decoy_label": group.target_decoy_label.value,
            "contaminant_flag": group.contaminant_flag,
        }
        for group in groups
    ]
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
