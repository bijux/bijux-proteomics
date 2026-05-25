# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Dedicated owner for peptide-level target-decoy FDR."""

from __future__ import annotations

import csv
import hashlib
import io
import json

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import PsmRecord, TargetDecoyLabel
from bijux_proteomics_foundation import JsonModel


class PeptideFdrEvidence(JsonModel):
    """Collapsed peptide evidence derived from one or more supporting PSMs."""

    model_config = ConfigDict(extra="forbid")

    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    psm_count: int = Field(..., ge=1)
    spectrum_count: int = Field(..., ge=1)
    charge_states: tuple[int, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    supporting_spectrum_ids: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN


class PeptideTargetDecoyFdrPolicy(JsonModel):
    """Stable policy for one peptide-level target-decoy FDR calculation."""

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


class PeptideTargetDecoyFdrEntry(JsonModel):
    """One ranked peptide evidence row with cumulative target-decoy state."""

    model_config = ConfigDict(extra="forbid")

    evidence: PeptideFdrEvidence
    rank: int = Field(..., ge=1)
    tie_group_rank: int = Field(..., ge=1)
    tie_group_size: int = Field(..., ge=1)
    cumulative_targets: int = Field(..., ge=0)
    cumulative_decoys: int = Field(..., ge=0)
    raw_fdr: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    accepted: bool


class PeptideTargetDecoyFdrSummary(JsonModel):
    """Compact summary over one peptide-level target-decoy FDR run."""

    model_config = ConfigDict(extra="forbid")

    total_peptide_count: int = Field(..., ge=0)
    target_peptide_count: int = Field(..., ge=0)
    decoy_peptide_count: int = Field(..., ge=0)
    accepted_peptide_count: int = Field(..., ge=0)
    accepted_target_count: int = Field(..., ge=0)
    accepted_decoy_count: int = Field(..., ge=0)
    q_values_monotonic: bool


class PeptideTargetDecoyFdrReport(JsonModel):
    """Full ranked peptide-level target-decoy FDR report."""

    model_config = ConfigDict(extra="forbid")

    policy: PeptideTargetDecoyFdrPolicy
    summary: PeptideTargetDecoyFdrSummary
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)
    entries: tuple[PeptideTargetDecoyFdrEntry, ...] = Field(default_factory=tuple)


def _combine_labels(labels: tuple[TargetDecoyLabel, ...]) -> TargetDecoyLabel:
    active = tuple(label for label in labels if label is not TargetDecoyLabel.UNKNOWN)
    if not active:
        return TargetDecoyLabel.UNKNOWN
    if all(label is TargetDecoyLabel.DECOY for label in active):
        return TargetDecoyLabel.DECOY
    if all(label is TargetDecoyLabel.TARGET for label in active):
        return TargetDecoyLabel.TARGET
    if any(label is TargetDecoyLabel.MIXED for label in active):
        return TargetDecoyLabel.MIXED
    return TargetDecoyLabel.MIXED


def _best_record(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str,
) -> PsmRecord:
    if score_orientation == "higher_better":
        return max(
            records,
            key=lambda record: (
                record.score,
                -(record.q_value if record.q_value is not None else float("inf")),
                record.peptide,
                record.spectrum_id,
            ),
        )
    return min(
        records,
        key=lambda record: (
            record.score,
            record.q_value if record.q_value is not None else float("inf"),
            record.peptide,
            record.spectrum_id,
        ),
    )


def collapse_peptide_fdr_evidence(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str = "higher_better",
) -> tuple[PeptideFdrEvidence, ...]:
    """Collapse scored PSMs into one peptide evidence row per canonical peptide."""
    grouped: dict[str, list[PsmRecord]] = {}
    for record in records:
        grouped.setdefault(record.canonical_peptide, []).append(record)

    evidence_rows: list[PeptideFdrEvidence] = []
    for canonical_peptide in sorted(grouped):
        group = tuple(grouped[canonical_peptide])
        best = _best_record(group, score_orientation=score_orientation)
        q_values = [record.q_value for record in group if record.q_value is not None]
        evidence_rows.append(
            PeptideFdrEvidence(
                peptide=best.peptide,
                canonical_peptide=canonical_peptide,
                best_score=best.score,
                best_q_value=min(q_values) if q_values else None,
                psm_count=len(group),
                spectrum_count=len({record.spectrum_id for record in group}),
                charge_states=tuple(sorted({record.charge for record in group})),
                protein_refs=tuple(
                    sorted(
                        {
                            protein_ref
                            for record in group
                            for protein_ref in record.protein_refs
                        }
                    )
                ),
                supporting_spectrum_ids=tuple(
                    sorted({record.spectrum_id for record in group})
                ),
                target_decoy_label=_combine_labels(
                    tuple(record.target_decoy_label for record in group)
                ),
            )
        )
    return tuple(evidence_rows)


