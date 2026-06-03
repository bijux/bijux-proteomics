# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned target-decoy score-separation diagnostics for FDR stability review."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    NormalizedScoreEntry,
    PsmRecord,
    TargetDecoyLabel,
    normalize_psm_score_orientation,
)
from bijux_proteomics_foundation import JsonModel


class ScoreSeparationWarningTier(StrEnum):
    """Durable warning tiers for target-decoy score separation quality."""

    STABLE = "stable"
    WARNING = "warning"
    UNSTABLE = "unstable"


class ScoreSeparationDiagnosticPolicy(JsonModel):
    """Stable policy for one target-decoy score-separation calculation."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(
        default="higher_better",
        pattern="^(higher_better|lower_better)$",
    )
    bin_count: int = Field(default=10, ge=2)
    warning_overlap_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    unstable_overlap_threshold: float = Field(default=0.6, ge=0.0, le=1.0)


class ScoreSeparationBin(JsonModel):
    """One histogram bin over normalized target-decoy score space."""

    model_config = ConfigDict(extra="forbid")

    bin_lower: float = Field(..., ge=0.0, le=1.0)
    bin_upper: float = Field(..., ge=0.0, le=1.0)
    target_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    mixed_count: int = Field(..., ge=0)
    unknown_count: int = Field(..., ge=0)
    target_fraction: float = Field(..., ge=0.0, le=1.0)
    decoy_fraction: float = Field(..., ge=0.0, le=1.0)
    overlap_contribution: float = Field(..., ge=0.0, le=1.0)


class ScoreSeparationDiagnosticSummary(JsonModel):
    """Compact score-separation summary for FDR stability decisions."""

    model_config = ConfigDict(extra="forbid")

    total_record_count: int = Field(..., ge=0)
    labeled_record_count: int = Field(..., ge=0)
    target_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    target_dominance_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    overlap_metric: float = Field(..., ge=0.0, le=1.0)
    warning_tier: ScoreSeparationWarningTier
    fdr_unstable: bool
    note: str = Field(..., min_length=1)


class ScoreSeparationDiagnosticReport(JsonModel):
    """Owned target-decoy score-separation diagnostic with plot-ready bins."""

    model_config = ConfigDict(extra="forbid")

    policy: ScoreSeparationDiagnosticPolicy
    summary: ScoreSeparationDiagnosticSummary
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)
    bins: tuple[ScoreSeparationBin, ...] = Field(default_factory=tuple)


def build_score_separation_diagnostic_report(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str = "higher_better",
    bin_count: int = 10,
    warning_overlap_threshold: float = 0.3,
    unstable_overlap_threshold: float = 0.6,
) -> ScoreSeparationDiagnosticReport:
    """Compare target and decoy score distributions and classify FDR stability."""
    if warning_overlap_threshold > unstable_overlap_threshold:
        raise ValueError(
            "warning overlap threshold must be less than or equal to unstable overlap threshold"
        )
    policy = ScoreSeparationDiagnosticPolicy(
        score_orientation=score_orientation,
        bin_count=bin_count,
        warning_overlap_threshold=warning_overlap_threshold,
        unstable_overlap_threshold=unstable_overlap_threshold,
    )
    normalized_entries = normalize_psm_score_orientation(
        records,
        score_orientation=score_orientation,
    )
    target_count = sum(
        1
        for entry in normalized_entries
        if entry.target_decoy_label is TargetDecoyLabel.TARGET
    )
    decoy_count = sum(
        1
        for entry in normalized_entries
        if entry.target_decoy_label is TargetDecoyLabel.DECOY
    )
    bins = _build_bins(
        normalized_entries,
        bin_count=bin_count,
        target_count=target_count,
        decoy_count=decoy_count,
    )
    target_dominance_fraction = _target_dominance_fraction(
        records,
        score_orientation=score_orientation,
    )
    overlap_metric = (
        1.0
        if target_dominance_fraction is None
        else 4.0 * target_dominance_fraction * (1.0 - target_dominance_fraction)
    )
    warning_tier, note = _classify_warning_tier(
        total_record_count=len(records),
        target_count=target_count,
        decoy_count=decoy_count,
        target_dominance_fraction=target_dominance_fraction,
        overlap_metric=overlap_metric,
        warning_overlap_threshold=warning_overlap_threshold,
        unstable_overlap_threshold=unstable_overlap_threshold,
    )
    payload = {
        "policy": policy.to_dict(),
        "summary": {
            "total_record_count": len(records),
            "labeled_record_count": target_count + decoy_count,
            "target_count": target_count,
            "decoy_count": decoy_count,
            "target_dominance_fraction": target_dominance_fraction,
            "overlap_metric": overlap_metric,
            "warning_tier": warning_tier.value,
            "fdr_unstable": warning_tier is ScoreSeparationWarningTier.UNSTABLE,
            "note": note,
        },
        "bins": [entry.to_dict() for entry in bins],
    }
    return ScoreSeparationDiagnosticReport(
        policy=policy,
        summary=ScoreSeparationDiagnosticSummary(
            total_record_count=len(records),
            labeled_record_count=target_count + decoy_count,
            target_count=target_count,
            decoy_count=decoy_count,
            target_dominance_fraction=target_dominance_fraction,
            overlap_metric=overlap_metric,
            warning_tier=warning_tier,
            fdr_unstable=warning_tier is ScoreSeparationWarningTier.UNSTABLE,
            note=note,
        ),
        reproducibility_hash=hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        bins=bins,
    )


def render_score_separation_bins_tsv(report: ScoreSeparationDiagnosticReport) -> str:
    """Render plot-ready score-separation bins as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "bin_lower",
            "bin_upper",
            "target_count",
            "decoy_count",
            "mixed_count",
            "unknown_count",
            "target_fraction",
            "decoy_fraction",
            "overlap_contribution",
        )
    )
    for entry in report.bins:
        writer.writerow(
            (
                entry.bin_lower,
                entry.bin_upper,
                entry.target_count,
                entry.decoy_count,
                entry.mixed_count,
                entry.unknown_count,
                entry.target_fraction,
                entry.decoy_fraction,
                entry.overlap_contribution,
            )
        )
    return buffer.getvalue()


