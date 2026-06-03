# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned experiment-design validity engine for differential-analysis entrypoints."""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
from io import StringIO
import re
from typing import cast

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.study.design.design_diagnostics import (
    detect_batch_condition_confounding,
)
from bijux_proteomics.study.design.experiment_design import (
    ExperimentDesign,
    coerce_experiment_design,
)
from bijux_proteomics_foundation import JsonModel

_PREFIXED_NUMERIC_LABEL_RE = re.compile(
    r"^(?P<prefix>.*?)(?P<number>[+-]?\d+(?:\.\d+)?)$"
)


class ExperimentDesignValidityIssue(JsonModel):
    """One blocking design-validity issue over an owned experiment design."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    field: str | None = None
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    run_ids: tuple[str, ...] = Field(default_factory=tuple)
    condition_ids: tuple[str, ...] = Field(default_factory=tuple)
    batch_ids: tuple[str, ...] = Field(default_factory=tuple)
    pair_ids: tuple[str, ...] = Field(default_factory=tuple)
    channel_ids: tuple[str, ...] = Field(default_factory=tuple)
    plex_id: str | None = None


class ExperimentDesignValiditySummary(JsonModel):
    """Compact summary over experiment-design validity checks."""

    model_config = ConfigDict(extra="forbid")

    issue_count: int = Field(..., ge=0)
    sample_identity_conflict_count: int = Field(..., ge=0)
    duplicate_run_id_count: int = Field(..., ge=0)
    invalid_contrast_count: int = Field(..., ge=0)
    confounded_batch_condition_count: int = Field(..., ge=0)
    broken_pair_count: int = Field(..., ge=0)
    missing_channel_count: int = Field(..., ge=0)
    missing_timepoint_order_count: int = Field(..., ge=0)
    valid_for_differential_analysis: bool


class ExperimentDesignValidityReport(JsonModel):
    """Blocking validity review over one experiment design."""

    model_config = ConfigDict(extra="forbid")

    experiment_design: ExperimentDesign
    selected_conditions: tuple[str, ...] = Field(default_factory=tuple)
    batch_field: str | None = None
    pairing_field: str | None = None
    timepoint_field: str | None = None
    issues: tuple[ExperimentDesignValidityIssue, ...] = Field(default_factory=tuple)
    summary: ExperimentDesignValiditySummary
    note: str = Field(..., min_length=1)


def build_experiment_design_validity_report(
    design: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str | None = None,
    pairing_field: str | None = None,
    require_complete_plex_channels: bool = False,
    timepoint_field: str | None = None,
    ordered_timepoints: tuple[str, ...] = (),
) -> ExperimentDesignValidityReport:
    """Detect blocking design problems before differential statistics run."""

    experiment_design = coerce_experiment_design(design)
    issues: list[ExperimentDesignValidityIssue] = []
    selected_conditions = _selected_conditions(
        experiment_design,
        condition_a=condition_a,
        condition_b=condition_b,
        issues=issues,
    )
    issues.extend(_sample_identity_conflict_issues(experiment_design))
    issues.extend(_duplicate_run_issues(experiment_design))
    issues.extend(
        _confounded_batch_condition_issues(
            experiment_design,
            selected_conditions=selected_conditions,
            batch_field=batch_field,
        )
    )
    issues.extend(
        _broken_pair_issues(
            experiment_design,
            selected_conditions=selected_conditions,
            pairing_field=pairing_field,
        )
    )
    issues.extend(
        _missing_channel_issues(
            experiment_design,
            require_complete_plex_channels=require_complete_plex_channels,
        )
    )
    issues.extend(
        _timepoint_order_issues(
            experiment_design,
            timepoint_field=timepoint_field,
            ordered_timepoints=ordered_timepoints,
        )
    )
    issue_records = tuple(issues)
    return ExperimentDesignValidityReport(
        experiment_design=experiment_design,
        selected_conditions=selected_conditions,
        batch_field=batch_field,
        pairing_field=pairing_field,
        timepoint_field=timepoint_field,
        issues=issue_records,
        summary=ExperimentDesignValiditySummary(
            issue_count=len(issue_records),
            sample_identity_conflict_count=sum(
                1
                for issue in issue_records
                if issue.code == "conflicting_sample_identity"
            ),
            duplicate_run_id_count=sum(
                1 for issue in issue_records if issue.code == "duplicate_run_id"
            ),
            invalid_contrast_count=sum(
                1
                for issue in issue_records
                if issue.code.startswith("invalid_contrast_")
            ),
            confounded_batch_condition_count=sum(
                1
                for issue in issue_records
                if issue.code == "confounded_batch_condition"
            ),
            broken_pair_count=sum(
                1 for issue in issue_records if issue.code == "broken_pair"
            ),
            missing_channel_count=sum(
                1
                for issue in issue_records
                if issue.code == "missing_multiplex_channels"
            ),
            missing_timepoint_order_count=sum(
                1 for issue in issue_records if issue.code == "missing_timepoint_order"
            ),
            valid_for_differential_analysis=not issue_records,
        ),
        note=(
            "design validity review blocks invalid contrasts, confounded batches, broken "
            "pairs, missing multiplex channels, unordered timepoints, conflicting "
            "biological sample identity, and invalid repeated run identifiers before "
            "differential statistics run"
        ),
    )


def require_valid_experiment_design_for_differential_analysis(
    design: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str | None = None,
    pairing_field: str | None = None,
    require_complete_plex_channels: bool = False,
    timepoint_field: str | None = None,
    ordered_timepoints: tuple[str, ...] = (),
) -> ExperimentDesign:
    """Return one experiment design or raise before any differential statistics run."""

    report = build_experiment_design_validity_report(
        design,
        condition_a=condition_a,
        condition_b=condition_b,
        batch_field=batch_field,
        pairing_field=pairing_field,
        require_complete_plex_channels=require_complete_plex_channels,
        timepoint_field=timepoint_field,
        ordered_timepoints=ordered_timepoints,
    )
    if report.summary.valid_for_differential_analysis:
        return report.experiment_design
    issue_preview = "; ".join(
        f"{issue.code}: {issue.message}" for issue in report.issues[:3]
    )
    if len(report.issues) > 3:
        issue_preview += f"; plus {len(report.issues) - 3} more issue(s)"
    raise ValueError(
        "experiment design is invalid for differential analysis: " + issue_preview
    )


def render_experiment_design_validity_tsv(
    report: ExperimentDesignValidityReport,
) -> str:
    """Render blocking design-validity issues as a stable TSV ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "code",
            "message",
            "field",
            "sample_ids",
            "run_ids",
            "condition_ids",
            "batch_ids",
            "pair_ids",
            "channel_ids",
            "plex_id",
        ]
    )
    for issue in report.issues:
        writer.writerow(
            [
                issue.code,
                issue.message,
                issue.field or "",
                ";".join(issue.sample_ids),
                ";".join(issue.run_ids),
                ";".join(issue.condition_ids),
                ";".join(issue.batch_ids),
                ";".join(issue.pair_ids),
                ";".join(issue.channel_ids),
                issue.plex_id or "",
            ]
        )
    return buffer.getvalue()


