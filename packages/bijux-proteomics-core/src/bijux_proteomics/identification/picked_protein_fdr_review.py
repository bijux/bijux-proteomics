# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Review-oriented reporting over picked target-decoy protein FDR."""

from __future__ import annotations

import csv
import io

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    PickedProteinFdrEntry,
    PsmRecord,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
    build_shared_peptide_ambiguity_report,
    calculate_picked_protein_fdr,
)
from bijux_proteomics_foundation import JsonModel


class PickedProteinFdrThresholdSummary(JsonModel):
    """Accepted-count summary for one picked-protein FDR threshold."""

    model_config = ConfigDict(extra="forbid")

    threshold: float = Field(..., ge=0.0)
    total_count: int = Field(..., ge=0)
    total_target_count: int = Field(..., ge=0)
    total_decoy_count: int = Field(..., ge=0)
    total_contaminant_count: int = Field(..., ge=0)
    grouped_protein_count: int = Field(..., ge=0)
    accepted_count: int = Field(..., ge=0)
    accepted_target_count: int = Field(..., ge=0)
    accepted_decoy_count: int = Field(..., ge=0)
    accepted_contaminant_count: int = Field(..., ge=0)
    accepted_grouped_protein_count: int = Field(..., ge=0)


class PickedProteinFdrReviewEntry(JsonModel):
    """One picked-protein FDR row with protein-group context."""

    model_config = ConfigDict(extra="forbid")

    threshold: float = Field(..., ge=0.0)
    protein_ref: str = Field(..., min_length=1)
    partner_ref: str | None = None
    protein_group_ids: tuple[str, ...] = Field(default_factory=tuple)
    score: float
    q_value: float = Field(..., ge=0.0)
    fdr: float = Field(..., ge=0.0)
    rank: int = Field(..., ge=1)
    accepted: bool
    target_decoy_label: TargetDecoyLabel
    contaminant_flag: bool
    supporting_peptides: tuple[str, ...] = Field(default_factory=tuple)


