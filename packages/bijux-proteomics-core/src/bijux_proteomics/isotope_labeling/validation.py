# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned isotope-label validation over SILAC labels and multiplex channels."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics.isotope_labeling.silac_quantification import (
    SilacImportReport,
    SilacLabel,
)
from bijux_proteomics.multiplex.reporter_matrix import (
    TmtReporterFeatureBundle,
    build_tmt_reporter_matrix_report,
)
from bijux_proteomics.quantification import LabelBasedChannelRole
from bijux_proteomics_foundation import JsonModel


class SilacValidationPolicy(JsonModel):
    """Policy for SILAC label-presence and pair-coverage validation."""

    model_config = ConfigDict(extra="forbid")

    expected_labels: tuple[SilacLabel, ...] = (
        SilacLabel.LIGHT,
        SilacLabel.HEAVY,
    )
    separate_charge_states: bool = True
    weak_label_ratio_floor: float = Field(default=0.5, gt=0.0)
    weak_group_coverage_floor: float = Field(default=0.6, gt=0.0, le=1.0)
    abnormal_distribution_floor: float = Field(default=0.7, gt=0.0)
    abnormal_distribution_ceiling: float = Field(default=1.5, gt=0.0)

    @model_validator(mode="after")
    def _validate_expected_labels(self) -> SilacValidationPolicy:
        normalized = tuple(dict.fromkeys(self.expected_labels))
        if len(normalized) < 2:
            raise ValueError("silac validation requires at least two expected labels")
        self.expected_labels = normalized
        return self


class SilacLabelValidationEntry(JsonModel):
    """One expected SILAC label ledger row for a sample."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    label: SilacLabel
    expected_group_count: int = Field(..., ge=0)
    observed_group_count: int = Field(..., ge=0)
    missing_group_count: int = Field(..., ge=0)
    observed_feature_count: int = Field(..., ge=0)
    total_intensity: float = Field(..., ge=0.0)
    present: bool
    note: str = Field(..., min_length=1)


class SilacValidationSummary(JsonModel):
    """Compact summary over one SILAC label-validation run."""

    model_config = ConfigDict(extra="forbid")

    sample_count: int = Field(..., ge=0)
    expected_label_count: int = Field(..., ge=0)
    label_entry_count: int = Field(..., ge=0)
    missing_label_count: int = Field(..., ge=0)
    missing_pair_member_count: int = Field(..., ge=0)
    abnormal_distribution_count: int = Field(..., ge=0)
    weak_label_count: int = Field(..., ge=0)


class SilacLabelDistributionEntry(JsonModel):
    """One SILAC label-intensity distribution row for a sample."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    label: SilacLabel
    total_intensity: float = Field(..., ge=0.0)
    sample_median_total_intensity: float | None = Field(default=None, ge=0.0)
    ratio_to_sample_median: float | None = Field(default=None, ge=0.0)
    abnormal_distribution: bool
    note: str = Field(..., min_length=1)


class SilacWeakEvidenceEntry(JsonModel):
    """One weak SILAC label-evidence finding."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    label: SilacLabel
    issue_kind: str = Field(..., min_length=1)
    observed_group_fraction: float = Field(..., ge=0.0)
    total_intensity_ratio_to_sample_max: float = Field(..., ge=0.0)
    note: str = Field(..., min_length=1)


class SilacValidationReport(JsonModel):
    """Owned SILAC label-validation surface."""

    model_config = ConfigDict(extra="forbid")

    import_report: SilacImportReport
    policy: SilacValidationPolicy
    label_entries: tuple[SilacLabelValidationEntry, ...] = Field(default_factory=tuple)
    distribution_entries: tuple[SilacLabelDistributionEntry, ...] = Field(default_factory=tuple)
    weak_evidence: tuple[SilacWeakEvidenceEntry, ...] = Field(default_factory=tuple)
    summary: SilacValidationSummary
    note: str = Field(..., min_length=1)


class TmtValidationPolicy(JsonModel):
    """Policy for TMT channel-presence and weak-channel validation."""

    model_config = ConfigDict(extra="forbid")

    weak_channel_ratio_floor: float = Field(default=0.5, gt=0.0)
    abnormal_distribution_floor: float = Field(default=0.7, gt=0.0)
    abnormal_distribution_ceiling: float = Field(default=1.5, gt=0.0)


class TmtChannelValidationEntry(JsonModel):
    """One expected TMT channel ledger row."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    sample_id: str | None = None
    condition: str | None = None
    channel_role: LabelBasedChannelRole | None = None
    source_column_present: bool
    observed_row_count: int = Field(..., ge=0)
    missing_row_count: int = Field(..., ge=0)
    total_intensity: float = Field(..., ge=0.0)
    present: bool
    note: str = Field(..., min_length=1)


