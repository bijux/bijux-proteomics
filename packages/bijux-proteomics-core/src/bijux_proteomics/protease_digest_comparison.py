# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Protease-comparison digest reports over changed peptide spaces."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import ConfigDict, Field

from bijux_proteomics.digestion import digest_sequence
from bijux_proteomics_foundation import JsonModel


class ProteaseDigestComparisonEntry(JsonModel):
    """Digest peptide-space summary for one protease."""

    model_config = ConfigDict(extra="forbid")

    protease: str = Field(..., min_length=1)
    peptide_count: int = Field(..., ge=0)
    peptides: tuple[str, ...] = Field(default_factory=tuple)
    gained_vs_baseline: tuple[str, ...] = Field(default_factory=tuple)
    lost_vs_baseline: tuple[str, ...] = Field(default_factory=tuple)


class ProteaseDigestComparisonReport(JsonModel):
    """Digest report comparing peptide spaces across proteases."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1)
    baseline_protease: str = Field(..., min_length=1)
    entries: tuple[ProteaseDigestComparisonEntry, ...] = Field(default_factory=tuple)


def build_protease_digest_comparison_report(
    *,
    sequence: str,
    source_accession: str,
    proteases: Sequence[str],
    min_length: int = 1,
    max_length: int | None = None,
) -> ProteaseDigestComparisonReport:
    """Compare changed peptide spaces across multiple proteases."""
    if not proteases:
        raise ValueError("protease comparison requires at least one protease")
    normalized_sequence = sequence.strip().upper()
    baseline = proteases[0]
    baseline_peptides = {
        entry.sequence
        for entry in digest_sequence(
            normalized_sequence,
            source_accession=source_accession,
            protease=baseline,
            min_length=min_length,
            max_length=max_length,
        )
    }
    entries: list[ProteaseDigestComparisonEntry] = []
    for protease in proteases:
        peptides = {
            entry.sequence
            for entry in digest_sequence(
                normalized_sequence,
                source_accession=source_accession,
                protease=protease,
                min_length=min_length,
                max_length=max_length,
            )
        }
        entries.append(
            ProteaseDigestComparisonEntry(
                protease=protease,
                peptide_count=len(peptides),
                peptides=tuple(sorted(peptides)),
                gained_vs_baseline=tuple(sorted(peptides - baseline_peptides)),
                lost_vs_baseline=tuple(sorted(baseline_peptides - peptides)),
            )
        )
    return ProteaseDigestComparisonReport(
        sequence=normalized_sequence,
        baseline_protease=baseline,
        entries=tuple(entries),
    )
