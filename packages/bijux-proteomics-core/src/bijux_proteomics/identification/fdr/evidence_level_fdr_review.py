# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Review-oriented reporting over separate PSM, peptide, and protein FDR."""

from __future__ import annotations

import csv
import io

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    FdrEvidenceLevel,
    FdrLevelEntry,
    PsmRecord,
    TargetDecoyLabel,
    calculate_level_specific_fdr,
)
from bijux_proteomics_foundation import JsonModel


class EvidenceLevelFdrThresholdSummary(JsonModel):
    """Accepted-count summary for one evidence level at one FDR threshold."""

    model_config = ConfigDict(extra="forbid")

    threshold: float = Field(..., ge=0.0)
    evidence_level: FdrEvidenceLevel
    total_count: int = Field(..., ge=0)
    total_target_count: int = Field(..., ge=0)
    total_decoy_count: int = Field(..., ge=0)
    total_mixed_count: int = Field(..., ge=0)
    total_unknown_count: int = Field(..., ge=0)
    total_contaminant_count: int = Field(..., ge=0)
    accepted_count: int = Field(..., ge=0)
    accepted_target_count: int = Field(..., ge=0)
    accepted_decoy_count: int = Field(..., ge=0)
    accepted_mixed_count: int = Field(..., ge=0)
    accepted_unknown_count: int = Field(..., ge=0)
    accepted_contaminant_count: int = Field(..., ge=0)


class EvidenceLevelFdrAcceptedEntry(JsonModel):
    """One accepted entity at one evidence level and one FDR threshold."""

    model_config = ConfigDict(extra="forbid")

    threshold: float = Field(..., ge=0.0)
    evidence_level: FdrEvidenceLevel
    entity_id: str = Field(..., min_length=1)
    rank: int = Field(..., ge=1)
    score: float
    q_value: float = Field(..., ge=0.0)
    target_decoy_label: TargetDecoyLabel
    contaminant_flag: bool
    member_count: int = Field(..., ge=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)


