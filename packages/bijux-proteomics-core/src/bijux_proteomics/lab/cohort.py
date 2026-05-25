# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Laboratory-facing cohort balance and subgroup-interpretation diagnostics."""

from __future__ import annotations

import csv
from collections import defaultdict
from itertools import combinations
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics_foundation import JsonModel


class CohortBalanceEntry(JsonModel):
    """One covariate-level cohort-balance diagnostic row."""

    model_config = ConfigDict(extra="forbid")

    covariate: str = Field(..., min_length=1)
    group_counts: str = Field(..., min_length=1)
    imbalance_score: float = Field(..., ge=0.0, le=1.0)
    confounded_with_condition: bool
    analysis_warning: str = Field(..., min_length=1)


def check_cohort_balance(
    metadata: tuple[ExperimentalDesignEntry, ...],
) -> tuple[CohortBalanceEntry, ...]:
    """Check whether sample covariates are balanced enough for subgroup interpretation."""

    if len(metadata) < 2:
        raise ValueError("cohort balance requires at least two metadata rows")
    sample_ids = tuple(entry.sample_id for entry in metadata)
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("cohort balance requires unique sample_id rows")

    active_conditions = tuple(sorted({entry.condition for entry in metadata if entry.condition}))
    if len(active_conditions) < 2:
        raise ValueError("cohort balance requires at least two populated conditions")

    entries: list[CohortBalanceEntry] = []
    for covariate, counts in sorted(_covariate_condition_counts(metadata).items()):
        observed_level_count = sum(sum(level_counts.values()) > 0 for level_counts in counts.values())
        if observed_level_count < 2:
            continue
        imbalance_score = _imbalance_score(counts, active_conditions)
        confounded = _confounded_with_condition(counts, active_conditions)
        entries.append(
            CohortBalanceEntry(
                covariate=covariate,
                group_counts=_render_group_counts(counts, active_conditions),
                imbalance_score=round(imbalance_score, 4),
                confounded_with_condition=confounded,
                analysis_warning=_analysis_warning(
                    covariate=covariate,
                    imbalance_score=imbalance_score,
                    confounded_with_condition=confounded,
                ),
            )
        )
    return tuple(entries)


def render_cohort_balance_tsv(entries: tuple[CohortBalanceEntry, ...]) -> str:
    """Render cohort-balance diagnostics as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "covariate",
            "group_counts",
            "imbalance_score",
            "confounded_with_condition",
            "analysis_warning",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.covariate,
                entry.group_counts,
                f"{entry.imbalance_score:.4f}",
                str(entry.confounded_with_condition).lower(),
                entry.analysis_warning,
            )
        )
    return buffer.getvalue()


def _covariate_condition_counts(
    metadata: tuple[ExperimentalDesignEntry, ...],
) -> dict[str, dict[str, dict[str, int]]]:
    fields = ("batch", "cohort", "instrument", "search_engine", "sample_role")
    counts: dict[str, dict[str, dict[str, int]]] = {}
    for entry in metadata:
        for field in fields:
            value = getattr(entry, field)
            if value in (None, ""):
                continue
            covariate = field
            level = str(value)
            counts.setdefault(covariate, {}).setdefault(level, defaultdict(int))[entry.condition] += 1
        for key, value in entry.metadata.items():
            normalized_key = key.strip()
            normalized_value = value.strip()
            if not normalized_key or not normalized_value:
                continue
            counts.setdefault(normalized_key, {}).setdefault(
                normalized_value, defaultdict(int)
            )[entry.condition] += 1
    return counts


def _imbalance_score(
    counts: dict[str, dict[str, int]],
    active_conditions: tuple[str, ...],
) -> float:
    condition_distributions: dict[str, dict[str, float]] = {}
    for condition in active_conditions:
        total = sum(level_counts.get(condition, 0) for level_counts in counts.values())
        if total <= 0:
            condition_distributions[condition] = {
                level: 0.0 for level in counts
            }
            continue
        condition_distributions[condition] = {
            level: level_counts.get(condition, 0) / total
            for level, level_counts in counts.items()
        }
    pairwise_scores: list[float] = []
    for left_condition, right_condition in combinations(active_conditions, 2):
        left_distribution = condition_distributions[left_condition]
        right_distribution = condition_distributions[right_condition]
        pairwise_scores.append(
            0.5
            * sum(
                abs(left_distribution[level] - right_distribution[level])
                for level in counts
            )
        )
    return max(pairwise_scores, default=0.0)


def _confounded_with_condition(
    counts: dict[str, dict[str, int]],
    active_conditions: tuple[str, ...],
) -> bool:
    level_condition_sets = {
        level: {condition for condition in active_conditions if level_counts.get(condition, 0) > 0}
        for level, level_counts in counts.items()
    }
    if any(len(condition_set) != 1 for condition_set in level_condition_sets.values()):
        return False
    condition_level_sets = {
        condition: {
            level
            for level, level_counts in counts.items()
            if level_counts.get(condition, 0) > 0
        }
        for condition in active_conditions
    }
    return all(condition_level_sets.values()) and all(
        len(condition_level_sets[condition_a] & condition_level_sets[condition_b]) == 0
        for condition_a, condition_b in combinations(active_conditions, 2)
    )


def _render_group_counts(
    counts: dict[str, dict[str, int]],
    active_conditions: tuple[str, ...],
) -> str:
    return ";".join(
        f"{level}["
        + ",".join(
            f"{condition}={level_counts.get(condition, 0)}"
            for condition in active_conditions
        )
        + "]"
        for level, level_counts in sorted(counts.items())
    )


def _analysis_warning(
    *,
    covariate: str,
    imbalance_score: float,
    confounded_with_condition: bool,
) -> str:
    if confounded_with_condition:
        return (
            f"covariate {covariate} is fully confounded with condition and blocks naive subgroup interpretation"
        )
    if imbalance_score >= 0.6:
        return (
            f"covariate {covariate} is materially imbalanced across conditions; subgroup interpretation requires caution"
        )
    return (
        f"covariate {covariate} spans the active conditions without blocking subgroup interpretation"
    )


__all__ = [
    "CohortBalanceEntry",
    "check_cohort_balance",
    "render_cohort_balance_tsv",
]
