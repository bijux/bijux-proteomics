# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Score calculation for pathway activity reports."""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from bijux_proteomics.interpretation.pathway_activity.member_resolution import (
    build_member_specs,
    member_label,
)
from bijux_proteomics.interpretation.pathway_activity.models import (
    PathwayActivityConfidenceStatus,
    PathwayConditionComparisonEntry,
    PathwayConditionScoreEntry,
    PathwayMemberContributionEntry,
    PathwaySampleScoreEntry,
    UnresolvedPathwayActivityMemberEntry,
)
from bijux_proteomics.interpretation.pathway_enrichment import PathwayMembershipRecord


def build_sample_scores_and_member_contributions(
    *,
    pathway_groups: dict[str, list[PathwayMembershipRecord]],
    sample_ids: tuple[str, ...],
    sample_conditions: dict[str, str],
    sample_batches: dict[str, str | None],
    protein_scores: dict[tuple[str, str], float | None],
    available_protein_refs: set[str],
    gene_to_proteins: dict[str, tuple[str, ...]],
    minimum_observed_member_count: int,
    minimum_knowledge_coverage_fraction: float,
    coverage_by_pathway_id: dict[str, object],
) -> tuple[
    list[PathwaySampleScoreEntry],
    list[PathwayMemberContributionEntry],
    list[UnresolvedPathwayActivityMemberEntry],
]:
    """Build sample-level scores, member contribution rows, and unresolved members."""

    unresolved_members: list[UnresolvedPathwayActivityMemberEntry] = []
    member_contributions: list[PathwayMemberContributionEntry] = []
    sample_scores: list[PathwaySampleScoreEntry] = []
    for pathway_id in sorted(pathway_groups):
        records = pathway_groups[pathway_id]
        first = records[0]
        pathway_coverage = coverage_by_pathway_id.get(pathway_id)
        member_specs = build_member_specs(
            records,
            available_protein_refs=available_protein_refs,
            gene_to_proteins=gene_to_proteins,
            unresolved_members=unresolved_members,
        )
        for sample_id in sample_ids:
            observed_member_ids: list[str] = []
            missing_member_ids: list[str] = []
            member_scores: list[float] = []
            for member_kind, member_id, resolved_protein_refs in member_specs:
                observed_protein_refs = tuple(
                    protein_ref
                    for protein_ref in resolved_protein_refs
                    if protein_scores.get((protein_ref, sample_id)) is not None
                )
                member_activity_score = (
                    round(
                        float(
                            np.mean(
                                [
                                    protein_scores[(protein_ref, sample_id)]
                                    for protein_ref in observed_protein_refs
                                ]
                            )
                        ),
                        6,
                    )
                    if observed_protein_refs
                    else None
                )
                labeled_member = member_label(member_kind, member_id)
                if member_activity_score is None:
                    missing_member_ids.append(labeled_member)
                else:
                    observed_member_ids.append(labeled_member)
                    member_scores.append(member_activity_score)
                member_contributions.append(
                    PathwayMemberContributionEntry(
                        pathway_id=pathway_id,
                        pathway_name=first.pathway_name,
                        source_name=first.source_name,
                        source_accession=first.source_accession,
                        sample_id=sample_id,
                        condition=sample_conditions.get(sample_id),
                        batch=sample_batches.get(sample_id),
                        member_kind=member_kind,
                        member_id=member_id,
                        resolved_protein_refs=resolved_protein_refs,
                        observed_protein_refs=observed_protein_refs,
                        resolved_protein_count=len(resolved_protein_refs),
                        observed_protein_count=len(observed_protein_refs),
                        missing_protein_count=len(resolved_protein_refs)
                        - len(observed_protein_refs),
                        member_activity_score=member_activity_score,
                        observed=member_activity_score is not None,
                    )
                )
            total_member_count = len(member_specs)
            observed_member_count = len(observed_member_ids)
            sample_scores.append(
                PathwaySampleScoreEntry(
                    pathway_id=pathway_id,
                    pathway_name=first.pathway_name,
                    source_name=first.source_name,
                    source_accession=first.source_accession,
                    sample_id=sample_id,
                    condition=sample_conditions.get(sample_id),
                    batch=sample_batches.get(sample_id),
                    activity_score=(
                        round(float(np.mean(member_scores)), 6)
                        if member_scores
                        else None
                    ),
                    total_member_count=total_member_count,
                    observed_member_count=observed_member_count,
                    missing_member_count=total_member_count - observed_member_count,
                    observed_fraction=(
                        observed_member_count / total_member_count
                        if total_member_count > 0
                        else 0.0
                    ),
                    minimum_observed_member_count=minimum_observed_member_count,
                    confidence_status=sample_confidence_status(
                        observed_member_count=observed_member_count,
                        minimum_observed_member_count=minimum_observed_member_count,
                        pathway_coverage_status=(
                            None
                            if pathway_coverage is None
                            else pathway_coverage.confidence_status.value
                        ),
                    ),
                    confidence_reason=confidence_reason(
                        observed_member_count=observed_member_count,
                        minimum_observed_member_count=minimum_observed_member_count,
                        pathway_coverage_status=(
                            None
                            if pathway_coverage is None
                            else pathway_coverage.confidence_status.value
                        ),
                        pathway_coverage_fraction=(
                            None
                            if pathway_coverage is None
                            else pathway_coverage.coverage_fraction
                        ),
                        minimum_knowledge_coverage_fraction=(
                            minimum_knowledge_coverage_fraction
                        ),
                    ),
                    observed_member_ids=tuple(observed_member_ids),
                    missing_member_ids=tuple(missing_member_ids),
                )
            )
    return sample_scores, member_contributions, unresolved_members


