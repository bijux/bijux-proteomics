# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned TMT reporter-channel normalization and distribution review surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

import numpy as np
from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.multiplex.reporter_matrix import (
    TmtChannelMappingEntry,
    TmtReporterFeatureBundle,
    TmtReporterMatrixReport,
    build_tmt_reporter_matrix_report,
    render_tmt_peptide_matrix_tsv,
    render_tmt_protein_matrix_tsv,
)
from bijux_proteomics.quantification.contracts import (
    LabelBasedChannelRole,
    MissingValueKind,
    Ms1FeatureRecord,
)
from bijux_proteomics_foundation import JsonModel


class TmtNormalizationMethod(StrEnum):
    """Supported TMT-specific reporter-channel normalization policies."""

    TOTAL_SIGNAL = "total_signal"
    MEDIAN = "median"
    REFERENCE_CHANNEL = "reference_channel"


class TmtNormalizationPolicy(JsonModel):
    """Policy for TMT reporter-channel normalization and balance review."""

    model_config = ConfigDict(extra="forbid")

    method: TmtNormalizationMethod = TmtNormalizationMethod.MEDIAN
    balance_ratio_threshold: float = Field(default=1.5, ge=1.0)
    reference_role_priority: tuple[LabelBasedChannelRole, ...] = (
        LabelBasedChannelRole.REFERENCE,
        LabelBasedChannelRole.QC_BRIDGE,
    )


