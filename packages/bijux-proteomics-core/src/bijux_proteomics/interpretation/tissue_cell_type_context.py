# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Sample tissue and cell-type context consistency over protein marker evidence."""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
from collections.abc import Mapping
from enum import StrEnum
from io import StringIO
from typing import TypedDict

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.interpretation.biological_context_mapping import (
    BiologicalContextKind,
    BiologicalContextRecord,
)
from bijux_proteomics.interpretation.protein_set_scoring import (
    ProteinSetRecord,
    ProteinSetSampleScoreEntry,
    ProteinSetScoringPolicy,
    ProteinSetScoringReport,
    build_protein_set_scoring_report,
)
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    QuantEntityLevel,
    QuantMeasureKind,
)
from bijux_proteomics.study import ExperimentDesign, coerce_experiment_design
from bijux_proteomics_foundation import JsonModel


class TissueCellTypeContextStatus(StrEnum):
    """Stable sample-level tissue and cell-type consistency states."""

    CONSISTENT = "consistent"
    MISMATCH_WARNING = "mismatch_warning"
    INSUFFICIENT_MARKER_SUPPORT = "insufficient_marker_support"
    MISSING_SAMPLE_CONTEXT = "missing_sample_context"
    MISSING_MARKER_DEFINITION = "missing_marker_definition"


class TissueCellTypeContextPolicy(JsonModel):
    """Confidence policy for tissue and cell-type marker consistency review."""

    model_config = ConfigDict(extra="forbid")

    minimum_observed_marker_count: int = Field(default=2, ge=1)
    minimum_unexpected_activity_score: float = Field(default=0.25)
    minimum_mismatch_score_delta: float = Field(default=0.5, ge=0.0)
    maximum_reported_unexpected_contexts_per_sample: int = Field(default=3, ge=1)


class TissueCellTypeUnexpectedSignalEntry(JsonModel):
    """One unexpected tissue or cell-type marker signal in one sample."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    batch: str | None = None
    tissue_or_cell_type: str | None = None
    context_kind: BiologicalContextKind
    context_id: str = Field(..., min_length=1)
    context_name: str | None = None
    activity_score: float = Field(...)
    score_delta_vs_expected: float | None = None
    observed_marker_count: int = Field(..., ge=0)
    missing_marker_count: int = Field(..., ge=0)
    observed_fraction: float = Field(..., ge=0.0, le=1.0)
    observed_marker_ids: tuple[str, ...] = Field(default_factory=tuple)
    missing_marker_ids: tuple[str, ...] = Field(default_factory=tuple)


class TissueCellTypeSampleConsistencyEntry(JsonModel):
    """One sample-level tissue or cell-type consistency decision."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    batch: str | None = None
    tissue_or_cell_type: str | None = None
    matched_context_ids: tuple[str, ...] = Field(default_factory=tuple)
    matched_context_names: tuple[str, ...] = Field(default_factory=tuple)
    matched_context_kinds: tuple[BiologicalContextKind, ...] = Field(default_factory=tuple)
    expected_marker_score: float | None = None
    expected_total_marker_count: int = Field(..., ge=0)
    expected_observed_marker_count: int = Field(..., ge=0)
    expected_missing_marker_count: int = Field(..., ge=0)
    expected_observed_fraction: float = Field(..., ge=0.0, le=1.0)
    observed_expected_marker_ids: tuple[str, ...] = Field(default_factory=tuple)
    missing_expected_marker_ids: tuple[str, ...] = Field(default_factory=tuple)
    highest_unexpected_context_id: str | None = None
    highest_unexpected_context_name: str | None = None
    highest_unexpected_context_kind: BiologicalContextKind | None = None
    highest_unexpected_marker_score: float | None = None
    unexpected_signal_count: int = Field(..., ge=0)
    status: TissueCellTypeContextStatus
    qc_warning: bool
    warning_code: str | None = None
    interpretation: str = Field(..., min_length=1)


class TissueCellTypeInterpretationEntry(JsonModel):
    """One aggregated interpretation over samples sharing a context label."""

    model_config = ConfigDict(extra="forbid")

    tissue_or_cell_type: str = Field(..., min_length=1)
    sample_count: int = Field(..., ge=0)
    consistent_sample_count: int = Field(..., ge=0)
    mismatch_warning_count: int = Field(..., ge=0)
    insufficient_marker_support_count: int = Field(..., ge=0)
    mean_expected_marker_score: float | None = None
    dominant_unexpected_context_id: str | None = None
    dominant_unexpected_context_name: str | None = None
    interpretation: str = Field(..., min_length=1)


