# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Study metadata and lab handoff surfaces for iteration 08."""

from __future__ import annotations

import csv
from pathlib import Path
import re

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
    multiplex_channel: str | None = None
    spectra_file: str | None = None


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


class ExperimentalDesignValidationIssue(JsonModel):
    """One deterministic experimental design validation issue."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    sample_id: str | None = None
    condition_id: str | None = None


class ExperimentalDesignValidationReport(JsonModel):
    """Validation report for study metadata experimental design entries."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    issues: tuple[ExperimentalDesignValidationIssue, ...] = Field(default_factory=tuple)


class FractionationRecord(JsonModel):
    """One fractionation entry connecting sample metadata and evidence aggregation."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    fraction_id: str = Field(..., min_length=1)
    fraction_number: int = Field(..., ge=1)
    method: str = Field(..., min_length=1)
    pooled: bool = False
    peptide_evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    protein_evidence_ids: tuple[str, ...] = Field(default_factory=tuple)


class FractionationAggregationReport(JsonModel):
    """Fractionation summary and aggregation links to peptide/protein evidence."""

    model_config = ConfigDict(extra="forbid")

    fraction_count: int = Field(..., ge=0)
    pooled_fraction_count: int = Field(..., ge=0)
    methods: tuple[str, ...] = Field(default_factory=tuple)
    peptide_evidence_count: int = Field(..., ge=0)
    protein_evidence_count: int = Field(..., ge=0)
    records: tuple[FractionationRecord, ...] = Field(default_factory=tuple)


_FRACTION_RE = re.compile(r"^F[1-9][0-9]*$")
_CHANNEL_RE = re.compile(r"^(12[6-9]|13[01])[NC]?$")


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
                    multiplex_channel=raw_fields.get("multiplex_channel", "").strip()
                    or None,
                    spectra_file=raw_fields.get("spectra_file", "").strip() or None,
                )
            )
    return DesignTableParseReport(
        total_rows=len(accepted) + len(rejected),
        accepted_records=tuple(accepted),
        rejected_rows=tuple(rejected),
    )


def validate_experimental_design_records(
    records: tuple[StudyMetadataRecord, ...],
    *,
    expected_spectra_files: tuple[str, ...] = (),
) -> ExperimentalDesignValidationReport:
    """Reject inconsistent experimental design entries with deterministic issue reports."""
    issues: list[ExperimentalDesignValidationIssue] = []
    seen_samples: set[str] = set()
    condition_counts: dict[str, int] = {}
    expected_files = set(expected_spectra_files)
    for record in records:
        if record.sample_id in seen_samples:
            issues.append(
                ExperimentalDesignValidationIssue(
                    code="duplicate_sample_id",
                    message="sample_id appears more than once in the design table",
                    sample_id=record.sample_id,
                    condition_id=record.condition_id,
                )
            )
        else:
            seen_samples.add(record.sample_id)
        condition_counts[record.condition_id] = (
            condition_counts.get(record.condition_id, 0) + 1
        )
        if not _FRACTION_RE.match(record.fraction_id):
            issues.append(
                ExperimentalDesignValidationIssue(
                    code="invalid_fraction_id",
                    message="fraction_id must match F<number> pattern such as F1",
                    sample_id=record.sample_id,
                    condition_id=record.condition_id,
                )
            )
        if record.multiplex_channel and not _CHANNEL_RE.match(record.multiplex_channel):
            issues.append(
                ExperimentalDesignValidationIssue(
                    code="invalid_multiplex_channel",
                    message="multiplex_channel is not a recognized reporter-channel token",
                    sample_id=record.sample_id,
                    condition_id=record.condition_id,
                )
            )
        if expected_files and (
            record.spectra_file is None or record.spectra_file not in expected_files
        ):
            issues.append(
                ExperimentalDesignValidationIssue(
                    code="inconsistent_spectra_file",
                    message="spectra_file is missing from expected file manifests",
                    sample_id=record.sample_id,
                    condition_id=record.condition_id,
                )
            )
    for condition_id, count in sorted(condition_counts.items()):
        if count < 2:
            issues.append(
                ExperimentalDesignValidationIssue(
                    code="missing_replicates",
                    message="condition has fewer than two replicate samples",
                    condition_id=condition_id,
                )
            )
    return ExperimentalDesignValidationReport(valid=not issues, issues=tuple(issues))


def build_fractionation_aggregation_report(
    records: tuple[FractionationRecord, ...],
) -> FractionationAggregationReport:
    """Build deterministic fractionation summary linked to peptide/protein evidence."""
    return FractionationAggregationReport(
        fraction_count=len(records),
        pooled_fraction_count=sum(1 for record in records if record.pooled),
        methods=tuple(sorted({record.method for record in records})),
        peptide_evidence_count=len(
            {token for record in records for token in record.peptide_evidence_ids}
        ),
        protein_evidence_count=len(
            {token for record in records for token in record.protein_evidence_ids}
        ),
        records=records,
    )
