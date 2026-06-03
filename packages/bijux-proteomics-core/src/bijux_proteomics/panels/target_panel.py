# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""User-defined peptide and protein panel review over DIA and LFQ matrices."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.dia import (
    DiaPeptideMatrixReport,
    DiaProteinMatrixReport,
    DiaProteinMatrixTargetKind,
    build_diann_peptide_matrix_report,
    build_diann_protein_matrix_report,
)
from bijux_proteomics.io import (
    TargetPanelEntry,
    TargetPanelKind,
    TargetPanelParseReport,
    parse_target_panel_table,
)
from bijux_proteomics.quantification import (
    PeptideIntensityMatrixReport,
    ProteinIntensityMatrixReport,
    ProteinLfqReport,
    ProteinMatrixTargetKind,
    build_peptide_intensity_matrix_from_features,
    build_protein_intensity_matrix_from_features,
    build_protein_lfq_report_from_features,
    parse_ms1_feature_table,
)
from bijux_proteomics_foundation import JsonModel


class TargetPanelSourceKind(StrEnum):
    """Supported matrix families that can be filtered to one target panel."""

    DIA_PEPTIDE = "dia_peptide"
    LFQ_PEPTIDE = "lfq_peptide"
    DIA_PROTEIN = "dia_protein"
    LFQ_PROTEIN = "lfq_protein"
    LFQ_PROTEIN_LFQ = "lfq_protein_lfq"


