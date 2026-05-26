# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned DIA precursor-matrix surfaces over DIA-native precursor evidence."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics.quantification.contracts import MissingValueKind
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.identification.diann_import import DiaNnPrecursorReviewEntry
    from bijux_proteomics.identification.spectronaut_import import (
        SpectronautPrecursorReviewEntry,
    )

    DiaNativePrecursorMatrixEntry = (
        DiaNnPrecursorReviewEntry | SpectronautPrecursorReviewEntry
    )


class DiaPrecursorQValueFilterTiming(StrEnum):
    """When precursor q-value filtering is applied relative to matrix construction."""

    BEFORE_MATRIX_CONSTRUCTION = "before_matrix_construction"
    AFTER_MATRIX_CONSTRUCTION = "after_matrix_construction"


class DiaPrecursorExclusionReason(StrEnum):
    """Governed reasons for excluding precursor observations from matrix cells."""

    DECOY_EXCLUDED = "decoy_excluded"
    Q_VALUE_THRESHOLD = "q_value_threshold"


class DiaPrecursorMatrixPolicy(JsonModel):
    """Owned policy controlling DIA precursor matrix inclusion semantics."""

    model_config = ConfigDict(extra="forbid")

    include_decoys: bool = False
    max_q_value: float | None = Field(default=None, ge=0.0, le=1.0)
    q_value_filter_timing: DiaPrecursorQValueFilterTiming = (
        DiaPrecursorQValueFilterTiming.BEFORE_MATRIX_CONSTRUCTION
    )


class DiaPrecursorMatrixValue(JsonModel):
    """One sample-specific DIA precursor matrix cell."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    run_names: tuple[str, ...] = Field(default_factory=tuple)
    source_precursor_ids: tuple[str, ...] = Field(default_factory=tuple)
    abundance: float | None = Field(default=None, ge=0.0)
    q_value: float | None = Field(default=None, ge=0.0, le=1.0)
    source_observation_count: int = Field(..., ge=0)
    retained_observation_count: int = Field(..., ge=0)
    excluded_q_value_observation_count: int = Field(..., ge=0)
    missing_value_kind: MissingValueKind
    detected: bool


class DiaPrecursorMatrixRow(JsonModel):
    """One DIA precursor row across all samples."""

    model_config = ConfigDict(extra="forbid")

    precursor_key: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    modified_peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    protein_group_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    source_precursor_ids: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel
    values: tuple[DiaPrecursorMatrixValue, ...] = Field(default_factory=tuple)


class DiaPrecursorMetadataEntry(JsonModel):
    """One precursor metadata row carried alongside the wide matrices."""

    model_config = ConfigDict(extra="forbid")

    precursor_key: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    modified_peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    protein_group_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    source_precursor_ids: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel
    source_observation_count: int = Field(..., ge=0)
    retained_observation_count: int = Field(..., ge=0)
    excluded_q_value_observation_count: int = Field(..., ge=0)
    detected_sample_count: int = Field(..., ge=0)


class DiaPrecursorExclusionEntry(JsonModel):
    """One excluded precursor observation preserved outside the matrix cells."""

    model_config = ConfigDict(extra="forbid")

    precursor_key: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    modified_peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    protein_group_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    source_precursor_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    run_name: str = Field(..., min_length=1)
    target_decoy_label: TargetDecoyLabel
    q_value: float = Field(..., ge=0.0, le=1.0)
    reason: DiaPrecursorExclusionReason


class DiaPrecursorMatrixSummary(JsonModel):
    """Compact summary over one DIA precursor-by-sample matrix."""

    model_config = ConfigDict(extra="forbid")

    precursor_row_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    run_count: int = Field(..., ge=0)
    observed_cell_count: int = Field(..., ge=0)
    missing_cell_count: int = Field(..., ge=0)
    target_row_count: int = Field(..., ge=0)
    decoy_row_count: int = Field(..., ge=0)
    excluded_decoy_count: int = Field(..., ge=0)
    excluded_q_value_count: int = Field(..., ge=0)
    source_observation_count: int = Field(..., ge=0)
    retained_observation_count: int = Field(..., ge=0)
    q_value_filter_timing: DiaPrecursorQValueFilterTiming
    max_q_value: float | None = Field(default=None, ge=0.0, le=1.0)


class DiaPrecursorMatrixReport(JsonModel):
    """Owned DIA precursor matrix retaining source IDs, q-values, and filter policy."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(default="DIA-native", min_length=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    run_names: tuple[str, ...] = Field(default_factory=tuple)
    policy: DiaPrecursorMatrixPolicy
    rows: tuple[DiaPrecursorMatrixRow, ...] = Field(default_factory=tuple)
    metadata_entries: tuple[DiaPrecursorMetadataEntry, ...] = Field(default_factory=tuple)
    excluded_entries: tuple[DiaPrecursorExclusionEntry, ...] = Field(default_factory=tuple)
    summary: DiaPrecursorMatrixSummary
    note: str = Field(..., min_length=1)