def _selected_conditions(
    experiment_design: ExperimentDesign,
    *,
    condition_a: str | None,
    condition_b: str | None,
    issues: list[ExperimentDesignValidityIssue],
) -> tuple[str, ...]:
    if bool(condition_a) ^ bool(condition_b):
        incomplete_conditions = tuple(
            cast(str, condition)
            for condition in (condition_a, condition_b)
            if condition not in (None, "")
        )
        issues.append(
            ExperimentDesignValidityIssue(
                code="invalid_contrast_incomplete_pair",
                message="both contrast conditions are required together",
                condition_ids=incomplete_conditions,
            )
        )
        return ()
    if condition_a is not None and condition_b is not None:
        if condition_a == condition_b:
            issues.append(
                ExperimentDesignValidityIssue(
                    code="invalid_contrast_same_condition",
                    message="contrast conditions must differ",
                    condition_ids=(condition_a, condition_b),
                )
            )
            return ()
        missing = tuple(
            condition
            for condition in (condition_a, condition_b)
            if condition not in experiment_design.conditions
        )
        if missing:
            issues.append(
                ExperimentDesignValidityIssue(
                    code="invalid_contrast_unknown_condition",
                    message=("contrast conditions must exist in the experiment design"),
                    condition_ids=(condition_a, condition_b),
                )
            )
            return ()
        return (condition_a, condition_b)
    if len(experiment_design.conditions) < 2:
        issues.append(
            ExperimentDesignValidityIssue(
                code="invalid_contrast_insufficient_conditions",
                message="differential analysis requires at least two conditions",
                condition_ids=experiment_design.conditions,
            )
        )
        return ()
    return experiment_design.conditions