class EvidenceLevelFdrReviewReport(JsonModel):
    """Comparison report over PSM, peptide, and protein FDR thresholds."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    thresholds: tuple[float, ...] = Field(default_factory=tuple)
    summaries: tuple[EvidenceLevelFdrThresholdSummary, ...] = Field(
        default_factory=tuple
    )
    accepted_entries: tuple[EvidenceLevelFdrAcceptedEntry, ...] = Field(
        default_factory=tuple
    )


def _entry_contaminant_flag(entry: FdrLevelEntry) -> bool:
    return any(protein_ref.startswith("CON__") for protein_ref in entry.protein_refs)


def _label_count(entries: tuple[FdrLevelEntry, ...], label: TargetDecoyLabel) -> int:
    return sum(1 for entry in entries if entry.target_decoy_label is label)


def _build_threshold_summary(
    *,
    threshold: float,
    evidence_level: FdrEvidenceLevel,
    entries: tuple[FdrLevelEntry, ...],
) -> EvidenceLevelFdrThresholdSummary:
    accepted_entries = tuple(entry for entry in entries if entry.accepted)
    return EvidenceLevelFdrThresholdSummary(
        threshold=threshold,
        evidence_level=evidence_level,
        total_count=len(entries),
        total_target_count=_label_count(entries, TargetDecoyLabel.TARGET),
        total_decoy_count=_label_count(entries, TargetDecoyLabel.DECOY),
        total_mixed_count=_label_count(entries, TargetDecoyLabel.MIXED),
        total_unknown_count=_label_count(entries, TargetDecoyLabel.UNKNOWN),
        total_contaminant_count=sum(
            1 for entry in entries if _entry_contaminant_flag(entry)
        ),
        accepted_count=len(accepted_entries),
        accepted_target_count=_label_count(accepted_entries, TargetDecoyLabel.TARGET),
        accepted_decoy_count=_label_count(accepted_entries, TargetDecoyLabel.DECOY),
        accepted_mixed_count=_label_count(accepted_entries, TargetDecoyLabel.MIXED),
        accepted_unknown_count=_label_count(accepted_entries, TargetDecoyLabel.UNKNOWN),
        accepted_contaminant_count=sum(
            1 for entry in accepted_entries if _entry_contaminant_flag(entry)
        ),
    )


def build_evidence_level_fdr_review_report(
    records: tuple[PsmRecord, ...],
    *,
    thresholds: tuple[float, ...] = (0.01, 0.05, 0.1),
    score_orientation: str = "higher_better",
) -> EvidenceLevelFdrReviewReport:
    """Build a direct comparison report over PSM, peptide, and protein FDR."""
    if not thresholds:
        raise ValueError("thresholds must not be empty")
    normalized_thresholds = tuple(sorted(dict.fromkeys(thresholds)))
    if any(threshold < 0.0 for threshold in normalized_thresholds):
        raise ValueError("thresholds must be non-negative")

    summaries: list[EvidenceLevelFdrThresholdSummary] = []
    accepted_entries: list[EvidenceLevelFdrAcceptedEntry] = []
    for threshold in normalized_thresholds:
        level_report = calculate_level_specific_fdr(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        entry_sets = (
            level_report.psm_entries,
            level_report.peptide_entries,
            level_report.protein_entries,
        )
        for entries in entry_sets:
            evidence_level = entries[0].evidence_level if entries else None
            if evidence_level is None:
                continue
            summaries.append(
                _build_threshold_summary(
                    threshold=threshold,
                    evidence_level=evidence_level,
                    entries=entries,
                )
            )
            for entry in entries:
                if not entry.accepted:
                    continue
                accepted_entries.append(
                    EvidenceLevelFdrAcceptedEntry(
                        threshold=threshold,
                        evidence_level=evidence_level,
                        entity_id=entry.entity_id,
                        rank=entry.rank,
                        score=entry.score,
                        q_value=entry.q_value,
                        target_decoy_label=entry.target_decoy_label,
                        contaminant_flag=_entry_contaminant_flag(entry),
                        member_count=entry.member_count,
                        protein_refs=entry.protein_refs,
                    )
                )
    return EvidenceLevelFdrReviewReport(
        score_orientation=score_orientation,
        thresholds=normalized_thresholds,
        summaries=tuple(summaries),
        accepted_entries=tuple(accepted_entries),
    )


def render_evidence_level_fdr_summary_tsv(report: EvidenceLevelFdrReviewReport) -> str:
    """Render threshold summaries over PSM, peptide, and protein FDR."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "threshold",
            "evidence_level",
            "total_count",
            "total_target_count",
            "total_decoy_count",
            "total_mixed_count",
            "total_unknown_count",
            "total_contaminant_count",
            "accepted_count",
            "accepted_target_count",
            "accepted_decoy_count",
            "accepted_mixed_count",
            "accepted_unknown_count",
            "accepted_contaminant_count",
        )
    )
    for summary in report.summaries:
        writer.writerow(
            (
                summary.threshold,
                summary.evidence_level.value,
                summary.total_count,
                summary.total_target_count,
                summary.total_decoy_count,
                summary.total_mixed_count,
                summary.total_unknown_count,
                summary.total_contaminant_count,
                summary.accepted_count,
                summary.accepted_target_count,
                summary.accepted_decoy_count,
                summary.accepted_mixed_count,
                summary.accepted_unknown_count,
                summary.accepted_contaminant_count,
            )
        )
    return buffer.getvalue()


def render_evidence_level_fdr_entries_tsv(report: EvidenceLevelFdrReviewReport) -> str:
    """Render accepted-entity rows across evidence levels and thresholds."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "threshold",
            "evidence_level",
            "entity_id",
            "rank",
            "score",
            "q_value",
            "target_decoy_label",
            "contaminant_flag",
            "member_count",
            "protein_refs",
        )
    )
    for entry in report.accepted_entries:
        writer.writerow(
            (
                entry.threshold,
                entry.evidence_level.value,
                entry.entity_id,
                entry.rank,
                entry.score,
                entry.q_value,
                entry.target_decoy_label.value,
                str(entry.contaminant_flag).lower(),
                entry.member_count,
                ";".join(entry.protein_refs),
            )
        )
    return buffer.getvalue()
