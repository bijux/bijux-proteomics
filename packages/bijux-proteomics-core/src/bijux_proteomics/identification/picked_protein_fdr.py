# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Dedicated owner for picked target-decoy protein FDR."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import defaultdict

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    ProteinEvidenceEntry,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
    rollup_protein_evidence,
)
from bijux_proteomics_foundation import JsonModel


class PickedProteinFdrPolicy(JsonModel):
    """Stable policy for one picked-protein FDR calculation."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(
        default="higher_better",
        pattern="^(higher_better|lower_better)$",
    )
    threshold: float | None = Field(default=None, ge=0.0)
    protein_prefix: str = Field(default="DECOY_")
    protein_suffix: str | None = None


class PickedProteinPairEntry(JsonModel):
    """One explicit target-decoy competition pair and its winner."""

    model_config = ConfigDict(extra="forbid")

    pair_id: str = Field(..., min_length=1)
    base_accession: str = Field(..., min_length=1)
    target_ref: str | None = None
    decoy_ref: str | None = None
    target_score: float | None = None
    decoy_score: float | None = None
    winner_ref: str = Field(..., min_length=1)
    winner_target_decoy_label: TargetDecoyLabel
    winner_score: float
    winner_supporting_peptides: tuple[str, ...] = Field(default_factory=tuple)
    winner_peptide_count: int = Field(..., ge=0)
    winner_unique_peptide_count: int = Field(..., ge=0)
    winner_shared_peptide_count: int = Field(..., ge=0)
    winner_spectrum_count: int = Field(..., ge=0)
    rank: int = Field(..., ge=1)
    cumulative_targets: int = Field(..., ge=0)
    cumulative_decoys: int = Field(..., ge=0)
    raw_fdr: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    accepted: bool


class PickedProteinFdrSummary(JsonModel):
    """Compact summary over one picked-protein FDR run."""

    model_config = ConfigDict(extra="forbid")

    total_pair_count: int = Field(..., ge=0)
    target_winner_count: int = Field(..., ge=0)
    decoy_winner_count: int = Field(..., ge=0)
    accepted_pair_count: int = Field(..., ge=0)
    accepted_target_winner_count: int = Field(..., ge=0)
    accepted_decoy_winner_count: int = Field(..., ge=0)
    q_values_monotonic: bool


class PickedProteinFdrReport(JsonModel):
    """Full explicit picked-protein competition report."""

    model_config = ConfigDict(extra="forbid")

    policy: PickedProteinFdrPolicy
    summary: PickedProteinFdrSummary
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)
    entries: tuple[PickedProteinPairEntry, ...] = Field(default_factory=tuple)


def _build_pair_id(base_accession: str) -> str:
    return f"picked:{base_accession}"


def _base_accession(
    protein_ref: str,
    *,
    policy: TargetDecoyLabelPolicy,
) -> str:
    value = protein_ref
    if policy.protein_prefix and value.startswith(policy.protein_prefix):
        value = value[len(policy.protein_prefix) :]
    if policy.protein_suffix and value.endswith(policy.protein_suffix):
        value = value[: -len(policy.protein_suffix)]
    return value


def _winner_key(
    evidence: ProteinEvidenceEntry,
    *,
    score_orientation: str,
) -> tuple[object, ...]:
    if score_orientation == "higher_better":
        return (-evidence.best_score, evidence.protein_ref)
    return (evidence.best_score, evidence.protein_ref)


def _score_value(
    evidence: ProteinEvidenceEntry | None,
) -> float | None:
    return None if evidence is None else evidence.best_score


def _raw_payload(
    entries: tuple[PickedProteinPairEntry, ...],
    *,
    policy: PickedProteinFdrPolicy,
) -> bytes:
    payload = {
        "policy": policy.to_dict(),
        "entries": [
            {
                "pair_id": entry.pair_id,
                "base_accession": entry.base_accession,
                "target_ref": entry.target_ref,
                "decoy_ref": entry.decoy_ref,
                "target_score": entry.target_score,
                "decoy_score": entry.decoy_score,
                "winner_ref": entry.winner_ref,
                "winner_target_decoy_label": entry.winner_target_decoy_label.value,
                "winner_score": entry.winner_score,
                "rank": entry.rank,
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


def build_picked_protein_fdr_report(
    protein_evidence: tuple[ProteinEvidenceEntry, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> PickedProteinFdrReport:
    """Build one explicit picked-protein target-decoy competition report."""
    active_decoy_policy = decoy_policy or TargetDecoyLabelPolicy()
    policy = PickedProteinFdrPolicy(
        threshold=threshold,
        score_orientation=score_orientation,
        protein_prefix=active_decoy_policy.protein_prefix,
        protein_suffix=active_decoy_policy.protein_suffix,
    )

    paired: dict[str, list[ProteinEvidenceEntry]] = defaultdict(list)
    for evidence in protein_evidence:
        paired[_base_accession(evidence.protein_ref, policy=active_decoy_policy)].append(
            evidence
        )

    winners: list[tuple[str, str, ProteinEvidenceEntry | None, ProteinEvidenceEntry | None, ProteinEvidenceEntry]] = []
    for base_accession, members in sorted(paired.items()):
        target_entry = next(
            (entry for entry in members if entry.target_decoy_label is TargetDecoyLabel.TARGET),
            None,
        )
        decoy_entry = next(
            (entry for entry in members if entry.target_decoy_label is TargetDecoyLabel.DECOY),
            None,
        )
        candidates = [entry for entry in (target_entry, decoy_entry) if entry is not None]
        winner = sorted(
            candidates,
            key=lambda entry: _winner_key(entry, score_orientation=score_orientation),
        )[0]
        winners.append(
            (
                _build_pair_id(base_accession),
                base_accession,
                target_entry,
                decoy_entry,
                winner,
            )
        )

    ranked_winners = tuple(
        sorted(
            winners,
            key=lambda item: _winner_key(item[4], score_orientation=score_orientation),
        )
    )

    raw_entries: list[PickedProteinPairEntry] = []
    cumulative_targets = 0
    cumulative_decoys = 0
    rank = 1
    for pair_id, base_accession, target_entry, decoy_entry, winner in ranked_winners:
        if winner.target_decoy_label is TargetDecoyLabel.DECOY:
            cumulative_decoys += 1
        else:
            cumulative_targets += 1
        raw_fdr = min(cumulative_decoys / max(cumulative_targets, 1), 1.0)
        raw_entries.append(
            PickedProteinPairEntry(
                pair_id=pair_id,
                base_accession=base_accession,
                target_ref=None if target_entry is None else target_entry.protein_ref,
                decoy_ref=None if decoy_entry is None else decoy_entry.protein_ref,
                target_score=_score_value(target_entry),
                decoy_score=_score_value(decoy_entry),
                winner_ref=winner.protein_ref,
                winner_target_decoy_label=winner.target_decoy_label,
                winner_score=winner.best_score,
                winner_supporting_peptides=winner.peptides,
                winner_peptide_count=winner.peptide_count,
                winner_unique_peptide_count=winner.unique_peptide_count,
                winner_shared_peptide_count=winner.shared_peptide_count,
                winner_spectrum_count=winner.spectrum_count,
                rank=rank,
                cumulative_targets=cumulative_targets,
                cumulative_decoys=cumulative_decoys,
                raw_fdr=raw_fdr,
                q_value=raw_fdr,
                accepted=threshold is None or raw_fdr <= threshold,
            )
        )
        rank += 1

    running_min = float("inf")
    monotonic_entries: list[PickedProteinPairEntry] = []
    for entry in reversed(raw_entries):
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
    summary = PickedProteinFdrSummary(
        total_pair_count=len(entries),
        target_winner_count=sum(
            1
            for entry in entries
            if entry.winner_target_decoy_label is TargetDecoyLabel.TARGET
        ),
        decoy_winner_count=sum(
            1
            for entry in entries
            if entry.winner_target_decoy_label is TargetDecoyLabel.DECOY
        ),
        accepted_pair_count=sum(1 for entry in entries if entry.accepted),
        accepted_target_winner_count=sum(
            1
            for entry in entries
            if entry.accepted
            and entry.winner_target_decoy_label is TargetDecoyLabel.TARGET
        ),
        accepted_decoy_winner_count=sum(
            1
            for entry in entries
            if entry.accepted
            and entry.winner_target_decoy_label is TargetDecoyLabel.DECOY
        ),
        q_values_monotonic=all(
            left.q_value <= right.q_value
            for left, right in zip(entries, entries[1:], strict=False)
        ),
    )
    return PickedProteinFdrReport(
        policy=policy,
        summary=summary,
        reproducibility_hash=hashlib.sha256(
            _raw_payload(entries, policy=policy)
        ).hexdigest(),
        entries=entries,
    )


def build_picked_protein_fdr_report_from_psm_records(
    records: tuple,
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> PickedProteinFdrReport:
    """Roll up PSM records and then build picked-protein competition results."""
    return build_picked_protein_fdr_report(
        rollup_protein_evidence(records),
        threshold=threshold,
        score_orientation=score_orientation,
        decoy_policy=decoy_policy,
    )


def render_picked_protein_pair_tsv(report: PickedProteinFdrReport) -> str:
    """Render one row per picked-protein target-decoy competition pair."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pair_id",
            "base_accession",
            "target_ref",
            "decoy_ref",
            "target_score",
            "decoy_score",
            "winner_ref",
            "winner_target_decoy_label",
            "winner_score",
            "winner_peptide_count",
            "winner_unique_peptide_count",
            "winner_shared_peptide_count",
            "winner_spectrum_count",
            "winner_supporting_peptides",
            "rank",
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
                entry.pair_id,
                entry.base_accession,
                "" if entry.target_ref is None else entry.target_ref,
                "" if entry.decoy_ref is None else entry.decoy_ref,
                entry.target_score,
                entry.decoy_score,
                entry.winner_ref,
                entry.winner_target_decoy_label.value,
                entry.winner_score,
                entry.winner_peptide_count,
                entry.winner_unique_peptide_count,
                entry.winner_shared_peptide_count,
                entry.winner_spectrum_count,
                ";".join(entry.winner_supporting_peptides),
                entry.rank,
                entry.cumulative_targets,
                entry.cumulative_decoys,
                entry.raw_fdr,
                entry.q_value,
                str(entry.accepted).lower(),
            )
        )
    return buffer.getvalue()
