# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Study metadata and lab handoff surfaces for iteration 08."""

from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class StudyMetadataRecord(JsonModel):
    """One normalized study metadata row connecting sample and run context."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    cohort_id: str = Field(..., min_length=1)
    condition_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    replicate_id: str = Field(..., min_length=1)
    fraction_id: str = Field(..., min_length=1)
    instrument_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    batch_id: str = Field(..., min_length=1)


class StudyMetadataModel(JsonModel):
    """Stable collection of normalized study metadata records."""

    model_config = ConfigDict(extra="forbid")

    records: tuple[StudyMetadataRecord, ...] = Field(default_factory=tuple)
    study_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    run_count: int = Field(..., ge=0)


class DesignTableParseIssue(JsonModel):
    """One issue while parsing a design table row."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class RejectedDesignTableRow(JsonModel):
    """One rejected design-table row."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[DesignTableParseIssue, ...] = Field(default_factory=tuple)


class DesignTableParseReport(JsonModel):
    """Stable parse report for study design TSV ingestion."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[StudyMetadataRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedDesignTableRow, ...] = Field(default_factory=tuple)


def build_study_metadata_model(
    records: tuple[StudyMetadataRecord, ...],
) -> StudyMetadataModel:
    """Build study metadata model with deterministic collection summaries."""
    return StudyMetadataModel(
        records=records,
        study_count=len({record.study_id for record in records}),
        sample_count=len({record.sample_id for record in records}),
        run_count=len({record.run_id for record in records}),
    )


def parse_study_design_table(path: Path) -> DesignTableParseReport:
    """Parse a study design TSV into normalized study metadata records."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("study design table must include a header row")
        required = (
            "study_id",
            "cohort_id",
            "condition_id",
            "sample_id",
            "replicate_id",
            "fraction_id",
            "instrument_id",
            "run_id",
            "batch_id",
        )
        for column in required:
            if column not in reader.fieldnames:
                raise ValueError(f"missing required design-table column {column!r}")
        accepted: list[StudyMetadataRecord] = []
        rejected: list[RejectedDesignTableRow] = []
        for row_number, row in enumerate(reader, start=2):
            raw_fields = {str(key): str(value or "") for key, value in row.items() if key}
            issues: list[DesignTableParseIssue] = []
            for column in required:
                if not raw_fields.get(column, "").strip():
                    issues.append(
                        DesignTableParseIssue(
                            row_number=row_number,
                            code=f"missing_{column}",
                            message=f"required column {column!r} is missing or blank",
                        )
                    )
            if issues:
                rejected.append(
                    RejectedDesignTableRow(
                        row_number=row_number,
                        raw_fields=raw_fields,
                        issues=tuple(issues),
                    )
                )
                continue
            accepted.append(
                StudyMetadataRecord(
                    study_id=raw_fields["study_id"].strip(),
                    cohort_id=raw_fields["cohort_id"].strip(),
                    condition_id=raw_fields["condition_id"].strip(),
                    sample_id=raw_fields["sample_id"].strip(),
                    replicate_id=raw_fields["replicate_id"].strip(),
                    fraction_id=raw_fields["fraction_id"].strip(),
                    instrument_id=raw_fields["instrument_id"].strip(),
                    run_id=raw_fields["run_id"].strip(),
                    batch_id=raw_fields["batch_id"].strip(),
                )
            )
    return DesignTableParseReport(
        total_rows=len(accepted) + len(rejected),
        accepted_records=tuple(accepted),
        rejected_rows=tuple(rejected),
    )
