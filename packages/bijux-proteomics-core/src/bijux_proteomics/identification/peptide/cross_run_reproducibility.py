# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Cross-run reproducibility scoring over peptide and protein evidence."""

from __future__ import annotations

from collections import defaultdict
import csv
from enum import StrEnum
import hashlib
import io
import json

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import PsmRecord
from bijux_proteomics_foundation import JsonModel


class CrossRunEntityType(StrEnum):
    """Entity scopes supported by cross-run reproducibility scoring."""

    PEPTIDE = "peptide"
    PROTEIN = "protein"


class CrossRunReproducibilityClass(StrEnum):
    """Cross-run support classes for reviewable evidence promotion."""

    REPRODUCIBLE = "reproducible"
    CONDITION_SPECIFIC = "condition_specific"
    SINGLE_RUN_ONLY = "single_run_only"
    EXPLORATORY = "exploratory"


class RunDetectionContext(JsonModel):
    """Stable run-level context used for reproducibility scoring."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    condition_id: str | None = None
    replicate_id: str | None = None


class CrossRunReproducibilityEntry(JsonModel):
    """One peptide or protein reproducibility row."""

    model_config = ConfigDict(extra="forbid")

    entity_type: CrossRunEntityType
    entity_id: str = Field(..., min_length=1)
    detected_run_count: int = Field(..., ge=0)
    total_run_count: int = Field(..., ge=0)
    detection_frequency: float = Field(..., ge=0.0, le=1.0)
    detected_condition_count: int = Field(..., ge=0)
    detected_conditions: tuple[str, ...] = Field(default_factory=tuple)
    primary_condition: str | None = None
    condition_specificity: float = Field(..., ge=0.0, le=1.0)
    detected_replicate_count: int = Field(..., ge=0)
    total_replicate_count: int = Field(..., ge=0)
    replicate_consistency: float = Field(..., ge=0.0, le=1.0)
    single_run_only: bool
    exploratory_override: bool
    reproducibility_class: CrossRunReproducibilityClass
    run_ids: tuple[str, ...] = Field(default_factory=tuple)
    explanation: str = Field(..., min_length=1)


class CrossRunReproducibilitySummary(JsonModel):
    """Summary over one entity-level reproducibility report."""

    model_config = ConfigDict(extra="forbid")

    entity_type: CrossRunEntityType
    total_entries: int = Field(..., ge=0)
    reproducible_count: int = Field(..., ge=0)
    condition_specific_count: int = Field(..., ge=0)
    single_run_only_count: int = Field(..., ge=0)
    exploratory_count: int = Field(..., ge=0)
    condition_aware_entry_count: int = Field(..., ge=0)


class CrossRunReproducibilityReport(JsonModel):
    """Owned reproducibility packet for peptide or protein evidence."""

    model_config = ConfigDict(extra="forbid")

    summary: CrossRunReproducibilitySummary
    run_context_count: int = Field(..., ge=0)
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)
    entries: tuple[CrossRunReproducibilityEntry, ...] = Field(default_factory=tuple)


def build_peptide_cross_run_reproducibility_report(
    records: tuple[PsmRecord, ...],
    *,
    run_contexts: tuple[RunDetectionContext, ...] = (),
    exploratory_canonical_peptides: tuple[str, ...] = (),
) -> CrossRunReproducibilityReport:
    """Score peptide reproducibility across runs, replicates, and conditions."""

    grouped: dict[str, list[PsmRecord]] = defaultdict(list)
    for record in records:
        grouped[record.canonical_peptide].append(record)
    return _build_cross_run_reproducibility_report(
        entity_type=CrossRunEntityType.PEPTIDE,
        grouped_records=grouped,
        run_contexts=run_contexts,
        exploratory_entities=exploratory_canonical_peptides,
    )


def build_protein_cross_run_reproducibility_report(
    records: tuple[PsmRecord, ...],
    *,
    run_contexts: tuple[RunDetectionContext, ...] = (),
    exploratory_protein_refs: tuple[str, ...] = (),
) -> CrossRunReproducibilityReport:
    """Score protein reproducibility across runs, replicates, and conditions."""

    grouped: dict[str, list[PsmRecord]] = defaultdict(list)
    for record in records:
        for protein_ref in record.protein_refs:
            grouped[protein_ref].append(record)
    return _build_cross_run_reproducibility_report(
        entity_type=CrossRunEntityType.PROTEIN,
        grouped_records=grouped,
        run_contexts=run_contexts,
        exploratory_entities=exploratory_protein_refs,
    )


def render_cross_run_reproducibility_summary_tsv(
    report: CrossRunReproducibilityReport,
) -> str:
    """Render one compact reproducibility summary ledger as TSV."""

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("metric", "value"))
    for metric, value in (
        ("entity_type", report.summary.entity_type.value),
        ("total_entries", report.summary.total_entries),
        ("reproducible_count", report.summary.reproducible_count),
        ("condition_specific_count", report.summary.condition_specific_count),
        ("single_run_only_count", report.summary.single_run_only_count),
        ("exploratory_count", report.summary.exploratory_count),
        ("condition_aware_entry_count", report.summary.condition_aware_entry_count),
        ("run_context_count", report.run_context_count),
        ("reproducibility_hash", report.reproducibility_hash),
    ):
        writer.writerow((metric, value))
    return buffer.getvalue()


def render_cross_run_reproducibility_entries_tsv(
    report: CrossRunReproducibilityReport,
) -> str:
    """Render reproducibility entries as TSV."""

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_type",
            "entity_id",
            "detected_run_count",
            "total_run_count",
            "detection_frequency",
            "detected_condition_count",
            "detected_conditions",
            "primary_condition",
            "condition_specificity",
            "detected_replicate_count",
            "total_replicate_count",
            "replicate_consistency",
            "single_run_only",
            "exploratory_override",
            "reproducibility_class",
            "run_ids",
            "explanation",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.entity_type.value,
                entry.entity_id,
                entry.detected_run_count,
                entry.total_run_count,
                f"{entry.detection_frequency:.6g}",
                entry.detected_condition_count,
                ";".join(entry.detected_conditions),
                entry.primary_condition or "",
                f"{entry.condition_specificity:.6g}",
                entry.detected_replicate_count,
                entry.total_replicate_count,
                f"{entry.replicate_consistency:.6g}",
                str(entry.single_run_only).lower(),
                str(entry.exploratory_override).lower(),
                entry.reproducibility_class.value,
                ";".join(entry.run_ids),
                entry.explanation,
            )
        )
    return buffer.getvalue()


def _build_cross_run_reproducibility_report(
    *,
    entity_type: CrossRunEntityType,
    grouped_records: dict[str, list[PsmRecord]],
    run_contexts: tuple[RunDetectionContext, ...],
    exploratory_entities: tuple[str, ...],
) -> CrossRunReproducibilityReport:
    context_by_run = {context.run_id: context for context in run_contexts}
    total_run_ids = tuple(sorted(context_by_run)) or tuple(
        sorted(
            {
                record.run_id
                for records in grouped_records.values()
                for record in records
                if record.run_id
            }
        )
    )
    exploratory_entity_ids = set(exploratory_entities)
    entries = tuple(
        sorted(
            (
                _build_entry(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    supporting_records=tuple(records),
                    total_run_ids=total_run_ids,
                    context_by_run=context_by_run,
                    exploratory_override=entity_id in exploratory_entity_ids,
                )
                for entity_id, records in grouped_records.items()
            ),
            key=lambda entry: entry.entity_id,
        )
    )
    payload = {
        "entity_type": entity_type.value,
        "run_contexts": [context.to_dict() for context in run_contexts],
        "entries": [entry.to_dict() for entry in entries],
    }
    return CrossRunReproducibilityReport(
        summary=CrossRunReproducibilitySummary(
            entity_type=entity_type,
            total_entries=len(entries),
            reproducible_count=sum(
                1
                for entry in entries
                if entry.reproducibility_class
                is CrossRunReproducibilityClass.REPRODUCIBLE
            ),
            condition_specific_count=sum(
                1
                for entry in entries
                if entry.reproducibility_class
                is CrossRunReproducibilityClass.CONDITION_SPECIFIC
            ),
            single_run_only_count=sum(
                1
                for entry in entries
                if entry.reproducibility_class
                is CrossRunReproducibilityClass.SINGLE_RUN_ONLY
            ),
            exploratory_count=sum(
                1
                for entry in entries
                if entry.reproducibility_class
                is CrossRunReproducibilityClass.EXPLORATORY
            ),
            condition_aware_entry_count=sum(
                1 for entry in entries if entry.detected_condition_count > 0
            ),
        ),
        run_context_count=len(run_contexts),
        reproducibility_hash=hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        entries=entries,
    )


def _build_entry(
    *,
    entity_type: CrossRunEntityType,
    entity_id: str,
    supporting_records: tuple[PsmRecord, ...],
    total_run_ids: tuple[str, ...],
    context_by_run: dict[str, RunDetectionContext],
    exploratory_override: bool,
) -> CrossRunReproducibilityEntry:
    explicit_run_ids = tuple(
        sorted({record.run_id for record in supporting_records if record.run_id})
    )
    if explicit_run_ids:
        detected_run_count = len(explicit_run_ids)
        total_run_count = len(total_run_ids) if total_run_ids else len(explicit_run_ids)
        detection_frequency = (
            detected_run_count / total_run_count if total_run_count else 0.0
        )
        detected_contexts = tuple(
            context_by_run[run_id]
            for run_id in explicit_run_ids
            if run_id in context_by_run
        )
        condition_runs: dict[str, set[str]] = defaultdict(set)
        condition_samples: dict[str, set[str]] = defaultdict(set)
        condition_total_samples: dict[str, set[str]] = defaultdict(set)
        for context in detected_contexts:
            if context.condition_id:
                condition_runs[context.condition_id].add(context.run_id)
                sample_token = (
                    context.sample_id or context.replicate_id or context.run_id
                )
                condition_samples[context.condition_id].add(sample_token)
        for context in context_by_run.values():
            if context.condition_id:
                sample_token = (
                    context.sample_id or context.replicate_id or context.run_id
                )
                condition_total_samples[context.condition_id].add(sample_token)
        detected_conditions = tuple(sorted(condition_runs))
        detected_condition_count = len(detected_conditions)
        if condition_runs:
            primary_condition = max(
                condition_runs.items(),
                key=lambda item: (len(item[1]), item[0]),
            )[0]
            max_condition_runs = max(
                len(run_ids) for run_ids in condition_runs.values()
            )
            condition_specificity = max_condition_runs / detected_run_count
        else:
            primary_condition = None
            condition_specificity = 0.0
        detected_replicate_count = sum(
            len(condition_samples[condition_id]) for condition_id in detected_conditions
        )
        total_replicate_count = sum(
            len(condition_total_samples.get(condition_id, set()))
            for condition_id in detected_conditions
        )
        replicate_consistency = (
            detected_replicate_count / total_replicate_count
            if total_replicate_count
            else (1.0 if detected_run_count > 1 else 0.0)
        )
    else:
        explicit_run_ids = ()
        detected_run_count = 1 if supporting_records else 0
        total_run_count = detected_run_count
        detection_frequency = 1.0 if supporting_records else 0.0
        detected_conditions = ()
        detected_condition_count = 0
        primary_condition = None
        condition_specificity = 0.0
        detected_replicate_count = len(
            {record.spectrum_id for record in supporting_records}
        )
        total_replicate_count = detected_replicate_count
        replicate_consistency = 1.0 if detected_replicate_count > 1 else 0.0
    single_run_only = bool(explicit_run_ids) and detected_run_count == 1
    reproducibility_class, explanation = _classify_reproducibility(
        explicit_run_ids=explicit_run_ids,
        detected_condition_count=detected_condition_count,
        condition_specificity=condition_specificity,
        single_run_only=single_run_only,
        exploratory_override=exploratory_override,
        replicate_consistency=replicate_consistency,
    )
    return CrossRunReproducibilityEntry(
        entity_type=entity_type,
        entity_id=entity_id,
        detected_run_count=detected_run_count,
        total_run_count=total_run_count,
        detection_frequency=detection_frequency,
        detected_condition_count=detected_condition_count,
        detected_conditions=detected_conditions,
        primary_condition=primary_condition,
        condition_specificity=condition_specificity,
        detected_replicate_count=detected_replicate_count,
        total_replicate_count=total_replicate_count,
        replicate_consistency=replicate_consistency,
        single_run_only=single_run_only,
        exploratory_override=exploratory_override,
        reproducibility_class=reproducibility_class,
        run_ids=explicit_run_ids,
        explanation=explanation,
    )


def _classify_reproducibility(
    *,
    explicit_run_ids: tuple[str, ...],
    detected_condition_count: int,
    condition_specificity: float,
    single_run_only: bool,
    exploratory_override: bool,
    replicate_consistency: float,
) -> tuple[CrossRunReproducibilityClass, str]:
    if not explicit_run_ids:
        return (
            CrossRunReproducibilityClass.REPRODUCIBLE,
            "support is present, but run context is unavailable so reproducibility remains provisional",
        )
    if single_run_only and exploratory_override:
        return (
            CrossRunReproducibilityClass.EXPLORATORY,
            "evidence is observed in one run only, but explicit exploratory review preserves it from automatic downgrade",
        )
    if single_run_only:
        return (
            CrossRunReproducibilityClass.SINGLE_RUN_ONLY,
            "evidence is observed in one run only and should be downgraded unless explicitly exploratory",
        )
    if (
        explicit_run_ids
        and detected_condition_count == 1
        and condition_specificity == 1.0
    ):
        return (
            CrossRunReproducibilityClass.CONDITION_SPECIFIC,
            "evidence is reproducible across runs within one condition and remains condition-specific rather than cross-condition broad",
        )
    return (
        CrossRunReproducibilityClass.REPRODUCIBLE,
        "evidence is observed across multiple runs with reproducible support",
    )


__all__ = [
    "CrossRunEntityType",
    "CrossRunReproducibilityClass",
    "CrossRunReproducibilityEntry",
    "CrossRunReproducibilityReport",
    "CrossRunReproducibilitySummary",
    "RunDetectionContext",
    "build_peptide_cross_run_reproducibility_report",
    "build_protein_cross_run_reproducibility_report",
    "render_cross_run_reproducibility_entries_tsv",
    "render_cross_run_reproducibility_summary_tsv",
]