def _sample_identity_conflict_issues(
    experiment_design: ExperimentDesign,
) -> tuple[ExperimentDesignValidityIssue, ...]:
    entries_by_sample: dict[str, list[ExperimentalDesignEntry]] = defaultdict(list)
    for entry in experiment_design.entries:
        entries_by_sample[entry.sample_id].append(entry)
    issues: list[ExperimentDesignValidityIssue] = []
    for sample_id, sample_entries in sorted(entries_by_sample.items()):
        if len(sample_entries) <= 1:
            continue
        for field in _SAMPLE_IDENTITY_FIELDS:
            values = {
                value
                for value in (
                    _resolve_entry_value(entry, field) for entry in sample_entries
                )
                if value not in (None, "")
            }
            if len(values) <= 1:
                continue
            issues.append(
                ExperimentDesignValidityIssue(
                    code="conflicting_sample_identity",
                    message=(
                        "one biological sample id maps to conflicting study identity "
                        f"values for {field!r} across multiple runs"
                    ),
                    field=field,
                    sample_ids=(sample_id,),
                    run_ids=tuple(
                        sorted(entry.spectra_file for entry in sample_entries)
                    ),
                )
            )
    return tuple(issues)


def _duplicate_run_issues(
    experiment_design: ExperimentDesign,
) -> tuple[ExperimentDesignValidityIssue, ...]:
    entries_by_run: dict[str, list[ExperimentalDesignEntry]] = defaultdict(list)
    for entry in experiment_design.entries:
        entries_by_run[entry.spectra_file].append(entry)
    issues: list[ExperimentDesignValidityIssue] = []
    for run_id, run_entries in sorted(entries_by_run.items()):
        if len(run_entries) <= 1:
            continue
        if _is_valid_multiplex_run_layout(tuple(run_entries)):
            continue
        issues.append(
            ExperimentDesignValidityIssue(
                code="duplicate_run_id",
                message=(
                    "differential analysis requires unique LC-MS run identifiers "
                    "unless repeated rows are one valid multiplex run layout"
                ),
                field="spectra_file",
                sample_ids=tuple(sorted(entry.sample_id for entry in run_entries)),
                run_ids=(run_id,),
            )
        )
    return tuple(issues)


def _confounded_batch_condition_issues(
    experiment_design: ExperimentDesign,
    *,
    selected_conditions: tuple[str, ...],
    batch_field: str | None,
) -> tuple[ExperimentDesignValidityIssue, ...]:
    if batch_field in (None, "") or len(selected_conditions) < 2:
        return ()
    resolved_batch_field = cast(str, batch_field)
    report = detect_batch_condition_confounding(
        experiment_design,
        batch_field=resolved_batch_field,
        selected_conditions=selected_conditions,
    )
    if not report.is_confounded:
        return ()
    batch_ids = tuple(
        sorted(
            {term.split(":", 1)[1] for term in report.confounded_terms if ":" in term}
        )
    )
    return (
        ExperimentDesignValidityIssue(
            code="confounded_batch_condition",
            message=(
                "batch assignments are confounded with condition labels for the "
                "selected differential analysis"
            ),
            field=resolved_batch_field,
            condition_ids=selected_conditions,
            batch_ids=batch_ids,
        ),
    )


