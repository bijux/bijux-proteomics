# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned TMT reporter-ion channel mapping and feature-conversion surfaces."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    ExperimentalDesignSampleRole,
)
from bijux_proteomics.multiplex.reporter_ion_import import TmtReporterImportReport
from bijux_proteomics.quantification import (
    LabelBasedChannelRole,
    MissingValueKind,
    Ms1FeatureRecord,
)
from bijux_proteomics_foundation import JsonModel


class TmtChannelMappingEntry(JsonModel):
    """One design-aware TMT channel mapping row."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    sample_id: str | None = None
    condition: str | None = None
    sample_role: ExperimentalDesignSampleRole | None = None
    channel_role: LabelBasedChannelRole | None = None
    source_column_present: bool
    mapped_to_design: bool
    note: str = Field(..., min_length=1)


class TmtReporterFeatureSummary(JsonModel):
    """Compact summary over design-aware TMT feature materialization."""

    model_config = ConfigDict(extra="forbid")

    accepted_source_row_count: int = Field(..., ge=0)
    multiplex_group_count: int = Field(..., ge=0)
    mapped_channel_count: int = Field(..., ge=0)
    missing_channel_count: int = Field(..., ge=0)
    unexpected_source_channel_count: int = Field(..., ge=0)
    feature_record_count: int = Field(..., ge=0)


class TmtReporterFeatureBundle(JsonModel):
    """Design-aware sample-channel materialization over imported TMT reporter rows."""

    model_config = ConfigDict(extra="forbid")

    source_report: TmtReporterImportReport
    feature_records: tuple[Ms1FeatureRecord, ...] = Field(default_factory=tuple)
    channel_mapping: tuple[TmtChannelMappingEntry, ...] = Field(default_factory=tuple)
    summary: TmtReporterFeatureSummary
    note: str = Field(..., min_length=1)


def build_tmt_reporter_feature_bundle(
    import_report: TmtReporterImportReport,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> TmtReporterFeatureBundle:
    """Map imported TMT reporter rows onto design channels and sample feature records."""

    multiplex_design_entries = tuple(
        entry
        for entry in design_entries
        if entry.multiplex_group and entry.multiplex_channel
    )
    if not multiplex_design_entries:
        raise ValueError(
            "tmt reporter import requires design entries with multiplex_group and multiplex_channel"
        )
    design_by_group: dict[str, tuple[ExperimentalDesignEntry, ...]] = {}
    for entry in multiplex_design_entries:
        design_by_group.setdefault(entry.multiplex_group or "", []).append(entry)

    source_channel_lookup = {
        entry.multiplex_channel: entry.column_name
        for entry in import_report.channel_columns
    }
    feature_records: list[Ms1FeatureRecord] = []
    unexpected_channels: set[tuple[str, str]] = set()

    for observation in import_report.accepted_rows:
        group_entries = tuple(
            sorted(
                design_by_group.get(observation.multiplex_group, ()),
                key=lambda entry: entry.multiplex_channel or "",
            )
        )
        if not group_entries:
            raise ValueError(
                f"no multiplex design entries map group {observation.multiplex_group!r}"
            )
        intensity_lookup = {
            entry.multiplex_channel: entry.intensity
            for entry in observation.channel_intensities
        }
        design_channels = {
            entry.multiplex_channel or ""
            for entry in group_entries
        }
        for channel in intensity_lookup:
            if channel not in design_channels:
                unexpected_channels.add((observation.multiplex_group, channel))
        for design_entry in group_entries:
            multiplex_channel = design_entry.multiplex_channel or ""
            intensity = intensity_lookup.get(multiplex_channel)
            if intensity is None:
                missing_value_kind = MissingValueKind.NOT_OBSERVED
                missing_reason = "reporter_channel_missing"
            elif intensity == 0.0:
                missing_value_kind = MissingValueKind.ZERO
                missing_reason = None
            else:
                missing_value_kind = MissingValueKind.OBSERVED
                missing_reason = None
            feature_records.append(
                Ms1FeatureRecord(
                    feature_id=f"{observation.source_row_id}:{multiplex_channel}",
                    sample_id=design_entry.sample_id,
                    peptide=observation.modified_peptide,
                    canonical_peptide=observation.canonical_peptide,
                    intensity=intensity,
                    protein_refs=observation.protein_refs,
                    missing_value_kind=missing_value_kind,
                    missing_reason=missing_reason,
                )
            )

    channel_mapping: list[TmtChannelMappingEntry] = []
    for multiplex_group, entries in sorted(design_by_group.items()):
        for entry in sorted(entries, key=lambda item: item.multiplex_channel or ""):
            multiplex_channel = entry.multiplex_channel or ""
            source_column_present = multiplex_channel in source_channel_lookup
            channel_mapping.append(
                TmtChannelMappingEntry(
                    multiplex_group=multiplex_group,
                    multiplex_channel=multiplex_channel,
                    sample_id=entry.sample_id,
                    condition=entry.condition,
                    sample_role=entry.sample_role,
                    channel_role=_default_channel_role(entry),
                    source_column_present=source_column_present,
                    mapped_to_design=True,
                    note=(
                        "design channel is backed by a source reporter column"
                        if source_column_present
                        else "design channel is preserved even though the source table does not expose that reporter column"
                    ),
                )
            )
    for multiplex_group, multiplex_channel in sorted(unexpected_channels):
        channel_mapping.append(
            TmtChannelMappingEntry(
                multiplex_group=multiplex_group,
                multiplex_channel=multiplex_channel,
                sample_id=None,
                condition=None,
                sample_role=None,
                channel_role=None,
                source_column_present=True,
                mapped_to_design=False,
                note="source reporter channel was observed but is not mapped in the design table",
            )
        )

    missing_channel_count = sum(
        1
        for entry in channel_mapping
        if entry.mapped_to_design and not entry.source_column_present
    )
    return TmtReporterFeatureBundle(
        source_report=import_report,
        feature_records=tuple(feature_records),
        channel_mapping=tuple(channel_mapping),
        summary=TmtReporterFeatureSummary(
            accepted_source_row_count=import_report.summary.accepted_row_count,
            multiplex_group_count=len(
                {
                    entry.multiplex_group
                    for entry in channel_mapping
                    if entry.mapped_to_design
                }
            ),
            mapped_channel_count=sum(
                1 for entry in channel_mapping if entry.mapped_to_design
            ),
            missing_channel_count=missing_channel_count,
            unexpected_source_channel_count=len(unexpected_channels),
            feature_record_count=len(feature_records),
        ),
        note=(
            "tmt reporter channel mapping turns multiplex-group reporter rows into explicit sample-channel feature records while preserving missing and unmapped channels"
        ),
    )


def _default_channel_role(
    entry: ExperimentalDesignEntry,
) -> LabelBasedChannelRole:
    if entry.sample_role is ExperimentalDesignSampleRole.POOLED_REFERENCE:
        return LabelBasedChannelRole.REFERENCE
    if entry.sample_role is ExperimentalDesignSampleRole.QC_BRIDGE:
        return LabelBasedChannelRole.QC_BRIDGE
    return LabelBasedChannelRole.SAMPLE