def build_condition_scores(
    sample_scores: list[PathwaySampleScoreEntry],
) -> list[PathwayConditionScoreEntry]:
    """Aggregate sample-level scores into condition-level pathway activity rows."""

    grouped: dict[tuple[str, str], list[PathwaySampleScoreEntry]] = defaultdict(list)
    for entry in sample_scores:
        if entry.condition is None:
            continue
        grouped[(entry.pathway_id, entry.condition)].append(entry)
    results: list[PathwayConditionScoreEntry] = []
    for (pathway_id, condition), entries in sorted(grouped.items()):
        first = entries[0]
        scored_values = [
            entry.activity_score
            for entry in entries
            if entry.activity_score is not None
        ]
        results.append(
            PathwayConditionScoreEntry(
                pathway_id=pathway_id,
                pathway_name=first.pathway_name,
                source_name=first.source_name,
                source_accession=first.source_accession,
                condition=condition,
                sample_count=len(entries),
                scored_sample_count=len(scored_values),
                high_confidence_sample_count=sum(
                    1
                    for entry in entries
                    if entry.confidence_status
                    is PathwayActivityConfidenceStatus.HIGH_CONFIDENCE
                ),
                low_confidence_sample_count=sum(
                    1
                    for entry in entries
                    if entry.confidence_status
                    is PathwayActivityConfidenceStatus.LOW_CONFIDENCE
                ),
                confidence_status=aggregate_confidence_status(
                    tuple(entry.confidence_status for entry in entries)
                ),
                mean_activity_score=(
                    round(float(np.mean(scored_values)), 6) if scored_values else None
                ),
            )
        )
    return results


def build_condition_comparisons(
    condition_scores: list[PathwayConditionScoreEntry],
) -> list[PathwayConditionComparisonEntry]:
    """Build pairwise condition contrasts for each pathway."""

    grouped: dict[str, list[PathwayConditionScoreEntry]] = defaultdict(list)
    for entry in condition_scores:
        grouped[entry.pathway_id].append(entry)
    results: list[PathwayConditionComparisonEntry] = []
    for pathway_id in sorted(grouped):
        entries = sorted(grouped[pathway_id], key=lambda entry: entry.condition)
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
                    PathwayConditionComparisonEntry(
                        pathway_id=pathway_id,
                        pathway_name=left.pathway_name,
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
    return results


def sample_confidence_status(
    *,
    observed_member_count: int,
    minimum_observed_member_count: int,
    pathway_coverage_status: str | None,
) -> PathwayActivityConfidenceStatus:
    """Assign sample-level confidence from observed and knowledge coverage."""

    if observed_member_count < minimum_observed_member_count:
        return PathwayActivityConfidenceStatus.LOW_CONFIDENCE
    if pathway_coverage_status == "low_confidence":
        return PathwayActivityConfidenceStatus.LOW_CONFIDENCE
    return PathwayActivityConfidenceStatus.HIGH_CONFIDENCE


def aggregate_confidence_status(
    statuses: tuple[PathwayActivityConfidenceStatus, ...],
) -> PathwayActivityConfidenceStatus:
    """Reduce multiple confidence labels to the owned aggregate status."""

    if all(
        status is PathwayActivityConfidenceStatus.HIGH_CONFIDENCE for status in statuses
    ):
        return PathwayActivityConfidenceStatus.HIGH_CONFIDENCE
    return PathwayActivityConfidenceStatus.LOW_CONFIDENCE


def confidence_reason(
    *,
    observed_member_count: int,
    minimum_observed_member_count: int,
    pathway_coverage_status: str | None,
    pathway_coverage_fraction: float | None,
    minimum_knowledge_coverage_fraction: float,
) -> str | None:
    """Explain low-confidence pathway scores when coverage thresholds are missed."""

    reasons: list[str] = []
    if observed_member_count < minimum_observed_member_count:
        reasons.append(
            "observed member count "
            f"{observed_member_count} was below minimum {minimum_observed_member_count}"
        )
    if pathway_coverage_status == "low_confidence":
        if pathway_coverage_fraction is None:
            raise RuntimeError(
                "low-confidence pathway coverage reasoning requires an explicit coverage fraction"
            )
        reasons.append(
            "pathway knowledge coverage "
            f"{pathway_coverage_fraction:g} was below minimum "
            f"{minimum_knowledge_coverage_fraction:g}"
        )
    if not reasons:
        return None
    return "; ".join(reasons)
