# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein-set scoring calculations over normalized protein tables."""

from __future__ import annotations

from collections import defaultdict
import math
from typing import TYPE_CHECKING

import numpy as np

from bijux_proteomics.interpretation.protein_set_scoring.models import (
    ProteinSetConditionComparisonEntry,
    ProteinSetConditionScoreEntry,
    ProteinSetRecord,
    ProteinSetSampleScoreEntry,
    ProteinSetScoreConfidenceStatus,
    UnresolvedProteinSetMemberEntry,
)
from bijux_proteomics.quantification.contracts.matrix_building import (
    _condition_lookup,
    _matrix_value_index,
)
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable

if TYPE_CHECKING:
    from bijux_proteomics.io.formats import ExperimentalDesignEntry


def build_sample_scores_and_unresolved_members(
    table: LabelFreeQuantTable,
    protein_set_records: tuple[ProteinSetRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...] = (),
    minimum_observed_member_count: int,
) -> tuple[
    tuple[ProteinSetSampleScoreEntry, ...], tuple[UnresolvedProteinSetMemberEntry, ...]
]:
    """Build sample-level scores and unresolved members for one protein-set collection."""

    sample_ids = table.sample_ids
    sample_conditions = _condition_lookup(design_entries)
    sample_batches = {entry.sample_id: entry.batch for entry in design_entries}
    grouped_sets: dict[str, list[ProteinSetRecord]] = defaultdict(list)
    for record in protein_set_records:
        grouped_sets[record.set_id].append(record)
    standardized_values = standardized_protein_values(table)
    available_proteins = set(table.entity_ids)

    unresolved_members: list[UnresolvedProteinSetMemberEntry] = []
    sample_scores: list[ProteinSetSampleScoreEntry] = []
    for set_id in sorted(grouped_sets):
        records = grouped_sets[set_id]
        first = records[0]
        member_ids = tuple(dict.fromkeys(record.protein_ref for record in records))
        unresolved_ids = tuple(
            protein_ref
            for protein_ref in member_ids
            if protein_ref not in available_proteins
        )
        for protein_ref in unresolved_ids:
            unresolved_members.append(
                UnresolvedProteinSetMemberEntry(
                    set_id=set_id,
                    set_name=first.set_name,
                    set_category=first.set_category,
                    source_name=first.source_name,
                    source_accession=first.source_accession,
                    protein_ref=protein_ref,
                    reason="protein set member was not present in the quantification table",
                )
            )
        for sample_id in sample_ids:
            observed_member_ids: list[str] = []
            missing_member_ids: list[str] = []
            observed_scores: list[float] = []
            for protein_ref in member_ids:
                standardized = standardized_values.get((protein_ref, sample_id))
                if standardized is None:
                    missing_member_ids.append(protein_ref)
                    continue
                observed_member_ids.append(protein_ref)
                observed_scores.append(standardized)
            total_member_count = len(member_ids)
            observed_member_count = len(observed_member_ids)
            confidence_status = sample_confidence_status(
                observed_member_count=observed_member_count,
                minimum_observed_member_count=minimum_observed_member_count,
            )
            activity_score = (
                round(float(np.mean(observed_scores)), 6) if observed_scores else None
            )
            sample_scores.append(
                ProteinSetSampleScoreEntry(
                    set_id=set_id,
                    set_name=first.set_name,
                    set_category=first.set_category,
                    source_name=first.source_name,
                    source_accession=first.source_accession,
                    sample_id=sample_id,
                    condition=sample_conditions.get(sample_id),
                    batch=sample_batches.get(sample_id),
                    activity_score=activity_score,
                    total_member_count=total_member_count,
                    observed_member_count=observed_member_count,
                    missing_member_count=total_member_count - observed_member_count,
                    observed_fraction=(
                        observed_member_count / total_member_count
                        if total_member_count > 0
                        else 0.0
                    ),
                    minimum_observed_member_count=minimum_observed_member_count,
                    confidence_status=confidence_status,
                    confidence_reason=confidence_reason(
                        observed_member_count=observed_member_count,
                        minimum_observed_member_count=minimum_observed_member_count,
                    ),
                    observed_member_ids=tuple(observed_member_ids),
                    missing_member_ids=tuple(missing_member_ids),
                )
            )
    return tuple(sample_scores), tuple(unresolved_members)


def build_condition_scores(
    sample_scores: tuple[ProteinSetSampleScoreEntry, ...],
) -> tuple[ProteinSetConditionScoreEntry, ...]:
    """Aggregate sample-level protein-set scores into condition-level summaries."""

    grouped: dict[tuple[str, str], list[ProteinSetSampleScoreEntry]] = defaultdict(list)
    for entry in sample_scores:
        if entry.condition is None:
            continue
        grouped[(entry.set_id, entry.condition)].append(entry)
    results: list[ProteinSetConditionScoreEntry] = []
    for (set_id, condition), entries in sorted(grouped.items()):
        first = entries[0]
        scored_values = [
            entry.activity_score
            for entry in entries
            if entry.activity_score is not None
        ]
        results.append(
            ProteinSetConditionScoreEntry(
                set_id=set_id,
                set_name=first.set_name,
                set_category=first.set_category,
                source_name=first.source_name,
                source_accession=first.source_accession,
                condition=condition,
                sample_count=len(entries),
                scored_sample_count=len(scored_values),
                high_confidence_sample_count=sum(
                    1
                    for entry in entries
                    if entry.confidence_status
                    is ProteinSetScoreConfidenceStatus.HIGH_CONFIDENCE
                ),
                low_confidence_sample_count=sum(
                    1
                    for entry in entries
                    if entry.confidence_status
                    is ProteinSetScoreConfidenceStatus.LOW_CONFIDENCE
                ),
                confidence_status=aggregate_confidence_status(
                    tuple(entry.confidence_status for entry in entries)
                ),
                mean_activity_score=(
                    round(float(np.mean(scored_values)), 6) if scored_values else None
                ),
            )
        )
    return tuple(results)


