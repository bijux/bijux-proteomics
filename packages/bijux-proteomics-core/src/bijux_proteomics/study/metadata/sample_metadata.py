# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned study sample-metadata parsing and shared-run semantics."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import RejectedEvidence, SampleMetadata
from bijux_proteomics._scientific_tables import (
    ScientificTableValidationIssue,
    build_samples_table_schema,
    validate_scientific_table,
)
from bijux_proteomics_foundation import JsonModel


class StudySampleMetadataIssue(JsonModel):
    """One stable issue over a governed study samples table."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=1)
    column: str | None = None


class StudySampleMetadataRejectedRow(JsonModel):
    """One rejected study sample-metadata row."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=1)
    raw_values: dict[str, str] = Field(default_factory=dict)
    issues: tuple[StudySampleMetadataIssue, ...] = Field(default_factory=tuple)

    def to_domain_record(self) -> RejectedEvidence:
        """Expose one rejected sample row as canonical rejected evidence."""

        return RejectedEvidence(
            record_kind="sample_metadata",
            rejection_reason="; ".join(issue.message for issue in self.issues)
            or "rejected sample metadata row",
            row_number=self.row_number,
            raw_fields=self.raw_values,
            metadata={
                "source_contract": "study.sample_metadata_rejected_row",
                "issue_codes": ";".join(issue.code for issue in self.issues),
            },
        )


class StudySampleMetadataSummary(JsonModel):
    """Compact summary over one parsed study samples table."""

    model_config = ConfigDict(extra="forbid")

    sample_count: int = Field(..., ge=0)
    run_count: int = Field(..., ge=0)
    condition_count: int = Field(..., ge=0)
    paired_sample_count: int = Field(..., ge=0)
    timepoint_sample_count: int = Field(..., ge=0)
    multiplex_sample_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)


