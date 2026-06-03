# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned TMT reporter-ion channel mapping and feature-conversion surfaces."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    ExperimentalDesignSampleRole,
)
from bijux_proteomics.multiplex.reporter_ion_import import TmtReporterImportReport
from bijux_proteomics.quantification import (
    LabelBasedChannelRole,
    MissingValueKind,
    Ms1FeatureRecord,
    QuantRollupMethod,
    build_peptide_intensity_matrix_from_features,
    build_protein_intensity_matrix_from_features,
)
from bijux_proteomics.quantification.peptide_intensity_matrix import (
    PeptideIntensityMatrixReport,
    PeptideMatrixGroupingMode,
    render_peptide_intensity_matrix_tsv,
)
from bijux_proteomics.quantification.protein_intensity_matrix import (
    ProteinIntensityMatrixReport,
    ProteinMatrixTargetKind,
    render_protein_intensity_matrix_tsv,
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
    design_entries: tuple[ExperimentalDesignEntry, ...] = Field(default_factory=tuple)
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
    design_by_group: dict[str, list[ExperimentalDesignEntry]] = {}
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
        design_channels = {entry.multiplex_channel or "" for entry in group_entries}
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
        design_entries=tuple(multiplex_design_entries),
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


class TmtChannelTotalEntry(JsonModel):
    """One multiplex channel total with explicit sample and missingness context."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    sample_id: str | None = None
    condition: str | None = None
    channel_role: LabelBasedChannelRole | None = None
    total_intensity: float = Field(..., ge=0.0)
    observed_row_count: int = Field(..., ge=0)
    missing_row_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class TmtReporterMatrixSummary(JsonModel):
    """Compact summary over TMT channel totals plus peptide/protein matrices."""

    model_config = ConfigDict(extra="forbid")

    feature_record_count: int = Field(..., ge=0)
    missing_channel_count: int = Field(..., ge=0)
    peptide_row_count: int = Field(..., ge=0)
    protein_row_count: int = Field(..., ge=0)
    channel_total_count: int = Field(..., ge=0)


class TmtReporterMatrixReport(JsonModel):
    """Owned TMT reporter-ion review over channel mapping, totals, and matrices."""

    model_config = ConfigDict(extra="forbid")

    source_report: TmtReporterImportReport
    feature_bundle: TmtReporterFeatureBundle
    peptide_matrix: PeptideIntensityMatrixReport
    protein_matrix: ProteinIntensityMatrixReport
    channel_totals: tuple[TmtChannelTotalEntry, ...] = Field(default_factory=tuple)
    summary: TmtReporterMatrixSummary
    note: str = Field(..., min_length=1)


def build_tmt_reporter_matrix_report(
    feature_bundle: TmtReporterFeatureBundle,
    *,
    grouping_mode: PeptideMatrixGroupingMode = PeptideMatrixGroupingMode.MODIFIED_PEPTIDE,
    separate_charge_states: bool = False,
    target_kind: ProteinMatrixTargetKind = ProteinMatrixTargetKind.PROTEIN,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    unique_only: bool = False,
    top_n: int = 3,
) -> TmtReporterMatrixReport:
    """Build channel totals plus peptide/protein matrices from TMT feature materialization."""

    peptide_matrix = build_peptide_intensity_matrix_from_features(
        feature_bundle.feature_records,
        grouping_mode=grouping_mode,
        separate_charge_states=separate_charge_states,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    protein_matrix = build_protein_intensity_matrix_from_features(
        feature_bundle.feature_records,
        grouping_mode=grouping_mode,
        separate_charge_states=separate_charge_states,
        target_kind=target_kind,
        aggregation_method=aggregation_method,
        unique_only=unique_only,
        top_n=top_n,
    )
    records_by_sample: dict[str, list[Ms1FeatureRecord]] = {}
    for record in feature_bundle.feature_records:
        records_by_sample.setdefault(record.sample_id, []).append(record)
    channel_totals: list[TmtChannelTotalEntry] = []
    for entry in feature_bundle.channel_mapping:
        if not entry.mapped_to_design or entry.sample_id is None:
            continue
        sample_records = records_by_sample.get(entry.sample_id, [])
        total_intensity = float(
            sum(
                record.intensity or 0.0
                for record in sample_records
                if record.intensity is not None
            )
        )
        observed_row_count = sum(
            1 for record in sample_records if record.intensity is not None
        )
        missing_row_count = sum(
            1 for record in sample_records if record.intensity is None
        )
        channel_totals.append(
            TmtChannelTotalEntry(
                multiplex_group=entry.multiplex_group,
                multiplex_channel=entry.multiplex_channel,
                sample_id=entry.sample_id,
                condition=entry.condition,
                channel_role=entry.channel_role,
                total_intensity=total_intensity,
                observed_row_count=observed_row_count,
                missing_row_count=missing_row_count,
                note=entry.note,
            )
        )
    return TmtReporterMatrixReport(
        source_report=feature_bundle.source_report,
        feature_bundle=feature_bundle,
        peptide_matrix=peptide_matrix,
        protein_matrix=protein_matrix,
        channel_totals=tuple(
            sorted(
                channel_totals,
                key=lambda entry: (entry.multiplex_group, entry.multiplex_channel),
            )
        ),
        summary=TmtReporterMatrixSummary(
            feature_record_count=len(feature_bundle.feature_records),
            missing_channel_count=feature_bundle.summary.missing_channel_count,
            peptide_row_count=peptide_matrix.summary.peptide_row_count,
            protein_row_count=protein_matrix.summary.protein_row_count,
            channel_total_count=len(channel_totals),
        ),
        note=(
            "tmt reporter review preserves design-aware channel totals alongside peptide and protein channel matrices"
        ),
    )


def render_tmt_report_summary_tsv(report: TmtReporterMatrixReport) -> str:
    """Render a compact summary over the TMT reporter review surface."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "accepted_source_row_count",
            "rejected_source_row_count",
            "multiplex_group_count",
            "mapped_channel_count",
            "missing_channel_count",
            "unexpected_source_channel_count",
            "feature_record_count",
            "peptide_row_count",
            "protein_row_count",
            "channel_total_count",
        ]
    )
    writer.writerow(
        [
            report.source_report.summary.accepted_row_count,
            report.source_report.summary.rejected_row_count,
            report.feature_bundle.summary.multiplex_group_count,
            report.feature_bundle.summary.mapped_channel_count,
            report.summary.missing_channel_count,
            report.feature_bundle.summary.unexpected_source_channel_count,
            report.summary.feature_record_count,
            report.summary.peptide_row_count,
            report.summary.protein_row_count,
            report.summary.channel_total_count,
        ]
    )
    return buffer.getvalue()


