# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein-set scoring surfaces for sample-level biological program review."""

from __future__ import annotations

from collections import defaultdict
import csv
from io import StringIO
import json
import math
from typing import TYPE_CHECKING

import numpy as np

from bijux_proteomics.interpretation.protein_set_scoring.definition_import import (
    parse_protein_set_table,
)
from bijux_proteomics.quantification.contracts.matrix_building import (
    _condition_lookup,
    _matrix_value_index,
)
from bijux_proteomics.quantification.contracts.input_models import QuantEntityLevel
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable
from bijux_proteomics.interpretation.protein_set_scoring.models import (
    ProteinSetConditionComparisonEntry,
    ProteinSetConditionScoreEntry,
    ProteinSetScoreConfidenceStatus,
    ProteinSetImportReport,
    ProteinSetSampleScoreEntry,
    ProteinSetScoringPolicy,
    ProteinSetScoringReport,
    ProteinSetScoringSummary,
    UnresolvedProteinSetMemberEntry,
)

if TYPE_CHECKING:
    from bijux_proteomics.io.formats import ExperimentalDesignEntry


def build_protein_set_scoring_report(
    table: LabelFreeQuantTable,
    protein_set_records: tuple[ProteinSetRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...] = (),
    policy: ProteinSetScoringPolicy | None = None,
) -> ProteinSetScoringReport:
    """Score protein sets per sample over one normalized protein quant table."""

    if table.entity_level is not QuantEntityLevel.PROTEIN:
        raise ValueError(
            "protein set scoring requires a protein-level quantification table"
        )

    active_policy = policy or ProteinSetScoringPolicy()
    sample_ids = table.sample_ids
    sample_conditions = _condition_lookup(design_entries)
    sample_batches = {entry.sample_id: entry.batch for entry in design_entries}
    grouped_sets: dict[str, list[ProteinSetRecord]] = defaultdict(list)
    for record in protein_set_records:
        grouped_sets[record.set_id].append(record)
    standardized_values = _standardized_protein_values(table)
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
            confidence_status = _sample_confidence_status(
                observed_member_count=observed_member_count,
                minimum_observed_member_count=active_policy.minimum_observed_member_count,
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
                    minimum_observed_member_count=active_policy.minimum_observed_member_count,
                    confidence_status=confidence_status,
                    confidence_reason=_confidence_reason(
                        observed_member_count=observed_member_count,
                        minimum_observed_member_count=active_policy.minimum_observed_member_count,
                    ),
                    observed_member_ids=tuple(observed_member_ids),
                    missing_member_ids=tuple(missing_member_ids),
                )
            )

    condition_scores = _build_condition_scores(sample_scores)
    condition_comparisons = _build_condition_comparisons(condition_scores)
    return ProteinSetScoringReport(
        sample_ids=sample_ids,
        sample_scores=tuple(sample_scores),
        condition_scores=tuple(condition_scores),
        condition_comparisons=tuple(condition_comparisons),
        unresolved_members=tuple(unresolved_members),
        summary=ProteinSetScoringSummary(
            entity_level=table.entity_level,
            measure_kind=table.measure_kind,
            aggregation_method=table.aggregation_method,
            normalization_method=table.normalization_method,
            set_count=len(grouped_sets),
            sample_count=len(sample_ids),
            feature_protein_count=len(table.entity_ids),
            sample_score_count=len(sample_scores),
            scored_sample_count=sum(
                1 for entry in sample_scores if entry.activity_score is not None
            ),
            high_confidence_sample_score_count=sum(
                1
                for entry in sample_scores
                if entry.confidence_status
                is ProteinSetScoreConfidenceStatus.HIGH_CONFIDENCE
            ),
            low_confidence_sample_score_count=sum(
                1
                for entry in sample_scores
                if entry.confidence_status
                is ProteinSetScoreConfidenceStatus.LOW_CONFIDENCE
            ),
            sample_entries_with_missing_members=sum(
                1 for entry in sample_scores if entry.missing_member_count > 0
            ),
            unresolved_member_count=len(unresolved_members),
            condition_count=len({entry.condition for entry in condition_scores}),
            condition_comparison_count=len(condition_comparisons),
        ),
        note=(
            "protein set scoring standardizes normalized protein abundances across samples, averages observed member signal per sample, preserves member coverage explicitly, and marks sparse member support as low confidence"
        ),
    )


