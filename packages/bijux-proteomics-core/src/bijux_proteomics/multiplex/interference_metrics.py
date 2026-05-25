# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned TMT interference review over governed reporter-ion search outputs."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.multiplex.reporter_ion_import import TmtReporterImportReport
from bijux_proteomics.multiplex.reporter_matrix import (
    TmtReporterFeatureBundle,
    build_tmt_reporter_feature_bundle,
)
from bijux_proteomics.quantification import LabelBasedChannelRole
from bijux_proteomics_foundation import JsonModel


class TmtInterferencePolicy(JsonModel):
    """Policy for interference review over TMT search-result rows."""

    model_config = ConfigDict(extra="forbid")

    interference_fraction_threshold: float = Field(default=0.3, ge=0.0, le=1.0)


class TmtInterferenceObservationEntry(JsonModel):
    """One source-row/channel observation with explicit interference context."""

    model_config = ConfigDict(extra="forbid")

    source_row_id: str = Field(..., min_length=1)
    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    sample_role: str = Field(..., min_length=1)
    channel_role: LabelBasedChannelRole
    modified_peptide: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    reporter_intensity: float = Field(..., ge=0.0)
    isolation_interference_fraction: float | None = Field(
        default=None, ge=0.0, le=1.0
    )
    threshold_exceeded: bool
    note: str = Field(..., min_length=1)


class TmtInterferenceSummary(JsonModel):
    """Compact summary over one TMT interference review run."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group_count: int = Field(..., ge=0)
    observed_channel_row_count: int = Field(..., ge=0)
    missing_interference_count: int = Field(..., ge=0)
    threshold_exceeded_count: int = Field(..., ge=0)
    filtered_channel_row_count: int = Field(..., ge=0)
    channel_summary_count: int = Field(..., ge=0)


class TmtInterferenceChannelSummaryEntry(JsonModel):
    """One sample/channel summary over observed interference-bearing rows."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    sample_role: str = Field(..., min_length=1)
    channel_role: LabelBasedChannelRole
    observed_row_count: int = Field(..., ge=0)
    missing_interference_count: int = Field(..., ge=0)
    threshold_exceeded_count: int = Field(..., ge=0)
    mean_interference_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    max_interference_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    flagged: bool
    note: str = Field(..., min_length=1)


class TmtInterferenceReport(JsonModel):
    """Owned TMT interference review over governed search-result observations."""

    model_config = ConfigDict(extra="forbid")

    source_report: TmtReporterImportReport
    feature_bundle: TmtReporterFeatureBundle
    policy: TmtInterferencePolicy
    observations: tuple[TmtInterferenceObservationEntry, ...] = Field(
        default_factory=tuple
    )
    filtered_observations: tuple[TmtInterferenceObservationEntry, ...] = Field(
        default_factory=tuple
    )
    channel_summaries: tuple[TmtInterferenceChannelSummaryEntry, ...] = Field(
        default_factory=tuple
    )
    summary: TmtInterferenceSummary
    note: str = Field(..., min_length=1)


