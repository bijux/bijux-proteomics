# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PSM evidence inspection and distribution reporting."""

from __future__ import annotations

from collections import defaultdict

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import PsmParseReport
from bijux_proteomics.sequences.digestion import (
    ProteaseRule,
    count_missed_cleavages,
    resolve_protease_rule,
)
from bijux_proteomics_foundation import JsonModel

_Q_VALUE_BUCKETS: tuple[tuple[float, float, str], ...] = (
    (0.0, 0.01, "0-0.01"),
    (0.01, 0.05, "0.01-0.05"),
    (0.05, 0.1, "0.05-0.1"),
    (0.1, 0.2, "0.1-0.2"),
)
_PEPTIDE_LENGTH_BUCKETS: tuple[tuple[int, int | None, str], ...] = (
    (1, 7, "1-7"),
    (8, 14, "8-14"),
    (15, 24, "15-24"),
    (25, 39, "25-39"),
    (40, None, "40+"),
)


class PsmInspectionDistributionEntry(JsonModel):
    """One reviewer-facing bucket inside a PSM evidence distribution."""

    model_config = ConfigDict(extra="forbid")

    bucket: str = Field(..., min_length=1)
    count: int = Field(..., ge=0)


class PsmEvidenceInspectionReport(JsonModel):
    """Review-oriented inspection report over accepted and rejected PSM evidence."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_rows: int = Field(..., ge=0)
    rejected_rows: int = Field(..., ge=0)
    protease: str = Field(..., min_length=1)
    score_distribution: tuple[PsmInspectionDistributionEntry, ...] = Field(
        default_factory=tuple
    )
    q_value_distribution: tuple[PsmInspectionDistributionEntry, ...] = Field(
        default_factory=tuple
    )
    charge_distribution: tuple[PsmInspectionDistributionEntry, ...] = Field(
        default_factory=tuple
    )
    peptide_length_distribution: tuple[PsmInspectionDistributionEntry, ...] = Field(
        default_factory=tuple
    )
    missed_cleavage_distribution: tuple[PsmInspectionDistributionEntry, ...] = Field(
        default_factory=tuple
    )


def build_psm_evidence_inspection_report(
    parse_report: PsmParseReport,
    *,
    protease: ProteaseRule | str = "trypsin",
    score_bin_size: float = 10.0,
) -> PsmEvidenceInspectionReport:
    """Build one review-oriented inspection report over parsed PSM evidence."""
    if score_bin_size <= 0:
        raise ValueError("score_bin_size must be greater than zero")
    protease_rule = (
        resolve_protease_rule(protease) if isinstance(protease, str) else protease
    )
    score_distribution = _build_score_distribution(
        parse_report=parse_report,
        score_bin_size=score_bin_size,
    )
    q_value_distribution = _build_q_value_distribution(parse_report=parse_report)
    charge_distribution = _build_charge_distribution(parse_report=parse_report)
    peptide_length_distribution = _build_peptide_length_distribution(
        parse_report=parse_report
    )
    missed_cleavage_distribution = _build_missed_cleavage_distribution(
        parse_report=parse_report,
        protease=protease_rule,
    )
    return PsmEvidenceInspectionReport(
        total_rows=parse_report.total_rows,
        accepted_rows=len(parse_report.accepted_records),
        rejected_rows=len(parse_report.rejected_rows),
        protease=protease_rule.name,
        score_distribution=score_distribution,
        q_value_distribution=q_value_distribution,
        charge_distribution=charge_distribution,
        peptide_length_distribution=peptide_length_distribution,
        missed_cleavage_distribution=missed_cleavage_distribution,
    )


def render_psm_evidence_inspection_summary_tsv(
    report: PsmEvidenceInspectionReport,
) -> str:
    """Render one PSM evidence inspection summary ledger as TSV."""
    lines = ["metric\tvalue"]
    for metric, value in (
        ("total_rows", str(report.total_rows)),
        ("accepted_rows", str(report.accepted_rows)),
        ("rejected_rows", str(report.rejected_rows)),
        ("protease", report.protease),
    ):
        lines.append(f"{metric}\t{value}")
    return "\n".join(lines) + "\n"


def render_psm_inspection_distribution_tsv(
    entries: tuple[PsmInspectionDistributionEntry, ...],
) -> str:
    """Render one PSM evidence distribution ledger as TSV."""
    lines = ["bucket\tcount"]
    for entry in entries:
        lines.append(f"{entry.bucket}\t{entry.count}")
    return "\n".join(lines) + "\n"


def _build_score_distribution(
    *,
    parse_report: PsmParseReport,
    score_bin_size: float,
) -> tuple[PsmInspectionDistributionEntry, ...]:
    counts: dict[str, int] = defaultdict(int)
    for record in parse_report.accepted_records:
        lower = int(record.score // score_bin_size) * int(score_bin_size)
        upper = lower + int(score_bin_size)
        counts[f"{lower}-{upper}"] += 1
    return _render_distribution_entries(counts)


def _build_q_value_distribution(
    *,
    parse_report: PsmParseReport,
) -> tuple[PsmInspectionDistributionEntry, ...]:
    counts: dict[str, int] = defaultdict(int)
    for record in parse_report.accepted_records:
        if record.q_value is None:
            counts["missing"] += 1
            continue
        matched_bucket = False
        for lower, upper, label in _Q_VALUE_BUCKETS:
            if lower <= record.q_value < upper:
                counts[label] += 1
                matched_bucket = True
                break
        if not matched_bucket:
            counts["0.2+"] += 1
    return _render_distribution_entries(
        counts,
        ordered_buckets=(
            "0-0.01",
            "0.01-0.05",
            "0.05-0.1",
            "0.1-0.2",
            "0.2+",
            "missing",
        ),
    )


def _build_charge_distribution(
    *,
    parse_report: PsmParseReport,
) -> tuple[PsmInspectionDistributionEntry, ...]:
    counts: dict[str, int] = defaultdict(int)
    for record in parse_report.accepted_records:
        counts[str(record.charge)] += 1
    return tuple(
        PsmInspectionDistributionEntry(bucket=bucket, count=counts[bucket])
        for bucket in sorted(counts, key=lambda value: int(value))
    )


def _build_peptide_length_distribution(
    *,
    parse_report: PsmParseReport,
) -> tuple[PsmInspectionDistributionEntry, ...]:
    counts: dict[str, int] = defaultdict(int)
    for record in parse_report.accepted_records:
        length = len(record.peptide_sequence or record.peptide)
        for lower, upper, label in _PEPTIDE_LENGTH_BUCKETS:
            if upper is None:
                if length >= lower:
                    counts[label] += 1
                    break
            elif lower <= length <= upper:
                counts[label] += 1
                break
    return _render_distribution_entries(
        counts,
        ordered_buckets=("1-7", "8-14", "15-24", "25-39", "40+"),
    )


def _build_missed_cleavage_distribution(
    *,
    parse_report: PsmParseReport,
    protease: ProteaseRule,
) -> tuple[PsmInspectionDistributionEntry, ...]:
    counts: dict[str, int] = defaultdict(int)
    for record in parse_report.accepted_records:
        sequence = record.peptide_sequence or record.peptide
        counts[str(count_missed_cleavages(sequence, protease))] += 1
    return tuple(
        PsmInspectionDistributionEntry(bucket=bucket, count=counts[bucket])
        for bucket in sorted(counts, key=lambda value: int(value))
    )


def _render_distribution_entries(
    counts: dict[str, int],
    *,
    ordered_buckets: tuple[str, ...] | None = None,
) -> tuple[PsmInspectionDistributionEntry, ...]:
    if ordered_buckets is not None:
        entries = [
            PsmInspectionDistributionEntry(bucket=bucket, count=counts[bucket])
            for bucket in ordered_buckets
            if bucket in counts
        ]
        return tuple(entries)
    return tuple(
        PsmInspectionDistributionEntry(bucket=bucket, count=counts[bucket])
        for bucket in sorted(counts)
    )
