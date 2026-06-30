# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Queryable sample evidence cards over governed exploratory sample outputs."""

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
from bijux_proteomics.domain.confidence import ConfidenceTier
from bijux_proteomics.domain.semantic_ids import build_sample_card_id
from bijux_proteomics.quantification import (
    SampleExplorationReport,
    SampleOutlierEntry,
    SamplePcaEntry,
)


def build_sample_evidence_cards(
    report: SampleExplorationReport,
) -> tuple[StandardCardEntry, ...]:
    """Project governed sample exploration into shared card rows."""

    outliers_by_sample = {
        entry.sample_id: entry for entry in report.sample_outlier_report.entries
    }
    return tuple(
        _build_sample_card(
            entry,
            report=report,
            outlier=outliers_by_sample.get(entry.sample_id),
        )
        for entry in sorted(
            report.sample_pca_report.entries, key=lambda item: item.sample_id
        )
    )


def render_sample_evidence_card_tsv(report: SampleExplorationReport) -> str:
    """Render governed sample evidence cards as TSV."""

    cards = build_sample_evidence_cards(report)
    pca_by_sample = {
        entry.sample_id: entry for entry in report.sample_pca_report.entries
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
            "condition",
            "batch",
            "pc1",
            "pc2",
            "distance_from_global_centroid",
            "distance_from_condition_centroid",
            "global_centroid_outlier",
            "condition_centroid_outlier",
            "outlier",
        )
    )
    for card in cards:
        entry = pca_by_sample[card.subject_id]
        writer.writerow(
            (
                *render_standard_card_row(card),
                entry.condition,
                "" if entry.batch is None else entry.batch,
                f"{entry.pc1:g}",
                f"{entry.pc2:g}",
                f"{entry.distance_from_global_centroid:g}",
                f"{entry.distance_from_condition_centroid:g}",
                str(entry.global_centroid_outlier).lower(),
                str(entry.condition_centroid_outlier).lower(),
                str(entry.outlier).lower(),
            )
        )
    return handle.getvalue()


def export_sample_evidence_card_tsv(
    report: SampleExplorationReport,
    path: Path,
) -> None:
    """Write governed sample evidence cards as one stable TSV artifact."""

    write_output_table_tsv(path, render_sample_evidence_card_tsv(report))


def _build_sample_card(
    entry: SamplePcaEntry,
    *,
    report: SampleExplorationReport,
    outlier: SampleOutlierEntry | None,
) -> StandardCardEntry:
    return StandardCardEntry(
        card_id=build_sample_card_id(entry.sample_id),
        card_kind=StandardCardKind.SAMPLE,
        subject_kind=StandardCardSubjectKind.SAMPLE,
        subject_id=entry.sample_id,
        subject_label=entry.sample_id,
        claim=_claim_text(entry),
        evidence_for=(
            f"sample belongs to condition {entry.condition}; "
            f"pc1={entry.pc1:g}, pc2={entry.pc2:g}; "
            f"distance from condition centroid={entry.distance_from_condition_centroid:g}."
        ),
        evidence_against=_evidence_against_text(
            entry,
            outlier=outlier,
            clustered_by_condition=report.summary.clustered_by_condition,
        ),
        confidence=_confidence(
            entry, clustered_by_condition=report.summary.clustered_by_condition
        ),
        warning_codes=_warning_codes(
            entry, clustered_by_condition=report.summary.clustered_by_condition
        ),
        source_ids=tuple(
            part
            for part in (
                entry.sample_id,
                entry.condition,
                entry.batch,
            )
            if part
        ),
    )


def _claim_text(entry: SamplePcaEntry) -> str:
    if entry.outlier:
        return (
            f"Sample {entry.sample_id} deviates from its expected study neighborhood and "
            "should stay under review."
        )
    return f"Sample {entry.sample_id} remains consistent with its expected study neighborhood."


def _evidence_against_text(
    entry: SamplePcaEntry,
    *,
    outlier: SampleOutlierEntry | None,
    clustered_by_condition: bool,
) -> str:
    parts = list[str]()
    if outlier is not None and outlier.outlier_reasons:
        parts.append("outlier reasons were " + ", ".join(outlier.outlier_reasons))
    if not clustered_by_condition:
        parts.append(
            "samples did not cluster cleanly by condition in the governed study summary"
        )
    if not parts:
        return "no explicit weakening evidence was preserved on this sample exploration card."
    return ". ".join(parts) + "."


def _confidence(
    entry: SamplePcaEntry,
    *,
    clustered_by_condition: bool,
) -> ConfidenceTier:
    if entry.outlier:
        return ConfidenceTier.LOW
    if not clustered_by_condition:
        return ConfidenceTier.MODERATE
    return ConfidenceTier.HIGH


def _warning_codes(
    entry: SamplePcaEntry,
    *,
    clustered_by_condition: bool,
) -> tuple[str, ...]:
    warnings = set(entry.outlier_reasons)
    if not clustered_by_condition:
        warnings.add("condition_not_clustered")
    return tuple(sorted(warnings))


__all__ = [
    "build_sample_evidence_cards",
    "export_sample_evidence_card_tsv",
    "render_sample_evidence_card_tsv",
]