def _sort_key(
    evidence: PeptideFdrEvidence,
    *,
    policy: PeptideTargetDecoyFdrPolicy,
) -> tuple[object, ...]:
    if policy.score_orientation == "higher_better":
        base = (-evidence.best_score,)
    else:
        base = (evidence.best_score,)
    if policy.evidence_policy == "combined_evidence":
        return (
            *base,
            -evidence.psm_count,
            -evidence.spectrum_count,
            evidence.canonical_peptide,
        )
    return (
        *base,
        evidence.canonical_peptide,
    )


def _tie_group_key(
    evidence: PeptideFdrEvidence,
    *,
    policy: PeptideTargetDecoyFdrPolicy,
) -> tuple[object, ...]:
    if policy.score_orientation == "higher_better":
        base = (evidence.best_score,)
    else:
        base = (evidence.best_score,)
    if policy.evidence_policy == "combined_evidence":
        return (
            *base,
            evidence.psm_count,
            evidence.spectrum_count,
        )
    return base


def _raw_fdr_payload(
    entries: tuple[PeptideTargetDecoyFdrEntry, ...],
    *,
    policy: PeptideTargetDecoyFdrPolicy,
) -> bytes:
    payload = {
        "policy": policy.to_dict(),
        "entries": [
            {
                "rank": entry.rank,
                "tie_group_rank": entry.tie_group_rank,
                "tie_group_size": entry.tie_group_size,
                "canonical_peptide": entry.evidence.canonical_peptide,
                "best_score": entry.evidence.best_score,
                "psm_count": entry.evidence.psm_count,
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


def build_peptide_target_decoy_fdr_report(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    evidence_policy: str = "best_score",
) -> PeptideTargetDecoyFdrReport:
    """Build one ranked peptide-level target-decoy FDR report."""
    policy = PeptideTargetDecoyFdrPolicy(
        threshold=threshold,
        score_orientation=score_orientation,
        evidence_policy=evidence_policy,
    )
    evidence_rows = tuple(
        sorted(
            collapse_peptide_fdr_evidence(
                records,
                score_orientation=score_orientation,
            ),
            key=lambda evidence: _sort_key(evidence, policy=policy),
        )
    )

    ranked_entries: list[PeptideTargetDecoyFdrEntry] = []
    cumulative_targets = 0
    cumulative_decoys = 0
    rank = 1
    tie_group_rank = 0
    group_index = 0
    while group_index < len(evidence_rows):
        current = evidence_rows[group_index]
        group_key = _tie_group_key(current, policy=policy)
        tie_group: list[PeptideFdrEvidence] = []
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
                PeptideTargetDecoyFdrEntry(
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
    monotonic_entries: list[PeptideTargetDecoyFdrEntry] = []
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
    summary = PeptideTargetDecoyFdrSummary(
        total_peptide_count=len(entries),
        target_peptide_count=sum(
            1
            for evidence in evidence_rows
            if evidence.target_decoy_label is not TargetDecoyLabel.DECOY
        ),
        decoy_peptide_count=sum(
            1
            for evidence in evidence_rows
            if evidence.target_decoy_label is TargetDecoyLabel.DECOY
        ),
        accepted_peptide_count=sum(1 for entry in entries if entry.accepted),
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
    return PeptideTargetDecoyFdrReport(
        policy=policy,
        summary=summary,
        reproducibility_hash=hashlib.sha256(
            _raw_fdr_payload(entries, policy=policy)
        ).hexdigest(),
        entries=entries,
    )


def render_peptide_target_decoy_fdr_tsv(report: PeptideTargetDecoyFdrReport) -> str:
    """Render one row per ranked peptide-level FDR entry."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "rank",
            "tie_group_rank",
            "tie_group_size",
            "peptide",
            "canonical_peptide",
            "best_score",
            "best_q_value",
            "psm_count",
            "spectrum_count",
            "charge_states",
            "protein_refs",
            "supporting_spectrum_ids",
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
                entry.evidence.peptide,
                entry.evidence.canonical_peptide,
                entry.evidence.best_score,
                entry.evidence.best_q_value,
                entry.evidence.psm_count,
                entry.evidence.spectrum_count,
                ";".join(str(charge) for charge in entry.evidence.charge_states),
                ";".join(entry.evidence.protein_refs),
                ";".join(entry.evidence.supporting_spectrum_ids),
                entry.evidence.target_decoy_label.value,
                entry.cumulative_targets,
                entry.cumulative_decoys,
                entry.raw_fdr,
                entry.q_value,
                str(entry.accepted).lower(),
            )
        )
    return buffer.getvalue()


def render_peptide_target_decoy_fdr_summary_tsv(
    report: PeptideTargetDecoyFdrReport,
) -> str:
    """Render one summary row for the peptide-level FDR report."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "score_orientation",
            "evidence_policy",
            "threshold",
            "total_peptide_count",
            "target_peptide_count",
            "decoy_peptide_count",
            "accepted_peptide_count",
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
            report.summary.total_peptide_count,
            report.summary.target_peptide_count,
            report.summary.decoy_peptide_count,
            report.summary.accepted_peptide_count,
            report.summary.accepted_target_count,
            report.summary.accepted_decoy_count,
            str(report.summary.q_values_monotonic).lower(),
            report.reproducibility_hash,
        )
    )
    return buffer.getvalue()