def _broken_pair_issues(
    experiment_design: ExperimentDesign,
    *,
    selected_conditions: tuple[str, ...],
    pairing_field: str | None,
) -> tuple[ExperimentDesignValidityIssue, ...]:
    if pairing_field in (None, "") or len(selected_conditions) != 2:
        return ()
    resolved_pairing_field = cast(str, pairing_field)
    relevant_entries = tuple(
        entry
        for entry in experiment_design.entries
        if entry.condition in selected_conditions
    )
    if not relevant_entries:
        return ()
    entries_by_pair: dict[str, list[ExperimentalDesignEntry]] = defaultdict(list)
    missing_pair_samples = tuple(
        sorted(
            entry.sample_id
            for entry in relevant_entries
            if _resolve_entry_value(entry, resolved_pairing_field) in (None, "")
        )
    )
    for entry in relevant_entries:
        pair_value = _resolve_entry_value(entry, resolved_pairing_field)
        if pair_value in (None, ""):
            continue
        entries_by_pair[str(pair_value)].append(entry)
    issues: list[ExperimentDesignValidityIssue] = []
    if missing_pair_samples:
        issues.append(
            ExperimentDesignValidityIssue(
                code="broken_pair",
                message="paired differential analysis requires a pair identifier for every selected sample",
                field=resolved_pairing_field,
                sample_ids=missing_pair_samples,
                condition_ids=selected_conditions,
            )
        )
    for pair_id, pair_entries in sorted(entries_by_pair.items()):
        counts = Counter(entry.condition for entry in pair_entries)
        if any(counts.get(condition, 0) != 1 for condition in selected_conditions):
            issues.append(
                ExperimentDesignValidityIssue(
                    code="broken_pair",
                    message=(
                        "paired differential analysis requires exactly one sample per "
                        "selected condition in each pair"
                    ),
                    field=resolved_pairing_field,
                    sample_ids=tuple(sorted(entry.sample_id for entry in pair_entries)),
                    condition_ids=selected_conditions,
                    pair_ids=(pair_id,),
                )
            )
    return tuple(issues)


def _missing_channel_issues(
    experiment_design: ExperimentDesign,
    *,
    require_complete_plex_channels: bool,
) -> tuple[ExperimentDesignValidityIssue, ...]:
    if not require_complete_plex_channels or not experiment_design.plexes:
        return ()
    expected_channels = {
        channel.channel_id
        for plex in experiment_design.plexes
        for channel in plex.channels
        if channel.channel_id
    }
    issues: list[ExperimentDesignValidityIssue] = []
    for plex in experiment_design.plexes:
        observed = {
            channel.channel_id for channel in plex.channels if channel.channel_id
        }
        missing = tuple(sorted(expected_channels - observed))
        if missing:
            issues.append(
                ExperimentDesignValidityIssue(
                    code="missing_multiplex_channels",
                    message=(
                        "multiplex differential analysis requires every plex to carry "
                        "the full declared channel set"
                    ),
                    field="multiplex_channel",
                    run_ids=plex.run_ids,
                    channel_ids=missing,
                    plex_id=plex.plex_id,
                )
            )
    return tuple(issues)


