# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Reference-case validation for target-decoy FDR behavior."""

from __future__ import annotations

import csv
import io
from typing import Any

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    PsmRecord,
)
from bijux_proteomics.identification.fdr.psm_target_decoy_fdr import (
    build_psm_target_decoy_fdr_report,
)
from bijux_proteomics_foundation import JsonModel


class TargetDecoyReferenceExpectation(JsonModel):
    """One expected ranked FDR row inside a target-decoy reference case."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(..., ge=1)
    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    cumulative_targets: int = Field(..., ge=0)
    cumulative_decoys: int = Field(..., ge=0)
    fdr: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    accepted: bool


class TargetDecoyReferenceCase(JsonModel):
    """One curated target-decoy FDR reference case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    score_orientation: str = Field(
        default="higher_better",
        pattern="^(higher_better|lower_better)$",
    )
    tie_handling: str = Field(
        default="score_group",
        pattern="^(score_group|stable_record_order)$",
    )
    threshold: float | None = Field(default=None, ge=0.0)
    records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    expected_entries: tuple[TargetDecoyReferenceExpectation, ...] = Field(
        default_factory=tuple
    )


class TargetDecoyReferenceValidationEntry(JsonModel):
    """Validation result for one expected ranked FDR row."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    rank: int = Field(..., ge=1)
    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    passed: bool
    mismatches: tuple[str, ...] = Field(default_factory=tuple)
    expected_cumulative_targets: int = Field(..., ge=0)
    observed_cumulative_targets: int | None = Field(default=None, ge=0)
    expected_cumulative_decoys: int = Field(..., ge=0)
    observed_cumulative_decoys: int | None = Field(default=None, ge=0)
    expected_fdr: float = Field(..., ge=0.0)
    observed_fdr: float | None = Field(default=None, ge=0.0)
    expected_q_value: float = Field(..., ge=0.0)
    observed_q_value: float | None = Field(default=None, ge=0.0)
    expected_accepted: bool
    observed_accepted: bool | None = None


class TargetDecoyReferenceCaseReport(JsonModel):
    """Validation report for one curated target-decoy FDR case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    tie_handling: str = Field(..., pattern="^(score_group|stable_record_order)$")
    threshold: float | None = Field(default=None, ge=0.0)
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)
    q_values_monotonic: bool
    expected_entry_count: int = Field(..., ge=0)
    observed_entry_count: int = Field(..., ge=0)
    failed_entry_count: int = Field(..., ge=0)
    valid: bool
    case_issues: tuple[str, ...] = Field(default_factory=tuple)
    entries: tuple[TargetDecoyReferenceValidationEntry, ...] = Field(
        default_factory=tuple
    )


