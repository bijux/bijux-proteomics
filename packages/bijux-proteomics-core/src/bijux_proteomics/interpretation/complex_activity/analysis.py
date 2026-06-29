# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein complex activity scoring over protein matrices with limiting subunits."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

import numpy as np

from bijux_proteomics.interpretation.complex_activity.member_resolution import (
    build_member_specs,
    gene_to_protein_refs,
    group_complex_records,
    member_label,
    protein_gene_annotations,
    protein_refs_in_table,
    standardized_protein_ref_values,
)
from bijux_proteomics.interpretation.complex_enrichment import (
    ComplexMemberKind,
    ComplexMembershipRecord,
)
from bijux_proteomics.interpretation.complex_activity.models import (
    ComplexActivityConfidenceStatus,
    ComplexActivityPolicy,
    ComplexActivityReport,
    ComplexActivitySummary,
    ComplexConditionComparisonEntry,
    ComplexConditionScoreEntry,
    ComplexMemberContributionEntry,
    ComplexSampleScoreEntry,
    UnresolvedComplexActivityMemberEntry,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationRecord,
)
from bijux_proteomics.quantification.contracts.input_models import (
    QuantEntityLevel,
)
from bijux_proteomics.quantification.contracts.matrix_building import _condition_lookup
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable
from bijux_proteomics.sequences.core import NormalizedProteinRecord

if TYPE_CHECKING:
    from bijux_proteomics.io.formats import ExperimentalDesignEntry


