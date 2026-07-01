# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""TSV rendering for deterministic result queries."""

from __future__ import annotations

import csv
from io import StringIO

from bijux_proteomics.review.claims.result_query_models import ResultQueryReport


def render_result_query_summary_tsv(report: ResultQueryReport) -> str:
    """Render one-row deterministic result-query summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "query_count",
            "answered_query_count",
            "not_found_query_count",
            "unsupported_query_count",
        )
    )
    writer.writerow(
        (
            report.summary.query_count,
            report.summary.answered_query_count,
            report.summary.not_found_query_count,
            report.summary.unsupported_query_count,
        )
    )
    return buffer.getvalue()


def render_result_query_answer_tsv(report: ResultQueryReport) -> str:
    """Render deterministic answers as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "query_id",
            "query_kind",
            "status",
            "subject_id",
            "subject_label",
            "answer_text",
            "result_row_ids",
            "graph_node_ids",
            "note",
        )
    )
    for answer in report.answers:
        writer.writerow(
            (
                answer.query_id,
                answer.query_kind.value,
                answer.status.value,
                "" if answer.subject_id is None else answer.subject_id,
                "" if answer.subject_label is None else answer.subject_label,
                answer.answer_text,
                ";".join(answer.result_row_ids),
                ";".join(answer.graph_node_ids),
                answer.note,
            )
        )
    return buffer.getvalue()


def render_result_query_evidence_tsv(report: ResultQueryReport) -> str:
    """Render explicit deterministic evidence citations as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "query_id",
            "result_surface",
            "row_id",
            "graph_node_ids",
            "source_row_refs",
            "note",
        )
    )
    for answer in report.answers:
        for link in answer.evidence_links:
            writer.writerow(
                (
                    link.query_id,
                    link.result_surface,
                    link.row_id,
                    ";".join(link.graph_node_ids),
                    ";".join(link.source_row_refs),
                    link.note,
                )
            )
    return buffer.getvalue()


__all__ = [
    "render_result_query_answer_tsv",
    "render_result_query_evidence_tsv",
    "render_result_query_summary_tsv",
]