class TargetPanelMatrixValue(JsonModel):
    """One sample-specific filtered target value."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    detected: bool


class TargetPanelFilteredRow(JsonModel):
    """One matrix row retained by one target-panel match."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    target_kind: TargetPanelKind
    matched_entity_id: str = Field(..., min_length=1)
    peptide_sequence: str | None = None
    modified_peptide: str | None = None
    expected_charge: int | None = Field(default=None, ge=1)
    charge_states: tuple[int, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    values: tuple[TargetPanelMatrixValue, ...] = Field(default_factory=tuple)


class TargetPanelIntensityEntry(JsonModel):
    """One long-form intensity cell kept after panel filtering."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    target_kind: TargetPanelKind
    matched_entity_id: str = Field(..., min_length=1)
    modified_peptide: str | None = None
    expected_charge: int | None = Field(default=None, ge=1)
    sample_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    detected: bool


class TargetPanelMatchedTarget(JsonModel):
    """One requested target that matched at least one retained matrix row."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    target_kind: TargetPanelKind
    modified_peptide: str | None = None
    expected_charge: int | None = Field(default=None, ge=1)
    matched_entity_ids: tuple[str, ...] = Field(default_factory=tuple)
    detected_sample_count: int = Field(..., ge=0)


class TargetPanelMissingTarget(JsonModel):
    """One requested target that could not be reviewed on the selected matrix surface."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    target_kind: TargetPanelKind
    modified_peptide: str | None = None
    expected_charge: int | None = Field(default=None, ge=1)
    reason: str = Field(..., min_length=1)


class TargetPanelSummary(JsonModel):
    """Compact summary over one filtered panel review."""

    model_config = ConfigDict(extra="forbid")

    total_target_count: int = Field(..., ge=0)
    matched_target_count: int = Field(..., ge=0)
    missing_target_count: int = Field(..., ge=0)
    matched_entity_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)


class TargetPanelReport(JsonModel):
    """Owned user-defined target-panel review over one matrix surface."""

    model_config = ConfigDict(extra="forbid")

    source_kind: TargetPanelSourceKind
    source_name: str = Field(..., min_length=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    matched_targets: tuple[TargetPanelMatchedTarget, ...] = Field(default_factory=tuple)
    missing_targets: tuple[TargetPanelMissingTarget, ...] = Field(default_factory=tuple)
    filtered_rows: tuple[TargetPanelFilteredRow, ...] = Field(default_factory=tuple)
    intensity_entries: tuple[TargetPanelIntensityEntry, ...] = Field(
        default_factory=tuple
    )
    summary: TargetPanelSummary
    note: str = Field(..., min_length=1)


def build_diann_peptide_target_panel_report(
    result_tsv_path: Path,
    panel_path: Path,
    *,
    config_path: Path | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = None,
) -> TargetPanelReport:
    """Filter a DIA peptide-by-sample matrix to one user-defined target panel."""

    matrix_report = build_diann_peptide_matrix_report(
        result_tsv_path,
        config_path=config_path,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
    )
    return build_target_panel_report_from_dia_peptide_matrix(
        parse_target_panel_table(panel_path),
        matrix_report,
    )


def build_lfq_peptide_target_panel_report(
    feature_table_path: Path,
    panel_path: Path,
) -> TargetPanelReport:
    """Filter an LFQ peptide-by-sample matrix to one user-defined target panel."""

    feature_report = parse_ms1_feature_table(feature_table_path)
    matrix_report = build_peptide_intensity_matrix_from_features(
        feature_report.accepted_records
    )
    return build_target_panel_report_from_peptide_intensity_matrix(
        parse_target_panel_table(panel_path),
        matrix_report,
    )


def build_diann_protein_target_panel_report(
    result_tsv_path: Path,
    panel_path: Path,
    *,
    config_path: Path | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = None,
) -> TargetPanelReport:
    """Filter a DIA protein-by-sample matrix to one user-defined target panel."""

    matrix_report = build_diann_protein_matrix_report(
        result_tsv_path,
        config_path=config_path,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
        target_kind=DiaProteinMatrixTargetKind.PROTEIN,
    )
    return build_target_panel_report_from_dia_protein_matrix(
        parse_target_panel_table(panel_path),
        matrix_report,
    )


def build_lfq_protein_target_panel_report(
    feature_table_path: Path,
    panel_path: Path,
) -> TargetPanelReport:
    """Filter an LFQ protein-intensity matrix to one user-defined target panel."""

    feature_report = parse_ms1_feature_table(feature_table_path)
    matrix_report = build_protein_intensity_matrix_from_features(
        feature_report.accepted_records,
        target_kind=ProteinMatrixTargetKind.PROTEIN,
    )
    return build_target_panel_report_from_protein_intensity_matrix(
        parse_target_panel_table(panel_path),
        matrix_report,
    )


def build_lfq_protein_lfq_target_panel_report(
    feature_table_path: Path,
    panel_path: Path,
) -> TargetPanelReport:
    """Filter an LFQ MaxLFQ-like protein matrix to one user-defined target panel."""

    feature_report = parse_ms1_feature_table(feature_table_path)
    matrix_report = build_protein_lfq_report_from_features(
        feature_report.accepted_records,
        target_kind=ProteinMatrixTargetKind.PROTEIN,
    )
    return build_target_panel_report_from_protein_lfq_matrix(
        parse_target_panel_table(panel_path),
        matrix_report,
    )


def build_target_panel_report_from_dia_peptide_matrix(
    panel_report: TargetPanelParseReport,
    matrix_report: DiaPeptideMatrixReport,
) -> TargetPanelReport:
    """Filter one DIA peptide matrix to one user-defined target panel."""

    return _build_peptide_target_panel_report(
        panel_report,
        source_kind=TargetPanelSourceKind.DIA_PEPTIDE,
        source_name=matrix_report.source_name,
        sample_ids=matrix_report.sample_ids,
        row_specs=tuple(
            _PeptideRowSpec(
                entity_id=row.peptide_key,
                peptide_sequence=row.canonical_peptide,
                modified_peptides=(row.modified_peptide,),
                charge_states=tuple(
                    sorted(
                        {
                            charge
                            for value in row.values
                            for charge in value.charge_states
                        }
                    )
                ),
                protein_refs=row.protein_refs,
                values=tuple(
                    _TargetValueSpec(
                        sample_id=value.sample_id,
                        abundance=value.abundance,
                        detected=value.detected,
                    )
                    for value in row.values
                ),
            )
            for row in matrix_report.rows
        ),
    )


def build_target_panel_report_from_peptide_intensity_matrix(
    panel_report: TargetPanelParseReport,
    matrix_report: PeptideIntensityMatrixReport,
) -> TargetPanelReport:
    """Filter one LFQ peptide matrix to one user-defined target panel."""

    return _build_peptide_target_panel_report(
        panel_report,
        source_kind=TargetPanelSourceKind.LFQ_PEPTIDE,
        source_name=matrix_report.source_kind.value,
        sample_ids=matrix_report.sample_ids,
        row_specs=tuple(
            _PeptideRowSpec(
                entity_id=row.entity_id,
                peptide_sequence=row.peptide_sequence,
                modified_peptides=row.modified_peptides,
                charge_states=row.charge_states,
                protein_refs=row.protein_refs,
                values=tuple(
                    _TargetValueSpec(
                        sample_id=value.sample_id,
                        abundance=value.abundance,
                        detected=value.abundance is not None,
                    )
                    for value in row.values
                ),
            )
            for row in matrix_report.rows
        ),
    )


def build_target_panel_report_from_dia_protein_matrix(
    panel_report: TargetPanelParseReport,
    matrix_report: DiaProteinMatrixReport,
) -> TargetPanelReport:
    """Filter one DIA protein matrix to one user-defined target panel."""

    return _build_protein_target_panel_report(
        panel_report,
        source_kind=TargetPanelSourceKind.DIA_PROTEIN,
        source_name=matrix_report.source_name,
        sample_ids=matrix_report.sample_ids,
        row_specs=tuple(
            _ProteinRowSpec(
                entity_id=row.entity_id,
                protein_refs=row.protein_refs,
                values=tuple(
                    _TargetValueSpec(
                        sample_id=value.sample_id,
                        abundance=value.abundance,
                        detected=value.detected,
                    )
                    for value in row.values
                ),
            )
            for row in matrix_report.rows
        ),
    )


def build_target_panel_report_from_protein_intensity_matrix(
    panel_report: TargetPanelParseReport,
    matrix_report: ProteinIntensityMatrixReport,
) -> TargetPanelReport:
    """Filter one LFQ protein-intensity matrix to one user-defined target panel."""

    return _build_protein_target_panel_report(
        panel_report,
        source_kind=TargetPanelSourceKind.LFQ_PROTEIN,
        source_name=matrix_report.source_kind.value,
        sample_ids=matrix_report.sample_ids,
        row_specs=tuple(
            _ProteinRowSpec(
                entity_id=row.entity_id,
                protein_refs=row.protein_refs,
                values=tuple(
                    _TargetValueSpec(
                        sample_id=value.sample_id,
                        abundance=value.abundance,
                        detected=value.abundance is not None,
                    )
                    for value in row.values
                ),
            )
            for row in matrix_report.rows
        ),
    )


def build_target_panel_report_from_protein_lfq_matrix(
    panel_report: TargetPanelParseReport,
    matrix_report: ProteinLfqReport,
) -> TargetPanelReport:
    """Filter one LFQ MaxLFQ-like protein matrix to one user-defined target panel."""

    return _build_protein_target_panel_report(
        panel_report,
        source_kind=TargetPanelSourceKind.LFQ_PROTEIN_LFQ,
        source_name=matrix_report.source_kind.value,
        sample_ids=matrix_report.sample_ids,
        row_specs=tuple(
            _ProteinRowSpec(
                entity_id=row.entity_id,
                protein_refs=row.protein_refs,
                values=tuple(
                    _TargetValueSpec(
                        sample_id=value.sample_id,
                        abundance=value.abundance,
                        detected=value.abundance is not None,
                    )
                    for value in row.values
                ),
            )
            for row in matrix_report.rows
        ),
    )


@dataclass(frozen=True)
class _TargetValueSpec:
    sample_id: str
    abundance: float | None
    detected: bool


@dataclass(frozen=True)
class _PeptideRowSpec:
    entity_id: str
    peptide_sequence: str
    modified_peptides: tuple[str, ...]
    charge_states: tuple[int, ...]
    protein_refs: tuple[str, ...]
    values: tuple[_TargetValueSpec, ...]


@dataclass(frozen=True)
class _ProteinRowSpec:
    entity_id: str
    protein_refs: tuple[str, ...]
    values: tuple[_TargetValueSpec, ...]


def _build_peptide_target_panel_report(
    panel_report: TargetPanelParseReport,
    *,
    source_kind: TargetPanelSourceKind,
    source_name: str,
    sample_ids: tuple[str, ...],
    row_specs: tuple[_PeptideRowSpec, ...],
) -> TargetPanelReport:
    filtered_rows: list[TargetPanelFilteredRow] = []
    intensity_entries: list[TargetPanelIntensityEntry] = []
    matched_targets: list[TargetPanelMatchedTarget] = []
    missing_targets: list[TargetPanelMissingTarget] = []

    for target in panel_report.accepted_entries:
        matching_rows = tuple(_matching_peptide_rows(target, row_specs))
        if not matching_rows:
            missing_targets.append(
                TargetPanelMissingTarget(
                    target_id=target.target_id,
                    target_kind=target.target_kind,
                    modified_peptide=target.modified_peptide,
                    expected_charge=target.expected_charge,
                    reason="target is absent from the selected peptide-level matrix",
                )
            )
            continue
        detected_samples = {
            value.sample_id
            for row in matching_rows
            for value in row.values
            if value.detected
        }
        matched_targets.append(
            TargetPanelMatchedTarget(
                target_id=target.target_id,
                target_kind=target.target_kind,
                modified_peptide=target.modified_peptide,
                expected_charge=target.expected_charge,
                matched_entity_ids=tuple(row.entity_id for row in matching_rows),
                detected_sample_count=len(detected_samples),
            )
        )
        for row in matching_rows:
            filtered_rows.append(
                TargetPanelFilteredRow(
                    target_id=target.target_id,
                    target_kind=target.target_kind,
                    matched_entity_id=row.entity_id,
                    peptide_sequence=row.peptide_sequence,
                    modified_peptide=target.modified_peptide,
                    expected_charge=target.expected_charge,
                    charge_states=row.charge_states,
                    protein_refs=row.protein_refs,
                    values=tuple(
                        TargetPanelMatrixValue(
                            sample_id=value.sample_id,
                            abundance=value.abundance,
                            detected=value.detected,
                        )
                        for value in row.values
                    ),
                )
            )
            for value in row.values:
                intensity_entries.append(
                    TargetPanelIntensityEntry(
                        target_id=target.target_id,
                        target_kind=target.target_kind,
                        matched_entity_id=row.entity_id,
                        modified_peptide=target.modified_peptide,
                        expected_charge=target.expected_charge,
                        sample_id=value.sample_id,
                        abundance=value.abundance,
                        detected=value.detected,
                    )
                )

    return TargetPanelReport(
        source_kind=source_kind,
        source_name=source_name,
        sample_ids=sample_ids,
        matched_targets=tuple(matched_targets),
        missing_targets=tuple(missing_targets),
        filtered_rows=tuple(filtered_rows),
        intensity_entries=tuple(intensity_entries),
        summary=TargetPanelSummary(
            total_target_count=len(panel_report.accepted_entries),
            matched_target_count=len(matched_targets),
            missing_target_count=len(missing_targets),
            matched_entity_count=len(filtered_rows),
            sample_count=len(sample_ids),
        ),
        note=(
            "target-panel review keeps peptide-level rows, missing targets, and sample intensities explicit for user-defined biomarker-focused analysis"
        ),
    )


def _build_protein_target_panel_report(
    panel_report: TargetPanelParseReport,
    *,
    source_kind: TargetPanelSourceKind,
    source_name: str,
    sample_ids: tuple[str, ...],
    row_specs: tuple[_ProteinRowSpec, ...],
) -> TargetPanelReport:
    filtered_rows: list[TargetPanelFilteredRow] = []
    intensity_entries: list[TargetPanelIntensityEntry] = []
    matched_targets: list[TargetPanelMatchedTarget] = []
    missing_targets: list[TargetPanelMissingTarget] = []

    for target in panel_report.accepted_entries:
        if target.target_kind is TargetPanelKind.PEPTIDE:
            missing_targets.append(
                TargetPanelMissingTarget(
                    target_id=target.target_id,
                    target_kind=target.target_kind,
                    modified_peptide=target.modified_peptide,
                    expected_charge=target.expected_charge,
                    reason="peptide targets require a peptide-level matrix",
                )
            )
            continue
        matching_rows = tuple(_matching_protein_rows(target, row_specs))
        if not matching_rows:
            missing_targets.append(
                TargetPanelMissingTarget(
                    target_id=target.target_id,
                    target_kind=target.target_kind,
                    modified_peptide=target.modified_peptide,
                    expected_charge=target.expected_charge,
                    reason="target is absent from the selected protein-level matrix",
                )
            )
            continue
        detected_samples = {
            value.sample_id
            for row in matching_rows
            for value in row.values
            if value.detected
        }
        matched_targets.append(
            TargetPanelMatchedTarget(
                target_id=target.target_id,
                target_kind=target.target_kind,
                modified_peptide=target.modified_peptide,
                expected_charge=target.expected_charge,
                matched_entity_ids=tuple(row.entity_id for row in matching_rows),
                detected_sample_count=len(detected_samples),
            )
        )
        for row in matching_rows:
            filtered_rows.append(
                TargetPanelFilteredRow(
                    target_id=target.target_id,
                    target_kind=target.target_kind,
                    matched_entity_id=row.entity_id,
                    modified_peptide=target.modified_peptide,
                    expected_charge=target.expected_charge,
                    protein_refs=row.protein_refs,
                    values=tuple(
                        TargetPanelMatrixValue(
                            sample_id=value.sample_id,
                            abundance=value.abundance,
                            detected=value.detected,
                        )
                        for value in row.values
                    ),
                )
            )
            for value in row.values:
                intensity_entries.append(
                    TargetPanelIntensityEntry(
                        target_id=target.target_id,
                        target_kind=target.target_kind,
                        matched_entity_id=row.entity_id,
                        modified_peptide=target.modified_peptide,
                        expected_charge=target.expected_charge,
                        sample_id=value.sample_id,
                        abundance=value.abundance,
                        detected=value.detected,
                    )
                )

    return TargetPanelReport(
        source_kind=source_kind,
        source_name=source_name,
        sample_ids=sample_ids,
        matched_targets=tuple(matched_targets),
        missing_targets=tuple(missing_targets),
        filtered_rows=tuple(filtered_rows),
        intensity_entries=tuple(intensity_entries),
        summary=TargetPanelSummary(
            total_target_count=len(panel_report.accepted_entries),
            matched_target_count=len(matched_targets),
            missing_target_count=len(missing_targets),
            matched_entity_count=len(filtered_rows),
            sample_count=len(sample_ids),
        ),
        note=(
            "target-panel review keeps protein-level rows, missing targets, and sample intensities explicit for user-defined biomarker-focused analysis"
        ),
    )


def _matching_peptide_rows(
    target: TargetPanelEntry,
    row_specs: tuple[_PeptideRowSpec, ...],
) -> tuple[_PeptideRowSpec, ...]:
    if target.target_kind is TargetPanelKind.PEPTIDE:
        return tuple(
            row
            for row in row_specs
            if row.peptide_sequence == target.peptide_sequence
            and (
                target.modified_peptide is None
                or target.modified_peptide in row.modified_peptides
            )
            and (
                target.expected_charge is None
                or target.expected_charge in row.charge_states
            )
        )
    return tuple(row for row in row_specs if target.protein_ref in row.protein_refs)


def _matching_protein_rows(
    target: TargetPanelEntry,
    row_specs: tuple[_ProteinRowSpec, ...],
) -> tuple[_ProteinRowSpec, ...]:
    return tuple(
        row
        for row in row_specs
        if row.entity_id == target.protein_ref or target.protein_ref in row.protein_refs
    )


def render_target_panel_summary_tsv(report: TargetPanelReport) -> str:
    """Render a compact summary for one target-panel review."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "source_kind",
            "source_name",
            "total_target_count",
            "matched_target_count",
            "missing_target_count",
            "matched_entity_count",
            "sample_count",
            "note",
        ]
    )
    writer.writerow(
        [
            report.source_kind.value,
            report.source_name,
            report.summary.total_target_count,
            report.summary.matched_target_count,
            report.summary.missing_target_count,
            report.summary.matched_entity_count,
            report.summary.sample_count,
            report.note,
        ]
    )
    return buffer.getvalue()