class TissueCellTypeContextSummary(JsonModel):
    """Compact summary over tissue and cell-type context review."""

    model_config = ConfigDict(extra="forbid")

    sample_count: int = Field(..., ge=0)
    labeled_sample_count: int = Field(..., ge=0)
    unlabeled_sample_count: int = Field(..., ge=0)
    marker_context_count: int = Field(..., ge=0)
    sample_with_marker_definition_count: int = Field(..., ge=0)
    consistent_sample_count: int = Field(..., ge=0)
    mismatch_warning_count: int = Field(..., ge=0)
    insufficient_marker_support_count: int = Field(..., ge=0)
    missing_marker_definition_count: int = Field(..., ge=0)
    unexpected_signal_count: int = Field(..., ge=0)
    interpretation_entry_count: int = Field(..., ge=0)


class TissueCellTypeContextReport(JsonModel):
    """Owned tissue and cell-type context report over sample marker evidence."""

    model_config = ConfigDict(extra="forbid")

    marker_score_report: ProteinSetScoringReport
    sample_consistency_entries: tuple[TissueCellTypeSampleConsistencyEntry, ...] = Field(
        default_factory=tuple
    )
    unexpected_signal_entries: tuple[TissueCellTypeUnexpectedSignalEntry, ...] = Field(
        default_factory=tuple
    )
    interpretation_entries: tuple[TissueCellTypeInterpretationEntry, ...] = Field(
        default_factory=tuple
    )
    summary: TissueCellTypeContextSummary
    note: str = Field(..., min_length=1)


class _MarkerContextSet(TypedDict):
    context_kind: BiologicalContextKind
    context_id: str
    context_name: str | None
    member_ids: tuple[str, ...]


