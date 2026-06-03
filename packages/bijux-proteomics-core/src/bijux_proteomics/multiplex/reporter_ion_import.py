# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned TMT reporter-ion import surfaces over search-result tables."""

from __future__ import annotations

import csv
from enum import StrEnum
from pathlib import Path
import re

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.chemistry import canonicalize_modified_peptide
from bijux_proteomics_foundation import JsonModel

_MAXQUANT_REPORTER_RE = re.compile(
    r"^Reporter intensity(?: corrected)? (?P<channel>\S+)$"
)
_FRAGPIPE_REPORTER_RE = re.compile(r"^TMT[-_ ]?(?P<channel>\S+)$", re.IGNORECASE)
_GENERIC_REPORTER_RE = re.compile(
    r"^(?P<channel>12[6789](?:[NC])?|13[01](?:[NC])?|13[2-5][NC])$"
)


class TmtSearchResultSourceKind(StrEnum):
    """Supported search-result families for TMT reporter-ion import."""

    GENERIC = "generic"
    MAXQUANT = "maxquant"
    FRAGPIPE = "fragpipe"


class TmtReporterValidationIssue(JsonModel):
    """One stable validation issue while parsing a TMT reporter-ion table."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=2)


class RejectedTmtReporterRow(JsonModel):
    """One rejected TMT reporter-ion row with raw fields and issues."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[TmtReporterValidationIssue, ...] = Field(default_factory=tuple)


class TmtReporterChannelColumn(JsonModel):
    """One resolved reporter channel and its source column name."""

    model_config = ConfigDict(extra="forbid")

    multiplex_channel: str = Field(..., min_length=1)
    column_name: str = Field(..., min_length=1)

    @field_validator("multiplex_channel", "column_name", mode="before")
    @classmethod
    def _strip_text(cls, value: object) -> str:
        text = str(value).strip()
        if not text:
            raise ValueError("text value must not be empty")
        return text


class TmtReporterColumnMapping(JsonModel):
    """User-supplied mapping from a search-result table to the TMT import contract."""

    model_config = ConfigDict(extra="forbid")

    source_row_id: str | None = None
    peptide: str | None = None
    protein_refs: str | None = None
    multiplex_group: str | None = None
    isolation_interference: str | None = None
    default_multiplex_group: str | None = None
    protein_separator: str = ";"


class TmtReporterIntensity(JsonModel):
    """One reporter-channel intensity carried by a governed row observation."""

    model_config = ConfigDict(extra="forbid")

    multiplex_channel: str = Field(..., min_length=1)
    intensity: float | None = Field(default=None, ge=0.0)


class TmtReporterObservation(JsonModel):
    """One accepted search-result row with peptide, protein, plex, and channel evidence."""

    model_config = ConfigDict(extra="forbid")

    source_row_id: str = Field(..., min_length=1)
    multiplex_group: str = Field(..., min_length=1)
    modified_peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    isolation_interference_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    channel_intensities: tuple[TmtReporterIntensity, ...] = Field(default_factory=tuple)


