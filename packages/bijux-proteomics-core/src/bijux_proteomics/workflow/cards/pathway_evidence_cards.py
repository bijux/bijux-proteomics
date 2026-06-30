# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Queryable pathway evidence cards over biological pathway-activity outputs."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.domain.card_schema import (
    StandardCardEntry,
    StandardCardKind,
    StandardCardSubjectKind,
    render_standard_card_row,
)
from bijux_proteomics.domain.confidence import (
    ConfidenceTier,
    coerce_confidence_tier,
)
from bijux_proteomics.domain.semantic_ids import build_pathway_card_id
from bijux_proteomics.interpretation import (
    PathwayActivityReport,
    PathwayConditionComparisonEntry,
    PathwayConditionScoreEntry,
    PathwayMemberContributionEntry,
    UnresolvedPathwayActivityMemberEntry,
)


def build_pathway_evidence_cards(
    report: PathwayActivityReport,
) -> tuple[StandardCardEntry, ...]:
    """Project governed pathway activity comparisons into shared card rows."""

    condition_scores = {
        (entry.pathway_id, entry.condition): entry for entry in report.condition_scores
    }
    member_ids_by_pathway = _member_ids_by_pathway(report.member_contributions)
    unresolved_by_pathway = _unresolved_members_by_pathway(report.unresolved_members)
    return tuple(
        _build_pathway_card(
            entry,
            condition_scores=condition_scores,
            member_ids=member_ids_by_pathway.get(entry.pathway_id, ()),
            unresolved_members=unresolved_by_pathway.get(entry.pathway_id, ()),
        )
        for entry in sorted(
            report.condition_comparisons,
            key=lambda item: (item.pathway_id, item.condition_a, item.condition_b),
        )
    )


def render_pathway_evidence_card_tsv(report: PathwayActivityReport) -> str:
    """Render governed pathway evidence cards as TSV."""

    cards = build_pathway_evidence_cards(report)
    comparison_by_card_id = {
        build_pathway_card_id(
            entry.pathway_id, entry.condition_a, entry.condition_b
        ): entry
        for entry in report.condition_comparisons
    }
    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "card_id",
            "card_kind",
            "subject_kind",
            "subject_id",
            "subject_label",
            "claim",
            "evidence_for",
            "evidence_against",
            "confidence",
            "warning_codes",
            "source_ids",
            "condition_a",
            "condition_b",
            "comparison_confidence_status",
            "mean_activity_score_a",
            "mean_activity_score_b",
            "activity_score_delta",
            "source_name",
            "source_accession",
        )
    )
    for card in cards:
        comparison = comparison_by_card_id[card.card_id]
        writer.writerow(
            (
                *render_standard_card_row(card),
                comparison.condition_a,
                comparison.condition_b,
                comparison.comparison_confidence_status.value,
                ""
                if comparison.mean_activity_score_a is None
                else f"{comparison.mean_activity_score_a:g}",
                ""
                if comparison.mean_activity_score_b is None
                else f"{comparison.mean_activity_score_b:g}",
                ""
                if comparison.activity_score_delta is None
                else f"{comparison.activity_score_delta:g}",
                "" if comparison.source_name is None else comparison.source_name,
                ""
                if comparison.source_accession is None
                else comparison.source_accession,
            )
        )
    return handle.getvalue()


def export_pathway_evidence_card_tsv(
    report: PathwayActivityReport,
    path: Path,
) -> None:
    """Write governed pathway evidence cards as one stable TSV artifact."""

    write_output_table_tsv(path, render_pathway_evidence_card_tsv(report))


def _build_pathway_card(
    entry: PathwayConditionComparisonEntry,
    *,
    condition_scores: dict[tuple[str, str], PathwayConditionScoreEntry],
    member_ids: tuple[str, ...],
    unresolved_members: tuple[UnresolvedPathwayActivityMemberEntry, ...],
) -> StandardCardEntry:
    return StandardCardEntry(
        card_id=build_pathway_card_id(
            entry.pathway_id, entry.condition_a, entry.condition_b
        ),
        card_kind=StandardCardKind.PATHWAY,
        subject_kind=StandardCardSubjectKind.PATHWAY,
        subject_id=entry.pathway_id,
        subject_label=entry.pathway_name or entry.pathway_id,
        claim=_claim_text(entry),
        evidence_for=_evidence_for_text(entry, condition_scores=condition_scores),
        evidence_against=_evidence_against_text(
            entry,
            unresolved_members=unresolved_members,
        ),
        confidence=_comparison_confidence(entry),
        warning_codes=_warning_codes(entry, unresolved_members=unresolved_members),
        source_ids=tuple(
            sorted(
                {
                    *member_ids,
                    *(item.member_id for item in unresolved_members),
                }
            )
        ),
    )