class TmtNormalizationTransformEntry(JsonModel):
    """One sample-channel transform applied by one TMT normalization policy."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    condition: str | None = None
    channel_role: LabelBasedChannelRole
    method: TmtNormalizationMethod
    scale_factor: float | None = Field(default=None, gt=0.0)
    reference_sample_id: str | None = None
    reference_channel: str | None = None
    note: str = Field(..., min_length=1)


class TmtDistributionStage(StrEnum):
    """Stage marker for before/after TMT channel distribution review."""

    BEFORE = "before"
    AFTER = "after"


class TmtChannelDistributionEntry(JsonModel):
    """One before/after channel distribution row over a normalized TMT bundle."""

    model_config = ConfigDict(extra="forbid")

    stage: TmtDistributionStage
    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    condition: str | None = None
    channel_role: LabelBasedChannelRole
    total_abundance: float = Field(..., ge=0.0)
    median_abundance: float = Field(..., ge=0.0)
    interquartile_range: float = Field(..., ge=0.0)
    ratio_to_group_median: float = Field(..., ge=0.0)
    flagged: bool
    note: str = Field(..., min_length=1)


class TmtNormalizationSummary(JsonModel):
    """Compact summary over one TMT normalization operation."""

    model_config = ConfigDict(extra="forbid")

    method: TmtNormalizationMethod
    multiplex_group_count: int = Field(..., ge=0)
    channel_count: int = Field(..., ge=0)
    transform_count: int = Field(..., ge=0)
    before_flagged_channel_count: int = Field(..., ge=0)
    after_flagged_channel_count: int = Field(..., ge=0)
    reference_group_count: int = Field(..., ge=0)


class TmtNormalizationReport(JsonModel):
    """Owned TMT normalization review with before/after matrix and balance evidence."""

    model_config = ConfigDict(extra="forbid")

    policy: TmtNormalizationPolicy
    before_report: TmtReporterMatrixReport
    after_report: TmtReporterMatrixReport
    transforms: tuple[TmtNormalizationTransformEntry, ...] = Field(
        default_factory=tuple
    )
    channel_distributions: tuple[TmtChannelDistributionEntry, ...] = Field(
        default_factory=tuple
    )
    summary: TmtNormalizationSummary
    note: str = Field(..., min_length=1)


def build_tmt_normalization_report(
    feature_bundle: TmtReporterFeatureBundle,
    *,
    policy: TmtNormalizationPolicy | None = None,
) -> TmtNormalizationReport:
    """Normalize TMT reporter-channel feature evidence and preserve before/after review."""

    active_policy = policy or TmtNormalizationPolicy()
    before_report = build_tmt_reporter_matrix_report(feature_bundle)

    if active_policy.method is TmtNormalizationMethod.MEDIAN:
        normalized_records, transforms = _apply_median_normalization(
            feature_bundle,
            policy=active_policy,
        )
    elif active_policy.method is TmtNormalizationMethod.TOTAL_SIGNAL:
        normalized_records, transforms = _apply_total_signal_normalization(
            feature_bundle,
            policy=active_policy,
        )
    elif active_policy.method is TmtNormalizationMethod.REFERENCE_CHANNEL:
        normalized_records, transforms, reference_group_count = (
            _apply_reference_channel_normalization(
                feature_bundle,
                policy=active_policy,
            )
        )
    else:
        raise ValueError(
            "tmt normalization currently supports median, total-signal, and reference-channel methods in the owned multiplex surface"
        )
    if active_policy.method is not TmtNormalizationMethod.REFERENCE_CHANNEL:
        reference_group_count = 0
    after_bundle = feature_bundle.model_copy(
        update={
            "feature_records": normalized_records,
            "note": (
                "tmt reporter feature materialization preserves design-aware channels after multiplex normalization"
            ),
        }
    )
    after_report = build_tmt_reporter_matrix_report(after_bundle)
    distributions = _build_channel_distribution_entries(
        before_bundle=feature_bundle,
        after_bundle=after_bundle,
        channel_mapping=feature_bundle.channel_mapping,
        policy=active_policy,
    )
    before_flagged = sum(
        1
        for entry in distributions
        if entry.stage is TmtDistributionStage.BEFORE and entry.flagged
    )
    after_flagged = sum(
        1
        for entry in distributions
        if entry.stage is TmtDistributionStage.AFTER and entry.flagged
    )
    return TmtNormalizationReport(
        policy=active_policy,
        before_report=before_report,
        after_report=after_report,
        transforms=transforms,
        channel_distributions=distributions,
        summary=TmtNormalizationSummary(
            method=active_policy.method,
            multiplex_group_count=len(
                {entry.multiplex_group for entry in feature_bundle.channel_mapping}
            ),
            channel_count=len(
                [
                    entry
                    for entry in feature_bundle.channel_mapping
                    if entry.mapped_to_design
                ]
            ),
            transform_count=len(transforms),
            before_flagged_channel_count=before_flagged,
            after_flagged_channel_count=after_flagged,
            reference_group_count=reference_group_count,
        ),
        note=(
            "tmt normalization preserves before and after multiplex channel distributions alongside normalized peptide and protein matrices"
        ),
    )


def _apply_median_normalization(
    feature_bundle: TmtReporterFeatureBundle,
    *,
    policy: TmtNormalizationPolicy,
) -> tuple[tuple[Ms1FeatureRecord, ...], tuple[TmtNormalizationTransformEntry, ...]]:
    sample_records: dict[str, list[Ms1FeatureRecord]] = {}
    for record in feature_bundle.feature_records:
        sample_records.setdefault(record.sample_id, []).append(record)

    mapping_by_sample = {
        entry.sample_id: entry
        for entry in feature_bundle.channel_mapping
        if entry.mapped_to_design and entry.sample_id is not None
    }
    grouped_sample_ids: dict[str, list[str]] = {}
    for sample_id, entry in mapping_by_sample.items():
        grouped_sample_ids.setdefault(entry.multiplex_group, []).append(sample_id)

    factors: dict[str, float] = {}
    transforms: list[TmtNormalizationTransformEntry] = []
    for multiplex_group, group_sample_ids in sorted(grouped_sample_ids.items()):
        sample_medians: dict[str, float] = {}
        for sample_id in group_sample_ids:
            intensities = np.array(
                [
                    float(record.intensity)
                    for record in sample_records.get(sample_id, ())
                    if record.intensity is not None
                ],
                dtype=float,
            )
            sample_medians[sample_id] = (
                float(np.median(intensities)) if intensities.size else float("nan")
            )
        finite_medians = [
            value
            for value in sample_medians.values()
            if np.isfinite(value) and value > 0.0
        ]
        group_median = (
            float(np.median(np.array(finite_medians, dtype=float)))
            if finite_medians
            else 1.0
        )
        for sample_id in sorted(group_sample_ids):
            sample_median = sample_medians[sample_id]
            factor = (
                group_median / sample_median
                if np.isfinite(sample_median) and sample_median > 0.0
                else 1.0
            )
            factors[sample_id] = factor
            mapping_entry = mapping_by_sample[sample_id]
            transforms.append(
                TmtNormalizationTransformEntry(
                    multiplex_group=multiplex_group,
                    multiplex_channel=mapping_entry.multiplex_channel,
                    sample_id=sample_id,
                    condition=mapping_entry.condition,
                    channel_role=mapping_entry.channel_role
                    or LabelBasedChannelRole.SAMPLE,
                    method=policy.method,
                    scale_factor=factor,
                    reference_sample_id=None,
                    reference_channel=None,
                    note="sample channel is scaled toward the plex median reporter intensity",
                )
            )

    normalized_records = tuple(
        record.model_copy(
            update={
                "intensity": (
                    None
                    if record.intensity is None
                    else float(record.intensity) * factors.get(record.sample_id, 1.0)
                )
            }
        )
        for record in feature_bundle.feature_records
    )
    return normalized_records, tuple(transforms)


def _apply_total_signal_normalization(
    feature_bundle: TmtReporterFeatureBundle,
    *,
    policy: TmtNormalizationPolicy,
) -> tuple[tuple[Ms1FeatureRecord, ...], tuple[TmtNormalizationTransformEntry, ...]]:
    sample_records: dict[str, list[Ms1FeatureRecord]] = {}
    for record in feature_bundle.feature_records:
        sample_records.setdefault(record.sample_id, []).append(record)

    mapping_by_sample = {
        entry.sample_id: entry
        for entry in feature_bundle.channel_mapping
        if entry.mapped_to_design and entry.sample_id is not None
    }
    grouped_sample_ids: dict[str, list[str]] = {}
    for sample_id, entry in mapping_by_sample.items():
        grouped_sample_ids.setdefault(entry.multiplex_group, []).append(sample_id)

    factors: dict[str, float] = {}
    transforms: list[TmtNormalizationTransformEntry] = []
    for multiplex_group, group_sample_ids in sorted(grouped_sample_ids.items()):
        sample_totals = {
            sample_id: float(
                sum(
                    float(record.intensity)
                    for record in sample_records.get(sample_id, ())
                    if record.intensity is not None
                )
            )
            for sample_id in group_sample_ids
        }
        positive_totals = [
            value
            for value in sample_totals.values()
            if np.isfinite(value) and value > 0.0
        ]
        group_target = (
            float(np.mean(np.array(positive_totals, dtype=float)))
            if positive_totals
            else 1.0
        )
        for sample_id in sorted(group_sample_ids):
            sample_total = sample_totals[sample_id]
            factor = (
                group_target / sample_total
                if np.isfinite(sample_total) and sample_total > 0.0
                else 1.0
            )
            factors[sample_id] = factor
            mapping_entry = mapping_by_sample[sample_id]
            transforms.append(
                TmtNormalizationTransformEntry(
                    multiplex_group=multiplex_group,
                    multiplex_channel=mapping_entry.multiplex_channel,
                    sample_id=sample_id,
                    condition=mapping_entry.condition,
                    channel_role=mapping_entry.channel_role
                    or LabelBasedChannelRole.SAMPLE,
                    method=policy.method,
                    scale_factor=factor,
                    reference_sample_id=None,
                    reference_channel=None,
                    note="sample channel is scaled toward the plex mean total reporter signal",
                )
            )

    normalized_records = tuple(
        record.model_copy(
            update={
                "intensity": (
                    None
                    if record.intensity is None
                    else float(record.intensity) * factors.get(record.sample_id, 1.0)
                )
            }
        )
        for record in feature_bundle.feature_records
    )
    return normalized_records, tuple(transforms)


def _apply_reference_channel_normalization(
    feature_bundle: TmtReporterFeatureBundle,
    *,
    policy: TmtNormalizationPolicy,
) -> tuple[
    tuple[Ms1FeatureRecord, ...],
    tuple[TmtNormalizationTransformEntry, ...],
    int,
]:
    mapped_entries = [
        entry
        for entry in feature_bundle.channel_mapping
        if entry.mapped_to_design and entry.sample_id is not None
    ]
    group_entries: dict[str, list[TmtChannelMappingEntry]] = {}
    for entry in mapped_entries:
        group_entries.setdefault(entry.multiplex_group, []).append(entry)

    reference_entry_by_group: dict[str, TmtChannelMappingEntry] = {}
    transforms: list[TmtNormalizationTransformEntry] = []
    for multiplex_group, entries in sorted(group_entries.items()):
        reference_entry = _select_reference_channel_entry(
            entries,
            role_priority=policy.reference_role_priority,
        )
        reference_entry_by_group[multiplex_group] = reference_entry
        for entry in sorted(entries, key=lambda item: item.multiplex_channel):
            transforms.append(
                TmtNormalizationTransformEntry(
                    multiplex_group=multiplex_group,
                    multiplex_channel=entry.multiplex_channel,
                    sample_id=entry.sample_id or "",
                    condition=entry.condition,
                    channel_role=entry.channel_role or LabelBasedChannelRole.SAMPLE,
                    method=policy.method,
                    scale_factor=None,
                    reference_sample_id=reference_entry.sample_id,
                    reference_channel=reference_entry.multiplex_channel,
                    note=(
                        "reference channel is normalized to one and all other channels are expressed as per-observation ratios to that governed reference"
                        if entry.sample_id == reference_entry.sample_id
                        else "sample channel is expressed as a per-observation ratio to the governed reference channel"
                    ),
                )
            )

    normalized_records = []
    for observation in feature_bundle.source_report.accepted_rows:
        intensity_lookup = {
            item.multiplex_channel: item.intensity
            for item in observation.channel_intensities
        }
        group = observation.multiplex_group
        reference_entry = reference_entry_by_group[group]
        reference_intensity = intensity_lookup.get(reference_entry.multiplex_channel)
        for entry in sorted(
            group_entries[group], key=lambda item: item.multiplex_channel
        ):
            raw_intensity = intensity_lookup.get(entry.multiplex_channel)
            normalized_intensity, missing_kind, missing_reason = _reference_ratio_value(
                raw_intensity=raw_intensity,
                reference_intensity=reference_intensity,
            )
            normalized_records.append(
                next(
                    record.model_copy(
                        update={
                            "intensity": normalized_intensity,
                            "missing_value_kind": missing_kind,
                            "missing_reason": missing_reason,
                        }
                    )
                    for record in feature_bundle.feature_records
                    if record.feature_id
                    == f"{observation.source_row_id}:{entry.multiplex_channel}"
                )
            )
    return (
        tuple(normalized_records),
        tuple(transforms),
        len(reference_entry_by_group),
    )


def _build_channel_distribution_entries(
    *,
    before_bundle: TmtReporterFeatureBundle,
    after_bundle: TmtReporterFeatureBundle,
    channel_mapping: tuple[TmtChannelMappingEntry, ...],
    policy: TmtNormalizationPolicy,
) -> tuple[TmtChannelDistributionEntry, ...]:
    entries: list[TmtChannelDistributionEntry] = []
    entries.extend(
        _bundle_distribution_entries(
            before_bundle,
            channel_mapping=channel_mapping,
            stage=TmtDistributionStage.BEFORE,
            policy=policy,
        )
    )
    entries.extend(
        _bundle_distribution_entries(
            after_bundle,
            channel_mapping=channel_mapping,
            stage=TmtDistributionStage.AFTER,
            policy=policy,
        )
    )
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.stage.value,
                entry.multiplex_group,
                entry.multiplex_channel,
            ),
        )
    )


def _bundle_distribution_entries(
    bundle: TmtReporterFeatureBundle,
    *,
    channel_mapping: tuple[TmtChannelMappingEntry, ...],
    stage: TmtDistributionStage,
    policy: TmtNormalizationPolicy,
) -> list[TmtChannelDistributionEntry]:
    sample_records: dict[str, list[Ms1FeatureRecord]] = {}
    for record in bundle.feature_records:
        sample_records.setdefault(record.sample_id, []).append(record)

    mapped_entries = [
        entry
        for entry in channel_mapping
        if entry.mapped_to_design and entry.sample_id is not None
    ]
    totals_by_group: dict[str, list[float]] = {}
    provisional: list[tuple[TmtChannelMappingEntry, float, float, float]] = []
    for entry in mapped_entries:
        records = sample_records.get(entry.sample_id or "", [])
        observed = np.array(
            [
                float(record.intensity)
                for record in records
                if record.intensity is not None
            ],
            dtype=float,
        )
        total_abundance = float(np.sum(observed)) if observed.size else 0.0
        median_abundance = float(np.median(observed)) if observed.size else 0.0
        interquartile_range = (
            float(np.percentile(observed, 75.0) - np.percentile(observed, 25.0))
            if observed.size
            else 0.0
        )
        totals_by_group.setdefault(entry.multiplex_group, []).append(total_abundance)
        provisional.append(
            (entry, total_abundance, median_abundance, interquartile_range)
        )
    group_medians = {
        group: float(np.median(np.array(totals, dtype=float))) if totals else 0.0
        for group, totals in totals_by_group.items()
    }
    rendered: list[TmtChannelDistributionEntry] = []
    for entry, total_abundance, median_abundance, interquartile_range in provisional:
        group_median = group_medians.get(entry.multiplex_group, 0.0)
        ratio = total_abundance / group_median if group_median > 0.0 else 0.0
        rendered.append(
            TmtChannelDistributionEntry(
                stage=stage,
                multiplex_group=entry.multiplex_group,
                multiplex_channel=entry.multiplex_channel,
                sample_id=entry.sample_id or "",
                condition=entry.condition,
                channel_role=entry.channel_role or LabelBasedChannelRole.SAMPLE,
                total_abundance=total_abundance,
                median_abundance=median_abundance,
                interquartile_range=interquartile_range,
                ratio_to_group_median=ratio,
                flagged=(
                    ratio > policy.balance_ratio_threshold
                    or (ratio > 0.0 and ratio < 1.0 / policy.balance_ratio_threshold)
                ),
                note=entry.note,
            )
        )
    return rendered


def _select_reference_channel_entry(
    entries: list[TmtChannelMappingEntry],
    *,
    role_priority: tuple[LabelBasedChannelRole, ...],
) -> TmtChannelMappingEntry:
    for role in role_priority:
        matches = [
            entry
            for entry in entries
            if entry.channel_role is role and entry.sample_id is not None
        ]
        if matches:
            return sorted(matches, key=lambda entry: entry.multiplex_channel)[0]
    raise ValueError(
        "reference-channel normalization requires at least one reference or qc bridge channel per multiplex group"
    )


def _reference_ratio_value(
    *,
    raw_intensity: float | None,
    reference_intensity: float | None,
) -> tuple[float | None, MissingValueKind, str | None]:
    if raw_intensity is None:
        return None, MissingValueKind.NOT_OBSERVED, "reporter_channel_missing"
    if reference_intensity is None:
        return None, MissingValueKind.FILTERED, "reference_channel_missing"
    if reference_intensity <= 0.0:
        return None, MissingValueKind.FILTERED, "reference_channel_zero"
    normalized = float(raw_intensity) / float(reference_intensity)
    if normalized == 0.0:
        return 0.0, MissingValueKind.ZERO, None
    return normalized, MissingValueKind.OBSERVED, None


def render_tmt_normalization_summary_tsv(report: TmtNormalizationReport) -> str:
    """Render a compact summary over one TMT normalization review."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "method",
            "multiplex_group_count",
            "channel_count",
            "transform_count",
            "before_flagged_channel_count",
            "after_flagged_channel_count",
            "reference_group_count",
        ]
    )
    writer.writerow(
        [
            report.summary.method.value,
            report.summary.multiplex_group_count,
            report.summary.channel_count,
            report.summary.transform_count,
            report.summary.before_flagged_channel_count,
            report.summary.after_flagged_channel_count,
            report.summary.reference_group_count,
        ]
    )
    return buffer.getvalue()