def build_tissue_cell_type_context_report(
    table: LabelFreeQuantTable,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    context_records: tuple[BiologicalContextRecord, ...],
    *,
    policy: TissueCellTypeContextPolicy | None = None,
) -> TissueCellTypeContextReport:
    """Review sample tissue and cell-type labels against expected marker proteins."""

    if table.entity_level is not QuantEntityLevel.PROTEIN:
        raise ValueError("tissue and cell-type context review requires a protein-level table")
    if table.measure_kind is not QuantMeasureKind.INTENSITY:
        raise ValueError(
            "tissue and cell-type context review requires intensity-based protein quantification"
        )

    experiment_design = coerce_experiment_design(design_entries)
    active_policy = policy or TissueCellTypeContextPolicy()
    marker_records = tuple(
        record
        for record in context_records
        if record.context_kind
        in {
            BiologicalContextKind.TISSUE_MARKER,
            BiologicalContextKind.CELL_TYPE_MARKER,
        }
    )
    protein_set_records, context_sets, set_aliases = _build_marker_sets(marker_records)
    marker_score_report = build_protein_set_scoring_report(
        table,
        protein_set_records,
        design_entries=experiment_design.entries,
        policy=ProteinSetScoringPolicy(
            minimum_observed_member_count=active_policy.minimum_observed_marker_count
        ),
    )
    score_by_sample_and_set = {
        (entry.sample_id, entry.set_id): entry for entry in marker_score_report.sample_scores
    }
    sample_batches = {
        sample.sample_id: sample.batch_ids[0] if sample.batch_ids else None
        for sample in experiment_design.samples
    }

    unexpected_entries: list[TissueCellTypeUnexpectedSignalEntry] = []
    sample_consistency_entries: list[TissueCellTypeSampleConsistencyEntry] = []
    for sample in experiment_design.samples:
        label = sample.tissue_or_cell_type
        matched_set_ids = _matched_set_ids(label, set_aliases)
        (
            expected_marker_score,
            expected_total_marker_count,
            expected_observed_marker_ids,
            expected_missing_marker_ids,
            expected_context_ids,
            expected_context_names,
            expected_context_kinds,
        ) = _expected_signal_summary(
            sample.sample_id,
            matched_set_ids,
            score_by_sample_and_set,
            context_sets,
        )
        sample_unexpected_entries = _build_unexpected_signal_entries(
            sample.sample_id,
            sample.condition,
            sample_batches.get(sample.sample_id),
            label,
            matched_set_ids,
            score_by_sample_and_set,
            context_sets,
            minimum_activity_score=active_policy.minimum_unexpected_activity_score,
            expected_marker_score=expected_marker_score,
            maximum_entries=active_policy.maximum_reported_unexpected_contexts_per_sample,
        )
        unexpected_entries.extend(sample_unexpected_entries)
        status, qc_warning, warning_code, interpretation = _sample_status(
            label=label,
            matched_set_ids=matched_set_ids,
            expected_marker_score=expected_marker_score,
            expected_observed_marker_count=len(expected_observed_marker_ids),
            unexpected_entries=sample_unexpected_entries,
            minimum_observed_marker_count=active_policy.minimum_observed_marker_count,
            minimum_mismatch_score_delta=active_policy.minimum_mismatch_score_delta,
        )
        sample_consistency_entries.append(
            TissueCellTypeSampleConsistencyEntry(
                sample_id=sample.sample_id,
                condition=sample.condition,
                batch=sample_batches.get(sample.sample_id),
                tissue_or_cell_type=label,
                matched_context_ids=expected_context_ids,
                matched_context_names=expected_context_names,
                matched_context_kinds=expected_context_kinds,
                expected_marker_score=expected_marker_score,
                expected_total_marker_count=expected_total_marker_count,
                expected_observed_marker_count=len(expected_observed_marker_ids),
                expected_missing_marker_count=len(expected_missing_marker_ids),
                expected_observed_fraction=(
                    len(expected_observed_marker_ids) / expected_total_marker_count
                    if expected_total_marker_count > 0
                    else 0.0
                ),
                observed_expected_marker_ids=expected_observed_marker_ids,
                missing_expected_marker_ids=expected_missing_marker_ids,
                highest_unexpected_context_id=(
                    None if not sample_unexpected_entries else sample_unexpected_entries[0].context_id
                ),
                highest_unexpected_context_name=(
                    None
                    if not sample_unexpected_entries
                    else sample_unexpected_entries[0].context_name
                ),
                highest_unexpected_context_kind=(
                    None
                    if not sample_unexpected_entries
                    else sample_unexpected_entries[0].context_kind
                ),
                highest_unexpected_marker_score=(
                    None
                    if not sample_unexpected_entries
                    else sample_unexpected_entries[0].activity_score
                ),
                unexpected_signal_count=len(sample_unexpected_entries),
                status=status,
                qc_warning=qc_warning,
                warning_code=warning_code,
                interpretation=interpretation,
            )
        )

    interpretation_entries = _build_interpretation_entries(sample_consistency_entries)
    return TissueCellTypeContextReport(
        marker_score_report=marker_score_report,
        sample_consistency_entries=tuple(sample_consistency_entries),
        unexpected_signal_entries=tuple(unexpected_entries),
        interpretation_entries=tuple(interpretation_entries),
        summary=TissueCellTypeContextSummary(
            sample_count=len(experiment_design.samples),
            labeled_sample_count=sum(
                1 for sample in experiment_design.samples if sample.tissue_or_cell_type
            ),
            unlabeled_sample_count=sum(
                1 for sample in experiment_design.samples if not sample.tissue_or_cell_type
            ),
            marker_context_count=len(context_sets),
            sample_with_marker_definition_count=sum(
                1 for entry in sample_consistency_entries if entry.matched_context_ids
            ),
            consistent_sample_count=sum(
                1
                for entry in sample_consistency_entries
                if entry.status is TissueCellTypeContextStatus.CONSISTENT
            ),
            mismatch_warning_count=sum(1 for entry in sample_consistency_entries if entry.qc_warning),
            insufficient_marker_support_count=sum(
                1
                for entry in sample_consistency_entries
                if entry.status is TissueCellTypeContextStatus.INSUFFICIENT_MARKER_SUPPORT
            ),
            missing_marker_definition_count=sum(
                1
                for entry in sample_consistency_entries
                if entry.status is TissueCellTypeContextStatus.MISSING_MARKER_DEFINITION
            ),
            unexpected_signal_count=len(unexpected_entries),
            interpretation_entry_count=len(interpretation_entries),
        ),
        note=(
            "tissue and cell-type context review scores only explicit sample labels against "
            "explicit tissue-marker and cell-type-marker protein sets, preserves unexpected "
            "marker signals, and raises qc warnings only when observed marker evidence "
            "supports a real sample-label mismatch"
        ),
    )