class TmtReporterImportSummary(JsonModel):
    """Compact summary over one TMT reporter-ion import result."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_row_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    multiplex_group_count: int = Field(..., ge=0)
    reporter_channel_count: int = Field(..., ge=0)


class TmtReporterImportReport(JsonModel):
    """Stable parse report for one TMT reporter-ion search-result table."""

    model_config = ConfigDict(extra="forbid")

    source_kind: TmtSearchResultSourceKind
    column_mapping: TmtReporterColumnMapping
    channel_columns: tuple[TmtReporterChannelColumn, ...] = Field(default_factory=tuple)
    accepted_rows: tuple[TmtReporterObservation, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedTmtReporterRow, ...] = Field(default_factory=tuple)
    summary: TmtReporterImportSummary
    note: str = Field(..., min_length=1)


def parse_tmt_reporter_table(
    input_path: Path,
    *,
    source_kind: TmtSearchResultSourceKind = TmtSearchResultSourceKind.GENERIC,
    mapping: TmtReporterColumnMapping | None = None,
    channel_columns: tuple[TmtReporterChannelColumn, ...] = (),
) -> TmtReporterImportReport:
    """Parse one TMT reporter-ion search-result table into governed row observations."""

    active_mapping = mapping or TmtReporterColumnMapping()
    text = input_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines:
        raise ValueError("reporter-ion input table is empty")
    delimiter = "\t" if "\t" in lines[0] else ","
    reader = csv.DictReader(lines, delimiter=delimiter)
    if reader.fieldnames is None:
        raise ValueError("reporter-ion input table must include a header row")
    header = tuple(reader.fieldnames)
    peptide_column = _resolve_column_name(
        explicit=active_mapping.peptide,
        source_kind=source_kind,
        target="peptide",
    )
    multiplex_group_column = _resolve_column_name(
        explicit=active_mapping.multiplex_group,
        source_kind=source_kind,
        target="multiplex_group",
    )
    protein_refs_column = _resolve_column_name(
        explicit=active_mapping.protein_refs,
        source_kind=source_kind,
        target="protein_refs",
    )
    isolation_interference_column = _resolve_column_name(
        explicit=active_mapping.isolation_interference,
        source_kind=source_kind,
        target="isolation_interference",
    )
    row_id_column = _resolve_column_name(
        explicit=active_mapping.source_row_id,
        source_kind=source_kind,
        target="source_row_id",
    )
    if peptide_column not in header:
        raise ValueError(f"required peptide column {peptide_column!r} is missing")
    if (
        multiplex_group_column is not None
        and multiplex_group_column not in header
        and active_mapping.default_multiplex_group is None
    ):
        raise ValueError(
            f"required multiplex-group column {multiplex_group_column!r} is missing"
        )
    if protein_refs_column is not None and protein_refs_column not in header:
        raise ValueError(
            f"configured protein-reference column {protein_refs_column!r} is missing"
        )
    if (
        isolation_interference_column is not None
        and isolation_interference_column not in header
    ):
        if active_mapping.isolation_interference is not None:
            raise ValueError(
                "configured isolation-interference column "
                f"{isolation_interference_column!r} is missing"
            )
        isolation_interference_column = None
    if row_id_column is not None and row_id_column not in header:
        raise ValueError(
            f"configured source-row-id column {row_id_column!r} is missing"
        )

    resolved_channels = _resolve_reporter_channel_columns(
        header,
        source_kind=source_kind,
        explicit=channel_columns,
    )
    accepted_rows: list[TmtReporterObservation] = []
    rejected_rows: list[RejectedTmtReporterRow] = []

    for row_number, raw_fields in enumerate(reader, start=2):
        issues: list[TmtReporterValidationIssue] = []
        modified_peptide = (raw_fields.get(peptide_column) or "").strip()
        multiplex_group = active_mapping.default_multiplex_group or (
            ""
            if multiplex_group_column is None
            else (raw_fields.get(multiplex_group_column) or "").strip()
        )
        if not modified_peptide:
            issues.append(
                TmtReporterValidationIssue(
                    code="missing_peptide",
                    message="peptide column is empty",
                    row_number=row_number,
                )
            )
        if not multiplex_group:
            issues.append(
                TmtReporterValidationIssue(
                    code="missing_multiplex_group",
                    message="multiplex group is empty and no default_multiplex_group was supplied",
                    row_number=row_number,
                )
            )
        canonical_peptide = ""
        isolation_interference_fraction: float | None = None
        if modified_peptide:
            try:
                canonical_peptide = canonicalize_modified_peptide(modified_peptide)
            except Exception as exc:  # noqa: BLE001
                issues.append(
                    TmtReporterValidationIssue(
                        code="invalid_peptide",
                        message=str(exc),
                        row_number=row_number,
                    )
                )

        if isolation_interference_column is not None:
            raw_interference = (
                raw_fields.get(isolation_interference_column) or ""
            ).strip()
            if raw_interference:
                try:
                    isolation_interference_fraction = _parse_interference_fraction(
                        raw_interference
                    )
                except ValueError as exc:
                    issues.append(
                        TmtReporterValidationIssue(
                            code="invalid_isolation_interference",
                            message=str(exc),
                            row_number=row_number,
                        )
                    )

        reporter_values: list[TmtReporterIntensity] = []
        observed_reporter_count = 0
        for channel in resolved_channels:
            raw_value = (raw_fields.get(channel.column_name) or "").strip()
            if not raw_value:
                reporter_values.append(
                    TmtReporterIntensity(
                        multiplex_channel=channel.multiplex_channel,
                        intensity=None,
                    )
                )
                continue
            try:
                intensity = float(raw_value)
            except ValueError:
                issues.append(
                    TmtReporterValidationIssue(
                        code="invalid_reporter_intensity",
                        message=(
                            f"reporter channel {channel.multiplex_channel!r} does not carry a valid numeric intensity"
                        ),
                        row_number=row_number,
                    )
                )
                continue
            if intensity < 0:
                issues.append(
                    TmtReporterValidationIssue(
                        code="negative_reporter_intensity",
                        message=(
                            f"reporter channel {channel.multiplex_channel!r} carries a negative intensity"
                        ),
                        row_number=row_number,
                    )
                )
                continue
            reporter_values.append(
                TmtReporterIntensity(
                    multiplex_channel=channel.multiplex_channel,
                    intensity=intensity,
                )
            )
            observed_reporter_count += 1
        if observed_reporter_count == 0:
            issues.append(
                TmtReporterValidationIssue(
                    code="missing_reporter_intensities",
                    message="row does not carry any observed reporter intensity",
                    row_number=row_number,
                )
            )
        if issues:
            rejected_rows.append(
                RejectedTmtReporterRow(
                    row_number=row_number,
                    raw_fields={key: value or "" for key, value in raw_fields.items()},
                    issues=tuple(issues),
                )
            )
            continue
        source_row_id = (
            (raw_fields.get(row_id_column) or "").strip()
            if row_id_column is not None
            else ""
        )
        if not source_row_id:
            source_row_id = f"row-{row_number}"
        accepted_rows.append(
            TmtReporterObservation(
                source_row_id=source_row_id,
                multiplex_group=multiplex_group,
                modified_peptide=modified_peptide,
                canonical_peptide=canonical_peptide,
                protein_refs=_parse_protein_refs(
                    raw_fields.get(protein_refs_column),
                    separator=active_mapping.protein_separator,
                )
                if protein_refs_column is not None
                else (),
                isolation_interference_fraction=isolation_interference_fraction,
                channel_intensities=tuple(reporter_values),
            )
        )

    summary = TmtReporterImportSummary(
        total_rows=max(len(lines) - 1, 0),
        accepted_row_count=len(accepted_rows),
        rejected_row_count=len(rejected_rows),
        multiplex_group_count=len({row.multiplex_group for row in accepted_rows}),
        reporter_channel_count=len(resolved_channels),
    )
    return TmtReporterImportReport(
        source_kind=source_kind,
        column_mapping=active_mapping,
        channel_columns=resolved_channels,
        accepted_rows=tuple(accepted_rows),
        rejected_rows=tuple(rejected_rows),
        summary=summary,
        note=(
            "tmt reporter-ion import preserves one governed peptide row with multiplex-group identity, optional isolation interference, and explicit per-channel intensities"
        ),
    )


def _resolve_column_name(
    *,
    explicit: str | None,
    source_kind: TmtSearchResultSourceKind,
    target: str,
) -> str | None:
    if explicit is not None:
        return explicit
    if source_kind is TmtSearchResultSourceKind.MAXQUANT:
        defaults = {
            "peptide": "Modified sequence",
            "protein_refs": "Leading proteins",
            "multiplex_group": "Experiment",
            "isolation_interference": "Isolation interference [%]",
            "source_row_id": "id",
        }
        return defaults.get(target)
    if source_kind is TmtSearchResultSourceKind.FRAGPIPE:
        defaults = {
            "peptide": "Modified Peptide",
            "protein_refs": "Protein",
            "multiplex_group": "Spectrum File",
            "isolation_interference": "Isolation Interference",
            "source_row_id": "Spectrum",
        }
        return defaults.get(target)
    generic_defaults = {
        "peptide": "modified_peptide",
        "protein_refs": "proteins",
        "multiplex_group": "multiplex_group",
        "isolation_interference": "isolation_interference",
        "source_row_id": "source_row_id",
    }
    return generic_defaults.get(target)


def _resolve_reporter_channel_columns(
    header: tuple[str, ...],
    *,
    source_kind: TmtSearchResultSourceKind,
    explicit: tuple[TmtReporterChannelColumn, ...],
) -> tuple[TmtReporterChannelColumn, ...]:
    resolved: dict[str, TmtReporterChannelColumn] = {
        entry.multiplex_channel: entry for entry in explicit
    }
    if source_kind is TmtSearchResultSourceKind.MAXQUANT:
        pattern = _MAXQUANT_REPORTER_RE
    elif source_kind is TmtSearchResultSourceKind.FRAGPIPE:
        pattern = _FRAGPIPE_REPORTER_RE
    else:
        pattern = _GENERIC_REPORTER_RE
    for column_name in header:
        matched = pattern.match(column_name)
        if matched is None:
            continue
        multiplex_channel = matched.group("channel").strip()
        resolved.setdefault(
            multiplex_channel,
            TmtReporterChannelColumn(
                multiplex_channel=multiplex_channel,
                column_name=column_name,
            ),
        )
    if not resolved:
        raise ValueError(
            "reporter-ion input does not expose any resolvable TMT reporter-channel columns"
        )
    return tuple(
        sorted(
            resolved.values(),
            key=lambda entry: entry.multiplex_channel,
        )
    )


def _parse_protein_refs(raw_value: str | None, *, separator: str) -> tuple[str, ...]:
    if raw_value in (None, ""):
        return ()
    refs = tuple(
        token.strip() for token in str(raw_value).split(separator) if token.strip()
    )
    return tuple(dict.fromkeys(refs))


def _parse_interference_fraction(raw_value: str) -> float:
    value = float(raw_value)
    if value < 0.0:
        raise ValueError("isolation interference must not be negative")
    if value > 1.0:
        if value <= 100.0:
            return value / 100.0
        raise ValueError("isolation interference above 100% is invalid")
    return value