class TmtChannelDistributionEntry(JsonModel):
    """One TMT channel-distribution review row."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    sample_id: str | None = None
    channel_role: LabelBasedChannelRole | None = None
    total_intensity: float = Field(..., ge=0.0)
    channel_median_total_intensity: float | None = Field(default=None, ge=0.0)
    ratio_to_channel_median: float | None = Field(default=None, ge=0.0)
    abnormal_distribution: bool
    note: str = Field(..., min_length=1)


class TmtWeakEvidenceEntry(JsonModel):
    """One weak TMT channel-evidence finding."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    sample_id: str | None = None
    channel_role: LabelBasedChannelRole | None = None
    issue_kind: str = Field(..., min_length=1)
    total_intensity_ratio_to_channel_max: float = Field(..., ge=0.0)
    note: str = Field(..., min_length=1)


class TmtValidationSummary(JsonModel):
    """Compact summary over one TMT channel-validation run."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group_count: int = Field(..., ge=0)
    expected_channel_count: int = Field(..., ge=0)
    missing_channel_count: int = Field(..., ge=0)
    abnormal_distribution_count: int = Field(..., ge=0)
    weak_channel_count: int = Field(..., ge=0)


class TmtValidationReport(JsonModel):
    """Owned TMT channel-validation surface."""

    model_config = ConfigDict(extra="forbid")

    feature_bundle: TmtReporterFeatureBundle
    policy: TmtValidationPolicy
    channel_entries: tuple[TmtChannelValidationEntry, ...] = Field(default_factory=tuple)
    distribution_entries: tuple[TmtChannelDistributionEntry, ...] = Field(default_factory=tuple)
    weak_evidence: tuple[TmtWeakEvidenceEntry, ...] = Field(default_factory=tuple)
    summary: TmtValidationSummary
    note: str = Field(..., min_length=1)


def build_silac_validation_report(
    import_report: SilacImportReport,
    *,
    policy: SilacValidationPolicy | None = None,
) -> SilacValidationReport:
    """Validate expected SILAC labels and pair coverage over imported feature rows."""

    active_policy = policy or SilacValidationPolicy()
    sample_groups: dict[str, set[tuple[str, int | None]]] = {}
    groups_by_sample_and_label: dict[tuple[str, SilacLabel], set[tuple[str, int | None]]] = {}
    rows_by_sample_and_label: dict[tuple[str, SilacLabel], list[float]] = {}

    for row in import_report.accepted_rows:
        group_key = (
            row.peptide,
            row.charge if active_policy.separate_charge_states else None,
        )
        sample_groups.setdefault(row.sample_id, set()).add(group_key)
        groups_by_sample_and_label.setdefault((row.sample_id, row.label), set()).add(group_key)
        rows_by_sample_and_label.setdefault((row.sample_id, row.label), []).append(row.intensity)

    label_entries: list[SilacLabelValidationEntry] = []
    for sample_id in sorted(sample_groups):
        expected_group_count = len(sample_groups[sample_id])
        for label in active_policy.expected_labels:
            observed_groups = groups_by_sample_and_label.get((sample_id, label), set())
            observed_rows = rows_by_sample_and_label.get((sample_id, label), [])
            missing_group_count = max(expected_group_count - len(observed_groups), 0)
            label_entries.append(
                SilacLabelValidationEntry(
                    sample_id=sample_id,
                    label=label,
                    expected_group_count=expected_group_count,
                    observed_group_count=len(observed_groups),
                    missing_group_count=missing_group_count,
                    observed_feature_count=len(observed_rows),
                    total_intensity=float(sum(observed_rows)),
                    present=bool(observed_rows),
                    note=(
                        "expected SILAC label is represented across all observed peptide groups"
                        if missing_group_count == 0 and observed_rows
                        else "expected SILAC label is preserved even though one or more peptide groups are missing that label state"
                    ),
                )
            )

    distribution_entries: list[SilacLabelDistributionEntry] = []
    weak_evidence: list[SilacWeakEvidenceEntry] = []
    entries_by_sample = {
        sample_id: tuple(
            entry for entry in label_entries if entry.sample_id == sample_id
        )
        for sample_id in sorted(sample_groups)
    }
    for sample_id, sample_entries in entries_by_sample.items():
        positive_totals = sorted(
            entry.total_intensity for entry in sample_entries if entry.total_intensity > 0.0
        )
        sample_median_total_intensity = (
            _median(positive_totals) if positive_totals else None
        )
        sample_max_total_intensity = max(
            (entry.total_intensity for entry in sample_entries),
            default=0.0,
        )
        for entry in sample_entries:
            ratio_to_sample_median = _ratio_or_none(
                numerator=entry.total_intensity,
                denominator=sample_median_total_intensity,
            )
            abnormal_distribution = (
                ratio_to_sample_median is not None
                and (
                    ratio_to_sample_median < active_policy.abnormal_distribution_floor
                    or ratio_to_sample_median > active_policy.abnormal_distribution_ceiling
                )
            )
            distribution_entries.append(
                SilacLabelDistributionEntry(
                    sample_id=sample_id,
                    label=entry.label,
                    total_intensity=entry.total_intensity,
                    sample_median_total_intensity=sample_median_total_intensity,
                    ratio_to_sample_median=ratio_to_sample_median,
                    abnormal_distribution=abnormal_distribution,
                    note=(
                        "label total intensity is within the sample-level isotope distribution envelope"
                        if not abnormal_distribution
                        else "label total intensity falls outside the sample-level isotope distribution envelope"
                    ),
                )
            )
            observed_group_fraction = (
                float(entry.observed_group_count) / float(entry.expected_group_count)
                if entry.expected_group_count > 0
                else 0.0
            )
            total_intensity_ratio_to_sample_max = (
                float(entry.total_intensity) / float(sample_max_total_intensity)
                if sample_max_total_intensity > 0.0
                else 0.0
            )
            if observed_group_fraction < active_policy.weak_group_coverage_floor:
                weak_evidence.append(
                    SilacWeakEvidenceEntry(
                        sample_id=sample_id,
                        label=entry.label,
                        issue_kind="incomplete_pair_coverage",
                        observed_group_fraction=observed_group_fraction,
                        total_intensity_ratio_to_sample_max=total_intensity_ratio_to_sample_max,
                        note="expected SILAC label is missing from too many peptide groups for this sample",
                    )
                )
            if total_intensity_ratio_to_sample_max < active_policy.weak_label_ratio_floor:
                weak_evidence.append(
                    SilacWeakEvidenceEntry(
                        sample_id=sample_id,
                        label=entry.label,
                        issue_kind="weak_total_intensity",
                        observed_group_fraction=observed_group_fraction,
                        total_intensity_ratio_to_sample_max=total_intensity_ratio_to_sample_max,
                        note="label total intensity is weak relative to the strongest observed label in the sample",
                    )
                )

    return SilacValidationReport(
        import_report=import_report,
        policy=active_policy,
        label_entries=tuple(label_entries),
        distribution_entries=tuple(distribution_entries),
        weak_evidence=tuple(weak_evidence),
        summary=SilacValidationSummary(
            sample_count=import_report.summary.sample_count,
            expected_label_count=len(active_policy.expected_labels),
            label_entry_count=len(label_entries),
            missing_label_count=sum(1 for entry in label_entries if not entry.present),
            missing_pair_member_count=sum(
                entry.missing_group_count for entry in label_entries
            ),
            abnormal_distribution_count=sum(
                1 for entry in distribution_entries if entry.abnormal_distribution
            ),
            weak_label_count=len(weak_evidence),
        ),
        note=(
            "silac validation preserves expected label coverage, intensity distribution, and weak-label evidence for isotope-health review"
        ),
    )


def build_tmt_validation_report(
    feature_bundle: TmtReporterFeatureBundle,
    *,
    policy: TmtValidationPolicy | None = None,
) -> TmtValidationReport:
    """Validate expected TMT channels and weak evidence over one feature bundle."""

    active_policy = policy or TmtValidationPolicy()
    matrix_report = build_tmt_reporter_matrix_report(feature_bundle)

    totals_by_key = {
        (entry.multiplex_group, entry.multiplex_channel): entry
        for entry in matrix_report.channel_totals
    }
    channel_entries: list[TmtChannelValidationEntry] = []
    mapped_entries = tuple(
        entry for entry in feature_bundle.channel_mapping if entry.mapped_to_design
    )
    for entry in sorted(
        mapped_entries,
        key=lambda item: (item.multiplex_group, item.multiplex_channel),
    ):
        total_entry = totals_by_key[(entry.multiplex_group, entry.multiplex_channel)]
        present = entry.source_column_present and total_entry.observed_row_count > 0
        channel_entries.append(
            TmtChannelValidationEntry(
                multiplex_group=entry.multiplex_group,
                multiplex_channel=entry.multiplex_channel,
                sample_id=entry.sample_id,
                condition=entry.condition,
                channel_role=entry.channel_role,
                source_column_present=entry.source_column_present,
                observed_row_count=total_entry.observed_row_count,
                missing_row_count=total_entry.missing_row_count,
                total_intensity=total_entry.total_intensity,
                present=present,
                note=(
                    "expected multiplex channel is backed by observed reporter evidence"
                    if present
                    else "expected multiplex channel is preserved even though source evidence is missing or empty"
                ),
            )
        )

    totals_by_channel: dict[str, list[float]] = {}
    for validation_entry in channel_entries:
        if validation_entry.total_intensity > 0.0:
            totals_by_channel.setdefault(validation_entry.multiplex_channel, []).append(
                validation_entry.total_intensity
            )

    distribution_entries: list[TmtChannelDistributionEntry] = []
    weak_evidence: list[TmtWeakEvidenceEntry] = []
    max_total_by_channel = {
        channel: max(values) for channel, values in totals_by_channel.items()
    }
    for validation_entry in channel_entries:
        channel_median_total_intensity = None
        if validation_entry.multiplex_channel in totals_by_channel:
            channel_median_total_intensity = _median(
                sorted(totals_by_channel[validation_entry.multiplex_channel])
            )
        ratio_to_channel_median = _ratio_or_none(
            numerator=validation_entry.total_intensity,
            denominator=channel_median_total_intensity,
        )
        abnormal_distribution = (
            ratio_to_channel_median is not None
            and (
                ratio_to_channel_median < active_policy.abnormal_distribution_floor
                or ratio_to_channel_median > active_policy.abnormal_distribution_ceiling
            )
        )
        distribution_entries.append(
            TmtChannelDistributionEntry(
                multiplex_group=validation_entry.multiplex_group,
                multiplex_channel=validation_entry.multiplex_channel,
                sample_id=validation_entry.sample_id,
                channel_role=validation_entry.channel_role,
                total_intensity=validation_entry.total_intensity,
                channel_median_total_intensity=channel_median_total_intensity,
                ratio_to_channel_median=ratio_to_channel_median,
                abnormal_distribution=abnormal_distribution,
                note=(
                    "channel total intensity is consistent with the same channel across multiplex groups"
                    if not abnormal_distribution
                    else "channel total intensity falls outside the same-channel study envelope"
                ),
            )
        )
        channel_max_total_intensity = max_total_by_channel.get(
            validation_entry.multiplex_channel,
            0.0,
        )
        total_intensity_ratio_to_channel_max = (
            float(validation_entry.total_intensity)
            / float(channel_max_total_intensity)
            if channel_max_total_intensity > 0.0
            else 0.0
        )
        if (
            not validation_entry.source_column_present
            or validation_entry.observed_row_count == 0
        ):
            weak_evidence.append(
                TmtWeakEvidenceEntry(
                    multiplex_group=validation_entry.multiplex_group,
                    multiplex_channel=validation_entry.multiplex_channel,
                    sample_id=validation_entry.sample_id,
                    channel_role=validation_entry.channel_role,
                    issue_kind="channel_missing",
                    total_intensity_ratio_to_channel_max=total_intensity_ratio_to_channel_max,
                    note="expected multiplex channel is missing from the source table or has no observed reporter evidence",
                )
            )
        elif total_intensity_ratio_to_channel_max < active_policy.weak_channel_ratio_floor:
            weak_evidence.append(
                TmtWeakEvidenceEntry(
                    multiplex_group=validation_entry.multiplex_group,
                    multiplex_channel=validation_entry.multiplex_channel,
                    sample_id=validation_entry.sample_id,
                    channel_role=validation_entry.channel_role,
                    issue_kind="weak_channel_intensity",
                    total_intensity_ratio_to_channel_max=total_intensity_ratio_to_channel_max,
                    note="channel total intensity is weak relative to the strongest observation for the same channel",
                )
            )

    return TmtValidationReport(
        feature_bundle=feature_bundle,
        policy=active_policy,
        channel_entries=tuple(channel_entries),
        distribution_entries=tuple(distribution_entries),
        weak_evidence=tuple(weak_evidence),
        summary=TmtValidationSummary(
            multiplex_group_count=feature_bundle.summary.multiplex_group_count,
            expected_channel_count=len(channel_entries),
            missing_channel_count=sum(1 for entry in channel_entries if not entry.present),
            abnormal_distribution_count=sum(
                1 for entry in distribution_entries if entry.abnormal_distribution
            ),
            weak_channel_count=len(weak_evidence),
        ),
        note=(
            "tmt validation preserves expected channel presence, same-channel distribution, and weak-channel evidence over design-aware reporter mappings"
        ),
    )


def _median(values: list[float]) -> float:
    midpoint = len(values) // 2
    if len(values) % 2 == 1:
        return float(values[midpoint])
    return float(values[midpoint - 1] + values[midpoint]) / 2.0


def _ratio_or_none(
    *,
    numerator: float,
    denominator: float | None,
) -> float | None:
    if denominator is None or denominator <= 0.0:
        return None
    return float(numerator) / float(denominator)


def render_silac_validation_summary_tsv(report: SilacValidationReport) -> str:
    """Render the compact SILAC validation summary ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "sample_count",
            "expected_label_count",
            "label_entry_count",
            "missing_label_count",
            "missing_pair_member_count",
            "abnormal_distribution_count",
            "weak_label_count",
        ]
    )
    writer.writerow(
        [
            report.summary.sample_count,
            report.summary.expected_label_count,
            report.summary.label_entry_count,
            report.summary.missing_label_count,
            report.summary.missing_pair_member_count,
            report.summary.abnormal_distribution_count,
            report.summary.weak_label_count,
        ]
    )
    return buffer.getvalue()


