# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Dedicated owner for protein-level target-decoy FDR."""

from __future__ import annotations

import csv
import hashlib
import io
import json

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    PsmRecord,
    ProteinEvidenceEntry,
    TargetDecoyLabel,
    rollup_protein_evidence,
)
from bijux_proteomics_foundation import JsonModel


class ProteinTargetDecoyFdrPolicy(JsonModel):
    """Stable policy for one protein-level target-decoy FDR calculation."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(
        default="higher_better",
        pattern="^(higher_better|lower_better)$",
    )
    evidence_policy: str = Field(
        default="best_score",
        pattern="^(best_score|combined_evidence)$",
    )
    threshold: float | None = Field(default=None, ge=0.0)


class ProteinTargetDecoyFdrEntry(JsonModel):
    """One ranked protein evidence row with cumulative target-decoy state."""

    model_config = ConfigDict(extra="forbid")

    evidence: ProteinEvidenceEntry
    rank: int = Field(..., ge=1)
    tie_group_rank: int = Field(..., ge=1)
    tie_group_size: int = Field(..., ge=1)
    cumulative_targets: int = Field(..., ge=0)
    cumulative_decoys: int = Field(..., ge=0)
    raw_fdr: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    accepted: bool


class ProteinTargetDecoyFdrSummary(JsonModel):
    """Compact summary over one protein-level target-decoy FDR run."""

    model_config = ConfigDict(extra="forbid")

    total_protein_count: int = Field(..., ge=0)
    target_protein_count: int = Field(..., ge=0)
    decoy_protein_count: int = Field(..., ge=0)
    accepted_protein_count: int = Field(..., ge=0)
    accepted_target_count: int = Field(..., ge=0)
    accepted_decoy_count: int = Field(..., ge=0)
    q_values_monotonic: bool


class ProteinTargetDecoyFdrReport(JsonModel):
    """Full ranked protein-level target-decoy FDR report."""

    model_config = ConfigDict(extra="forbid")

    policy: ProteinTargetDecoyFdrPolicy
    summary: ProteinTargetDecoyFdrSummary
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)
    entries: tuple[ProteinTargetDecoyFdrEntry, ...] = Field(default_factory=tuple)


def _sort_key(
    evidence: ProteinEvidenceEntry,
    *,
    policy: ProteinTargetDecoyFdrPolicy,
) -> tuple[object, ...]:
    if policy.score_orientation == "higher_better":
        base = (-evidence.best_score,)
    else:
        base = (evidence.best_score,)
    if policy.evidence_policy == "combined_evidence":
        return (
            *base,
            -evidence.peptide_count,
            -evidence.unique_peptide_count,
            -evidence.spectrum_count,
            evidence.protein_ref,
        )
    return (
        *base,
        evidence.protein_ref,
    )


def _tie_group_key(
    evidence: ProteinEvidenceEntry,
    *,
    policy: ProteinTargetDecoyFdrPolicy,
) -> tuple[object, ...]:
    base = (evidence.best_score,)
    if policy.evidence_policy == "combined_evidence":
        return (
            *base,
            evidence.peptide_count,
            evidence.unique_peptide_count,
            evidence.spectrum_count,
        )
    return base


def _raw_fdr_payload(
    entries: tuple[ProteinTargetDecoyFdrEntry, ...],
    *,
    policy: ProteinTargetDecoyFdrPolicy,
) -> bytes:
    payload = {
        "policy": policy.to_dict(),
        "entries": [
            {
                "rank": entry.rank,
                "tie_group_rank": entry.tie_group_rank,
                "tie_group_size": entry.tie_group_size,
                "protein_ref": entry.evidence.protein_ref,
                "best_score": entry.evidence.best_score,
                "peptide_count": entry.evidence.peptide_count,
                "unique_peptide_count": entry.evidence.unique_peptide_count,
                "shared_peptide_count": entry.evidence.shared_peptide_count,
                "spectrum_count": entry.evidence.spectrum_count,
                "target_decoy_label": entry.evidence.target_decoy_label.value,
                "cumulative_targets": entry.cumulative_targets,
                "cumulative_decoys": entry.cumulative_decoys,
                "raw_fdr": entry.raw_fdr,
                "q_value": entry.q_value,
                "accepted": entry.accepted,
            }
            for entry in entries
        ],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_protein_target_decoy_fdr_report(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    evidence_policy: str = "best_score",
) -> ProteinTargetDecoyFdrReport:
    """Build one ranked protein-level target-decoy FDR report."""
    policy = ProteinTargetDecoyFdrPolicy(
        threshold=threshold,
        score_orientation=score_orientation,
        evidence_policy=evidence_policy,
    )
    evidence_rows = tuple(
        sorted(
            rollup_protein_evidence(records),
            key=lambda evidence: _sort_key(evidence, policy=policy),
        )
    )

    ranked_entries: list[ProteinTargetDecoyFdrEntry] = []
    cumulative_targets = 0
    cumulative_decoys = 0
    rank = 1
    tie_group_rank = 0
    group_index = 0
    while group_index < len(evidence_rows):
        current = evidence_rows[group_index]
        group_key = _tie_group_key(current, policy=policy)
        tie_group: list[ProteinEvidenceEntry] = []
        while group_index < len(evidence_rows):
            candidate = evidence_rows[group_index]
            if _tie_group_key(candidate, policy=policy) != group_key:
                break
            tie_group.append(candidate)
            group_index += 1
        tie_group_rank += 1
        group_target_count = sum(
            1
            for evidence in tie_group
            if evidence.target_decoy_label is not TargetDecoyLabel.DECOY
        )
        group_decoy_count = len(tie_group) - group_target_count
        cumulative_targets += group_target_count
        cumulative_decoys += group_decoy_count
        raw_fdr = min(cumulative_decoys / max(cumulative_targets, 1), 1.0)
        for evidence in tie_group:
            ranked_entries.append(
                ProteinTargetDecoyFdrEntry(
                    evidence=evidence,
                    rank=rank,
                    tie_group_rank=tie_group_rank,
                    tie_group_size=len(tie_group),
                    cumulative_targets=cumulative_targets,
                    cumulative_decoys=cumulative_decoys,
                    raw_fdr=raw_fdr,
                    q_value=raw_fdr,
                    accepted=threshold is None or raw_fdr <= threshold,
                )
            )
            rank += 1

    running_min = float("inf")
    monotonic_entries: list[ProteinTargetDecoyFdrEntry] = []
    for entry in reversed(ranked_entries):
        running_min = min(running_min, entry.raw_fdr)
        monotonic_entries.append(
            entry.model_copy(
                update={
                    "q_value": running_min,
                    "accepted": threshold is None or running_min <= threshold,
                }
            )
        )
    entries = tuple(reversed(monotonic_entries))
    summary = ProteinTargetDecoyFdrSummary(
        total_protein_count=len(entries),
        target_protein_count=sum(
            1
            for evidence in evidence_rows
            if evidence.target_decoy_label is not TargetDecoyLabel.DECOY
        ),
        decoy_protein_count=sum(
            1
            for evidence in evidence_rows
            if evidence.target_decoy_label is TargetDecoyLabel.DECOY
        ),
        accepted_protein_count=sum(1 for entry in entries if entry.accepted),
        accepted_target_count=sum(
            1
            for entry in entries
            if entry.accepted
            and entry.evidence.target_decoy_label is not TargetDecoyLabel.DECOY
        ),
        accepted_decoy_count=sum(
            1
            for entry in entries
            if entry.accepted
            and entry.evidence.target_decoy_label is TargetDecoyLabel.DECOY
        ),
        q_values_monotonic=all(
            left.q_value <= right.q_value
            for left, right in zip(entries, entries[1:], strict=False)
        ),
    )
    return ProteinTargetDecoyFdrReport(
        policy=policy,
        summary=summary,
        reproducibility_hash=hashlib.sha256(
            _raw_fdr_payload(entries, policy=policy)
        ).hexdigest(),
        entries=entries,
    )


def render_protein_target_decoy_fdr_tsv(report: ProteinTargetDecoyFdrReport) -> str:
    """Render one row per ranked protein-level FDR entry."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "rank",
            "tie_group_rank",
            "tie_group_size",
            "protein_ref",
            "best_score",
            "best_q_value",
            "peptide_count",
            "unique_peptide_count",
            "shared_peptide_count",
            "spectrum_count",
            "peptides",
            "target_decoy_label",
            "cumulative_targets",
            "cumulative_decoys",
            "raw_fdr",
            "q_value",
            "accepted",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.rank,
                entry.tie_group_rank,
                entry.tie_group_size,
                entry.evidence.protein_ref,
                entry.evidence.best_score,
                entry.evidence.best_q_value,
                entry.evidence.peptide_count,
                entry.evidence.unique_peptide_count,
                entry.evidence.shared_peptide_count,
                entry.evidence.spectrum_count,
                ";".join(entry.evidence.peptides),
                entry.evidence.target_decoy_label.value,
                entry.cumulative_targets,
                entry.cumulative_decoys,
                entry.raw_fdr,
                entry.q_value,
                str(entry.accepted).lower(),
            )
        )
    return buffer.getvalue()


def render_protein_target_decoy_fdr_summary_tsv(
    report: ProteinTargetDecoyFdrReport,
) -> str:
    """Render one summary row for the protein-level FDR report."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "score_orientation",
            "evidence_policy",
            "threshold",
            "total_protein_count",
            "target_protein_count",
            "decoy_protein_count",
            "accepted_protein_count",
            "accepted_target_count",
            "accepted_decoy_count",
            "q_values_monotonic",
            "reproducibility_hash",
        )
    )
    writer.writerow(
        (
            report.policy.score_orientation,
            report.policy.evidence_policy,
            report.policy.threshold,
            report.summary.total_protein_count,
            report.summary.target_protein_count,
            report.summary.decoy_protein_count,
            report.summary.accepted_protein_count,
            report.summary.accepted_target_count,
            report.summary.accepted_decoy_count,
            str(report.summary.q_values_monotonic).lower(),
            report.reproducibility_hash,
        )
    )
    return buffer.getvalue()
