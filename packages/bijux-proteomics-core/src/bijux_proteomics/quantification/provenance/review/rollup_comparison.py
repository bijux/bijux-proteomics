# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Protein rollup strategy comparison builders for review surfaces."""

from __future__ import annotations

from bijux_proteomics.quantification.contracts import Ms1FeatureRecord
from bijux_proteomics.quantification.provenance.review.models import (
    ProteinRollupStrategyComparisonEntry,
    ProteinRollupStrategyComparisonReport,
    ProteinRollupStrategyKind,
    ProteinRollupStrategyValue,
)


def _rollup_value_for_strategy(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    protein_ref: str,
    sample_id: str,
    strategy: ProteinRollupStrategyKind,
    top_n: int,
) -> float | None:
    bucket = [
        record
        for record in records
        if record.sample_id == sample_id
        and record.intensity is not None
        and protein_ref in record.protein_refs
    ]
    if not bucket:
        return None
    intensities = [float(record.intensity or 0.0) for record in bucket]
    if strategy is ProteinRollupStrategyKind.SUM:
        return float(sum(intensities))
    if strategy is ProteinRollupStrategyKind.TOP_N:
        return float(sum(sorted(intensities, reverse=True)[:top_n]))
    if strategy is ProteinRollupStrategyKind.MEDIAN_POLISH_LIKE:
        ordered = sorted(intensities)
        middle = len(ordered) // 2
        if len(ordered) % 2:
            return float(ordered[middle])
        return float((ordered[middle - 1] + ordered[middle]) / 2.0)
    if strategy is ProteinRollupStrategyKind.RAZOR_ONLY:
        unique = [
            float(record.intensity or 0.0)
            for record in bucket
            if len(record.protein_refs) == 1
        ]
        return float(sum(unique)) if unique else None
    if strategy is ProteinRollupStrategyKind.SHARED_EXCLUDED:
        non_shared = [
            float(record.intensity or 0.0)
            for record in bucket
            if len(record.protein_refs) == 1
        ]
        return float(sum(non_shared)) if non_shared else 0.0
    weighted = [
        float(record.intensity or 0.0) / max(1, len(record.protein_refs))
        for record in bucket
    ]
    return float(sum(weighted))


def build_protein_rollup_strategy_comparison_report(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    top_n: int = 3,
) -> ProteinRollupStrategyComparisonReport:
    """Compare protein rollup outcomes across six explicit strategy families."""
    proteins = tuple(
        sorted(
            {protein_ref for record in records for protein_ref in record.protein_refs}
        )
    )
    samples = tuple(sorted({record.sample_id for record in records}))
    strategies = (
        ProteinRollupStrategyKind.SUM,
        ProteinRollupStrategyKind.TOP_N,
        ProteinRollupStrategyKind.MEDIAN_POLISH_LIKE,
        ProteinRollupStrategyKind.RAZOR_ONLY,
        ProteinRollupStrategyKind.SHARED_EXCLUDED,
        ProteinRollupStrategyKind.EVIDENCE_WEIGHTED,
    )
    entries: list[ProteinRollupStrategyComparisonEntry] = []
    for protein_ref in proteins:
        for sample_id in samples:
            values = tuple(
                ProteinRollupStrategyValue(
                    strategy=strategy,
                    abundance=_rollup_value_for_strategy(
                        records,
                        protein_ref=protein_ref,
                        sample_id=sample_id,
                        strategy=strategy,
                        top_n=top_n,
                    ),
                )
                for strategy in strategies
            )
            finite = [
                value.abundance for value in values if value.abundance is not None
            ]
            entries.append(
                ProteinRollupStrategyComparisonEntry(
                    protein_ref=protein_ref,
                    sample_id=sample_id,
                    strategy_values=values,
                    max_strategy_difference=(
                        max(finite) - min(finite) if finite else 0.0
                    ),
                )
            )
    return ProteinRollupStrategyComparisonReport(entries=tuple(entries))


__all__ = ["build_protein_rollup_strategy_comparison_report"]