def render_target_panel_target_tsv(report: TargetPanelReport) -> str:
    """Render one row per matched target."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "target_id",
            "target_kind",
            "modified_peptide",
            "expected_charge",
            "matched_entity_ids",
            "detected_sample_count",
        ]
    )
    for entry in report.matched_targets:
        writer.writerow(
            [
                entry.target_id,
                entry.target_kind.value,
                entry.modified_peptide or "",
                "" if entry.expected_charge is None else entry.expected_charge,
                ";".join(entry.matched_entity_ids),
                entry.detected_sample_count,
            ]
        )
    return buffer.getvalue()


def render_target_panel_missing_tsv(report: TargetPanelReport) -> str:
    """Render missing targets and stable reasons."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        ["target_id", "target_kind", "modified_peptide", "expected_charge", "reason"]
    )
    for entry in report.missing_targets:
        writer.writerow(
            [
                entry.target_id,
                entry.target_kind.value,
                entry.modified_peptide or "",
                "" if entry.expected_charge is None else entry.expected_charge,
                entry.reason,
            ]
        )
    return buffer.getvalue()


def render_target_panel_intensity_tsv(report: TargetPanelReport) -> str:
    """Render long-form target intensities."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "target_id",
            "target_kind",
            "matched_entity_id",
            "modified_peptide",
            "expected_charge",
            "sample_id",
            "abundance",
            "detected",
        ]
    )
    for entry in report.intensity_entries:
        writer.writerow(
            [
                entry.target_id,
                entry.target_kind.value,
                entry.matched_entity_id,
                entry.modified_peptide or "",
                "" if entry.expected_charge is None else entry.expected_charge,
                entry.sample_id,
                "" if entry.abundance is None else entry.abundance,
                str(entry.detected).lower(),
            ]
        )
    return buffer.getvalue()


def render_target_panel_matrix_tsv(report: TargetPanelReport) -> str:
    """Render the filtered target panel as one wide matrix."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "target_id",
            "target_kind",
            "matched_entity_id",
            "peptide_sequence",
            "modified_peptide",
            "expected_charge",
            "charge_states",
            "protein_refs",
            *report.sample_ids,
        ]
    )
    for row in report.filtered_rows:
        values_by_sample = {value.sample_id: value.abundance for value in row.values}
        writer.writerow(
            [
                row.target_id,
                row.target_kind.value,
                row.matched_entity_id,
                row.peptide_sequence or "",
                row.modified_peptide or "",
                "" if row.expected_charge is None else row.expected_charge,
                ";".join(str(charge) for charge in row.charge_states),
                ";".join(row.protein_refs),
                *[
                    ""
                    if values_by_sample.get(sample_id) is None
                    else values_by_sample[sample_id]
                    for sample_id in report.sample_ids
                ],
            ]
        )
    return buffer.getvalue()


def export_target_panel_summary_tsv(report: TargetPanelReport, path: Path) -> None:
    write_output_table_tsv(path, render_target_panel_summary_tsv(report))


def export_target_panel_target_tsv(report: TargetPanelReport, path: Path) -> None:
    write_output_table_tsv(path, render_target_panel_target_tsv(report))


def export_target_panel_missing_tsv(report: TargetPanelReport, path: Path) -> None:
    write_output_table_tsv(path, render_target_panel_missing_tsv(report))


def export_target_panel_intensity_tsv(report: TargetPanelReport, path: Path) -> None:
    write_output_table_tsv(path, render_target_panel_intensity_tsv(report))


def export_target_panel_matrix_tsv(report: TargetPanelReport, path: Path) -> None:
    write_output_table_tsv(path, render_target_panel_matrix_tsv(report))
