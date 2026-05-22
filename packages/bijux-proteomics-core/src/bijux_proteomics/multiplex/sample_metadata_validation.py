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
    sample_id: str = Field(..., min_length=1)
    condition: str | None = None
    sample_role: str = Field(..., min_length=1)
    assigned: bool
    note: str = Field(..., min_length=1)


class MultiplexMetadataSummary(JsonModel):
    """Compact summary over multiplex design metadata validation."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group_count: int = Field(..., ge=0)
    multiplex_channel_count: int = Field(..., ge=0)
    assigned_channel_count: int = Field(..., ge=0)
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
    assignments = tuple(
        MultiplexChannelAssignmentEntry(
            multiplex_group=entry.multiplex_group or "",
            multiplex_channel=entry.multiplex_channel or "",
            sample_id=entry.sample_id,
            condition=entry.condition,
            sample_role=entry.sample_role.value,
            assigned=True,
            note="design row provides an explicit multiplex channel to sample mapping",
        )
        for entry in sorted(
            multiplex_entries,
            key=lambda item: (item.multiplex_group or "", item.multiplex_channel or ""),
        )
    )
    return MultiplexMetadataValidationReport(
        design_report=design_report,
        channel_assignments=assignments,
        summary=MultiplexMetadataSummary(
            multiplex_group_count=len(
                {entry.multiplex_group for entry in multiplex_entries}
            ),
            multiplex_channel_count=len(assignments),
            assigned_channel_count=len(assignments),
            duplicate_assignment_count=0,
            missing_condition_count=sum(
                1 for entry in multiplex_entries if not entry.condition
            ),
        ),
        note=(
            "multiplex metadata validation preserves design-backed channel assignments before missing-channel and duplicate-assignment review is applied"
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