def build_dia_precursor_matrix_report(
    rows: tuple[DiaNativePrecursorMatrixEntry, ...],
    *,
    source_name: str = "DIA-native",
    policy: DiaPrecursorMatrixPolicy | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = None,
    q_value_filter_timing: DiaPrecursorQValueFilterTiming = (
        DiaPrecursorQValueFilterTiming.BEFORE_MATRIX_CONSTRUCTION
    ),
) -> DiaPrecursorMatrixReport:
    """Build a DIA precursor-by-sample matrix from DIA-native precursor review rows."""

    active_policy = policy or DiaPrecursorMatrixPolicy(
        include_decoys=include_decoys,
        max_q_value=max_q_value,
        q_value_filter_timing=q_value_filter_timing,
    )
    sample_ids = tuple(sorted({row.sample_name for row in rows}))
    run_names = tuple(sorted({row.run_name for row in rows}))
    excluded_decoy_count = 0
    excluded_q_value_count = 0
    source_observation_count = 0
    excluded_entries: list[DiaPrecursorExclusionEntry] = []

    grouped: dict[str, dict[str, object]] = {}
    for row in rows:
        precursor_key = _build_precursor_key(row)
        if (
            not active_policy.include_decoys
            and row.target_decoy_label is TargetDecoyLabel.DECOY
        ):
            excluded_decoy_count += 1
            excluded_entries.append(
                _build_exclusion_entry(
                    row,
                    precursor_key=precursor_key,
                    reason=DiaPrecursorExclusionReason.DECOY_EXCLUDED,
                )
            )
            continue
        source_observation_count += 1
        if (
            active_policy.max_q_value is not None
            and active_policy.q_value_filter_timing
            is DiaPrecursorQValueFilterTiming.BEFORE_MATRIX_CONSTRUCTION
            and row.q_value > active_policy.max_q_value
        ):
            excluded_q_value_count += 1
            excluded_entries.append(
                _build_exclusion_entry(
                    row,
                    precursor_key=precursor_key,
                    reason=DiaPrecursorExclusionReason.Q_VALUE_THRESHOLD,
                )
            )
            continue
        group = grouped.setdefault(
            precursor_key,
            {
                "peptide_sequence": row.peptide_sequence,
                "modified_peptide": row.modified_peptide,
                "canonical_peptide": _canonical_peptide(row),
                "charge": row.charge,
                "protein_group_id": row.protein_group_id,
                "protein_refs": set(row.protein_refs),
                "source_precursor_ids": set(),
                "labels": set(),
                "sample_rows": {},
            },
        )
        protein_refs = group["protein_refs"]
        assert isinstance(protein_refs, set)
        protein_refs.update(row.protein_refs)
        source_precursor_ids = group["source_precursor_ids"]
        assert isinstance(source_precursor_ids, set)
        source_precursor_ids.add(row.precursor_id)
        labels = group["labels"]
        assert isinstance(labels, set)
        labels.add(row.target_decoy_label)
        sample_rows = group["sample_rows"]
        assert isinstance(sample_rows, dict)
        sample_rows.setdefault(row.sample_name, []).append(row)

    matrix_rows: list[DiaPrecursorMatrixRow] = []
    metadata_entries: list[DiaPrecursorMetadataEntry] = []
    observed_cell_count = 0
    missing_cell_count = 0
    target_row_count = 0
    decoy_row_count = 0
    retained_observation_count = 0
    for precursor_key in sorted(grouped):
        group = grouped[precursor_key]
        sample_rows = group["sample_rows"]
        assert isinstance(sample_rows, dict)
        labels = group["labels"]
        assert isinstance(labels, set)
        label = _combine_target_decoy_labels(labels)
        if label is TargetDecoyLabel.DECOY:
            decoy_row_count += 1
        else:
            target_row_count += 1
        values: list[DiaPrecursorMatrixValue] = []
        row_source_observation_count = 0
        row_retained_observation_count = 0
        row_excluded_q_value_observation_count = 0
        detected_sample_count = 0
        for sample_id in sample_ids:
            observations = tuple(sample_rows.get(sample_id, ()))
            row_source_observation_count += len(observations)
            retained_observations = observations
            if (
                active_policy.max_q_value is not None
                and active_policy.q_value_filter_timing
                is DiaPrecursorQValueFilterTiming.AFTER_MATRIX_CONSTRUCTION
            ):
                retained_observations = tuple(
                    observation
                    for observation in observations
                    if observation.q_value <= active_policy.max_q_value
                )
                excluded_for_sample = len(observations) - len(retained_observations)
                row_excluded_q_value_observation_count += excluded_for_sample
                excluded_q_value_count += excluded_for_sample
                if excluded_for_sample:
                    excluded_entries.extend(
                        _build_exclusion_entry(
                            observation,
                            precursor_key=precursor_key,
                            reason=DiaPrecursorExclusionReason.Q_VALUE_THRESHOLD,
                        )
                        for observation in observations
                        if observation.q_value > active_policy.max_q_value
                    )
            if not retained_observations:
                missing_cell_count += 1
                values.append(
                    DiaPrecursorMatrixValue(
                        sample_id=sample_id,
                        run_names=tuple(
                            sorted({observation.run_name for observation in observations})
                        ),
                        source_precursor_ids=tuple(
                            sorted(
                                {
                                    observation.precursor_id
                                    for observation in observations
                                }
                            )
                        ),
                        source_observation_count=len(observations),
                        retained_observation_count=0,
                        excluded_q_value_observation_count=len(observations),
                        missing_value_kind=(
                            MissingValueKind.EXCLUDED
                            if observations
                            else MissingValueKind.NOT_OBSERVED
                        ),
                        detected=False,
                    )
                )
                continue
            observed_cell_count += 1
            detected_sample_count += 1
            row_retained_observation_count += len(retained_observations)
            retained_observation_count += len(retained_observations)
            best_quantity = max(
                (
                    observation.precursor_quantity
                    for observation in retained_observations
                    if observation.precursor_quantity is not None
                ),
                default=None,
            )
            best_q_value = min(
                observation.q_value for observation in retained_observations
            )
            values.append(
                DiaPrecursorMatrixValue(
                    sample_id=sample_id,
                    run_names=tuple(
                        sorted(
                            {
                                observation.run_name
                                for observation in retained_observations
                            }
                        )
                    ),
                    source_precursor_ids=tuple(
                        sorted(
                            {
                                observation.precursor_id
                                for observation in retained_observations
                            }
                        )
                    ),
                    abundance=best_quantity,
                    q_value=best_q_value,
                    source_observation_count=len(observations),
                    retained_observation_count=len(retained_observations),
                    excluded_q_value_observation_count=(
                        len(observations) - len(retained_observations)
                    ),
                    missing_value_kind=_dia_precursor_missing_value_kind(
                        abundance=best_quantity,
                        detected=True,
                    ),
                    detected=True,
                )
            )
        protein_refs = group["protein_refs"]
        assert isinstance(protein_refs, set)
        source_precursor_ids = group["source_precursor_ids"]
        assert isinstance(source_precursor_ids, set)
        matrix_rows.append(
            DiaPrecursorMatrixRow(
                precursor_key=precursor_key,
                peptide_sequence=str(group["peptide_sequence"]),
                modified_peptide=str(group["modified_peptide"]),
                canonical_peptide=str(group["canonical_peptide"]),
                charge=int(group["charge"]),
                protein_group_id=str(group["protein_group_id"]),
                protein_refs=tuple(sorted(protein_refs)),
                source_precursor_ids=tuple(sorted(source_precursor_ids)),
                target_decoy_label=label,
                values=tuple(values),
            )
        )
        metadata_entries.append(
            DiaPrecursorMetadataEntry(
                precursor_key=precursor_key,
                peptide_sequence=str(group["peptide_sequence"]),
                modified_peptide=str(group["modified_peptide"]),
                canonical_peptide=str(group["canonical_peptide"]),
                charge=int(group["charge"]),
                protein_group_id=str(group["protein_group_id"]),
                protein_refs=tuple(sorted(protein_refs)),
                source_precursor_ids=tuple(sorted(source_precursor_ids)),
                target_decoy_label=label,
                source_observation_count=row_source_observation_count,
                retained_observation_count=row_retained_observation_count,
                excluded_q_value_observation_count=(
                    row_excluded_q_value_observation_count
                ),
                detected_sample_count=detected_sample_count,
            )
        )

    return DiaPrecursorMatrixReport(
        source_name=source_name,
        sample_ids=sample_ids,
        run_names=run_names,
        policy=active_policy,
        rows=tuple(matrix_rows),
        metadata_entries=tuple(metadata_entries),
        excluded_entries=tuple(
            sorted(
                excluded_entries,
                key=lambda entry: (
                    entry.precursor_key,
                    entry.sample_id,
                    entry.run_name,
                    entry.source_precursor_id,
                    entry.reason.value,
                ),
            )
        ),
        summary=DiaPrecursorMatrixSummary(
            precursor_row_count=len(matrix_rows),
            sample_count=len(sample_ids),
            run_count=len(run_names),
            observed_cell_count=observed_cell_count,
            missing_cell_count=missing_cell_count,
            target_row_count=target_row_count,
            decoy_row_count=decoy_row_count,
            excluded_decoy_count=excluded_decoy_count,
            excluded_q_value_count=excluded_q_value_count,
            source_observation_count=source_observation_count,
            retained_observation_count=retained_observation_count,
            q_value_filter_timing=active_policy.q_value_filter_timing,
            max_q_value=active_policy.max_q_value,
        ),
        note=(
            "precursor matrix groups DIA-native evidence by modified peptide, charge, and protein group while preserving run-scoped source precursor identifiers and explicit q-value filter timing"
        ),
    )


