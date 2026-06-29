# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""TSV rendering for pathway activity reports."""

from __future__ import annotations

from collections import defaultdict
import csv
from io import StringIO

from bijux_proteomics.interpretation.pathway_activity.models import (
    PathwayActivityReport,
    PathwaySampleScoreEntry,
)


def render_pathway_activity_summary_tsv(report: PathwayActivityReport) -> str:
    """Render the compact pathway activity summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_level",
            "measure_kind",
            "aggregation_method",
            "normalization_method",
            "pathway_count",
            "sample_count",
            "sample_score_count",
            "scored_sample_count",
            "high_confidence_sample_score_count",
            "low_confidence_sample_score_count",
            "sample_entries_with_missing_members",
            "member_contribution_count",
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
            report.summary.pathway_count,
            report.summary.sample_count,
            report.summary.sample_score_count,
            report.summary.scored_sample_count,
            report.summary.high_confidence_sample_score_count,
            report.summary.low_confidence_sample_score_count,
            report.summary.sample_entries_with_missing_members,
            report.summary.member_contribution_count,
            report.summary.unresolved_member_count,
            report.summary.condition_count,
            report.summary.condition_comparison_count,
        )
    )
    return buffer.getvalue()


def render_pathway_activity_matrix_tsv(report: PathwayActivityReport) -> str:
    """Render one pathway-by-sample activity matrix as TSV."""

    sample_ids = report.sample_ids
    grouped_entries: dict[str, dict[str, PathwaySampleScoreEntry]] = defaultdict(dict)
    metadata_by_pathway: dict[str, PathwaySampleScoreEntry] = {}
    for entry in report.sample_scores:
        grouped_entries[entry.pathway_id][entry.sample_id] = entry
        metadata_by_pathway.setdefault(entry.pathway_id, entry)

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pathway_id",
            "pathway_name",
            "source_name",
            "source_accession",
            *sample_ids,
        )
    )
    for pathway_id in sorted(grouped_entries):
        metadata = metadata_by_pathway[pathway_id]
        writer.writerow(
            (
                pathway_id,
                metadata.pathway_name or "",
                metadata.source_name or "",
                metadata.source_accession or "",
                *[
                    ""
                    if grouped_entries[pathway_id][sample_id].activity_score is None
                    else f"{grouped_entries[pathway_id][sample_id].activity_score:g}"
                    for sample_id in sample_ids
                ],
            )
        )
    return buffer.getvalue()


def render_pathway_activity_sample_score_tsv(report: PathwayActivityReport) -> str:
    """Render per-sample pathway activity scores as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pathway_id",
            "pathway_name",
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
                entry.pathway_id,
                entry.pathway_name or "",
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


def render_pathway_activity_condition_score_tsv(report: PathwayActivityReport) -> str:
    """Render condition-level mean pathway activity scores as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pathway_id",
            "pathway_name",
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
                entry.pathway_id,
                entry.pathway_name or "",
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


def render_pathway_activity_condition_comparison_tsv(
    report: PathwayActivityReport,
) -> str:
    """Render pairwise condition pathway activity contrasts as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pathway_id",
            "pathway_name",
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
                entry.pathway_id,
                entry.pathway_name or "",
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


def render_pathway_member_contribution_tsv(report: PathwayActivityReport) -> str:
    """Render sample-level pathway member contribution rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pathway_id",
            "pathway_name",
            "source_name",
            "source_accession",
            "sample_id",
            "condition",
            "batch",
            "member_kind",
            "member_id",
            "resolved_protein_refs",
            "observed_protein_refs",
            "resolved_protein_count",
            "observed_protein_count",
            "missing_protein_count",
            "member_activity_score",
            "observed",
        )
    )
    for entry in report.member_contributions:
        writer.writerow(
            (
                entry.pathway_id,
                entry.pathway_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.sample_id,
                entry.condition or "",
                entry.batch or "",
                entry.member_kind.value,
                entry.member_id,
                ";".join(entry.resolved_protein_refs),
                ";".join(entry.observed_protein_refs),
                entry.resolved_protein_count,
                entry.observed_protein_count,
                entry.missing_protein_count,
                ""
                if entry.member_activity_score is None
                else f"{entry.member_activity_score:g}",
                str(entry.observed).lower(),
            )
        )
    return buffer.getvalue()


def render_pathway_activity_unresolved_member_tsv(report: PathwayActivityReport) -> str:
    """Render unresolved pathway members as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pathway_id",
            "pathway_name",
            "source_name",
            "source_accession",
            "member_kind",
            "member_id",
            "reason",
        )
    )
    for entry in report.unresolved_members:
        writer.writerow(
            (
                entry.pathway_id,
                entry.pathway_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.member_kind.value,
                entry.member_id,
                entry.reason,
            )
        )
    return buffer.getvalue()