def _timepoint_order_issues(
    experiment_design: ExperimentDesign,
    *,
    timepoint_field: str | None,
    ordered_timepoints: tuple[str, ...],
) -> tuple[ExperimentDesignValidityIssue, ...]:
    if timepoint_field in (None, ""):
        return ()
    resolved_timepoint_field = cast(str, timepoint_field)
    labels = tuple(
        sorted(
            {
                str(value)
                for value in (
                    _resolve_entry_value(entry, resolved_timepoint_field)
                    for entry in experiment_design.entries
                )
                if value not in (None, "")
            }
        )
    )
    if len(labels) < 2:
        return ()
    if ordered_timepoints:
        declared_order = tuple(ordered_timepoints)
        if len(declared_order) != len(set(declared_order)) or set(
            declared_order
        ) != set(labels):
            return (
                ExperimentDesignValidityIssue(
                    code="missing_timepoint_order",
                    message=(
                        "declared timepoint order must contain each observed timepoint "
                        "label exactly once"
                    ),
                    field=resolved_timepoint_field,
                    condition_ids=labels,
                ),
            )
        return ()
    if _infer_numeric_timepoint_positions(labels) is not None:
        return ()
    return (
        ExperimentDesignValidityIssue(
            code="missing_timepoint_order",
            message=(
                "unordered timepoint labels require an explicit declared order before "
                "time-course statistics run"
            ),
            field=resolved_timepoint_field,
            condition_ids=labels,
        ),
    )


def _resolve_entry_value(entry: ExperimentalDesignEntry, field: str) -> str | None:
    direct_values: dict[str, str | None] = {
        "sample_id": cast(str, entry.sample_id),
        "cohort": cast(str | None, entry.cohort),
        "condition": cast(str, entry.condition),
        "batch": cast(str | None, entry.batch),
        "instrument": cast(str | None, entry.instrument),
        "search_engine": cast(str | None, entry.search_engine),
        "pair_id": cast(str | None, entry.pair_id),
        "spectra_file": cast(str, entry.spectra_file),
        "technical_replicate_id": cast(str | None, entry.technical_replicate_id),
        "multiplex_group": cast(str | None, entry.multiplex_group),
        "multiplex_channel": cast(str | None, entry.multiplex_channel),
        "sample_role": cast(str, entry.sample_role.value),
    }
    metadata = cast(dict[str, str], entry.metadata)
    if field == "tissue_or_cell_type":
        return (
            metadata.get("tissue_or_cell_type")
            or metadata.get("tissue")
            or metadata.get("cell_type")
        )
    if field in direct_values:
        return direct_values[field]
    return metadata.get(field)


def _infer_numeric_timepoint_positions(
    labels: tuple[str, ...],
) -> dict[str, float] | None:
    direct_numeric: dict[str, float] = {}
    try:
        for label in labels:
            direct_numeric[label] = float(label)
    except ValueError:
        direct_numeric = {}
    if direct_numeric:
        return direct_numeric
    parsed = []
    for label in labels:
        match = _PREFIXED_NUMERIC_LABEL_RE.match(label)
        if match is None:
            return None
        parsed.append((label, match.group("prefix"), float(match.group("number"))))
    prefixes = {prefix for _, prefix, _ in parsed}
    if len(prefixes) != 1:
        return None
    return {label: number for label, _prefix, number in parsed}


def _is_valid_multiplex_run_layout(
    run_entries: tuple[ExperimentalDesignEntry, ...],
) -> bool:
    plex_ids = {entry.multiplex_group for entry in run_entries if entry.multiplex_group}
    if len(plex_ids) != 1:
        return False
    channel_ids = tuple(entry.multiplex_channel for entry in run_entries)
    if any(channel_id in (None, "") for channel_id in channel_ids):
        return False
    return len(set(channel_ids)) == len(channel_ids)


_SAMPLE_IDENTITY_FIELDS = (
    "condition",
    "cohort",
    "pair_id",
    "sample_role",
    "timepoint",
    "species",
    "tissue_or_cell_type",
    "perturbation",
)


__all__ = [
    "ExperimentDesignValidityIssue",
    "ExperimentDesignValidityReport",
    "ExperimentDesignValiditySummary",
    "build_experiment_design_validity_report",
    "render_experiment_design_validity_tsv",
    "require_valid_experiment_design_for_differential_analysis",
]
