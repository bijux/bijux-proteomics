# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned replicate-structure semantics for study QC and statistical power."""

from __future__ import annotations

import csv
from collections import defaultdict
from io import StringIO
from typing import cast

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    ExperimentalDesignSampleRole,
)
from bijux_proteomics.study.design.experiment_design import (
    ExperimentDesign,
    ExperimentDesignSample,
    coerce_experiment_design,
)
from bijux_proteomics_foundation import JsonModel


class ReplicateStructureSampleEntry(JsonModel):
    """Replicate structure resolved for one biological sample."""

    model_config = ConfigDict(extra="forbid")

    biological_sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    sample_role: ExperimentalDesignSampleRole
    run_count: int = Field(..., ge=0)
    technical_replicate_count: int = Field(..., ge=0)
    injection_replicate_count: int = Field(..., ge=0)
    fraction_count: int = Field(..., ge=0)
    multiplex_channel_count: int = Field(..., ge=0)
    repeated_measure_subject_id: str | None = None
    effective_statistical_unit_id: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class ReplicateStructureConditionEntry(JsonModel):
    """Condition-level replicate structure used by QC and statistical policies."""

    model_config = ConfigDict(extra="forbid")

    condition: str = Field(..., min_length=1)
    biological_replicate_count: int = Field(..., ge=0)
    effective_statistical_unit_count: int = Field(..., ge=0)
    technical_replicate_count: int = Field(..., ge=0)
    injection_replicate_count: int = Field(..., ge=0)
    fractionated_sample_count: int = Field(..., ge=0)
    multiplex_channel_count: int = Field(..., ge=0)
    repeated_measure_subject_count: int = Field(..., ge=0)
    underpowered_for_statistics: bool
    note: str = Field(..., min_length=1)


class ReplicateStructureSummary(JsonModel):
    """Compact study-wide summary over replicate structure."""

    model_config = ConfigDict(extra="forbid")

    biological_sample_count: int = Field(..., ge=0)
    condition_count: int = Field(..., ge=0)
    effective_statistical_unit_count: int = Field(..., ge=0)
    technical_replicate_count: int = Field(..., ge=0)
    injection_replicate_count: int = Field(..., ge=0)
    fractionated_sample_count: int = Field(..., ge=0)
    multiplex_channel_count: int = Field(..., ge=0)
    repeated_measure_subject_count: int = Field(..., ge=0)


class ReplicateStructureReport(JsonModel):
    """Owned replicate-structure report over one experiment design."""

    model_config = ConfigDict(extra="forbid")

    experiment_design: ExperimentDesign
    minimum_statistical_units_per_condition: int = Field(..., ge=1)
    sample_entries: tuple[ReplicateStructureSampleEntry, ...] = Field(
        default_factory=tuple
    )
    condition_entries: tuple[ReplicateStructureConditionEntry, ...] = Field(
        default_factory=tuple
    )
    summary: ReplicateStructureSummary
    note: str = Field(..., min_length=1)


def build_replicate_structure_report(
    design: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    minimum_statistical_units_per_condition: int = 2,
) -> ReplicateStructureReport:
    """Distinguish replicate semantics that affect QC and statistics differently."""

    experiment_design = coerce_experiment_design(design)
    repeated_measure_subject_ids = _repeated_measure_subject_ids(experiment_design)
    sample_entries: list[ReplicateStructureSampleEntry] = []
    entries_by_sample = _entries_by_sample(experiment_design.entries)
    for sample in experiment_design.samples:
        entries = entries_by_sample[sample.sample_id]
        sample_entries.append(
            _build_sample_entry(
                sample=sample,
                entries=entries,
                repeated_measure_subject_ids=repeated_measure_subject_ids,
            )
        )
    condition_entries = _build_condition_entries(
        sample_entries,
        minimum_statistical_units_per_condition=minimum_statistical_units_per_condition,
    )
    sample_role_entries = tuple(
        entry
        for entry in sample_entries
        if entry.sample_role is ExperimentalDesignSampleRole.SAMPLE
    )
    repeated_measure_subject_count = len(
        {
            entry.repeated_measure_subject_id
            for entry in sample_role_entries
            if entry.repeated_measure_subject_id not in (None, "")
        }
    )
    return ReplicateStructureReport(
        experiment_design=experiment_design,
        minimum_statistical_units_per_condition=minimum_statistical_units_per_condition,
        sample_entries=tuple(
            sorted(
                sample_entries,
                key=lambda entry: (entry.condition, entry.biological_sample_id),
            )
        ),
        condition_entries=condition_entries,
        summary=ReplicateStructureSummary(
            biological_sample_count=len(sample_role_entries),
            condition_count=len(condition_entries),
            effective_statistical_unit_count=len(
                {
                    entry.effective_statistical_unit_id
                    for entry in sample_role_entries
                }
            ),
            technical_replicate_count=sum(
                entry.technical_replicate_count for entry in sample_role_entries
            ),
            injection_replicate_count=sum(
                entry.injection_replicate_count for entry in sample_role_entries
            ),
            fractionated_sample_count=sum(
                1 for entry in sample_role_entries if entry.fraction_count > 1
            ),
            multiplex_channel_count=sum(
                entry.multiplex_channel_count for entry in sample_role_entries
            ),
            repeated_measure_subject_count=repeated_measure_subject_count,
        ),
        note=(
            "replicate structure keeps biological replicates, technical replicates, "
            "reinjections, fractions, multiplex channels, and repeated-measure "
            "subjects separate so QC and statistical power do not treat every "
            "repeated label as interchangeable replicate support"
        ),
    )


