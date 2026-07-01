# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""TSV rendering for deterministic result explanations."""

from __future__ import annotations

import csv
from io import StringIO

from bijux_proteomics.review.explanations.result_explanation_models import (
    ResultExplanationReport,
)


def render_result_explanation_summary_tsv(report: ResultExplanationReport) -> str:
    """Render one-row deterministic explanation summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "explanation_count",
            "answered_explanation_count",
            "not_found_explanation_count",
            "unsupported_explanation_count",
        )
    )
    writer.writerow(
        (
            report.summary.explanation_count,
            report.summary.answered_explanation_count,
            report.summary.not_found_explanation_count,
            report.summary.unsupported_explanation_count,
        )
    )
    return buffer.getvalue()


def render_result_explanation_tsv(report: ResultExplanationReport) -> str:
    """Render deterministic explanations as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "explanation_id",
            "explanation_kind",
            "status",
            "subject_id",
            "subject_label",
            "claim",
            "decision",
            "confidence",
            "result_row_ids",
            "graph_node_ids",
            "note",
        )
    )
    for explanation in report.explanations:
        writer.writerow(
            (
                explanation.explanation_id,
                explanation.explanation_kind.value,
                explanation.status.value,
                "" if explanation.subject_id is None else explanation.subject_id,
                "" if explanation.subject_label is None else explanation.subject_label,
                explanation.claim,
                explanation.decision,
                explanation.confidence,
                ";".join(explanation.result_row_ids),
                ";".join(explanation.graph_node_ids),
                explanation.note,
            )
        )
    return buffer.getvalue()


def render_result_explanation_evidence_tsv(report: ResultExplanationReport) -> str:
    """Render deterministic explanation points as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "explanation_id",
            "explanation_kind",
            "evidence_role",
            "result_surface",
            "row_id",
            "graph_node_ids",
            "source_row_refs",
            "summary",
        )
    )
    for explanation in report.explanations:
        for point in (*explanation.evidence, *explanation.opposing_evidence):
            writer.writerow(
                (
                    explanation.explanation_id,
                    explanation.explanation_kind.value,
                    point.role.value,
                    point.result_surface,
                    point.row_id,
                    ";".join(point.graph_node_ids),
                    ";".join(point.source_row_refs),
                    point.summary,
                )
            )
    return buffer.getvalue()


__all__ = [
    "render_result_explanation_evidence_tsv",
    "render_result_explanation_summary_tsv",
    "render_result_explanation_tsv",
]