def build_tmt_interference_report(
    import_report: TmtReporterImportReport,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    policy: TmtInterferencePolicy | None = None,
) -> TmtInterferenceReport:
    """Build one interference review over TMT reporter observations."""

    active_policy = policy or TmtInterferencePolicy()
    feature_bundle = build_tmt_reporter_feature_bundle(
        import_report,
        design_entries=design_entries,
    )
    design_by_group_channel = {
        (entry.multiplex_group or "", entry.multiplex_channel or ""): entry
        for entry in feature_bundle.design_entries
        if entry.multiplex_group and entry.multiplex_channel
    }
    observations: list[TmtInterferenceObservationEntry] = []
    for row in import_report.accepted_rows:
        for channel in row.channel_intensities:
            if channel.intensity is None:
                continue
            design_entry = design_by_group_channel.get(
                (row.multiplex_group, channel.multiplex_channel)
            )
            if design_entry is None:
                continue
            fraction = row.isolation_interference_fraction
            threshold_exceeded = (
                fraction is not None
                and fraction >= active_policy.interference_fraction_threshold
            )
            observations.append(
                TmtInterferenceObservationEntry(
                    source_row_id=row.source_row_id,
                    multiplex_group=row.multiplex_group,
                    multiplex_channel=channel.multiplex_channel,
                    sample_id=design_entry.sample_id,
                    condition=design_entry.condition,
                    sample_role=design_entry.sample_role.value,
                    channel_role=_channel_role_for_sample(
                        feature_bundle,
                        sample_id=design_entry.sample_id,
                    ),
                    modified_peptide=row.modified_peptide,
                    protein_refs=row.protein_refs,
                    reporter_intensity=float(channel.intensity),
                    isolation_interference_fraction=fraction,
                    threshold_exceeded=threshold_exceeded,
                    note=(
                        "isolation interference crosses the configured threshold and should be considered unreliable for downstream interpretation"
                        if threshold_exceeded
                        else (
                            "isolation interference is preserved for review but remains below the configured threshold"
                            if fraction is not None
                            else "source row does not provide an isolation-interference value"
                        )
                    ),
                )
            )
    observations = sorted(
        observations,
        key=lambda entry: (
            entry.multiplex_group,
            entry.multiplex_channel,
            entry.source_row_id,
        ),
    )
    filtered_observations = tuple(
        entry for entry in observations if entry.threshold_exceeded
    )
    channel_summaries = _build_channel_summaries(observations)
    return TmtInterferenceReport(
        source_report=import_report,
        feature_bundle=feature_bundle,
        policy=active_policy,
        observations=tuple(observations),
        filtered_observations=filtered_observations,
        channel_summaries=channel_summaries,
        summary=TmtInterferenceSummary(
            multiplex_group_count=feature_bundle.summary.multiplex_group_count,
            observed_channel_row_count=len(observations),
            missing_interference_count=sum(
                1
                for entry in observations
                if entry.isolation_interference_fraction is None
            ),
            threshold_exceeded_count=sum(
                1 for entry in observations if entry.threshold_exceeded
            ),
            filtered_channel_row_count=len(filtered_observations),
            channel_summary_count=len(channel_summaries),
        ),
        note=(
            "tmt interference review preserves source-row isolation interference at the mapped sample-channel level for downstream filtering and audit"
        ),
    )


def render_tmt_interference_summary_tsv(report: TmtInterferenceReport) -> str:
    """Render the compact TMT interference-review summary ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "multiplex_group_count",
            "observed_channel_row_count",
            "missing_interference_count",
            "threshold_exceeded_count",
            "filtered_channel_row_count",
            "channel_summary_count",
        ]
    )
    writer.writerow(
        [
            report.summary.multiplex_group_count,
            report.summary.observed_channel_row_count,
            report.summary.missing_interference_count,
            report.summary.threshold_exceeded_count,
            report.summary.filtered_channel_row_count,
            report.summary.channel_summary_count,
        ]
    )
    return buffer.getvalue()


def render_tmt_interference_observation_tsv(report: TmtInterferenceReport) -> str:
    """Render the full TMT interference observation ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "source_row_id",
            "multiplex_group",
            "multiplex_channel",
            "sample_id",
            "condition",
            "sample_role",
            "channel_role",
            "modified_peptide",
            "protein_refs",
            "reporter_intensity",
            "isolation_interference_fraction",
            "threshold_exceeded",
            "note",
        ]
    )
    for entry in report.observations:
        writer.writerow(
            [
                entry.source_row_id,
                entry.multiplex_group,
                entry.multiplex_channel,
                entry.sample_id,
                entry.condition,
                entry.sample_role,
                entry.channel_role.value,
                entry.modified_peptide,
                ";".join(entry.protein_refs),
                entry.reporter_intensity,
                (
                    ""
                    if entry.isolation_interference_fraction is None
                    else entry.isolation_interference_fraction
                ),
                str(entry.threshold_exceeded).lower(),
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_tmt_filtered_interference_tsv(report: TmtInterferenceReport) -> str:
    """Render the threshold-exceeded TMT interference ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "source_row_id",
            "multiplex_group",
            "multiplex_channel",
            "sample_id",
            "condition",
            "sample_role",
            "channel_role",
            "modified_peptide",
            "protein_refs",
            "reporter_intensity",
            "isolation_interference_fraction",
            "note",
        ]
    )
    for entry in report.filtered_observations:
        writer.writerow(
            [
                entry.source_row_id,
                entry.multiplex_group,
                entry.multiplex_channel,
                entry.sample_id,
                entry.condition,
                entry.sample_role,
                entry.channel_role.value,
                entry.modified_peptide,
                ";".join(entry.protein_refs),
                entry.reporter_intensity,
                (
                    ""
                    if entry.isolation_interference_fraction is None
                    else entry.isolation_interference_fraction
                ),
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_tmt_interference_channel_summary_tsv(report: TmtInterferenceReport) -> str:
    """Render the per-sample-channel TMT interference summary ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "multiplex_group",
            "multiplex_channel",
            "sample_id",
            "condition",
            "sample_role",
            "channel_role",
            "observed_row_count",
            "missing_interference_count",
            "threshold_exceeded_count",
            "mean_interference_fraction",
            "max_interference_fraction",
            "flagged",
            "note",
        ]
    )
    for entry in report.channel_summaries:
        writer.writerow(
            [
                entry.multiplex_group,
                entry.multiplex_channel,
                entry.sample_id,
                entry.condition,
                entry.sample_role,
                entry.channel_role.value,
                entry.observed_row_count,
                entry.missing_interference_count,
                entry.threshold_exceeded_count,
                (
                    ""
                    if entry.mean_interference_fraction is None
                    else entry.mean_interference_fraction
                ),
                (
                    ""
                    if entry.max_interference_fraction is None
                    else entry.max_interference_fraction
                ),
                str(entry.flagged).lower(),
                entry.note,
            ]
        )
    return buffer.getvalue()


