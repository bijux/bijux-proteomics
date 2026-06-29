# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable TSV rendering for protein-set scoring surfaces."""

from __future__ import annotations

import csv
from io import StringIO
import json

from bijux_proteomics.interpretation.protein_set_scoring.models import (
    ProteinSetImportReport,
    ProteinSetSampleScoreEntry,
    ProteinSetScoringReport,
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
    grouped_entries: dict[str, dict[str, ProteinSetSampleScoreEntry]] = {}
    metadata_by_set: dict[str, ProteinSetSampleScoreEntry] = {}
    for entry in report.sample_scores:
        grouped_entries.setdefault(entry.set_id, {})[entry.sample_id] = entry
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
        writer.writerow((row.row_number, metadata_json(row.values), row.reason))
    return buffer.getvalue()


def metadata_json(values: dict[str, str]) -> str:
    """Serialize one rejected-row payload with stable key ordering."""

    return json.dumps(values, sort_keys=True)


__all__ = [
    "metadata_json",
    "render_protein_set_condition_comparison_tsv",
    "render_protein_set_condition_score_tsv",
    "render_protein_set_sample_score_tsv",
    "render_protein_set_score_matrix_tsv",
    "render_protein_set_scoring_summary_tsv",
    "render_protein_set_unresolved_member_tsv",
    "render_rejected_protein_set_tsv",
]