def _claim_text(entry: PathwayConditionComparisonEntry) -> str:
    label = entry.pathway_name or entry.pathway_id
    if entry.activity_score_delta is None:
        return (
            f"Pathway {label} did not retain a complete activity comparison between "
            f"{entry.condition_a} and {entry.condition_b}."
        )
    return (
        f"Pathway {label} shifts by {entry.activity_score_delta:g} between "
        f"{entry.condition_a} and {entry.condition_b}."
    )


def _evidence_for_text(
    entry: PathwayConditionComparisonEntry,
    *,
    condition_scores: dict[tuple[str, str], PathwayConditionScoreEntry],
) -> str:
    score_a = condition_scores.get((entry.pathway_id, entry.condition_a))
    score_b = condition_scores.get((entry.pathway_id, entry.condition_b))
    parts = [
        f"comparison confidence remained {entry.comparison_confidence_status.value}",
        (
            "mean activity scores were "
            f"{_format_optional_float(entry.mean_activity_score_a)} in {entry.condition_a} "
            f"and {_format_optional_float(entry.mean_activity_score_b)} in {entry.condition_b}"
        ),
    ]
    if score_a is not None:
        parts.append(
            f"{score_a.high_confidence_sample_count} high-confidence samples supported {entry.condition_a}"
        )
    if score_b is not None:
        parts.append(
            f"{score_b.high_confidence_sample_count} high-confidence samples supported {entry.condition_b}"
        )
    return ". ".join(parts) + "."


def _evidence_against_text(
    entry: PathwayConditionComparisonEntry,
    *,
    unresolved_members: tuple[UnresolvedPathwayActivityMemberEntry, ...],
) -> str:
    parts = list[str]()
    if entry.condition_a_confidence_status is not ConfidenceTier.HIGH:
        parts.append(
            f"{entry.condition_a} retained {entry.condition_a_confidence_status.value} confidence"
        )
    if entry.condition_b_confidence_status is not ConfidenceTier.HIGH:
        parts.append(
            f"{entry.condition_b} retained {entry.condition_b_confidence_status.value} confidence"
        )
    if unresolved_members:
        parts.append(
            f"{len(unresolved_members)} pathway members stayed unresolved on the study matrix"
        )
    if entry.activity_score_delta is None:
        parts.append("the comparison did not preserve a numeric activity delta")
    if not parts:
        return (
            "no explicit weakening evidence was preserved on this pathway comparison."
        )
    return ". ".join(parts) + "."


def _warning_codes(
    entry: PathwayConditionComparisonEntry,
    *,
    unresolved_members: tuple[UnresolvedPathwayActivityMemberEntry, ...],
) -> tuple[str, ...]:
    warnings = set[str]()
    if entry.condition_a_confidence_status is not ConfidenceTier.HIGH:
        warnings.add(
            f"{entry.condition_a}_confidence_{entry.condition_a_confidence_status.value}"
        )
    if entry.condition_b_confidence_status is not ConfidenceTier.HIGH:
        warnings.add(
            f"{entry.condition_b}_confidence_{entry.condition_b_confidence_status.value}"
        )
    if entry.comparison_confidence_status is not ConfidenceTier.HIGH:
        warnings.add(
            f"comparison_confidence_{entry.comparison_confidence_status.value}"
        )
    if entry.activity_score_delta is None:
        warnings.add("missing_activity_delta")
    if unresolved_members:
        warnings.add("unresolved_members")
    return tuple(sorted(warnings))


def _comparison_confidence(
    entry: PathwayConditionComparisonEntry,
) -> ConfidenceTier:
    confidence = coerce_confidence_tier(entry.comparison_confidence_status)
    if confidence is None:
        raise ValueError("pathway comparison confidence status cannot be empty")
    return confidence


def _member_ids_by_pathway(
    entries: tuple[PathwayMemberContributionEntry, ...],
) -> dict[str, tuple[str, ...]]:
    by_pathway: dict[str, set[str]] = {}
    for entry in entries:
        by_pathway.setdefault(entry.pathway_id, set()).add(entry.member_id)
    return {
        pathway_id: tuple(sorted(member_ids))
        for pathway_id, member_ids in by_pathway.items()
    }


def _unresolved_members_by_pathway(
    entries: tuple[UnresolvedPathwayActivityMemberEntry, ...],
) -> dict[str, tuple[UnresolvedPathwayActivityMemberEntry, ...]]:
    by_pathway: dict[str, list[UnresolvedPathwayActivityMemberEntry]] = {}
    for entry in entries:
        by_pathway.setdefault(entry.pathway_id, []).append(entry)
    return {
        pathway_id: tuple(sorted(values, key=lambda item: item.member_id))
        for pathway_id, values in by_pathway.items()
    }


def _format_optional_float(value: float | None) -> str:
    return "not_scored" if value is None else f"{value:g}"


__all__ = [
    "build_pathway_evidence_cards",
    "export_pathway_evidence_card_tsv",
    "render_pathway_evidence_card_tsv",
]
