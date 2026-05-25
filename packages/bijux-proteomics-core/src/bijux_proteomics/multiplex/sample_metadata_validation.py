# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned multiplex sample-metadata validation over experimental design tables."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    ExperimentalDesignReport,
)
from bijux_proteomics_foundation import JsonModel


class MultiplexChannelAssignmentEntry(JsonModel):
    """One multiplex-group channel assignment row."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    sample_id: str | None = None
    condition: str | None = None
    sample_role: str | None = None
    assigned: bool
    note: str = Field(..., min_length=1)


class MultiplexMetadataSummary(JsonModel):
    """Compact summary over multiplex design metadata validation."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group_count: int = Field(..., ge=0)
    multiplex_channel_count: int = Field(..., ge=0)
    assigned_channel_count: int = Field(..., ge=0)
    missing_channel_assignment_count: int = Field(..., ge=0)
    duplicate_assignment_count: int = Field(..., ge=0)
    missing_condition_count: int = Field(..., ge=0)


class MultiplexDuplicateAssignmentEntry(JsonModel):
    """One duplicate multiplex assignment finding."""

    model_config = ConfigDict(extra="forbid")

    issue_kind: str = Field(..., min_length=1)
    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str | None = None
    sample_id: str | None = None
    entry_count: int = Field(..., ge=2)
    note: str = Field(..., min_length=1)


class MultiplexMissingConditionEntry(JsonModel):
    """One multiplex design row with a missing condition."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    sample_role: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class MultiplexMetadataValidationReport(JsonModel):
    """Owned multiplex metadata-validation surface."""

    model_config = ConfigDict(extra="forbid")

    design_report: ExperimentalDesignReport
    channel_assignments: tuple[MultiplexChannelAssignmentEntry, ...] = Field(
        default_factory=tuple
    )
    duplicate_assignments: tuple[MultiplexDuplicateAssignmentEntry, ...] = Field(
        default_factory=tuple
    )
    missing_conditions: tuple[MultiplexMissingConditionEntry, ...] = Field(
        default_factory=tuple
    )
    summary: MultiplexMetadataSummary
    note: str = Field(..., min_length=1)


def build_multiplex_metadata_validation_report(
    design_report: ExperimentalDesignReport,
) -> MultiplexMetadataValidationReport:
    """Validate design-backed multiplex channel, sample, and condition mappings."""

    multiplex_entries = _multiplex_entries(design_report.accepted_entries)
    channel_union = tuple(
        sorted({entry.multiplex_channel or "" for entry in multiplex_entries})
    )
    entries_by_group_and_channel: dict[tuple[str, str], list[ExperimentalDesignEntry]] = {}
    entries_by_group_and_sample: dict[tuple[str, str], list[ExperimentalDesignEntry]] = {}
    for entry in multiplex_entries:
        group = entry.multiplex_group or ""
        channel = entry.multiplex_channel or ""
        entries_by_group_and_channel.setdefault((group, channel), []).append(entry)
        entries_by_group_and_sample.setdefault((group, entry.sample_id), []).append(entry)

    assignments: list[MultiplexChannelAssignmentEntry] = []
    for multiplex_group in sorted({entry.multiplex_group or "" for entry in multiplex_entries}):
        for multiplex_channel in channel_union:
            matches = entries_by_group_and_channel.get((multiplex_group, multiplex_channel), [])
            if not matches:
                assignments.append(
                    MultiplexChannelAssignmentEntry(
                        multiplex_group=multiplex_group,
                        multiplex_channel=multiplex_channel,
                        sample_id=None,
                        condition=None,
                        sample_role=None,
                        assigned=False,
                        note="expected multiplex channel is missing from this group in the design table",
                    )
                )
                continue
            entry = sorted(matches, key=lambda item: item.sample_id)[0]
            assignments.append(
                MultiplexChannelAssignmentEntry(
                    multiplex_group=multiplex_group,
                    multiplex_channel=multiplex_channel,
                    sample_id=entry.sample_id,
                    condition=entry.condition,
                    sample_role=entry.sample_role.value,
                    assigned=True,
                    note=(
                        "design row provides an explicit multiplex channel to sample mapping"
                        if len(matches) == 1
                        else "design channel maps to more than one sample row and requires duplicate-assignment review"
                    ),
                )
            )

    duplicate_assignments: list[MultiplexDuplicateAssignmentEntry] = []
    for (multiplex_group, multiplex_channel), matches in sorted(entries_by_group_and_channel.items()):
        if len(matches) > 1:
            duplicate_assignments.append(
                MultiplexDuplicateAssignmentEntry(
                    issue_kind="duplicate_channel_assignment",
                    multiplex_group=multiplex_group,
                    multiplex_channel=multiplex_channel,
                    sample_id=None,
                    entry_count=len(matches),
                    note="more than one design row assigns the same multiplex channel within one group",
                )
            )
    for (multiplex_group, sample_id), matches in sorted(entries_by_group_and_sample.items()):
        if len(matches) > 1:
            duplicate_assignments.append(
                MultiplexDuplicateAssignmentEntry(
                    issue_kind="duplicate_sample_assignment",
                    multiplex_group=multiplex_group,
                    multiplex_channel=None,
                    sample_id=sample_id,
                    entry_count=len(matches),
                    note="the same sample id is assigned to more than one multiplex channel within one group",
                )
            )

    missing_conditions = tuple(
        MultiplexMissingConditionEntry(
            multiplex_group=entry.multiplex_group or "",
            multiplex_channel=entry.multiplex_channel or "",
            sample_id=entry.sample_id,
            sample_role=entry.sample_role.value,
            note="design row leaves condition empty or placeholder-valued even though multiplex sample metadata requires it for biological comparison",
        )
        for entry in sorted(
            (entry for entry in multiplex_entries if _condition_missing(entry.condition)),
            key=lambda item: (item.multiplex_group or "", item.multiplex_channel or ""),
        )
    )
    return MultiplexMetadataValidationReport(
        design_report=design_report,
        channel_assignments=tuple(assignments),
        duplicate_assignments=tuple(duplicate_assignments),
        missing_conditions=missing_conditions,
        summary=MultiplexMetadataSummary(
            multiplex_group_count=len(
                {entry.multiplex_group for entry in multiplex_entries}
            ),
            multiplex_channel_count=len(assignments),
            assigned_channel_count=sum(1 for entry in assignments if entry.assigned),
            missing_channel_assignment_count=sum(
                1 for entry in assignments if not entry.assigned
            ),
            duplicate_assignment_count=len(duplicate_assignments),
            missing_condition_count=len(missing_conditions),
        ),
        note=(
            "multiplex metadata validation preserves expected channel coverage, duplicate-assignment findings, and missing-condition evidence for biological comparison review"
        ),
    )


def _multiplex_entries(
    accepted_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[ExperimentalDesignEntry, ...]:
    return tuple(
        entry
        for entry in accepted_entries
        if entry.multiplex_group and entry.multiplex_channel
    )


def _condition_missing(condition: str | None) -> bool:
    if condition is None:
        return True
    return condition.strip().lower() in {"", "na", "n/a", "unknown", "unassigned"}


def render_multiplex_metadata_summary_tsv(
    report: MultiplexMetadataValidationReport,
) -> str:
    """Render the compact multiplex metadata-validation summary ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "multiplex_group_count",
            "multiplex_channel_count",
            "assigned_channel_count",
            "missing_channel_assignment_count",
            "duplicate_assignment_count",
            "missing_condition_count",
        ]
    )
    writer.writerow(
        [
            report.summary.multiplex_group_count,
            report.summary.multiplex_channel_count,
            report.summary.assigned_channel_count,
            report.summary.missing_channel_assignment_count,
            report.summary.duplicate_assignment_count,
            report.summary.missing_condition_count,
        ]
    )
    return buffer.getvalue()