def render_score_separation_summary_tsv(report: ScoreSeparationDiagnosticReport) -> str:
    """Render one summary row for target-decoy score separation."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "score_orientation",
            "bin_count",
            "warning_overlap_threshold",
            "unstable_overlap_threshold",
            "total_record_count",
            "labeled_record_count",
            "target_count",
            "decoy_count",
            "target_dominance_fraction",
            "overlap_metric",
            "warning_tier",
            "fdr_unstable",
            "note",
            "reproducibility_hash",
        )
    )
    writer.writerow(
        (
            report.policy.score_orientation,
            report.policy.bin_count,
            report.policy.warning_overlap_threshold,
            report.policy.unstable_overlap_threshold,
            report.summary.total_record_count,
            report.summary.labeled_record_count,
            report.summary.target_count,
            report.summary.decoy_count,
            report.summary.target_dominance_fraction,
            report.summary.overlap_metric,
            report.summary.warning_tier.value,
            str(report.summary.fdr_unstable).lower(),
            report.summary.note,
            report.reproducibility_hash,
        )
    )
    return buffer.getvalue()


def _build_bins(
    normalized_entries: tuple[NormalizedScoreEntry, ...],
    *,
    bin_count: int,
    target_count: int,
    decoy_count: int,
) -> tuple[ScoreSeparationBin, ...]:
    bins: list[ScoreSeparationBin] = []
    for index in range(bin_count):
        lower = index / bin_count
        upper = (index + 1) / bin_count
        if index == bin_count - 1:
            bucket = tuple(
                entry
                for entry in normalized_entries
                if lower <= entry.normalized_score <= upper
            )
        else:
            bucket = tuple(
                entry
                for entry in normalized_entries
                if lower <= entry.normalized_score < upper
            )
        bucket_target_count = sum(
            1 for entry in bucket if entry.target_decoy_label is TargetDecoyLabel.TARGET
        )
        bucket_decoy_count = sum(
            1 for entry in bucket if entry.target_decoy_label is TargetDecoyLabel.DECOY
        )
        target_fraction = (
            bucket_target_count / target_count if target_count else 0.0
        )
        decoy_fraction = bucket_decoy_count / decoy_count if decoy_count else 0.0
        bins.append(
            ScoreSeparationBin(
                bin_lower=lower,
                bin_upper=upper,
                target_count=bucket_target_count,
                decoy_count=bucket_decoy_count,
                mixed_count=sum(
                    1
                    for entry in bucket
                    if entry.target_decoy_label is TargetDecoyLabel.MIXED
                ),
                unknown_count=sum(
                    1
                    for entry in bucket
                    if entry.target_decoy_label is TargetDecoyLabel.UNKNOWN
                ),
                target_fraction=target_fraction,
                decoy_fraction=decoy_fraction,
                overlap_contribution=min(target_fraction, decoy_fraction),
            )
        )
    return tuple(bins)


def _target_dominance_fraction(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str,
) -> float | None:
    target_scores = [
        _oriented_score(record.score, score_orientation=score_orientation)
        for record in records
        if record.target_decoy_label is TargetDecoyLabel.TARGET
    ]
    decoy_scores = [
        _oriented_score(record.score, score_orientation=score_orientation)
        for record in records
        if record.target_decoy_label is TargetDecoyLabel.DECOY
    ]
    if not target_scores or not decoy_scores:
        return None
    target_better = 0.0
    total_pairs = len(target_scores) * len(decoy_scores)
    for target_score in target_scores:
        for decoy_score in decoy_scores:
            if target_score > decoy_score:
                target_better += 1.0
            elif target_score == decoy_score:
                target_better += 0.5
    return target_better / total_pairs


def _classify_warning_tier(
    *,
    total_record_count: int,
    target_count: int,
    decoy_count: int,
    target_dominance_fraction: float | None,
    overlap_metric: float,
    warning_overlap_threshold: float,
    unstable_overlap_threshold: float,
) -> tuple[ScoreSeparationWarningTier, str]:
    if total_record_count == 0:
        return (
            ScoreSeparationWarningTier.UNSTABLE,
            "no PSM records are available to compare target and decoy score distributions",
        )
    if target_count == 0 or decoy_count == 0:
        return (
            ScoreSeparationWarningTier.UNSTABLE,
            "target-decoy score separation is unavailable because one comparison class is missing",
        )
    if target_dominance_fraction is None or target_dominance_fraction < 0.5:
        return (
            ScoreSeparationWarningTier.UNSTABLE,
            "decoy scores outrank or tie target scores too often under the declared score orientation",
        )
    if overlap_metric >= unstable_overlap_threshold:
        return (
            ScoreSeparationWarningTier.UNSTABLE,
            "target and decoy score distributions overlap enough to make FDR behavior unstable",
        )
    if overlap_metric >= warning_overlap_threshold:
        return (
            ScoreSeparationWarningTier.WARNING,
            "target and decoy score distributions show moderate overlap and should be reviewed before relying on FDR",
        )
    return (
        ScoreSeparationWarningTier.STABLE,
        "target and decoy score distributions remain well separated under the declared score orientation",
    )


def _oriented_score(score: float, *, score_orientation: str) -> float:
    return score if score_orientation == "higher_better" else -score


__all__ = [
    "ScoreSeparationBin",
    "ScoreSeparationDiagnosticPolicy",
    "ScoreSeparationDiagnosticReport",
    "ScoreSeparationDiagnosticSummary",
    "ScoreSeparationWarningTier",
    "build_score_separation_diagnostic_report",
    "render_score_separation_bins_tsv",
    "render_score_separation_summary_tsv",
]
