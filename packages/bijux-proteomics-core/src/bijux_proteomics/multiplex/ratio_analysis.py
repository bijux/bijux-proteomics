# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned TMT sample-to-control ratio analysis over multiplex channel matrices."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
import math
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.multiplex.normalization import (
    TmtNormalizationPolicy,
    build_tmt_normalization_report,
)
from bijux_proteomics.multiplex.reporter_matrix import (
    TmtReporterFeatureBundle,
    TmtReporterMatrixReport,
    build_tmt_reporter_matrix_report,
)
from bijux_proteomics.quantification.contracts import LabelBasedChannelRole
from bijux_proteomics.quantification.protein_intensity_matrix import (
    ProteinMatrixTargetKind,
)
from bijux_proteomics_foundation import JsonModel


class TmtRatioSourceKind(StrEnum):
    """Whether ratios were computed from raw or normalized TMT channel matrices."""

    RAW = "raw"
    NORMALIZED = "normalized"


class TmtPeptideRatioEntry(JsonModel):
    """One peptide/sample ratio against a governed control channel."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    numerator_channel: str = Field(..., min_length=1)
    numerator_sample_id: str = Field(..., min_length=1)
    numerator_condition: str | None = None
    numerator_role: LabelBasedChannelRole
    control_channel: str = Field(..., min_length=1)
    control_sample_id: str = Field(..., min_length=1)
    control_condition: str | None = None
    peptide_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    numerator_abundance: float | None = Field(default=None, ge=0.0)
    control_abundance: float | None = Field(default=None, ge=0.0)
    ratio: float | None = Field(default=None, ge=0.0)
    log2_ratio: float | None = None
    missing_reason: str | None = None
    note: str = Field(..., min_length=1)


class TmtRatioSummary(JsonModel):
    """Compact summary over one TMT ratio-analysis run."""

    model_config = ConfigDict(extra="forbid")

    source_kind: TmtRatioSourceKind
    normalization_method: str = Field(..., min_length=1)
    control_channel: str = Field(..., min_length=1)
    multiplex_group_count: int = Field(..., ge=0)
    peptide_ratio_count: int = Field(..., ge=0)
    protein_ratio_count: int = Field(..., ge=0)
    missing_ratio_count: int = Field(..., ge=0)


class TmtProteinRatioEntry(JsonModel):
    """One protein/sample ratio against a governed control channel."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    numerator_channel: str = Field(..., min_length=1)
    numerator_sample_id: str = Field(..., min_length=1)
    numerator_condition: str | None = None
    numerator_role: LabelBasedChannelRole
    control_channel: str = Field(..., min_length=1)
    control_sample_id: str = Field(..., min_length=1)
    control_condition: str | None = None
    protein_id: str = Field(..., min_length=1)
    target_kind: ProteinMatrixTargetKind
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    numerator_abundance: float | None = Field(default=None, ge=0.0)
    control_abundance: float | None = Field(default=None, ge=0.0)
    ratio: float | None = Field(default=None, ge=0.0)
    log2_ratio: float | None = None
    missing_reason: str | None = None
    note: str = Field(..., min_length=1)


