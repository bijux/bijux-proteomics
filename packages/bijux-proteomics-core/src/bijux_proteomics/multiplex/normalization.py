# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned TMT reporter-channel normalization and distribution review surfaces."""

from __future__ import annotations

from enum import StrEnum

import numpy as np
from pydantic import ConfigDict, Field

from bijux_proteomics.multiplex.reporter_matrix import (
    TmtChannelMappingEntry,
    TmtReporterFeatureBundle,
    TmtReporterMatrixReport,
    build_tmt_reporter_matrix_report,
)
from bijux_proteomics.quantification import LabelBasedChannelRole
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
    transforms: tuple[TmtNormalizationTransformEntry, ...] = Field(default_factory=tuple)
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

    if active_policy.method is not TmtNormalizationMethod.MEDIAN:
        raise ValueError(
            "tmt normalization currently supports only the median method in the owned multiplex surface"
        )

    normalized_records, transforms = _apply_median_normalization(
        feature_bundle,
        policy=active_policy,
    )
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
                [entry for entry in feature_bundle.channel_mapping if entry.mapped_to_design]
            ),
            transform_count=len(transforms),
            before_flagged_channel_count=before_flagged,
            after_flagged_channel_count=after_flagged,
            reference_group_count=0,
        ),
        note=(
            "tmt normalization preserves before and after multiplex channel distributions alongside normalized peptide and protein matrices"
        ),
    )


def _apply_median_normalization(
    feature_bundle: TmtReporterFeatureBundle,
    *,
    policy: TmtNormalizationPolicy,
) -> tuple[tuple, tuple[TmtNormalizationTransformEntry, ...]]:
    sample_records: dict[str, list] = {}
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
        group_median = float(np.median(np.array(finite_medians, dtype=float))) if finite_medians else 1.0
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
                    channel_role=mapping_entry.channel_role or LabelBasedChannelRole.SAMPLE,
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
    sample_records: dict[str, list] = {}
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
            [float(record.intensity) for record in records if record.intensity is not None],
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
                    or (
                        ratio > 0.0
                        and ratio < 1.0 / policy.balance_ratio_threshold
                    )
                ),
                note=entry.note,
            )
        )
    return rendered