def render_tmt_normalization_transform_tsv(report: TmtNormalizationReport) -> str:
    """Render one row per applied TMT normalization transform."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "multiplex_group",
            "multiplex_channel",
            "sample_id",
            "condition",
            "channel_role",
            "method",
            "scale_factor",
            "reference_sample_id",
            "reference_channel",
            "note",
        ]
    )
    for entry in report.transforms:
        writer.writerow(
            [
                entry.multiplex_group,
                entry.multiplex_channel,
                entry.sample_id,
                entry.condition or "",
                entry.channel_role.value,
                entry.method.value,
                "" if entry.scale_factor is None else entry.scale_factor,
                entry.reference_sample_id or "",
                entry.reference_channel or "",
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_tmt_channel_distribution_tsv(report: TmtNormalizationReport) -> str:
    """Render before/after TMT channel distributions as one TSV ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "stage",
            "multiplex_group",
            "multiplex_channel",
            "sample_id",
            "condition",
            "channel_role",
            "total_abundance",
            "median_abundance",
            "interquartile_range",
            "ratio_to_group_median",
            "flagged",
            "note",
        ]
    )
    for entry in report.channel_distributions:
        writer.writerow(
            [
                entry.stage.value,
                entry.multiplex_group,
                entry.multiplex_channel,
                entry.sample_id,
                entry.condition or "",
                entry.channel_role.value,
                entry.total_abundance,
                entry.median_abundance,
                entry.interquartile_range,
                entry.ratio_to_group_median,
                str(entry.flagged).lower(),
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_tmt_normalized_peptide_matrix_tsv(report: TmtNormalizationReport) -> str:
    """Render the normalized peptide-by-channel matrix as TSV."""

    return render_tmt_peptide_matrix_tsv(report.after_report)


def render_tmt_normalized_protein_matrix_tsv(report: TmtNormalizationReport) -> str:
    """Render the normalized protein-by-channel matrix as TSV."""

    return render_tmt_protein_matrix_tsv(report.after_report)


def export_tmt_normalization_summary_tsv(
    report: TmtNormalizationReport,
    path: Path,
) -> None:
    """Write the compact TMT normalization summary ledger."""

    write_output_table_tsv(path, render_tmt_normalization_summary_tsv(report))


def export_tmt_normalization_transform_tsv(
    report: TmtNormalizationReport,
    path: Path,
) -> None:
    """Write the TMT normalization transform ledger."""

    write_output_table_tsv(path, render_tmt_normalization_transform_tsv(report))


def export_tmt_channel_distribution_tsv(
    report: TmtNormalizationReport,
    path: Path,
) -> None:
    """Write the before/after TMT channel distribution ledger."""

    write_output_table_tsv(path, render_tmt_channel_distribution_tsv(report))


def export_tmt_normalized_peptide_matrix_tsv(
    report: TmtNormalizationReport,
    path: Path,
) -> None:
    """Write the normalized TMT peptide matrix."""

    write_output_table_tsv(path, render_tmt_normalized_peptide_matrix_tsv(report))


def export_tmt_normalized_protein_matrix_tsv(
    report: TmtNormalizationReport,
    path: Path,
) -> None:
    """Write the normalized TMT protein matrix."""

    write_output_table_tsv(path, render_tmt_normalized_protein_matrix_tsv(report))
