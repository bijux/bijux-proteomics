# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned multiplex sample-metadata validation over experimental design tables."""

from __future__ import annotations

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


class MultiplexMetadataValidationReport(JsonModel):
    """Owned multiplex metadata-validation surface."""

    model_config = ConfigDict(extra="forbid")

    design_report: ExperimentalDesignReport
    channel_assignments: tuple[MultiplexChannelAssignmentEntry, ...] = Field(
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
    entries_by_group_and_channel = {
        (entry.multiplex_group or "", entry.multiplex_channel or ""): entry
        for entry in multiplex_entries
    }
    assignments: list[MultiplexChannelAssignmentEntry] = []
    for multiplex_group in sorted({entry.multiplex_group or "" for entry in multiplex_entries}):
        for multiplex_channel in channel_union:
            entry = entries_by_group_and_channel.get((multiplex_group, multiplex_channel))
            if entry is None:
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
            assignments.append(
                MultiplexChannelAssignmentEntry(
                    multiplex_group=multiplex_group,
                    multiplex_channel=multiplex_channel,
                    sample_id=entry.sample_id,
                    condition=entry.condition,
                    sample_role=entry.sample_role.value,
                    assigned=True,
                    note="design row provides an explicit multiplex channel to sample mapping",
                )
            )
    return MultiplexMetadataValidationReport(
        design_report=design_report,
        channel_assignments=tuple(assignments),
        summary=MultiplexMetadataSummary(
            multiplex_group_count=len(
                {entry.multiplex_group for entry in multiplex_entries}
            ),
            multiplex_channel_count=len(assignments),
            assigned_channel_count=sum(1 for entry in assignments if entry.assigned),
            missing_channel_assignment_count=sum(
                1 for entry in assignments if not entry.assigned
            ),
            duplicate_assignment_count=0,
            missing_condition_count=sum(
                1 for entry in multiplex_entries if not entry.condition
            ),
        ),
        note=(
            "multiplex metadata validation preserves expected channel assignment coverage before duplicate-assignment review is applied"
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