def render_silac_validation_label_tsv(report: SilacValidationReport) -> str:
    """Render the SILAC expected-label coverage ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "sample_id",
            "label",
            "expected_group_count",
            "observed_group_count",
            "missing_group_count",
            "observed_feature_count",
            "total_intensity",
            "present",
            "note",
        ]
    )
    for entry in report.label_entries:
        writer.writerow(
            [
                entry.sample_id,
                entry.label.value,
                entry.expected_group_count,
                entry.observed_group_count,
                entry.missing_group_count,
                entry.observed_feature_count,
                entry.total_intensity,
                entry.present,
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_silac_validation_distribution_tsv(report: SilacValidationReport) -> str:
    """Render the SILAC label-distribution ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "sample_id",
            "label",
            "total_intensity",
            "sample_median_total_intensity",
            "ratio_to_sample_median",
            "abnormal_distribution",
            "note",
        ]
    )
    for entry in report.distribution_entries:
        writer.writerow(
            [
                entry.sample_id,
                entry.label.value,
                entry.total_intensity,
                (
                    ""
                    if entry.sample_median_total_intensity is None
                    else entry.sample_median_total_intensity
                ),
                "" if entry.ratio_to_sample_median is None else entry.ratio_to_sample_median,
                entry.abnormal_distribution,
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_silac_validation_weak_tsv(report: SilacValidationReport) -> str:
    """Render the SILAC weak-label-evidence ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "sample_id",
            "label",
            "issue_kind",
            "observed_group_fraction",
            "total_intensity_ratio_to_sample_max",
            "note",
        ]
    )
    for entry in report.weak_evidence:
        writer.writerow(
            [
                entry.sample_id,
                entry.label.value,
                entry.issue_kind,
                entry.observed_group_fraction,
                entry.total_intensity_ratio_to_sample_max,
                entry.note,
            ]
        )
    return buffer.getvalue()


def export_silac_validation_summary_tsv(report: SilacValidationReport, path: Path) -> None:
    """Write the compact SILAC validation summary ledger."""

    write_output_table_tsv(path, render_silac_validation_summary_tsv(report))


def export_silac_validation_label_tsv(report: SilacValidationReport, path: Path) -> None:
    """Write the SILAC expected-label coverage ledger."""

    write_output_table_tsv(path, render_silac_validation_label_tsv(report))


def export_silac_validation_distribution_tsv(
    report: SilacValidationReport,
    path: Path,
) -> None:
    """Write the SILAC label-distribution ledger."""

    write_output_table_tsv(path, render_silac_validation_distribution_tsv(report))


def export_silac_validation_weak_tsv(report: SilacValidationReport, path: Path) -> None:
    """Write the SILAC weak-label-evidence ledger."""

    write_output_table_tsv(path, render_silac_validation_weak_tsv(report))


def render_tmt_validation_summary_tsv(report: TmtValidationReport) -> str:
    """Render the compact TMT validation summary ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "multiplex_group_count",
            "expected_channel_count",
            "missing_channel_count",
            "abnormal_distribution_count",
            "weak_channel_count",
        ]
    )
    writer.writerow(
        [
            report.summary.multiplex_group_count,
            report.summary.expected_channel_count,
            report.summary.missing_channel_count,
            report.summary.abnormal_distribution_count,
            report.summary.weak_channel_count,
        ]
    )
    return buffer.getvalue()