class TargetDecoyReferenceValidationReport(JsonModel):
    """Validation report over curated target-decoy FDR reference cases."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    case_count: int = Field(..., ge=0)
    entry_count: int = Field(..., ge=0)
    failed_entry_count: int = Field(..., ge=0)
    cases: tuple[TargetDecoyReferenceCaseReport, ...] = Field(default_factory=tuple)


def _floats_match(expected: float, observed: float | None, *, tolerance: float) -> bool:
    return observed is not None and abs(expected - observed) <= tolerance


def _build_reference_validation_entry(
    case: TargetDecoyReferenceCase,
    expected: TargetDecoyReferenceExpectation,
    observed: Any | None,
) -> TargetDecoyReferenceValidationEntry:
    mismatches: list[str] = []
    observed_spectrum_id = None if observed is None else observed.psm.spectrum_id
    observed_canonical_peptide = (
        None if observed is None else observed.psm.canonical_peptide
    )
    if observed_spectrum_id != expected.spectrum_id:
        mismatches.append("spectrum_id")
    if observed_canonical_peptide != expected.canonical_peptide:
        mismatches.append("canonical_peptide")
    if observed is None or observed.cumulative_targets != expected.cumulative_targets:
        mismatches.append("cumulative_targets")
    if observed is None or observed.cumulative_decoys != expected.cumulative_decoys:
        mismatches.append("cumulative_decoys")
    if not _floats_match(
        expected.fdr, None if observed is None else observed.raw_fdr, tolerance=1e-9
    ):
        mismatches.append("fdr")
    if not _floats_match(
        expected.q_value,
        None if observed is None else observed.q_value,
        tolerance=1e-9,
    ):
        mismatches.append("q_value")
    if observed is None or observed.accepted is not expected.accepted:
        mismatches.append("accepted")

    return TargetDecoyReferenceValidationEntry(
        case_id=case.case_id,
        rank=expected.rank,
        spectrum_id=expected.spectrum_id,
        canonical_peptide=expected.canonical_peptide,
        passed=not mismatches,
        mismatches=tuple(mismatches),
        expected_cumulative_targets=expected.cumulative_targets,
        observed_cumulative_targets=None
        if observed is None
        else observed.cumulative_targets,
        expected_cumulative_decoys=expected.cumulative_decoys,
        observed_cumulative_decoys=None
        if observed is None
        else observed.cumulative_decoys,
        expected_fdr=expected.fdr,
        observed_fdr=None if observed is None else observed.raw_fdr,
        expected_q_value=expected.q_value,
        observed_q_value=None if observed is None else observed.q_value,
        expected_accepted=expected.accepted,
        observed_accepted=None if observed is None else observed.accepted,
    )


def build_target_decoy_reference_validation_report(
    cases: tuple[TargetDecoyReferenceCase, ...],
) -> TargetDecoyReferenceValidationReport:
    """Validate curated target-decoy reference cases against the owned FDR engine."""
    case_reports: list[TargetDecoyReferenceCaseReport] = []
    for case in cases:
        fdr_report = build_psm_target_decoy_fdr_report(
            case.records,
            threshold=case.threshold,
            score_orientation=case.score_orientation,
            tie_handling=case.tie_handling,
        )
        annotated = tuple(fdr_report.entries)
        entries = tuple(
            _build_reference_validation_entry(
                case,
                expected,
                annotated[expected.rank - 1]
                if expected.rank <= len(annotated)
                else None,
            )
            for expected in case.expected_entries
        )
        q_values = tuple(entry.q_value for entry in annotated)
        q_values_monotonic = all(
            previous <= current
            for previous, current in zip(q_values, q_values[1:], strict=False)
        )
        case_issues: list[str] = []
        if len(annotated) != len(case.expected_entries):
            case_issues.append(
                "observed entry count does not match the curated expectation"
            )
        if not q_values_monotonic:
            case_issues.append("observed q-values are not monotonic")
        failed_entry_count = sum(1 for entry in entries if not entry.passed)
        case_reports.append(
            TargetDecoyReferenceCaseReport(
                case_id=case.case_id,
                score_orientation=case.score_orientation,
                tie_handling=case.tie_handling,
                threshold=case.threshold,
                reproducibility_hash=fdr_report.reproducibility_hash,
                q_values_monotonic=q_values_monotonic,
                expected_entry_count=len(case.expected_entries),
                observed_entry_count=len(annotated),
                failed_entry_count=failed_entry_count,
                valid=failed_entry_count == 0 and not case_issues,
                case_issues=tuple(case_issues),
                entries=entries,
            )
        )
    return TargetDecoyReferenceValidationReport(
        valid=all(case.valid for case in case_reports),
        case_count=len(case_reports),
        entry_count=sum(len(case.entries) for case in case_reports),
        failed_entry_count=sum(case.failed_entry_count for case in case_reports),
        cases=tuple(case_reports),
    )


def render_target_decoy_reference_summary_tsv(
    report: TargetDecoyReferenceValidationReport,
) -> str:
    """Render one summary row per validated target-decoy reference case."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "case_id",
            "score_orientation",
            "tie_handling",
            "threshold",
            "valid",
            "q_values_monotonic",
            "expected_entry_count",
            "observed_entry_count",
            "failed_entry_count",
            "case_issues",
            "reproducibility_hash",
        )
    )
    for case in report.cases:
        writer.writerow(
            (
                case.case_id,
                case.score_orientation,
                case.tie_handling,
                "" if case.threshold is None else case.threshold,
                str(case.valid).lower(),
                str(case.q_values_monotonic).lower(),
                case.expected_entry_count,
                case.observed_entry_count,
                case.failed_entry_count,
                ";".join(case.case_issues),
                case.reproducibility_hash,
            )
        )
    return buffer.getvalue()


def render_target_decoy_reference_entries_tsv(
    report: TargetDecoyReferenceValidationReport,
) -> str:
    """Render one row per expected ranked target-decoy reference entry."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "case_id",
            "rank",
            "spectrum_id",
            "canonical_peptide",
            "passed",
            "expected_cumulative_targets",
            "observed_cumulative_targets",
            "expected_cumulative_decoys",
            "observed_cumulative_decoys",
            "expected_fdr",
            "observed_fdr",
            "expected_q_value",
            "observed_q_value",
            "expected_accepted",
            "observed_accepted",
            "mismatches",
        )
    )
    for case in report.cases:
        for entry in case.entries:
            writer.writerow(
                (
                    entry.case_id,
                    entry.rank,
                    entry.spectrum_id,
                    entry.canonical_peptide,
                    str(entry.passed).lower(),
                    entry.expected_cumulative_targets,
                    ""
                    if entry.observed_cumulative_targets is None
                    else entry.observed_cumulative_targets,
                    entry.expected_cumulative_decoys,
                    ""
                    if entry.observed_cumulative_decoys is None
                    else entry.observed_cumulative_decoys,
                    entry.expected_fdr,
                    "" if entry.observed_fdr is None else entry.observed_fdr,
                    entry.expected_q_value,
                    "" if entry.observed_q_value is None else entry.observed_q_value,
                    str(entry.expected_accepted).lower(),
                    ""
                    if entry.observed_accepted is None
                    else str(entry.observed_accepted).lower(),
                    ";".join(entry.mismatches),
                )
            )
    return buffer.getvalue()