def build_complex_activity_report(
    table: LabelFreeQuantTable,
    complex_records: tuple[ComplexMembershipRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...] = (),
    fasta_records: tuple[NormalizedProteinRecord, ...] = (),
    custom_annotations: tuple[ProteinAnnotationRecord, ...] = (),
    policy: ComplexActivityPolicy | None = None,
) -> ComplexActivityReport:
    """Score complex activity per sample over one protein quantification table."""

    if table.entity_level is not QuantEntityLevel.PROTEIN:
        raise ValueError(
            "complex activity scoring requires a protein-level quantification table"
        )

    active_policy = policy or ComplexActivityPolicy()
    sample_ids = table.sample_ids
    sample_conditions = _condition_lookup(design_entries)
    sample_batches = {entry.sample_id: entry.batch for entry in design_entries}
    complex_groups = group_complex_records(complex_records)
    protein_scores = standardized_protein_ref_values(table)
    available_protein_refs = {
        protein_ref for protein_ref in protein_refs_in_table(table)
    }
    gene_annotations = protein_gene_annotations(
        fasta_records=fasta_records,
        custom_annotations=custom_annotations,
    )
    gene_to_proteins = gene_to_protein_refs(
        available_protein_refs=available_protein_refs,
        gene_annotations=gene_annotations,
    )

    unresolved_members: list[UnresolvedComplexActivityMemberEntry] = []
    member_contributions: list[ComplexMemberContributionEntry] = []
    sample_scores: list[ComplexSampleScoreEntry] = []
    for complex_id in sorted(complex_groups):
        records = complex_groups[complex_id]
        first = records[0]
        member_specs = build_member_specs(
            records,
            available_protein_refs=available_protein_refs,
            gene_to_proteins=gene_to_proteins,
            unresolved_members=unresolved_members,
        )
        for sample_id in sample_ids:
            observed_member_ids: list[str] = []
            missing_member_ids: list[str] = []
            member_scores_by_label: dict[str, float] = {}
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
                    member_scores_by_label[labeled_member] = member_activity_score
                member_contributions.append(
                    ComplexMemberContributionEntry(
                        complex_id=complex_id,
                        complex_name=first.complex_name,
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
                ComplexSampleScoreEntry(
                    complex_id=complex_id,
                    complex_name=first.complex_name,
                    source_name=first.source_name,
                    source_accession=first.source_accession,
                    sample_id=sample_id,
                    condition=sample_conditions.get(sample_id),
                    batch=sample_batches.get(sample_id),
                    activity_score=(
                        round(float(np.mean(tuple(member_scores_by_label.values()))), 6)
                        if member_scores_by_label
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
                    minimum_observed_member_count=active_policy.minimum_observed_member_count,
                    confidence_status=_sample_confidence_status(
                        observed_member_count=observed_member_count,
                        minimum_observed_member_count=(
                            active_policy.minimum_observed_member_count
                        ),
                    ),
                    confidence_reason=_confidence_reason(
                        observed_member_count=observed_member_count,
                        minimum_observed_member_count=(
                            active_policy.minimum_observed_member_count
                        ),
                    ),
                    observed_member_ids=tuple(observed_member_ids),
                    missing_member_ids=tuple(missing_member_ids),
                    limiting_member_ids=_limiting_member_ids(member_scores_by_label),
                )
            )

    condition_scores = _build_condition_scores(sample_scores, member_contributions)
    condition_comparisons = _build_condition_comparisons(condition_scores)
    return ComplexActivityReport(
        sample_ids=sample_ids,
        sample_scores=tuple(sample_scores),
        condition_scores=tuple(condition_scores),
        condition_comparisons=tuple(condition_comparisons),
        member_contributions=tuple(member_contributions),
        unresolved_members=tuple(unresolved_members),
        summary=ComplexActivitySummary(
            entity_level=table.entity_level,
            measure_kind=table.measure_kind,
            aggregation_method=table.aggregation_method,
            normalization_method=table.normalization_method,
            complex_count=len(complex_groups),
            sample_count=len(sample_ids),
            sample_score_count=len(sample_scores),
            scored_sample_count=sum(
                1 for entry in sample_scores if entry.activity_score is not None
            ),
            high_confidence_sample_score_count=sum(
                1
                for entry in sample_scores
                if entry.confidence_status
                is ComplexActivityConfidenceStatus.HIGH_CONFIDENCE
            ),
            low_confidence_sample_score_count=sum(
                1
                for entry in sample_scores
                if entry.confidence_status
                is ComplexActivityConfidenceStatus.LOW_CONFIDENCE
            ),
            sample_entries_with_missing_members=sum(
                1 for entry in sample_scores if entry.missing_member_count > 0
            ),
            member_contribution_count=len(member_contributions),
            unresolved_member_count=len(unresolved_members),
            condition_count=len({entry.condition for entry in condition_scores}),
            condition_comparison_count=len(condition_comparisons),
        ),
        note=(
            "complex activity scoring computes sample-level complex scores from the "
            "protein matrix, preserves observed and missing members, reports limiting "
            "subunits explicitly, and downgrades sparse complexes to low confidence"
        ),
    )
def _sample_confidence_status(
    *,
    observed_member_count: int,
    minimum_observed_member_count: int,
) -> ComplexActivityConfidenceStatus:
    if observed_member_count >= minimum_observed_member_count:
        return ComplexActivityConfidenceStatus.HIGH_CONFIDENCE
    return ComplexActivityConfidenceStatus.LOW_CONFIDENCE


def _aggregate_confidence_status(
    statuses: tuple[ComplexActivityConfidenceStatus, ...],
) -> ComplexActivityConfidenceStatus:
    if all(
        status is ComplexActivityConfidenceStatus.HIGH_CONFIDENCE for status in statuses
    ):
        return ComplexActivityConfidenceStatus.HIGH_CONFIDENCE
    return ComplexActivityConfidenceStatus.LOW_CONFIDENCE


def _confidence_reason(
    *,
    observed_member_count: int,
    minimum_observed_member_count: int,
) -> str | None:
    if observed_member_count >= minimum_observed_member_count:
        return None
    return (
        "observed member count "
        f"{observed_member_count} was below minimum {minimum_observed_member_count}"
    )


def _build_condition_scores(
    sample_scores: list[ComplexSampleScoreEntry],
    member_contributions: list[ComplexMemberContributionEntry],
) -> list[ComplexConditionScoreEntry]:
    grouped: dict[tuple[str, str], list[ComplexSampleScoreEntry]] = defaultdict(list)
    for entry in sample_scores:
        if entry.condition is None:
            continue
        grouped[(entry.complex_id, entry.condition)].append(entry)

    contribution_lookup: dict[
        tuple[str, str, str], list[ComplexMemberContributionEntry]
    ] = defaultdict(list)
    for member_entry in member_contributions:
        if member_entry.condition is None:
            continue
        contribution_lookup[
            (member_entry.complex_id, member_entry.condition, member_entry.member_id)
        ].append(member_entry)

    results: list[ComplexConditionScoreEntry] = []
    for (complex_id, condition), entries in sorted(grouped.items()):
        first = entries[0]
        scored_values = [
            entry.activity_score
            for entry in entries
            if entry.activity_score is not None
        ]
        member_means: dict[str, float] = {}
        for (
            entry_complex_id,
            entry_condition,
            member_id,
        ), contribution_entries in contribution_lookup.items():
            if entry_complex_id != complex_id or entry_condition != condition:
                continue
            observed_values = [
                entry.member_activity_score
                for entry in contribution_entries
                if entry.member_activity_score is not None
            ]
            if observed_values:
                member_means[
                    member_label(contribution_entries[0].member_kind, member_id)
                ] = round(
                    float(np.mean(observed_values)),
                    6,
                )
        results.append(
            ComplexConditionScoreEntry(
                complex_id=complex_id,
                complex_name=first.complex_name,
                source_name=first.source_name,
                source_accession=first.source_accession,
                condition=condition,
                sample_count=len(entries),
                scored_sample_count=len(scored_values),
                high_confidence_sample_count=sum(
                    1
                    for entry in entries
                    if entry.confidence_status
                    is ComplexActivityConfidenceStatus.HIGH_CONFIDENCE
                ),
                low_confidence_sample_count=sum(
                    1
                    for entry in entries
                    if entry.confidence_status
                    is ComplexActivityConfidenceStatus.LOW_CONFIDENCE
                ),
                confidence_status=_aggregate_confidence_status(
                    tuple(entry.confidence_status for entry in entries)
                ),
                mean_activity_score=(
                    round(float(np.mean(scored_values)), 6) if scored_values else None
                ),
                limiting_member_ids=_limiting_member_ids(member_means),
            )
        )
    return results


def _build_condition_comparisons(
    condition_scores: list[ComplexConditionScoreEntry],
) -> list[ComplexConditionComparisonEntry]:
    grouped: dict[str, list[ComplexConditionScoreEntry]] = defaultdict(list)
    for entry in condition_scores:
        grouped[entry.complex_id].append(entry)
    results: list[ComplexConditionComparisonEntry] = []
    for complex_id in sorted(grouped):
        entries = sorted(grouped[complex_id], key=lambda entry: entry.condition)
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
                    ComplexConditionComparisonEntry(
                        complex_id=complex_id,
                        complex_name=left.complex_name,
                        source_name=left.source_name,
                        source_accession=left.source_accession,
                        condition_a=left.condition,
                        condition_b=right.condition,
                        condition_a_confidence_status=left.confidence_status,
                        condition_b_confidence_status=right.confidence_status,
                        comparison_confidence_status=_aggregate_confidence_status(
                            (left.confidence_status, right.confidence_status)
                        ),
                        mean_activity_score_a=left.mean_activity_score,
                        mean_activity_score_b=right.mean_activity_score,
                        activity_score_delta=delta,
                        condition_a_limiting_member_ids=left.limiting_member_ids,
                        condition_b_limiting_member_ids=right.limiting_member_ids,
                    )
                )
    return results


def _limiting_member_ids(member_scores_by_label: dict[str, float]) -> tuple[str, ...]:
    if not member_scores_by_label:
        return ()
    limiting_score = min(member_scores_by_label.values())
    return tuple(
        sorted(
            label
            for label, score in member_scores_by_label.items()
            if abs(score - limiting_score) <= 1e-9
        )
    )


__all__ = [
    "ComplexActivityConfidenceStatus",
    "ComplexActivityPolicy",
    "ComplexActivityReport",
    "ComplexActivitySummary",
    "ComplexConditionComparisonEntry",
    "ComplexConditionScoreEntry",
    "ComplexMemberContributionEntry",
    "ComplexSampleScoreEntry",
    "UnresolvedComplexActivityMemberEntry",
    "build_complex_activity_report",
]