def build_diann_precursor_matrix_report(
    result_tsv_path: Path,
    *,
    config_path: Path | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = None,
    q_value_filter_timing: DiaPrecursorQValueFilterTiming = (
        DiaPrecursorQValueFilterTiming.BEFORE_MATRIX_CONSTRUCTION
    ),
    policy: DiaPrecursorMatrixPolicy | None = None,
) -> DiaPrecursorMatrixReport:
    """Build a DIA precursor-by-sample matrix directly from a DIA-NN report."""

    from bijux_proteomics.identification.diann_import import build_diann_import_report

    report = build_diann_import_report(result_tsv_path, config_path=config_path)
    return build_dia_precursor_matrix_report(
        report.precursor_rows,
        source_name="DIA-NN",
        include_decoys=include_decoys,
        max_q_value=max_q_value,
        q_value_filter_timing=q_value_filter_timing,
        policy=policy,
    )


def build_spectronaut_precursor_matrix_report(
    result_tsv_path: Path,
    *,
    config_path: Path | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = None,
    q_value_filter_timing: DiaPrecursorQValueFilterTiming = (
        DiaPrecursorQValueFilterTiming.BEFORE_MATRIX_CONSTRUCTION
    ),
    policy: DiaPrecursorMatrixPolicy | None = None,
) -> DiaPrecursorMatrixReport:
    """Build a DIA precursor-by-sample matrix directly from a Spectronaut report."""

    from bijux_proteomics.identification.spectronaut_import import (
        build_spectronaut_import_report,
    )

    report = build_spectronaut_import_report(result_tsv_path, config_path=config_path)
    return build_dia_precursor_matrix_report(
        report.precursor_rows,
        source_name="Spectronaut",
        include_decoys=include_decoys,
        max_q_value=max_q_value,
        q_value_filter_timing=q_value_filter_timing,
        policy=policy,
    )