def count_effective_statistical_units_by_condition(
    design: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
) -> dict[str, int]:
    """Return one statistical-unit count per condition for replicate policies."""

    report = build_replicate_structure_report(design)
    return {
        entry.condition: entry.effective_statistical_unit_count
        for entry in report.condition_entries
    }


def render_replicate_structure_tsv(report: ReplicateStructureReport) -> str:
    """Render one stable condition-level replicate-structure table as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "condition",
            "biological_replicate_count",
            "effective_statistical_unit_count",
            "technical_replicate_count",
            "injection_replicate_count",
            "fractionated_sample_count",
            "multiplex_channel_count",
            "repeated_measure_subject_count",
            "underpowered_for_statistics",
            "note",
        )
    )
    for entry in report.condition_entries:
        writer.writerow(
            (
                entry.condition,
                entry.biological_replicate_count,
                entry.effective_statistical_unit_count,
                entry.technical_replicate_count,
                entry.injection_replicate_count,
                entry.fractionated_sample_count,
                entry.multiplex_channel_count,
                entry.repeated_measure_subject_count,
                str(entry.underpowered_for_statistics).lower(),
                entry.note,
            )
        )
    return buffer.getvalue()


def _build_sample_entry(
    *,
    sample: ExperimentDesignSample,
    entries: tuple[ExperimentalDesignEntry, ...],
    repeated_measure_subject_ids: set[str],
) -> ReplicateStructureSampleEntry:
    explicit_technical_groups = _explicit_technical_groups(entries)
    technical_replicate_count = (
        len(explicit_technical_groups) if explicit_technical_groups else len(entries)
    )
    injection_replicate_count = (
        sum(max(len(group_entries) - 1, 0) for group_entries in explicit_technical_groups.values())
        if explicit_technical_groups
        else 0
    )
    fraction_count = len({entry.fraction for entry in entries})
    multiplex_channel_count = len(
        {
            entry.multiplex_channel
            for entry in entries
            if entry.multiplex_channel not in (None, "")
        }
    )
    repeated_measure_subject_id = (
        sample.pair_id if sample.pair_id in repeated_measure_subject_ids else None
    )
    effective_statistical_unit_id = (
        repeated_measure_subject_id or sample.sample_id
    )
    notes: list[str] = []
    if technical_replicate_count > 1:
        notes.append("technical replicates add run support without adding biological power")
    if injection_replicate_count > 0:
        notes.append("reinjections stay within one technical replicate")
    if fraction_count > 1:
        notes.append("fractions stay within one biological sample")
    if multiplex_channel_count > 0:
        notes.append("multiplex channels preserve assay placement without adding replicates")
    if repeated_measure_subject_id is not None:
        notes.append("repeated-measure rows collapse to one subject-level statistical unit")
    return ReplicateStructureSampleEntry(
        biological_sample_id=sample.sample_id,
        condition=sample.condition,
        sample_role=entries[0].sample_role,
        run_count=len(entries),
        technical_replicate_count=technical_replicate_count,
        injection_replicate_count=injection_replicate_count,
        fraction_count=fraction_count,
        multiplex_channel_count=multiplex_channel_count,
        repeated_measure_subject_id=repeated_measure_subject_id,
        effective_statistical_unit_id=effective_statistical_unit_id,
        note="; ".join(notes) or "single biological sample without nested replicate structure",
    )


def _build_condition_entries(
    sample_entries: list[ReplicateStructureSampleEntry],
    *,
    minimum_statistical_units_per_condition: int,
) -> tuple[ReplicateStructureConditionEntry, ...]:
    by_condition: dict[str, list[ReplicateStructureSampleEntry]] = defaultdict(list)
    for entry in sample_entries:
        if entry.sample_role is ExperimentalDesignSampleRole.SAMPLE:
            by_condition[entry.condition].append(entry)
    condition_entries: list[ReplicateStructureConditionEntry] = []
    for condition in sorted(by_condition):
        condition_samples = by_condition[condition]
        effective_statistical_unit_count = len(
            {
                entry.effective_statistical_unit_id
                for entry in condition_samples
            }
        )
        biological_replicate_count = len(condition_samples)
        technical_replicate_count = sum(
            entry.technical_replicate_count for entry in condition_samples
        )
        injection_replicate_count = sum(
            entry.injection_replicate_count for entry in condition_samples
        )
        fractionated_sample_count = sum(
            1 for entry in condition_samples if entry.fraction_count > 1
        )
        multiplex_channel_count = sum(
            entry.multiplex_channel_count for entry in condition_samples
        )
        repeated_measure_subject_count = len(
            {
                entry.repeated_measure_subject_id
                for entry in condition_samples
                if entry.repeated_measure_subject_id not in (None, "")
            }
        )
        condition_entries.append(
            ReplicateStructureConditionEntry(
                condition=condition,
                biological_replicate_count=biological_replicate_count,
                effective_statistical_unit_count=effective_statistical_unit_count,
                technical_replicate_count=technical_replicate_count,
                injection_replicate_count=injection_replicate_count,
                fractionated_sample_count=fractionated_sample_count,
                multiplex_channel_count=multiplex_channel_count,
                repeated_measure_subject_count=repeated_measure_subject_count,
                underpowered_for_statistics=(
                    effective_statistical_unit_count
                    < minimum_statistical_units_per_condition
                ),
                note=_condition_note(
                    biological_replicate_count=biological_replicate_count,
                    effective_statistical_unit_count=effective_statistical_unit_count,
                    technical_replicate_count=technical_replicate_count,
                    injection_replicate_count=injection_replicate_count,
                    fractionated_sample_count=fractionated_sample_count,
                    multiplex_channel_count=multiplex_channel_count,
                    repeated_measure_subject_count=repeated_measure_subject_count,
                ),
            )
        )
    return tuple(condition_entries)


def _condition_note(
    *,
    biological_replicate_count: int,
    effective_statistical_unit_count: int,
    technical_replicate_count: int,
    injection_replicate_count: int,
    fractionated_sample_count: int,
    multiplex_channel_count: int,
    repeated_measure_subject_count: int,
) -> str:
    notes: list[str] = []
    if effective_statistical_unit_count != biological_replicate_count:
        notes.append("subject-level repeated measures reduce independent statistical units")
    if technical_replicate_count > biological_replicate_count:
        notes.append("technical replicate runs do not raise replicate power")
    if injection_replicate_count > 0:
        notes.append("reinjections remain within existing technical replicate support")
    if fractionated_sample_count > 0:
        notes.append("fractionated samples add depth without adding biological replicates")
    if multiplex_channel_count > 0:
        notes.append("multiplex channels record assay placement without increasing independent units")
    return "; ".join(notes) or "biological samples and statistical units are aligned"


def _repeated_measure_subject_ids(experiment_design: ExperimentDesign) -> set[str]:
    pair_timepoints: dict[str, set[str]] = defaultdict(set)
    pair_samples: dict[str, set[str]] = defaultdict(set)
    for sample in experiment_design.samples:
        if sample.pair_id in (None, ""):
            continue
        pair_id = cast(str, sample.pair_id)
        pair_samples[pair_id].add(sample.sample_id)
        if sample.timepoint not in (None, ""):
            pair_timepoints[pair_id].add(cast(str, sample.timepoint))
    return {
        pair_id
        for pair_id in pair_samples
        if len(pair_samples[pair_id]) > 1 or len(pair_timepoints[pair_id]) > 1
    }


def _entries_by_sample(
    entries: tuple[ExperimentalDesignEntry, ...],
) -> dict[str, tuple[ExperimentalDesignEntry, ...]]:
    grouped: dict[str, list[ExperimentalDesignEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.sample_id].append(entry)
    return {
        sample_id: tuple(
            sorted(
                sample_entries,
                key=lambda entry: (
                    entry.technical_replicate_id or "",
                    entry.fraction,
                    entry.spectra_file,
                ),
            )
        )
        for sample_id, sample_entries in grouped.items()
    }


def _explicit_technical_groups(
    entries: tuple[ExperimentalDesignEntry, ...],
) -> dict[tuple[str, int, str, str], tuple[ExperimentalDesignEntry, ...]]:
    groups: dict[tuple[str, int, str, str], list[ExperimentalDesignEntry]] = defaultdict(
        list
    )
    for entry in entries:
        if entry.technical_replicate_id in (None, ""):
            continue
        groups[
            (
                entry.technical_replicate_id,
                entry.fraction,
                entry.multiplex_group or "",
                entry.multiplex_channel or "",
            )
        ].append(entry)
    return {
        key: tuple(
            sorted(group_entries, key=lambda entry: entry.spectra_file)
        )
        for key, group_entries in groups.items()
    }


__all__ = [
    "ReplicateStructureConditionEntry",
    "ReplicateStructureReport",
    "ReplicateStructureSampleEntry",
    "ReplicateStructureSummary",
    "build_replicate_structure_report",
    "count_effective_statistical_units_by_condition",
    "render_replicate_structure_tsv",
]