def render_tissue_cell_type_context_summary_tsv(
    report: TissueCellTypeContextReport,
) -> str:
    """Render the compact tissue and cell-type context summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("sample_count", report.summary.sample_count))
    writer.writerow(("labeled_sample_count", report.summary.labeled_sample_count))
    writer.writerow(("unlabeled_sample_count", report.summary.unlabeled_sample_count))
    writer.writerow(("marker_context_count", report.summary.marker_context_count))
    writer.writerow(
        (
            "sample_with_marker_definition_count",
            report.summary.sample_with_marker_definition_count,
        )
    )
    writer.writerow(("consistent_sample_count", report.summary.consistent_sample_count))
    writer.writerow(("mismatch_warning_count", report.summary.mismatch_warning_count))
    writer.writerow(
        (
            "insufficient_marker_support_count",
            report.summary.insufficient_marker_support_count,
        )
    )
    writer.writerow(
        (
            "missing_marker_definition_count",
            report.summary.missing_marker_definition_count,
        )
    )
    writer.writerow(("unexpected_signal_count", report.summary.unexpected_signal_count))
    writer.writerow(
        ("interpretation_entry_count", report.summary.interpretation_entry_count)
    )
    writer.writerow(("note", report.note))
    return buffer.getvalue()


def render_tissue_cell_type_sample_consistency_tsv(
    report: TissueCellTypeContextReport,
) -> str:
    """Render per-sample tissue and cell-type consistency decisions as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "sample_id",
            "condition",
            "batch",
            "tissue_or_cell_type",
            "matched_context_ids",
            "matched_context_names",
            "matched_context_kinds",
            "expected_marker_score",
            "expected_total_marker_count",
            "expected_observed_marker_count",
            "expected_missing_marker_count",
            "expected_observed_fraction",
            "observed_expected_marker_ids",
            "missing_expected_marker_ids",
            "highest_unexpected_context_id",
            "highest_unexpected_context_name",
            "highest_unexpected_context_kind",
            "highest_unexpected_marker_score",
            "unexpected_signal_count",
            "status",
            "qc_warning",
            "warning_code",
            "interpretation",
        )
    )
    for entry in report.sample_consistency_entries:
        writer.writerow(
            (
                entry.sample_id,
                entry.condition,
                entry.batch or "",
                entry.tissue_or_cell_type or "",
                ";".join(entry.matched_context_ids),
                ";".join(name for name in entry.matched_context_names if name),
                ";".join(kind.value for kind in entry.matched_context_kinds),
                "" if entry.expected_marker_score is None else f"{entry.expected_marker_score:g}",
                entry.expected_total_marker_count,
                entry.expected_observed_marker_count,
                entry.expected_missing_marker_count,
                f"{entry.expected_observed_fraction:g}",
                ";".join(entry.observed_expected_marker_ids),
                ";".join(entry.missing_expected_marker_ids),
                entry.highest_unexpected_context_id or "",
                entry.highest_unexpected_context_name or "",
                ""
                if entry.highest_unexpected_context_kind is None
                else entry.highest_unexpected_context_kind.value,
                ""
                if entry.highest_unexpected_marker_score is None
                else f"{entry.highest_unexpected_marker_score:g}",
                entry.unexpected_signal_count,
                entry.status.value,
                str(entry.qc_warning).lower(),
                entry.warning_code or "",
                entry.interpretation,
            )
        )
    return buffer.getvalue()