def render_dia_precursor_matrix_summary_tsv(report: DiaPrecursorMatrixReport) -> str:
    """Render a compact summary for one DIA precursor matrix."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "source_name",
            "sample_count",
            "run_count",
            "precursor_row_count",
            "observed_cell_count",
            "missing_cell_count",
            "target_row_count",
            "decoy_row_count",
            "excluded_decoy_count",
            "excluded_q_value_count",
            "source_observation_count",
            "retained_observation_count",
            "q_value_filter_timing",
            "max_q_value",
            "note",
        ]
    )
    writer.writerow(
        [
            report.source_name,
            report.summary.sample_count,
            report.summary.run_count,
            report.summary.precursor_row_count,
            report.summary.observed_cell_count,
            report.summary.missing_cell_count,
            report.summary.target_row_count,
            report.summary.decoy_row_count,
            report.summary.excluded_decoy_count,
            report.summary.excluded_q_value_count,
            report.summary.source_observation_count,
            report.summary.retained_observation_count,
            report.summary.q_value_filter_timing.value,
            (
                ""
                if report.summary.max_q_value is None
                else f"{report.summary.max_q_value:.6g}"
            ),
            report.note,
        ]
    )
    return buffer.getvalue()


def render_dia_precursor_quantity_matrix_tsv(report: DiaPrecursorMatrixReport) -> str:
    """Render the DIA precursor-by-sample quantity matrix as a wide TSV."""

    return _render_dia_precursor_wide_matrix(
        report,
        value_getter=lambda value: (
            "" if value.abundance is None else f"{value.abundance:g}"
        ),
    )


def render_dia_precursor_q_value_matrix_tsv(report: DiaPrecursorMatrixReport) -> str:
    """Render the DIA precursor-by-sample q-value matrix as a wide TSV."""

    return _render_dia_precursor_wide_matrix(
        report,
        value_getter=lambda value: (
            "" if value.q_value is None else f"{value.q_value:.6g}"
        ),
    )


def render_dia_precursor_missingness_tsv(report: DiaPrecursorMatrixReport) -> str:
    """Render one DIA precursor missingness mask beside the wide matrices."""

    return _render_dia_precursor_wide_matrix(
        report,
        value_getter=lambda value: value.missing_value_kind.value,
    )


def render_dia_precursor_metadata_tsv(report: DiaPrecursorMatrixReport) -> str:
    """Render the precursor metadata ledger carried alongside the wide matrices."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "precursor_key",
            "peptide_sequence",
            "modified_peptide",
            "canonical_peptide",
            "charge",
            "protein_group_id",
            "protein_refs",
            "source_precursor_ids",
            "target_decoy_label",
            "source_observation_count",
            "retained_observation_count",
            "excluded_q_value_observation_count",
            "detected_sample_count",
        ]
    )
    for entry in report.metadata_entries:
        writer.writerow(
            [
                entry.precursor_key,
                entry.peptide_sequence,
                entry.modified_peptide,
                entry.canonical_peptide,
                entry.charge,
                entry.protein_group_id,
                ";".join(entry.protein_refs),
                ";".join(entry.source_precursor_ids),
                entry.target_decoy_label.value,
                entry.source_observation_count,
                entry.retained_observation_count,
                entry.excluded_q_value_observation_count,
                entry.detected_sample_count,
            ]
        )
    return buffer.getvalue()