def render_tmt_validation_channel_tsv(report: TmtValidationReport) -> str:
    """Render the TMT expected-channel coverage ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "multiplex_group",
            "multiplex_channel",
            "sample_id",
            "condition",
            "channel_role",
            "source_column_present",
            "observed_row_count",
            "missing_row_count",
            "total_intensity",
            "present",
            "note",
        ]
    )
    for entry in report.channel_entries:
        writer.writerow(
            [
                entry.multiplex_group,
                entry.multiplex_channel,
                entry.sample_id or "",
                entry.condition or "",
                "" if entry.channel_role is None else entry.channel_role.value,
                entry.source_column_present,
                entry.observed_row_count,
                entry.missing_row_count,
                entry.total_intensity,
                entry.present,
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_tmt_validation_distribution_tsv(report: TmtValidationReport) -> str:
    """Render the TMT channel-distribution ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "multiplex_group",
            "multiplex_channel",
            "sample_id",
            "channel_role",
            "total_intensity",
            "channel_median_total_intensity",
            "ratio_to_channel_median",
            "abnormal_distribution",
            "note",
        ]
    )
    for entry in report.distribution_entries:
        writer.writerow(
            [
                entry.multiplex_group,
                entry.multiplex_channel,
                entry.sample_id or "",
                "" if entry.channel_role is None else entry.channel_role.value,
                entry.total_intensity,
                (
                    ""
                    if entry.channel_median_total_intensity is None
                    else entry.channel_median_total_intensity
                ),
                "" if entry.ratio_to_channel_median is None else entry.ratio_to_channel_median,
                entry.abnormal_distribution,
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_tmt_validation_weak_tsv(report: TmtValidationReport) -> str:
    """Render the TMT weak-channel-evidence ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "multiplex_group",
            "multiplex_channel",
            "sample_id",
            "channel_role",
            "issue_kind",
            "total_intensity_ratio_to_channel_max",
            "note",
        ]
    )
    for entry in report.weak_evidence:
        writer.writerow(
            [
                entry.multiplex_group,
                entry.multiplex_channel,
                entry.sample_id or "",
                "" if entry.channel_role is None else entry.channel_role.value,
                entry.issue_kind,
                entry.total_intensity_ratio_to_channel_max,
                entry.note,
            ]
        )
    return buffer.getvalue()


def export_tmt_validation_summary_tsv(report: TmtValidationReport, path: Path) -> None:
    """Write the compact TMT validation summary ledger."""

    write_output_table_tsv(path, render_tmt_validation_summary_tsv(report))


def export_tmt_validation_channel_tsv(report: TmtValidationReport, path: Path) -> None:
    """Write the TMT expected-channel coverage ledger."""

    write_output_table_tsv(path, render_tmt_validation_channel_tsv(report))


def export_tmt_validation_distribution_tsv(report: TmtValidationReport, path: Path) -> None:
    """Write the TMT channel-distribution ledger."""

    write_output_table_tsv(path, render_tmt_validation_distribution_tsv(report))


def export_tmt_validation_weak_tsv(report: TmtValidationReport, path: Path) -> None:
    """Write the TMT weak-channel-evidence ledger."""

    write_output_table_tsv(path, render_tmt_validation_weak_tsv(report))