class TmtRatioReport(JsonModel):
    """Owned TMT ratio analysis with peptide and protein ledgers."""

    model_config = ConfigDict(extra="forbid")

    source_kind: TmtRatioSourceKind
    summary: TmtRatioSummary
    peptide_ratios: tuple[TmtPeptideRatioEntry, ...] = Field(default_factory=tuple)
    protein_ratios: tuple[TmtProteinRatioEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def build_tmt_ratio_report(
    feature_bundle: TmtReporterFeatureBundle,
    *,
    control_channel: str,
    normalization_policy: TmtNormalizationPolicy | None = None,
) -> TmtRatioReport:
    """Build peptide sample/control ratios over raw or normalized TMT matrices."""

    matrix_report, source_kind, normalization_method = _matrix_report_for_ratios(
        feature_bundle,
        normalization_policy=normalization_policy,
    )
    mapped_entries = tuple(
        entry
        for entry in feature_bundle.channel_mapping
        if entry.mapped_to_design and entry.sample_id is not None
    )
    control_by_group = {
        entry.multiplex_group: entry
        for entry in mapped_entries
        if entry.multiplex_channel == control_channel
    }
    if not control_by_group:
        raise ValueError("control channel is not present in the multiplex design")

    peptide_ratios: list[TmtPeptideRatioEntry] = []
    protein_ratios: list[TmtProteinRatioEntry] = []
    for peptide_row in matrix_report.peptide_matrix.rows:
        peptide_values_by_sample = {
            value.sample_id: value for value in peptide_row.values
        }
        for entry in sorted(
            mapped_entries,
            key=lambda item: (item.multiplex_group, item.multiplex_channel),
        ):
            if entry.multiplex_channel == control_channel:
                continue
            numerator_value = peptide_values_by_sample.get(entry.sample_id or "")
            control_entry = control_by_group.get(entry.multiplex_group)
            if control_entry is None:
                numerator_abundance = (
                    None if numerator_value is None else numerator_value.abundance
                )
                peptide_ratios.append(
                    TmtPeptideRatioEntry(
                        multiplex_group=entry.multiplex_group,
                        numerator_channel=entry.multiplex_channel,
                        numerator_sample_id=entry.sample_id or "",
                        numerator_condition=entry.condition,
                        numerator_role=entry.channel_role
                        or LabelBasedChannelRole.SAMPLE,
                        control_channel=control_channel,
                        control_sample_id="",
                        control_condition=None,
                        peptide_id=peptide_row.entity_id,
                        peptide_sequence=peptide_row.peptide_sequence,
                        protein_refs=peptide_row.protein_refs,
                        numerator_abundance=numerator_abundance,
                        control_abundance=None,
                        ratio=None,
                        log2_ratio=None,
                        missing_reason="control_channel_missing_from_design",
                        note="control channel is absent from the multiplex design for this group",
                    )
                )
                continue
            control_value = peptide_values_by_sample.get(control_entry.sample_id or "")
            ratio, log2_ratio, missing_reason = _ratio_from_values(
                numerator_abundance=(
                    None if numerator_value is None else numerator_value.abundance
                ),
                control_abundance=(
                    None if control_value is None else control_value.abundance
                ),
            )
            peptide_ratios.append(
                TmtPeptideRatioEntry(
                    multiplex_group=entry.multiplex_group,
                    numerator_channel=entry.multiplex_channel,
                    numerator_sample_id=entry.sample_id or "",
                    numerator_condition=entry.condition,
                    numerator_role=entry.channel_role or LabelBasedChannelRole.SAMPLE,
                    control_channel=control_channel,
                    control_sample_id=control_entry.sample_id or "",
                    control_condition=control_entry.condition,
                    peptide_id=peptide_row.entity_id,
                    peptide_sequence=peptide_row.peptide_sequence,
                    protein_refs=peptide_row.protein_refs,
                    numerator_abundance=(
                        None if numerator_value is None else numerator_value.abundance
                    ),
                    control_abundance=(
                        None if control_value is None else control_value.abundance
                    ),
                    ratio=ratio,
                    log2_ratio=log2_ratio,
                    missing_reason=missing_reason,
                    note=(
                        "sample/control ratio is computed within one multiplex group against the governed control channel"
                        if missing_reason is None
                        else "sample/control ratio is preserved even though one required channel value is missing"
                    ),
                )
            )
    for protein_row in matrix_report.protein_matrix.rows:
        protein_values_by_sample = {
            value.sample_id: value for value in protein_row.values
        }
        for entry in sorted(
            mapped_entries,
            key=lambda item: (item.multiplex_group, item.multiplex_channel),
        ):
            if entry.multiplex_channel == control_channel:
                continue
            protein_numerator_value = protein_values_by_sample.get(
                entry.sample_id or ""
            )
            control_entry = control_by_group.get(entry.multiplex_group)
            if control_entry is None:
                numerator_abundance = (
                    None
                    if protein_numerator_value is None
                    else protein_numerator_value.abundance
                )
                protein_ratios.append(
                    TmtProteinRatioEntry(
                        multiplex_group=entry.multiplex_group,
                        numerator_channel=entry.multiplex_channel,
                        numerator_sample_id=entry.sample_id or "",
                        numerator_condition=entry.condition,
                        numerator_role=entry.channel_role
                        or LabelBasedChannelRole.SAMPLE,
                        control_channel=control_channel,
                        control_sample_id="",
                        control_condition=None,
                        protein_id=protein_row.entity_id,
                        target_kind=protein_row.target_kind,
                        protein_refs=protein_row.protein_refs,
                        numerator_abundance=numerator_abundance,
                        control_abundance=None,
                        ratio=None,
                        log2_ratio=None,
                        missing_reason="control_channel_missing_from_design",
                        note="control channel is absent from the multiplex design for this group",
                    )
                )
                continue
            protein_control_value = protein_values_by_sample.get(
                control_entry.sample_id or ""
            )
            ratio, log2_ratio, missing_reason = _ratio_from_values(
                numerator_abundance=(
                    None
                    if protein_numerator_value is None
                    else protein_numerator_value.abundance
                ),
                control_abundance=(
                    None
                    if protein_control_value is None
                    else protein_control_value.abundance
                ),
            )
            protein_ratios.append(
                TmtProteinRatioEntry(
                    multiplex_group=entry.multiplex_group,
                    numerator_channel=entry.multiplex_channel,
                    numerator_sample_id=entry.sample_id or "",
                    numerator_condition=entry.condition,
                    numerator_role=entry.channel_role or LabelBasedChannelRole.SAMPLE,
                    control_channel=control_channel,
                    control_sample_id=control_entry.sample_id or "",
                    control_condition=control_entry.condition,
                    protein_id=protein_row.entity_id,
                    target_kind=protein_row.target_kind,
                    protein_refs=protein_row.protein_refs,
                    numerator_abundance=(
                        None
                        if protein_numerator_value is None
                        else protein_numerator_value.abundance
                    ),
                    control_abundance=(
                        None
                        if protein_control_value is None
                        else protein_control_value.abundance
                    ),
                    ratio=ratio,
                    log2_ratio=log2_ratio,
                    missing_reason=missing_reason,
                    note=(
                        "sample/control ratio is computed within one multiplex group against the governed control channel"
                        if missing_reason is None
                        else "sample/control ratio is preserved even though one required channel value is missing"
                    ),
                )
            )
    missing_ratio_count = sum(
        1 for entry in peptide_ratios if entry.missing_reason is not None
    ) + sum(1 for entry in protein_ratios if entry.missing_reason is not None)
    return TmtRatioReport(
        source_kind=source_kind,
        summary=TmtRatioSummary(
            source_kind=source_kind,
            normalization_method=normalization_method,
            control_channel=control_channel,
            multiplex_group_count=len(control_by_group),
            peptide_ratio_count=len(peptide_ratios),
            protein_ratio_count=len(protein_ratios),
            missing_ratio_count=missing_ratio_count,
        ),
        peptide_ratios=tuple(
            sorted(
                peptide_ratios,
                key=lambda entry: (
                    entry.multiplex_group,
                    entry.peptide_id,
                    entry.numerator_channel,
                ),
            )
        ),
        protein_ratios=tuple(
            sorted(
                protein_ratios,
                key=lambda entry: (
                    entry.multiplex_group,
                    entry.protein_id,
                    entry.numerator_channel,
                ),
            )
        ),
        note=(
            "tmt ratio analysis preserves explicit sample-to-control peptide and protein ratios within each multiplex group"
        ),
    )


def _matrix_report_for_ratios(
    feature_bundle: TmtReporterFeatureBundle,
    *,
    normalization_policy: TmtNormalizationPolicy | None,
) -> tuple[TmtReporterMatrixReport, TmtRatioSourceKind, str]:
    if normalization_policy is None:
        return (
            build_tmt_reporter_matrix_report(feature_bundle),
            TmtRatioSourceKind.RAW,
            "none",
        )
    normalization_report = build_tmt_normalization_report(
        feature_bundle,
        policy=normalization_policy,
    )
    return (
        normalization_report.after_report,
        TmtRatioSourceKind.NORMALIZED,
        normalization_policy.method.value,
    )


def _ratio_from_values(
    *,
    numerator_abundance: float | None,
    control_abundance: float | None,
) -> tuple[float | None, float | None, str | None]:
    if numerator_abundance is None:
        return None, None, "sample_channel_missing"
    if control_abundance is None:
        return None, None, "control_channel_missing"
    if control_abundance <= 0.0:
        return None, None, "control_channel_zero"
    ratio = float(numerator_abundance) / float(control_abundance)
    if ratio <= 0.0:
        return ratio, None, None
    return ratio, float(math.log2(ratio)), None


def render_tmt_ratio_summary_tsv(report: TmtRatioReport) -> str:
    """Render a compact summary over one TMT ratio-analysis run."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "source_kind",
            "normalization_method",
            "control_channel",
            "multiplex_group_count",
            "peptide_ratio_count",
            "protein_ratio_count",
            "missing_ratio_count",
        ]
    )
    writer.writerow(
        [
            report.summary.source_kind.value,
            report.summary.normalization_method,
            report.summary.control_channel,
            report.summary.multiplex_group_count,
            report.summary.peptide_ratio_count,
            report.summary.protein_ratio_count,
            report.summary.missing_ratio_count,
        ]
    )
    return buffer.getvalue()


def render_tmt_peptide_ratio_tsv(report: TmtRatioReport) -> str:
    """Render the peptide sample/control ratio ledger as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "multiplex_group",
            "numerator_channel",
            "numerator_sample_id",
            "numerator_condition",
            "numerator_role",
            "control_channel",
            "control_sample_id",
            "control_condition",
            "peptide_id",
            "peptide_sequence",
            "protein_refs",
            "numerator_abundance",
            "control_abundance",
            "ratio",
            "log2_ratio",
            "missing_reason",
            "note",
        ]
    )
    for entry in report.peptide_ratios:
        writer.writerow(
            [
                entry.multiplex_group,
                entry.numerator_channel,
                entry.numerator_sample_id,
                entry.numerator_condition or "",
                entry.numerator_role.value,
                entry.control_channel,
                entry.control_sample_id,
                entry.control_condition or "",
                entry.peptide_id,
                entry.peptide_sequence,
                ";".join(entry.protein_refs),
                "" if entry.numerator_abundance is None else entry.numerator_abundance,
                "" if entry.control_abundance is None else entry.control_abundance,
                "" if entry.ratio is None else entry.ratio,
                "" if entry.log2_ratio is None else entry.log2_ratio,
                entry.missing_reason or "",
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_tmt_protein_ratio_tsv(report: TmtRatioReport) -> str:
    """Render the protein sample/control ratio ledger as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "multiplex_group",
            "numerator_channel",
            "numerator_sample_id",
            "numerator_condition",
            "numerator_role",
            "control_channel",
            "control_sample_id",
            "control_condition",
            "protein_id",
            "target_kind",
            "protein_refs",
            "numerator_abundance",
            "control_abundance",
            "ratio",
            "log2_ratio",
            "missing_reason",
            "note",
        ]
    )
    for entry in report.protein_ratios:
        writer.writerow(
            [
                entry.multiplex_group,
                entry.numerator_channel,
                entry.numerator_sample_id,
                entry.numerator_condition or "",
                entry.numerator_role.value,
                entry.control_channel,
                entry.control_sample_id,
                entry.control_condition or "",
                entry.protein_id,
                entry.target_kind.value,
                ";".join(entry.protein_refs),
                "" if entry.numerator_abundance is None else entry.numerator_abundance,
                "" if entry.control_abundance is None else entry.control_abundance,
                "" if entry.ratio is None else entry.ratio,
                "" if entry.log2_ratio is None else entry.log2_ratio,
                entry.missing_reason or "",
                entry.note,
            ]
        )
    return buffer.getvalue()


def export_tmt_ratio_summary_tsv(report: TmtRatioReport, path: Path) -> None:
    """Write the compact TMT ratio summary ledger."""

    write_output_table_tsv(path, render_tmt_ratio_summary_tsv(report))


def export_tmt_peptide_ratio_tsv(report: TmtRatioReport, path: Path) -> None:
    """Write the peptide sample/control ratio ledger."""

    write_output_table_tsv(path, render_tmt_peptide_ratio_tsv(report))


def export_tmt_protein_ratio_tsv(report: TmtRatioReport, path: Path) -> None:
    """Write the protein sample/control ratio ledger."""

    write_output_table_tsv(path, render_tmt_protein_ratio_tsv(report))