def export_dia_precursor_matrix_summary_tsv(
    report: DiaPrecursorMatrixReport,
    path: Path,
) -> None:
    write_output_table_tsv(path, render_dia_precursor_matrix_summary_tsv(report))


def export_dia_precursor_quantity_matrix_tsv(
    report: DiaPrecursorMatrixReport,
    path: Path,
) -> None:
    write_output_table_tsv(path, render_dia_precursor_quantity_matrix_tsv(report))


def export_dia_precursor_q_value_matrix_tsv(
    report: DiaPrecursorMatrixReport,
    path: Path,
) -> None:
    write_output_table_tsv(path, render_dia_precursor_q_value_matrix_tsv(report))


def export_dia_precursor_missingness_tsv(
    report: DiaPrecursorMatrixReport,
    path: Path,
) -> None:
    write_output_table_tsv(path, render_dia_precursor_missingness_tsv(report))


def export_dia_precursor_metadata_tsv(
    report: DiaPrecursorMatrixReport,
    path: Path,
) -> None:
    write_output_table_tsv(path, render_dia_precursor_metadata_tsv(report))


def _build_precursor_key(row: DiaNativePrecursorMatrixEntry) -> str:
    return f"{row.modified_peptide}|z{row.charge}|{row.protein_group_id}"