def render_tmt_channel_mapping_tsv(report: TmtReporterMatrixReport) -> str:
    """Render the design-aware TMT channel mapping ledger as TSV."""

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
            "source_column_present",
            "mapped_to_design",
            "note",
        ]
    )
    for entry in report.feature_bundle.channel_mapping:
        writer.writerow(
            [
                entry.multiplex_group,
                entry.multiplex_channel,
                entry.sample_id or "",
                entry.condition or "",
                "" if entry.sample_role is None else entry.sample_role.value,
                "" if entry.channel_role is None else entry.channel_role.value,
                str(entry.source_column_present).lower(),
                str(entry.mapped_to_design).lower(),
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_tmt_channel_totals_tsv(report: TmtReporterMatrixReport) -> str:
    """Render one per-channel total ledger over the TMT review surface."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "multiplex_group",
            "multiplex_channel",
            "sample_id",
            "condition",
            "channel_role",
            "total_intensity",
            "observed_row_count",
            "missing_row_count",
            "note",
        ]
    )
    for entry in report.channel_totals:
        writer.writerow(
            [
                entry.multiplex_group,
                entry.multiplex_channel,
                entry.sample_id or "",
                entry.condition or "",
                "" if entry.channel_role is None else entry.channel_role.value,
                entry.total_intensity,
                entry.observed_row_count,
                entry.missing_row_count,
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_tmt_peptide_matrix_tsv(report: TmtReporterMatrixReport) -> str:
    """Render the TMT peptide-by-channel matrix as TSV."""

    return render_peptide_intensity_matrix_tsv(report.peptide_matrix)


def render_tmt_protein_matrix_tsv(report: TmtReporterMatrixReport) -> str:
    """Render the TMT protein-by-channel matrix as TSV."""

    return render_protein_intensity_matrix_tsv(report.protein_matrix)


def export_tmt_report_summary_tsv(report: TmtReporterMatrixReport, path: Path) -> None:
    """Write the compact TMT report summary ledger."""

    write_output_table_tsv(path, render_tmt_report_summary_tsv(report))


def export_tmt_channel_mapping_tsv(report: TmtReporterMatrixReport, path: Path) -> None:
    """Write the TMT channel mapping ledger."""

    write_output_table_tsv(path, render_tmt_channel_mapping_tsv(report))


def export_tmt_channel_totals_tsv(report: TmtReporterMatrixReport, path: Path) -> None:
    """Write the TMT channel totals ledger."""

    write_output_table_tsv(path, render_tmt_channel_totals_tsv(report))


def export_tmt_peptide_matrix_tsv(report: TmtReporterMatrixReport, path: Path) -> None:
    """Write the TMT peptide matrix."""

    write_output_table_tsv(path, render_tmt_peptide_matrix_tsv(report))


def export_tmt_protein_matrix_tsv(report: TmtReporterMatrixReport, path: Path) -> None:
    """Write the TMT protein matrix."""

    write_output_table_tsv(path, render_tmt_protein_matrix_tsv(report))


def _default_channel_role(
    entry: ExperimentalDesignEntry,
) -> LabelBasedChannelRole:
    if entry.sample_role is ExperimentalDesignSampleRole.POOLED_REFERENCE:
        return LabelBasedChannelRole.REFERENCE
    if entry.sample_role is ExperimentalDesignSampleRole.QC_BRIDGE:
        return LabelBasedChannelRole.QC_BRIDGE
    return LabelBasedChannelRole.SAMPLE
