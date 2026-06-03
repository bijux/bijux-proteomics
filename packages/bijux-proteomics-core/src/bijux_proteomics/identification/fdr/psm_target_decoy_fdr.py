# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Dedicated owner for score-sorted PSM target-decoy FDR."""

from __future__ import annotations

import csv
import hashlib
import io
import json

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import PsmRecord, TargetDecoyLabel
from bijux_proteomics_foundation import JsonModel


class PsmTargetDecoyFdrPolicy(JsonModel):
    """Stable policy for one PSM target-decoy FDR calculation."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(
        default="higher_better",
        pattern="^(higher_better|lower_better)$",
    )
    tie_handling: str = Field(
        default="score_group",
        pattern="^(score_group|stable_record_order)$",
    )
    threshold: float | None = Field(default=None, ge=0.0)


class PsmTargetDecoyFdrEntry(JsonModel):
    """One ranked PSM row with explicit cumulative target-decoy state."""

    model_config = ConfigDict(extra="forbid")

    psm: PsmRecord
    rank: int = Field(..., ge=1)
    tie_group_rank: int = Field(..., ge=1)
    tie_group_size: int = Field(..., ge=1)
    cumulative_targets: int = Field(..., ge=0)
    cumulative_decoys: int = Field(..., ge=0)
    raw_fdr: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    accepted: bool


class PsmTargetDecoyFdrSummary(JsonModel):
    """Compact summary over one ranked PSM target-decoy FDR run."""

    model_config = ConfigDict(extra="forbid")

    total_psm_count: int = Field(..., ge=0)
    target_psm_count: int = Field(..., ge=0)
    decoy_psm_count: int = Field(..., ge=0)
    accepted_psm_count: int = Field(..., ge=0)
    accepted_target_count: int = Field(..., ge=0)
    accepted_decoy_count: int = Field(..., ge=0)
    q_values_monotonic: bool


class PsmTargetDecoyFdrReport(JsonModel):
    """Full ranked target-decoy FDR report for PSM evidence."""

    model_config = ConfigDict(extra="forbid")

    policy: PsmTargetDecoyFdrPolicy
    summary: PsmTargetDecoyFdrSummary
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)
    entries: tuple[PsmTargetDecoyFdrEntry, ...] = Field(default_factory=tuple)


def _sorted_records(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str,
) -> tuple[PsmRecord, ...]:
    if score_orientation == "higher_better":
        key_fn = lambda record: (  # noqa: E731
            -record.score,
            record.spectrum_id,
            record.canonical_peptide,
            record.charge,
        )
    else:
        key_fn = lambda record: (  # noqa: E731
            record.score,
            record.spectrum_id,
            record.canonical_peptide,
            record.charge,
        )
    return tuple(sorted(records, key=key_fn))


def _score_groups(
    records: tuple[PsmRecord, ...],
    *,
    tie_handling: str,
) -> tuple[tuple[int, tuple[PsmRecord, ...]], ...]:
    if tie_handling == "stable_record_order":
        return tuple((rank, (record,)) for rank, record in enumerate(records, start=1))
    groups: list[tuple[int, tuple[PsmRecord, ...]]] = []
    current_score: float | None = None
    current_group: list[PsmRecord] = []
    group_rank = 0
    for record in records:
        if current_score is None or record.score == current_score:
            current_group.append(record)
            current_score = record.score
            continue
        group_rank += 1
        groups.append((group_rank, tuple(current_group)))
        current_group = [record]
        current_score = record.score
    if current_group:
        group_rank += 1
        groups.append((group_rank, tuple(current_group)))
    return tuple(groups)


def _raw_fdr_payload(
    entries: tuple[PsmTargetDecoyFdrEntry, ...],
    *,
    policy: PsmTargetDecoyFdrPolicy,
) -> bytes:
    payload = {
        "policy": policy.to_dict(),
        "entries": [
            {
                "rank": entry.rank,
                "tie_group_rank": entry.tie_group_rank,
                "tie_group_size": entry.tie_group_size,
                "spectrum_id": entry.psm.spectrum_id,
                "canonical_peptide": entry.psm.canonical_peptide,
                "charge": entry.psm.charge,
                "score": entry.psm.score,
                "target_decoy_label": entry.psm.target_decoy_label.value,
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


def build_psm_target_decoy_fdr_report(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    tie_handling: str = "score_group",
) -> PsmTargetDecoyFdrReport:
    """Build one ranked PSM target-decoy FDR report with monotonic q-values."""
    policy = PsmTargetDecoyFdrPolicy(
        threshold=threshold,
        score_orientation=score_orientation,
        tie_handling=tie_handling,
    )
    sorted_records = _sorted_records(records, score_orientation=score_orientation)
    groups = _score_groups(sorted_records, tie_handling=tie_handling)
    ranked_entries: list[PsmTargetDecoyFdrEntry] = []
    cumulative_targets = 0
    cumulative_decoys = 0
    rank = 1
    for tie_group_rank, group in groups:
        group_target_count = sum(
            1
            for record in group
            if record.target_decoy_label is not TargetDecoyLabel.DECOY
        )
        group_decoy_count = len(group) - group_target_count
        cumulative_targets += group_target_count
        cumulative_decoys += group_decoy_count
        raw_fdr = min(cumulative_decoys / max(cumulative_targets, 1), 1.0)
        for record in group:
            ranked_entries.append(
                PsmTargetDecoyFdrEntry(
                    psm=record,
                    rank=rank,
                    tie_group_rank=tie_group_rank,
                    tie_group_size=len(group),
                    cumulative_targets=cumulative_targets,
                    cumulative_decoys=cumulative_decoys,
                    raw_fdr=raw_fdr,
                    q_value=raw_fdr,
                    accepted=threshold is None or raw_fdr <= threshold,
                )
            )
            rank += 1

    running_min = float("inf")
    monotonic_entries: list[PsmTargetDecoyFdrEntry] = []
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
    summary = PsmTargetDecoyFdrSummary(
        total_psm_count=len(entries),
        target_psm_count=sum(
            1
            for record in records
            if record.target_decoy_label is not TargetDecoyLabel.DECOY
        ),
        decoy_psm_count=sum(
            1
            for record in records
            if record.target_decoy_label is TargetDecoyLabel.DECOY
        ),
        accepted_psm_count=sum(1 for entry in entries if entry.accepted),
        accepted_target_count=sum(
            1
            for entry in entries
            if entry.accepted
            and entry.psm.target_decoy_label is not TargetDecoyLabel.DECOY
        ),
        accepted_decoy_count=sum(
            1
            for entry in entries
            if entry.accepted and entry.psm.target_decoy_label is TargetDecoyLabel.DECOY
        ),
        q_values_monotonic=all(
            left.q_value <= right.q_value
            for left, right in zip(entries, entries[1:], strict=False)
        ),
    )
    return PsmTargetDecoyFdrReport(
        policy=policy,
        summary=summary,
        reproducibility_hash=hashlib.sha256(
            _raw_fdr_payload(entries, policy=policy)
        ).hexdigest(),
        entries=entries,
    )


def render_psm_target_decoy_fdr_tsv(report: PsmTargetDecoyFdrReport) -> str:
    """Render one row per ranked PSM FDR entry."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "rank",
            "tie_group_rank",
            "tie_group_size",
            "spectrum_id",
            "canonical_peptide",
            "charge",
            "score",
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
                entry.psm.spectrum_id,
                entry.psm.canonical_peptide,
                entry.psm.charge,
                entry.psm.score,
                entry.psm.target_decoy_label.value,
                entry.cumulative_targets,
                entry.cumulative_decoys,
                entry.raw_fdr,
                entry.q_value,
                str(entry.accepted).lower(),
            )
        )
    return buffer.getvalue()


def render_psm_target_decoy_fdr_summary_tsv(report: PsmTargetDecoyFdrReport) -> str:
    """Render one summary row for the ranked PSM FDR report."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "score_orientation",
            "tie_handling",
            "threshold",
            "total_psm_count",
            "target_psm_count",
            "decoy_psm_count",
            "accepted_psm_count",
            "accepted_target_count",
            "accepted_decoy_count",
            "q_values_monotonic",
            "reproducibility_hash",
        )
    )
    writer.writerow(
        (
            report.policy.score_orientation,
            report.policy.tie_handling,
            report.policy.threshold,
            report.summary.total_psm_count,
            report.summary.target_psm_count,
            report.summary.decoy_psm_count,
            report.summary.accepted_psm_count,
            report.summary.accepted_target_count,
            report.summary.accepted_decoy_count,
            str(report.summary.q_values_monotonic).lower(),
            report.reproducibility_hash,
        )
    )
    return buffer.getvalue()