def _canonical_peptide(row: DiaNativePrecursorMatrixEntry) -> str:
    canonical_peptide = getattr(row, "canonical_peptide", None)
    if canonical_peptide is not None:
        return canonical_peptide
    return row.canonical_modified_peptide


def _build_exclusion_entry(
    row: DiaNativePrecursorMatrixEntry,
    *,
    precursor_key: str,
    reason: DiaPrecursorExclusionReason,
) -> DiaPrecursorExclusionEntry:
    return DiaPrecursorExclusionEntry(
        precursor_key=precursor_key,
        peptide_sequence=row.peptide_sequence,
        modified_peptide=row.modified_peptide,
        canonical_peptide=_canonical_peptide(row),
        charge=row.charge,
        protein_group_id=row.protein_group_id,
        protein_refs=tuple(sorted(row.protein_refs)),
        source_precursor_id=row.precursor_id,
        sample_id=row.sample_name,
        run_name=row.run_name,
        target_decoy_label=row.target_decoy_label,
        q_value=row.q_value,
        reason=reason,
    )


def _combine_target_decoy_labels(
    labels: set[TargetDecoyLabel],
) -> TargetDecoyLabel:
    if labels == {TargetDecoyLabel.DECOY}:
        return TargetDecoyLabel.DECOY
    if labels == {TargetDecoyLabel.TARGET}:
        return TargetDecoyLabel.TARGET
    if not labels:
        return TargetDecoyLabel.UNKNOWN
    return TargetDecoyLabel.MIXED


def _dia_precursor_missing_value_kind(
    *,
    abundance: float | None,
    detected: bool,
) -> MissingValueKind:
    if abundance == 0.0:
        return MissingValueKind.ZERO
    if abundance is not None:
        return MissingValueKind.OBSERVED
    if detected:
        return MissingValueKind.CENSORED
    return MissingValueKind.NOT_OBSERVED


def _render_dia_precursor_wide_matrix(
    report: DiaPrecursorMatrixReport,
    *,
    value_getter: Callable[[DiaPrecursorMatrixValue], str],
) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "precursor_key",
            "peptide_sequence",
            "modified_peptide",
            "canonical_peptide",
            "charge",
            "protein_group_id",
            "protein_refs",
            "source_precursor_ids",
            "target_decoy_label",
            *report.sample_ids,
        ]
    )
    for row in report.rows:
        value_lookup = {value.sample_id: value for value in row.values}
        writer.writerow(
            [
                row.precursor_key,
                row.peptide_sequence,
                row.modified_peptide,
                row.canonical_peptide,
                row.charge,
                row.protein_group_id,
                ";".join(row.protein_refs),
                ";".join(row.source_precursor_ids),
                row.target_decoy_label.value,
                *[
                    value_getter(value_lookup[sample_id])
                    for sample_id in report.sample_ids
                ],
            ]
        )
    return buffer.getvalue()


__all__ = [
    "DiaPrecursorMetadataEntry",
    "DiaPrecursorMatrixPolicy",
    "DiaPrecursorMatrixReport",
    "DiaPrecursorMatrixRow",
    "DiaPrecursorMatrixSummary",
    "DiaPrecursorMatrixValue",
    "DiaPrecursorExclusionEntry",
    "DiaPrecursorExclusionReason",
    "DiaPrecursorQValueFilterTiming",
    "build_dia_precursor_matrix_report",
    "build_diann_precursor_matrix_report",
    "build_spectronaut_precursor_matrix_report",
    "export_dia_precursor_matrix_summary_tsv",
    "export_dia_precursor_metadata_tsv",
    "export_dia_precursor_missingness_tsv",
    "export_dia_precursor_q_value_matrix_tsv",
    "export_dia_precursor_quantity_matrix_tsv",
    "render_dia_precursor_matrix_summary_tsv",
    "render_dia_precursor_metadata_tsv",
    "render_dia_precursor_missingness_tsv",
    "render_dia_precursor_q_value_matrix_tsv",
    "render_dia_precursor_quantity_matrix_tsv",
]