class StudySampleMetadataReport(JsonModel):
    """Stable parse report for one governed `samples.tsv` table."""

    model_config = ConfigDict(extra="forbid")

    accepted_entries: tuple[SampleMetadata, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[StudySampleMetadataRejectedRow, ...] = Field(
        default_factory=tuple
    )
    summary: StudySampleMetadataSummary


def parse_sample_metadata_table(path: Path) -> StudySampleMetadataReport:
    """Parse one governed study samples TSV or CSV table into canonical records."""

    validation_report = validate_scientific_table(
        path,
        schema=build_samples_table_schema(),
    )
    owned_fields = {
        "sample_id",
        "run_id",
        "condition",
        "batch",
        "pair_id",
        "timepoint",
        "plex_id",
        "channel",
    }
    provisional_entries: list[tuple[int, dict[str, str], SampleMetadata]] = []
    rejected_rows = [
        StudySampleMetadataRejectedRow(
            row_number=row.row_number,
            raw_values=row.raw_values,
            issues=_translate_scientific_issues(row.issues),
        )
        for row in validation_report.rejected_rows
    ]

    for row in validation_report.accepted_rows:
        raw_values = dict(row.raw_values)
        metadata = {
            key: value
            for key, value in {**row.extra_values}.items()
            if key not in owned_fields and value
        }
        provisional_entries.append(
            (
                row.row_number,
                raw_values,
                SampleMetadata(
                    sample_id=str(row.values.get("sample_id") or ""),
                    run_id=str(row.values.get("run_id") or ""),
                    condition=str(row.values.get("condition") or ""),
                    batch=_optional_text(row.values.get("batch")),
                    pair_id=_optional_text(row.values.get("pair_id")),
                    timepoint=_optional_text(row.values.get("timepoint")),
                    plex_id=_optional_text(row.values.get("plex_id")),
                    channel=_optional_text(row.values.get("channel")),
                    metadata=metadata,
                ),
            )
        )

    rejected_row_numbers = {
        row.row_number for row in rejected_rows
    }
    rejected_rows.extend(
        _shared_run_semantic_rejections(provisional_entries, rejected_row_numbers)
    )
    final_rejected_numbers = {row.row_number for row in rejected_rows}
    accepted_entries = tuple(
        entry
        for row_number, _, entry in provisional_entries
        if row_number not in final_rejected_numbers
    )
    summary = StudySampleMetadataSummary(
        sample_count=len(accepted_entries),
        run_count=len({entry.run_id for entry in accepted_entries}),
        condition_count=len({entry.condition for entry in accepted_entries}),
        paired_sample_count=sum(1 for entry in accepted_entries if entry.pair_id),
        timepoint_sample_count=sum(1 for entry in accepted_entries if entry.timepoint),
        multiplex_sample_count=sum(
            1 for entry in accepted_entries if entry.plex_id and entry.channel
        ),
        rejected_row_count=len(rejected_rows),
    )
    return StudySampleMetadataReport(
        accepted_entries=accepted_entries,
        rejected_rows=tuple(sorted(rejected_rows, key=lambda row: row.row_number)),
        summary=summary,
    )


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _translate_scientific_issues(
    issues: tuple[ScientificTableValidationIssue, ...],
) -> tuple[StudySampleMetadataIssue, ...]:
    translated: list[StudySampleMetadataIssue] = []
    for issue in issues:
        if issue.code == "missing_column":
            translated.append(
                StudySampleMetadataIssue(
                    code="missing_sample_metadata_column",
                    message=f"samples table is missing required column {issue.column!r}",
                    row_number=issue.row_number,
                    column=issue.column,
                )
            )
            continue
        if issue.code == "missing_value":
            translated.append(
                StudySampleMetadataIssue(
                    code="missing_sample_metadata_value",
                    message=(
                        f"samples table row is missing required value for {issue.column!r}"
                    ),
                    row_number=issue.row_number,
                    column=issue.column,
                )
            )
            continue
        if issue.code == "duplicate_identifier":
            translated.append(
                StudySampleMetadataIssue(
                    code="duplicate_sample_id",
                    message=issue.message,
                    row_number=issue.row_number,
                    column=issue.column,
                )
            )
            continue
        if issue.code == "incomplete_linked_fields":
            translated.append(
                StudySampleMetadataIssue(
                    code="incomplete_multiplex_assignment",
                    message=issue.message,
                    row_number=issue.row_number,
                    column=issue.column,
                )
            )
            continue
        translated.append(
            StudySampleMetadataIssue(
                code="invalid_sample_metadata_row",
                message=issue.message,
                row_number=issue.row_number,
                column=issue.column,
            )
        )
    return tuple(translated)


def _shared_run_semantic_rejections(
    provisional_entries: list[tuple[int, dict[str, str], SampleMetadata]],
    rejected_row_numbers: set[int],
) -> list[StudySampleMetadataRejectedRow]:
    grouped_by_run: dict[str, list[tuple[int, dict[str, str], SampleMetadata]]] = {}
    for row_number, raw_values, entry in provisional_entries:
        if row_number in rejected_row_numbers:
            continue
        grouped_by_run.setdefault(entry.run_id, []).append((row_number, raw_values, entry))

    semantic_rejections: list[StudySampleMetadataRejectedRow] = []
    for run_entries in grouped_by_run.values():
        if len(run_entries) < 2:
            continue
        if not all(entry.plex_id and entry.channel for _, _, entry in run_entries):
            for row_number, raw_values, _ in run_entries:
                semantic_rejections.append(
                    StudySampleMetadataRejectedRow(
                        row_number=row_number,
                        raw_values=raw_values,
                        issues=(
                            StudySampleMetadataIssue(
                                code="ambiguous_shared_run",
                                message=(
                                    "shared run_id values require explicit plex_id and channel assignments"
                                ),
                                row_number=row_number,
                                column="run_id",
                            ),
                        ),
                    )
                )
            continue
        seen_channels: dict[tuple[str, str], int] = {}
        duplicate_rows: set[int] = set()
        for row_number, _, entry in run_entries:
            channel_key = (str(entry.plex_id), str(entry.channel))
            if channel_key in seen_channels:
                duplicate_rows.add(row_number)
                duplicate_rows.add(seen_channels[channel_key])
            else:
                seen_channels[channel_key] = row_number
        for row_number, raw_values, entry in run_entries:
            if row_number not in duplicate_rows:
                continue
            semantic_rejections.append(
                StudySampleMetadataRejectedRow(
                    row_number=row_number,
                    raw_values=raw_values,
                    issues=(
                        StudySampleMetadataIssue(
                            code="duplicate_run_channel_assignment",
                            message=(
                                "shared run multiplex assignments must keep each plex_id and channel combination unique"
                            ),
                            row_number=row_number,
                            column="channel" if entry.channel else "run_id",
                        ),
                    ),
                )
            )
    return semantic_rejections