def render_multiplex_channel_assignment_tsv(
    report: MultiplexMetadataValidationReport,
) -> str:
    """Render the multiplex channel-assignment ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "multiplex_group",
            "multiplex_channel",
            "sample_id",
            "condition",
            "sample_role",
            "assigned",
            "note",
        ]
    )
    for entry in report.channel_assignments:
        writer.writerow(
            [
                entry.multiplex_group,
                entry.multiplex_channel,
                entry.sample_id or "",
                entry.condition or "",
                entry.sample_role or "",
                entry.assigned,
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_multiplex_duplicate_assignment_tsv(
    report: MultiplexMetadataValidationReport,
) -> str:
    """Render the duplicate-assignment findings ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "issue_kind",
            "multiplex_group",
            "multiplex_channel",
            "sample_id",
            "entry_count",
            "note",
        ]
    )
    for entry in report.duplicate_assignments:
        writer.writerow(
            [
                entry.issue_kind,
                entry.multiplex_group,
                entry.multiplex_channel or "",
                entry.sample_id or "",
                entry.entry_count,
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_multiplex_missing_condition_tsv(
    report: MultiplexMetadataValidationReport,
) -> str:
    """Render the missing-condition findings ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "multiplex_group",
            "multiplex_channel",
            "sample_id",
            "sample_role",
            "note",
        ]
    )
    for entry in report.missing_conditions:
        writer.writerow(
            [
                entry.multiplex_group,
                entry.multiplex_channel,
                entry.sample_id,
                entry.sample_role,
                entry.note,
            ]
        )
    return buffer.getvalue()


def export_multiplex_metadata_summary_tsv(
    report: MultiplexMetadataValidationReport,
    path: Path,
) -> None:
    """Write the compact multiplex metadata-validation summary ledger."""

    write_output_table_tsv(path, render_multiplex_metadata_summary_tsv(report))


def export_multiplex_channel_assignment_tsv(
    report: MultiplexMetadataValidationReport,
    path: Path,
) -> None:
    """Write the multiplex channel-assignment ledger."""

    write_output_table_tsv(path, render_multiplex_channel_assignment_tsv(report))


def export_multiplex_duplicate_assignment_tsv(
    report: MultiplexMetadataValidationReport,
    path: Path,
) -> None:
    """Write the duplicate-assignment findings ledger."""

    write_output_table_tsv(path, render_multiplex_duplicate_assignment_tsv(report))


def export_multiplex_missing_condition_tsv(
    report: MultiplexMetadataValidationReport,
    path: Path,
) -> None:
    """Write the missing-condition findings ledger."""

    write_output_table_tsv(path, render_multiplex_missing_condition_tsv(report))