class PickedProteinFdrReviewReport(JsonModel):
    """Threshold comparison report over picked-protein FDR entries."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    thresholds: tuple[float, ...] = Field(default_factory=tuple)
    summaries: tuple[PickedProteinFdrThresholdSummary, ...] = Field(
        default_factory=tuple
    )
    entries: tuple[PickedProteinFdrReviewEntry, ...] = Field(default_factory=tuple)


def _entry_contaminant_flag(entry: PickedProteinFdrEntry) -> bool:
    return entry.protein_ref.startswith("CON__")


def build_picked_protein_fdr_review_report(
    records: tuple[PsmRecord, ...],
    *,
    thresholds: tuple[float, ...] = (0.01, 0.05, 0.1),
    score_orientation: str = "higher_better",
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> PickedProteinFdrReviewReport:
    """Build a direct review report over picked-protein FDR thresholds."""
    if not thresholds:
        raise ValueError("thresholds must not be empty")
    normalized_thresholds = tuple(sorted(dict.fromkeys(thresholds)))
    if any(threshold < 0.0 for threshold in normalized_thresholds):
        raise ValueError("thresholds must be non-negative")

    group_ids_by_protein: dict[str, set[str]] = {}
    for ambiguity_entry in build_shared_peptide_ambiguity_report(records).entries:
        for protein_ref in ambiguity_entry.protein_refs:
            group_ids_by_protein.setdefault(protein_ref, set()).add(
                ambiguity_entry.group_id
            )

    summaries: list[PickedProteinFdrThresholdSummary] = []
    entries: list[PickedProteinFdrReviewEntry] = []
    for threshold in normalized_thresholds:
        picked_entries = calculate_picked_protein_fdr(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
            decoy_policy=decoy_policy,
        )
        accepted_entries = tuple(entry for entry in picked_entries if entry.accepted)
        summaries.append(
            PickedProteinFdrThresholdSummary(
                threshold=threshold,
                total_count=len(picked_entries),
                total_target_count=sum(
                    1
                    for entry in picked_entries
                    if entry.target_decoy_label is TargetDecoyLabel.TARGET
                ),
                total_decoy_count=sum(
                    1
                    for entry in picked_entries
                    if entry.target_decoy_label is TargetDecoyLabel.DECOY
                ),
                total_contaminant_count=sum(
                    1 for entry in picked_entries if _entry_contaminant_flag(entry)
                ),
                grouped_protein_count=sum(
                    1
                    for entry in picked_entries
                    if group_ids_by_protein.get(entry.protein_ref)
                ),
                accepted_count=len(accepted_entries),
                accepted_target_count=sum(
                    1
                    for entry in accepted_entries
                    if entry.target_decoy_label is TargetDecoyLabel.TARGET
                ),
                accepted_decoy_count=sum(
                    1
                    for entry in accepted_entries
                    if entry.target_decoy_label is TargetDecoyLabel.DECOY
                ),
                accepted_contaminant_count=sum(
                    1 for entry in accepted_entries if _entry_contaminant_flag(entry)
                ),
                accepted_grouped_protein_count=sum(
                    1
                    for entry in accepted_entries
                    if group_ids_by_protein.get(entry.protein_ref)
                ),
            )
        )
        for entry in picked_entries:
            entries.append(
                PickedProteinFdrReviewEntry(
                    threshold=threshold,
                    protein_ref=entry.protein_ref,
                    partner_ref=entry.partner_ref,
                    protein_group_ids=tuple(
                        sorted(group_ids_by_protein.get(entry.protein_ref, set()))
                    ),
                    score=entry.score,
                    q_value=entry.q_value,
                    fdr=entry.fdr,
                    rank=entry.rank,
                    accepted=entry.accepted,
                    target_decoy_label=entry.target_decoy_label,
                    contaminant_flag=_entry_contaminant_flag(entry),
                    supporting_peptides=entry.supporting_peptides,
                )
            )
    return PickedProteinFdrReviewReport(
        score_orientation=score_orientation,
        thresholds=normalized_thresholds,
        summaries=tuple(summaries),
        entries=tuple(entries),
    )


def render_picked_protein_fdr_summary_tsv(report: PickedProteinFdrReviewReport) -> str:
    """Render picked-protein threshold summaries."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "threshold",
            "total_count",
            "total_target_count",
            "total_decoy_count",
            "total_contaminant_count",
            "grouped_protein_count",
            "accepted_count",
            "accepted_target_count",
            "accepted_decoy_count",
            "accepted_contaminant_count",
            "accepted_grouped_protein_count",
        )
    )
    for summary in report.summaries:
        writer.writerow(
            (
                summary.threshold,
                summary.total_count,
                summary.total_target_count,
                summary.total_decoy_count,
                summary.total_contaminant_count,
                summary.grouped_protein_count,
                summary.accepted_count,
                summary.accepted_target_count,
                summary.accepted_decoy_count,
                summary.accepted_contaminant_count,
                summary.accepted_grouped_protein_count,
            )
        )
    return buffer.getvalue()


def render_picked_protein_fdr_entries_tsv(report: PickedProteinFdrReviewReport) -> str:
    """Render picked-protein review rows across thresholds."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "threshold",
            "protein_ref",
            "partner_ref",
            "protein_group_ids",
            "score",
            "q_value",
            "fdr",
            "rank",
            "accepted",
            "target_decoy_label",
            "contaminant_flag",
            "supporting_peptides",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.threshold,
                entry.protein_ref,
                "" if entry.partner_ref is None else entry.partner_ref,
                ";".join(entry.protein_group_ids),
                entry.score,
                entry.q_value,
                entry.fdr,
                entry.rank,
                str(entry.accepted).lower(),
                entry.target_decoy_label.value,
                str(entry.contaminant_flag).lower(),
                ";".join(entry.supporting_peptides),
            )
        )
    return buffer.getvalue()