def render_protein_set_scoring_summary_tsv(report: ProteinSetScoringReport) -> str:
    """Render the compact protein-set scoring summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_level",
            "measure_kind",
            "aggregation_method",
            "normalization_method",
            "set_count",
            "sample_count",
            "feature_protein_count",
            "sample_score_count",
            "scored_sample_count",
            "high_confidence_sample_score_count",
            "low_confidence_sample_score_count",
            "sample_entries_with_missing_members",
            "unresolved_member_count",
            "condition_count",
            "condition_comparison_count",
        )
    )
    writer.writerow(
        (
            report.summary.entity_level.value,
            report.summary.measure_kind.value,
            report.summary.aggregation_method.value,
            report.summary.normalization_method.value,
            report.summary.set_count,
            report.summary.sample_count,
            report.summary.feature_protein_count,
            report.summary.sample_score_count,
            report.summary.scored_sample_count,
            report.summary.high_confidence_sample_score_count,
            report.summary.low_confidence_sample_score_count,
            report.summary.sample_entries_with_missing_members,
            report.summary.unresolved_member_count,
            report.summary.condition_count,
            report.summary.condition_comparison_count,
        )
    )
    return buffer.getvalue()


def render_protein_set_score_matrix_tsv(report: ProteinSetScoringReport) -> str:
    """Render one protein-set by sample activity matrix as TSV."""

    sample_ids = report.sample_ids
    grouped_entries: dict[str, dict[str, ProteinSetSampleScoreEntry]] = defaultdict(
        dict
    )
    metadata_by_set: dict[str, ProteinSetSampleScoreEntry] = {}
    for entry in report.sample_scores:
        grouped_entries[entry.set_id][entry.sample_id] = entry
        metadata_by_set.setdefault(entry.set_id, entry)

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "set_id",
            "set_name",
            "set_category",
            "source_name",
            "source_accession",
            *sample_ids,
        )
    )
    for set_id in sorted(grouped_entries):
        metadata = metadata_by_set[set_id]
        writer.writerow(
            (
                set_id,
                metadata.set_name or "",
                metadata.set_category or "",
                metadata.source_name or "",
                metadata.source_accession or "",
                *[
                    ""
                    if grouped_entries[set_id][sample_id].activity_score is None
                    else f"{grouped_entries[set_id][sample_id].activity_score:g}"
                    for sample_id in sample_ids
                ],
            )
        )
    return buffer.getvalue()


def render_protein_set_sample_score_tsv(report: ProteinSetScoringReport) -> str:
    """Render per-sample protein-set activity scores as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "set_id",
            "set_name",
            "set_category",
            "source_name",
            "source_accession",
            "sample_id",
            "condition",
            "batch",
            "activity_score",
            "total_member_count",
            "observed_member_count",
            "missing_member_count",
            "observed_fraction",
            "minimum_observed_member_count",
            "confidence_status",
            "confidence_reason",
            "observed_member_ids",
            "missing_member_ids",
        )
    )
    for entry in report.sample_scores:
        writer.writerow(
            (
                entry.set_id,
                entry.set_name or "",
                entry.set_category or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.sample_id,
                entry.condition or "",
                entry.batch or "",
                "" if entry.activity_score is None else f"{entry.activity_score:g}",
                entry.total_member_count,
                entry.observed_member_count,
                entry.missing_member_count,
                f"{entry.observed_fraction:g}",
                entry.minimum_observed_member_count,
                entry.confidence_status.value,
                entry.confidence_reason or "",
                ";".join(entry.observed_member_ids),
                ";".join(entry.missing_member_ids),
            )
        )
    return buffer.getvalue()


def render_protein_set_condition_score_tsv(report: ProteinSetScoringReport) -> str:
    """Render condition-level mean protein-set scores as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "set_id",
            "set_name",
            "set_category",
            "source_name",
            "source_accession",
            "condition",
            "sample_count",
            "scored_sample_count",
            "high_confidence_sample_count",
            "low_confidence_sample_count",
            "confidence_status",
            "mean_activity_score",
        )
    )
    for entry in report.condition_scores:
        writer.writerow(
            (
                entry.set_id,
                entry.set_name or "",
                entry.set_category or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.condition,
                entry.sample_count,
                entry.scored_sample_count,
                entry.high_confidence_sample_count,
                entry.low_confidence_sample_count,
                entry.confidence_status.value,
                ""
                if entry.mean_activity_score is None
                else f"{entry.mean_activity_score:g}",
            )
        )
    return buffer.getvalue()


def render_protein_set_condition_comparison_tsv(
    report: ProteinSetScoringReport,
) -> str:
    """Render pairwise condition comparisons over protein-set scores as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "set_id",
            "set_name",
            "set_category",
            "source_name",
            "source_accession",
            "condition_a",
            "condition_b",
            "condition_a_confidence_status",
            "condition_b_confidence_status",
            "comparison_confidence_status",
            "mean_activity_score_a",
            "mean_activity_score_b",
            "activity_score_delta",
        )
    )
    for entry in report.condition_comparisons:
        writer.writerow(
            (
                entry.set_id,
                entry.set_name or "",
                entry.set_category or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.condition_a,
                entry.condition_b,
                entry.condition_a_confidence_status.value,
                entry.condition_b_confidence_status.value,
                entry.comparison_confidence_status.value,
                ""
                if entry.mean_activity_score_a is None
                else f"{entry.mean_activity_score_a:g}",
                ""
                if entry.mean_activity_score_b is None
                else f"{entry.mean_activity_score_b:g}",
                ""
                if entry.activity_score_delta is None
                else f"{entry.activity_score_delta:g}",
            )
        )
    return buffer.getvalue()