def render_tissue_cell_type_unexpected_signal_tsv(
    report: TissueCellTypeContextReport,
) -> str:
    """Render unexpected tissue and cell-type marker signals as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "sample_id",
            "condition",
            "batch",
            "tissue_or_cell_type",
            "context_kind",
            "context_id",
            "context_name",
            "activity_score",
            "score_delta_vs_expected",
            "observed_marker_count",
            "missing_marker_count",
            "observed_fraction",
            "observed_marker_ids",
            "missing_marker_ids",
        )
    )
    for entry in report.unexpected_signal_entries:
        writer.writerow(
            (
                entry.sample_id,
                entry.condition,
                entry.batch or "",
                entry.tissue_or_cell_type or "",
                entry.context_kind.value,
                entry.context_id,
                entry.context_name or "",
                f"{entry.activity_score:g}",
                "" if entry.score_delta_vs_expected is None else f"{entry.score_delta_vs_expected:g}",
                entry.observed_marker_count,
                entry.missing_marker_count,
                f"{entry.observed_fraction:g}",
                ";".join(entry.observed_marker_ids),
                ";".join(entry.missing_marker_ids),
            )
        )
    return buffer.getvalue()


def render_tissue_cell_type_interpretation_tsv(
    report: TissueCellTypeContextReport,
) -> str:
    """Render aggregated tissue and cell-type interpretations as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "tissue_or_cell_type",
            "sample_count",
            "consistent_sample_count",
            "mismatch_warning_count",
            "insufficient_marker_support_count",
            "mean_expected_marker_score",
            "dominant_unexpected_context_id",
            "dominant_unexpected_context_name",
            "interpretation",
        )
    )
    for entry in report.interpretation_entries:
        writer.writerow(
            (
                entry.tissue_or_cell_type,
                entry.sample_count,
                entry.consistent_sample_count,
                entry.mismatch_warning_count,
                entry.insufficient_marker_support_count,
                "" if entry.mean_expected_marker_score is None else f"{entry.mean_expected_marker_score:g}",
                entry.dominant_unexpected_context_id or "",
                entry.dominant_unexpected_context_name or "",
                entry.interpretation,
            )
        )
    return buffer.getvalue()


def _build_marker_sets(
    marker_records: tuple[BiologicalContextRecord, ...],
) -> tuple[
    tuple[ProteinSetRecord, ...],
    dict[str, _MarkerContextSet],
    dict[str, set[str]],
]:
    grouped_records: dict[tuple[BiologicalContextKind, str], list[BiologicalContextRecord]] = (
        defaultdict(list)
    )
    for record in marker_records:
        grouped_records[(record.context_kind, record.context_id)].append(record)

    protein_set_records: list[ProteinSetRecord] = []
    context_sets: dict[str, _MarkerContextSet] = {}
    set_aliases: dict[str, set[str]] = {}
    for (context_kind, context_id), records in sorted(
        grouped_records.items(), key=lambda item: (item[0][0].value, item[0][1])
    ):
        set_id = f"{context_kind.value}:{context_id}"
        first = records[0]
        member_ids = tuple(sorted({record.protein_ref for record in records}))
        context_sets[set_id] = {
            "context_kind": context_kind,
            "context_id": context_id,
            "context_name": first.context_name,
            "member_ids": member_ids,
        }
        aliases = {_normalize_context_token(context_id)}
        if first.context_name:
            aliases.add(_normalize_context_token(first.context_name))
        set_aliases[set_id] = {alias for alias in aliases if alias}
        for protein_ref in member_ids:
            protein_set_records.append(
                ProteinSetRecord(
                    set_id=set_id,
                    protein_ref=protein_ref,
                    set_name=first.context_name or context_id,
                    set_category=context_kind.value,
                    source_name=first.source_name,
                    source_accession=first.source_accession,
                )
            )
    return tuple(protein_set_records), context_sets, set_aliases


def _matched_set_ids(
    label: str | None,
    set_aliases: dict[str, set[str]],
) -> tuple[str, ...]:
    if not label:
        return ()
    normalized = _normalize_context_token(label)
    return tuple(
        set_id for set_id, aliases in sorted(set_aliases.items()) if normalized in aliases
    )