def export_tmt_interference_summary_tsv(
    report: TmtInterferenceReport,
    path: Path,
) -> None:
    """Write the compact TMT interference-review summary ledger."""

    write_output_table_tsv(path, render_tmt_interference_summary_tsv(report))


def export_tmt_interference_observation_tsv(
    report: TmtInterferenceReport,
    path: Path,
) -> None:
    """Write the full TMT interference observation ledger."""

    write_output_table_tsv(path, render_tmt_interference_observation_tsv(report))


def export_tmt_filtered_interference_tsv(
    report: TmtInterferenceReport,
    path: Path,
) -> None:
    """Write the threshold-exceeded TMT interference ledger."""

    write_output_table_tsv(path, render_tmt_filtered_interference_tsv(report))


def export_tmt_interference_channel_summary_tsv(
    report: TmtInterferenceReport,
    path: Path,
) -> None:
    """Write the per-sample-channel TMT interference summary ledger."""

    write_output_table_tsv(path, render_tmt_interference_channel_summary_tsv(report))


def _channel_role_for_sample(
    feature_bundle: TmtReporterFeatureBundle,
    *,
    sample_id: str,
) -> LabelBasedChannelRole:
    for entry in feature_bundle.channel_mapping:
        if entry.sample_id == sample_id and entry.channel_role is not None:
            return entry.channel_role
    return LabelBasedChannelRole.SAMPLE


def _build_channel_summaries(
    observations: list[TmtInterferenceObservationEntry],
) -> tuple[TmtInterferenceChannelSummaryEntry, ...]:
    grouped: dict[tuple[str, str, str], list[TmtInterferenceObservationEntry]] = {}
    for observation in observations:
        grouped.setdefault(
            (
                observation.multiplex_group,
                observation.multiplex_channel,
                observation.sample_id,
            ),
            [],
        ).append(observation)
    summaries: list[TmtInterferenceChannelSummaryEntry] = []
    for multiplex_group, multiplex_channel, sample_id in sorted(grouped):
        entries = grouped[(multiplex_group, multiplex_channel, sample_id)]
        first_entry = entries[0]
        measured = [
            entry.isolation_interference_fraction
            for entry in entries
            if entry.isolation_interference_fraction is not None
        ]
        threshold_exceeded_count = sum(1 for entry in entries if entry.threshold_exceeded)
        missing_interference_count = sum(
            1 for entry in entries if entry.isolation_interference_fraction is None
        )
        mean_interference = (
            sum(measured) / len(measured) if measured else None
        )
        max_interference = max(measured) if measured else None
        flagged = threshold_exceeded_count > 0
        summaries.append(
            TmtInterferenceChannelSummaryEntry(
                multiplex_group=multiplex_group,
                multiplex_channel=multiplex_channel,
                sample_id=sample_id,
                condition=first_entry.condition,
                sample_role=first_entry.sample_role,
                channel_role=first_entry.channel_role,
                observed_row_count=len(entries),
                missing_interference_count=missing_interference_count,
                threshold_exceeded_count=threshold_exceeded_count,
                mean_interference_fraction=mean_interference,
                max_interference_fraction=max_interference,
                flagged=flagged,
                note=(
                    "one or more reporter rows for this sample channel exceed the configured interference threshold"
                    if flagged
                    else "sample channel stays below the configured interference threshold across observed reporter rows"
                ),
            )
        )
    return tuple(summaries)