def render_protein_set_unresolved_member_tsv(report: ProteinSetScoringReport) -> str:
    """Render unresolved protein-set members as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "set_id",
            "set_name",
            "set_category",
            "source_name",
            "source_accession",
            "protein_ref",
            "reason",
        )
    )
    for entry in report.unresolved_members:
        writer.writerow(
            (
                entry.set_id,
                entry.set_name or "",
                entry.set_category or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.protein_ref,
                entry.reason,
            )
        )
    return buffer.getvalue()


def render_rejected_protein_set_tsv(report: ProteinSetImportReport) -> str:
    """Render rejected protein-set rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("row_number", "values", "reason"))
    for row in report.rejected_rows:
        writer.writerow((row.row_number, _metadata_json(row.values), row.reason))
    return buffer.getvalue()


def _build_condition_scores(
    sample_scores: list[ProteinSetSampleScoreEntry],
) -> list[ProteinSetConditionScoreEntry]:
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
                confidence_status=_aggregate_confidence_status(
                    tuple(entry.confidence_status for entry in entries)
                ),
                mean_activity_score=(
                    round(float(np.mean(scored_values)), 6) if scored_values else None
                ),
            )
        )
    return results


def _build_condition_comparisons(
    condition_scores: list[ProteinSetConditionScoreEntry],
) -> list[ProteinSetConditionComparisonEntry]:
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
                        comparison_confidence_status=_aggregate_confidence_status(
                            (left.confidence_status, right.confidence_status)
                        ),
                        mean_activity_score_a=left.mean_activity_score,
                        mean_activity_score_b=right.mean_activity_score,
                        activity_score_delta=delta,
                    )
                )
    return results


def _standardized_protein_values(
    table: LabelFreeQuantTable,
) -> dict[tuple[str, str], float | None]:
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


def _sample_confidence_status(
    *,
    observed_member_count: int,
    minimum_observed_member_count: int,
) -> ProteinSetScoreConfidenceStatus:
    if observed_member_count >= minimum_observed_member_count:
        return ProteinSetScoreConfidenceStatus.HIGH_CONFIDENCE
    return ProteinSetScoreConfidenceStatus.LOW_CONFIDENCE


def _aggregate_confidence_status(
    statuses: tuple[ProteinSetScoreConfidenceStatus, ...],
) -> ProteinSetScoreConfidenceStatus:
    if all(
        status is ProteinSetScoreConfidenceStatus.HIGH_CONFIDENCE for status in statuses
    ):
        return ProteinSetScoreConfidenceStatus.HIGH_CONFIDENCE
    return ProteinSetScoreConfidenceStatus.LOW_CONFIDENCE


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


def _metadata_json(values: dict[str, str]) -> str:
    return json.dumps(values, sort_keys=True)


__all__ = [
    "ProteinSetColumnMapping",
    "ProteinSetConditionComparisonEntry",
    "ProteinSetConditionScoreEntry",
    "ProteinSetScoreConfidenceStatus",
    "ProteinSetImportReport",
    "ProteinSetImportSummary",
    "ProteinSetRecord",
    "ProteinSetSampleScoreEntry",
    "ProteinSetScoringPolicy",
    "ProteinSetScoringReport",
    "ProteinSetScoringSummary",
    "RejectedProteinSetRow",
    "UnresolvedProteinSetMemberEntry",
    "build_protein_set_scoring_report",
    "parse_protein_set_table",
    "render_protein_set_condition_comparison_tsv",
    "render_protein_set_condition_score_tsv",
    "render_protein_set_score_matrix_tsv",
    "render_protein_set_sample_score_tsv",
    "render_protein_set_scoring_summary_tsv",
    "render_protein_set_unresolved_member_tsv",
    "render_rejected_protein_set_tsv",
]