def _expected_signal_summary(
    sample_id: str,
    matched_set_ids: tuple[str, ...],
    score_by_sample_and_set: Mapping[tuple[str, str], ProteinSetSampleScoreEntry],
    context_sets: Mapping[str, _MarkerContextSet],
) -> tuple[
    float | None,
    int,
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[BiologicalContextKind, ...],
]:
    if not matched_set_ids:
        return None, 0, (), (), (), (), ()
    observed_expected_marker_ids: set[str] = set()
    missing_expected_marker_ids: set[str] = set()
    expected_scores: list[float] = []
    expected_context_ids: list[str] = []
    expected_context_names: list[str] = []
    expected_context_kinds: list[BiologicalContextKind] = []
    all_marker_ids: set[str] = set()
    for set_id in matched_set_ids:
        context = context_sets[set_id]
        all_marker_ids.update(context["member_ids"])
        expected_context_ids.append(context["context_id"])
        if context["context_name"] is not None:
            expected_context_names.append(context["context_name"])
        expected_context_kinds.append(context["context_kind"])
        sample_score = score_by_sample_and_set.get((sample_id, set_id))
        if sample_score is None:
            continue
        observed_expected_marker_ids.update(sample_score.observed_member_ids)
        missing_expected_marker_ids.update(sample_score.missing_member_ids)
        if sample_score.activity_score is not None:
            expected_scores.append(sample_score.activity_score)
    expected_marker_score = (
        round(sum(expected_scores) / len(expected_scores), 6) if expected_scores else None
    )
    return (
        expected_marker_score,
        len(all_marker_ids),
        tuple(sorted(observed_expected_marker_ids)),
        tuple(sorted(missing_expected_marker_ids)),
        tuple(expected_context_ids),
        tuple(expected_context_names),
        tuple(expected_context_kinds),
    )


def _build_unexpected_signal_entries(
    sample_id: str,
    condition: str,
    batch: str | None,
    label: str | None,
    matched_set_ids: tuple[str, ...],
    score_by_sample_and_set: Mapping[tuple[str, str], ProteinSetSampleScoreEntry],
    context_sets: Mapping[str, _MarkerContextSet],
    *,
    minimum_activity_score: float,
    expected_marker_score: float | None,
    maximum_entries: int,
) -> list[TissueCellTypeUnexpectedSignalEntry]:
    unexpected_entries: list[TissueCellTypeUnexpectedSignalEntry] = []
    for set_id, context in context_sets.items():
        if set_id in matched_set_ids:
            continue
        sample_score = score_by_sample_and_set.get((sample_id, set_id))
        if sample_score is None or sample_score.activity_score is None:
            continue
        if sample_score.activity_score < minimum_activity_score:
            continue
        unexpected_entries.append(
            TissueCellTypeUnexpectedSignalEntry(
                sample_id=sample_id,
                condition=condition,
                batch=batch,
                tissue_or_cell_type=label,
                context_kind=context["context_kind"],
                context_id=context["context_id"],
                context_name=context["context_name"],
                activity_score=sample_score.activity_score,
                score_delta_vs_expected=(
                    None
                    if expected_marker_score is None
                    else round(sample_score.activity_score - expected_marker_score, 6)
                ),
                observed_marker_count=sample_score.observed_member_count,
                missing_marker_count=sample_score.missing_member_count,
                observed_fraction=sample_score.observed_fraction,
                observed_marker_ids=sample_score.observed_member_ids,
                missing_marker_ids=sample_score.missing_member_ids,
            )
        )
    return sorted(
        unexpected_entries,
        key=lambda entry: (-entry.activity_score, entry.context_kind.value, entry.context_id),
    )[:maximum_entries]