def build_condition_comparisons(
    condition_scores: tuple[ProteinSetConditionScoreEntry, ...],
) -> tuple[ProteinSetConditionComparisonEntry, ...]:
    """Build pairwise condition comparisons for each scored protein set."""

    grouped: dict[str, list[ProteinSetConditionScoreEntry]] = defaultdict(list)
    for entry in condition_scores:
        grouped[entry.set_id].append(entry)
    results: list[ProteinSetConditionComparisonEntry] = []
    for set_id in sorted(grouped):
        entries = sorted(grouped[set_id], key=lambda entry: entry.condition)
        for left_index in range(len(entries)):
            for right_index in range(left_index + 1, len(entries)):
                left = entries[left_index]
                right = entries[right_index]
                delta = (
                    round(right.mean_activity_score - left.mean_activity_score, 6)
                    if left.mean_activity_score is not None
                    and right.mean_activity_score is not None
                    else None
                )
                results.append(
                    ProteinSetConditionComparisonEntry(
                        set_id=set_id,
                        set_name=left.set_name,
                        set_category=left.set_category,
                        source_name=left.source_name,
                        source_accession=left.source_accession,
                        condition_a=left.condition,
                        condition_b=right.condition,
                        condition_a_confidence_status=left.confidence_status,
                        condition_b_confidence_status=right.confidence_status,
                        comparison_confidence_status=aggregate_confidence_status(
                            (left.confidence_status, right.confidence_status)
                        ),
                        mean_activity_score_a=left.mean_activity_score,
                        mean_activity_score_b=right.mean_activity_score,
                        activity_score_delta=delta,
                    )
                )
    return tuple(results)


def standardized_protein_values(
    table: LabelFreeQuantTable,
) -> dict[tuple[str, str], float | None]:
    """Standardize protein abundances across samples for one protein matrix."""

    value_lookup = _matrix_value_index(table)
    standardized: dict[tuple[str, str], float | None] = {}
    for protein_ref in table.entity_ids:
        observed_values: list[float] = []
        sample_values: dict[str, float | None] = {}
        for sample_id in table.sample_ids:
            abundance = value_lookup[(protein_ref, sample_id)].abundance
            if abundance is None:
                sample_values[sample_id] = None
                continue
            log_value = math.log2(float(abundance) + 1.0)
            sample_values[sample_id] = log_value
            observed_values.append(log_value)
        if not observed_values:
            for sample_id in table.sample_ids:
                standardized[(protein_ref, sample_id)] = None
            continue
        mean_value = float(np.mean(observed_values))
        std_value = float(np.std(observed_values))
        for sample_id in table.sample_ids:
            value = sample_values[sample_id]
            if value is None:
                standardized[(protein_ref, sample_id)] = None
            elif std_value <= 1e-12:
                standardized[(protein_ref, sample_id)] = 0.0
            else:
                standardized[(protein_ref, sample_id)] = (
                    value - mean_value
                ) / std_value
    return standardized


def sample_confidence_status(
    *,
    observed_member_count: int,
    minimum_observed_member_count: int,
) -> ProteinSetScoreConfidenceStatus:
    """Determine sample-level scoring confidence from observed member coverage."""

    if observed_member_count >= minimum_observed_member_count:
        return ProteinSetScoreConfidenceStatus.HIGH_CONFIDENCE
    return ProteinSetScoreConfidenceStatus.LOW_CONFIDENCE


def aggregate_confidence_status(
    statuses: tuple[ProteinSetScoreConfidenceStatus, ...],
) -> ProteinSetScoreConfidenceStatus:
    """Collapse a set of confidence statuses into one owned aggregate label."""

    if all(
        status is ProteinSetScoreConfidenceStatus.HIGH_CONFIDENCE for status in statuses
    ):
        return ProteinSetScoreConfidenceStatus.HIGH_CONFIDENCE
    return ProteinSetScoreConfidenceStatus.LOW_CONFIDENCE


def confidence_reason(
    *,
    observed_member_count: int,
    minimum_observed_member_count: int,
) -> str | None:
    """Return one stable reason when member coverage falls below policy."""

    if observed_member_count >= minimum_observed_member_count:
        return None
    return (
        "observed member count "
        f"{observed_member_count} was below minimum {minimum_observed_member_count}"
    )


__all__ = [
    "aggregate_confidence_status",
    "build_condition_comparisons",
    "build_condition_scores",
    "build_sample_scores_and_unresolved_members",
    "confidence_reason",
    "sample_confidence_status",
    "standardized_protein_values",
]