def _sample_status(
    *,
    label: str | None,
    matched_set_ids: tuple[str, ...],
    expected_marker_score: float | None,
    expected_observed_marker_count: int,
    unexpected_entries: list[TissueCellTypeUnexpectedSignalEntry],
    minimum_observed_marker_count: int,
    minimum_mismatch_score_delta: float,
) -> tuple[TissueCellTypeContextStatus, bool, str | None, str]:
    if not label:
        return (
            TissueCellTypeContextStatus.MISSING_SAMPLE_CONTEXT,
            False,
            None,
            "sample metadata did not include a tissue or cell-type label for marker consistency review",
        )
    if not matched_set_ids:
        return (
            TissueCellTypeContextStatus.MISSING_MARKER_DEFINITION,
            False,
            None,
            "no explicit tissue or cell-type marker definition matched the sample label",
        )
    strongest_unexpected = unexpected_entries[0] if unexpected_entries else None
    if expected_marker_score is None:
        if strongest_unexpected is not None:
            return (
                TissueCellTypeContextStatus.MISMATCH_WARNING,
                True,
                "unexpected_marker_context_without_expected_support",
                "unexpected marker proteins dominated while the labeled tissue or cell-type markers were not observed strongly enough",
            )
        return (
            TissueCellTypeContextStatus.INSUFFICIENT_MARKER_SUPPORT,
            False,
            None,
            "labeled tissue or cell-type markers were too sparse to support a sample-context decision",
        )
    if strongest_unexpected is not None and (
        strongest_unexpected.score_delta_vs_expected is None
        or strongest_unexpected.score_delta_vs_expected >= minimum_mismatch_score_delta
    ):
        return (
            TissueCellTypeContextStatus.MISMATCH_WARNING,
            True,
            "unexpected_marker_context_dominates",
            (
                "unexpected "
                f"{strongest_unexpected.context_name or strongest_unexpected.context_id} "
                "marker signal exceeded the labeled tissue or cell-type marker signal"
            ),
        )
    if expected_observed_marker_count < minimum_observed_marker_count:
        return (
            TissueCellTypeContextStatus.INSUFFICIENT_MARKER_SUPPORT,
            False,
            None,
            "labeled tissue or cell-type markers were observed, but not with enough members for high-confidence review",
        )
    return (
        TissueCellTypeContextStatus.CONSISTENT,
        False,
        None,
        "observed marker proteins were consistent with the labeled tissue or cell type",
    )


def _build_interpretation_entries(
    sample_consistency_entries: list[TissueCellTypeSampleConsistencyEntry],
) -> tuple[TissueCellTypeInterpretationEntry, ...]:
    grouped_entries: dict[str, list[TissueCellTypeSampleConsistencyEntry]] = defaultdict(list)
    for entry in sample_consistency_entries:
        if entry.tissue_or_cell_type:
            grouped_entries[entry.tissue_or_cell_type].append(entry)
    interpretation_entries: list[TissueCellTypeInterpretationEntry] = []
    for label, entries in sorted(grouped_entries.items()):
        expected_scores = [
            entry.expected_marker_score
            for entry in entries
            if entry.expected_marker_score is not None
        ]
        unexpected_counter = Counter(
            entry.highest_unexpected_context_id
            for entry in entries
            if entry.highest_unexpected_context_id is not None
        )
        dominant_unexpected_context_id = (
            None
            if not unexpected_counter
            else sorted(
                unexpected_counter.items(),
                key=lambda item: (-item[1], item[0]),
            )[0][0]
        )
        dominant_unexpected_context_name = next(
            (
                entry.highest_unexpected_context_name
                for entry in entries
                if entry.highest_unexpected_context_id == dominant_unexpected_context_id
            ),
            None,
        )
        mismatch_warning_count = sum(1 for entry in entries if entry.qc_warning)
        insufficient_marker_support_count = sum(
            1
            for entry in entries
            if entry.status is TissueCellTypeContextStatus.INSUFFICIENT_MARKER_SUPPORT
        )
        if mismatch_warning_count > 0:
            interpretation = (
                f"{label} samples contained marker evidence for an unexpected "
                f"{dominant_unexpected_context_name or dominant_unexpected_context_id} context"
            )
        elif insufficient_marker_support_count == len(entries):
            interpretation = (
                f"{label} samples carried too little marker support for a confident context decision"
            )
        else:
            interpretation = f"{label} samples were broadly consistent with their expected markers"
        interpretation_entries.append(
            TissueCellTypeInterpretationEntry(
                tissue_or_cell_type=label,
                sample_count=len(entries),
                consistent_sample_count=sum(
                    1
                    for entry in entries
                    if entry.status is TissueCellTypeContextStatus.CONSISTENT
                ),
                mismatch_warning_count=mismatch_warning_count,
                insufficient_marker_support_count=insufficient_marker_support_count,
                mean_expected_marker_score=(
                    round(sum(expected_scores) / len(expected_scores), 6)
                    if expected_scores
                    else None
                ),
                dominant_unexpected_context_id=dominant_unexpected_context_id,
                dominant_unexpected_context_name=dominant_unexpected_context_name,
                interpretation=interpretation,
            )
        )
    return tuple(interpretation_entries)


def _normalize_context_token(value: str) -> str:
    return " ".join(value.strip().lower().split())
