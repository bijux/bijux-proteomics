# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned DIA peptide and protein matrix surfaces over precursor matrices."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path
from typing import Callable

from pydantic import ConfigDict, Field

from bijux_proteomics.dia.precursor_matrix import (
    DiaPrecursorMatrixReport,
    DiaPrecursorMatrixRow,
    DiaPrecursorMatrixValue,
    build_diann_precursor_matrix_report,
)
from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics_foundation import JsonModel


class DiaPeptideRollupMethod(StrEnum):
    """Supported DIA precursor-to-peptide rollup methods."""

    MAX = "max"
    SUM = "sum"


class DiaPeptideMatrixValue(JsonModel):
    """One sample-specific DIA peptide matrix cell."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    q_value: float | None = Field(default=None, ge=0.0, le=1.0)
    contributing_precursor_count: int = Field(..., ge=0)
    source_precursor_keys: tuple[str, ...] = Field(default_factory=tuple)
    charge_states: tuple[int, ...] = Field(default_factory=tuple)
    detected: bool


class DiaPeptideMatrixRow(JsonModel):
    """One DIA peptide row across all samples."""

    model_config = ConfigDict(extra="forbid")

    peptide_key: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    modified_peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    protein_group_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    source_precursor_count: int = Field(..., ge=0)
    target_decoy_label: TargetDecoyLabel
    values: tuple[DiaPeptideMatrixValue, ...] = Field(default_factory=tuple)


class DiaPeptideMatrixSummary(JsonModel):
    """Compact summary over one DIA peptide-by-sample matrix."""

    model_config = ConfigDict(extra="forbid")

    peptide_row_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    observed_cell_count: int = Field(..., ge=0)
    missing_cell_count: int = Field(..., ge=0)
    shared_peptide_row_count: int = Field(..., ge=0)


class DiaPeptideMatrixReport(JsonModel):
    """Owned DIA peptide matrix derived from sample-resolved precursor evidence."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(default="DIA-NN", min_length=1)
    rollup_method: DiaPeptideRollupMethod
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[DiaPeptideMatrixRow, ...] = Field(default_factory=tuple)
    summary: DiaPeptideMatrixSummary
    note: str = Field(..., min_length=1)


class DiaProteinMatrixTargetKind(StrEnum):
    """Supported DIA protein-level rollup targets."""

    PROTEIN = "protein"
    PROTEIN_GROUP = "protein_group"


class DiaSharedPeptidePolicy(StrEnum):
    """How shared DIA peptides participate in protein-level rollup."""

    INCLUDE = "include"
    EXCLUDE = "exclude"


class DiaProteinRollupMethod(StrEnum):
    """Supported DIA peptide-to-protein rollup methods."""

    SUM = "sum"
    MAX = "max"


class DiaProteinMatrixValue(JsonModel):
    """One sample-specific DIA protein matrix cell."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    q_value: float | None = Field(default=None, ge=0.0, le=1.0)
    contributing_peptide_count: int = Field(..., ge=0)
    detected: bool


class DiaProteinMatrixRow(JsonModel):
    """One DIA protein or protein-group row across all samples."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    target_kind: DiaProteinMatrixTargetKind
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    contributing_peptides: tuple[str, ...] = Field(default_factory=tuple)
    values: tuple[DiaProteinMatrixValue, ...] = Field(default_factory=tuple)


class DiaProteinMatrixSummary(JsonModel):
    """Compact summary over one DIA protein-by-sample matrix."""

    model_config = ConfigDict(extra="forbid")

    protein_row_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    observed_cell_count: int = Field(..., ge=0)
    missing_cell_count: int = Field(..., ge=0)
    shared_peptide_row_count: int = Field(..., ge=0)
    excluded_shared_peptide_count: int = Field(..., ge=0)


class DiaProteinMatrixReport(JsonModel):
    """Owned DIA protein matrix derived from peptide-level rollup evidence."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(default="DIA-NN", min_length=1)
    target_kind: DiaProteinMatrixTargetKind
    shared_peptide_policy: DiaSharedPeptidePolicy
    rollup_method: DiaProteinRollupMethod
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[DiaProteinMatrixRow, ...] = Field(default_factory=tuple)
    summary: DiaProteinMatrixSummary
    note: str = Field(..., min_length=1)


def build_diann_peptide_matrix_report(
    result_tsv_path: Path,
    *,
    config_path: Path | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = None,
    rollup_method: DiaPeptideRollupMethod = DiaPeptideRollupMethod.MAX,
) -> DiaPeptideMatrixReport:
    """Build a DIA peptide-by-sample matrix directly from one DIA-NN report."""

    precursor_matrix = build_diann_precursor_matrix_report(
        result_tsv_path,
        config_path=config_path,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
    )
    return build_dia_peptide_matrix_report(
        precursor_matrix,
        rollup_method=rollup_method,
    )


def build_diann_protein_matrix_report(
    result_tsv_path: Path,
    *,
    config_path: Path | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = None,
    peptide_rollup_method: DiaPeptideRollupMethod = DiaPeptideRollupMethod.MAX,
    target_kind: DiaProteinMatrixTargetKind = DiaProteinMatrixTargetKind.PROTEIN_GROUP,
    shared_peptide_policy: DiaSharedPeptidePolicy = DiaSharedPeptidePolicy.INCLUDE,
    protein_rollup_method: DiaProteinRollupMethod = DiaProteinRollupMethod.SUM,
) -> DiaProteinMatrixReport:
    """Build a DIA protein-by-sample matrix directly from one DIA-NN report."""

    peptide_matrix = build_diann_peptide_matrix_report(
        result_tsv_path,
        config_path=config_path,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
        rollup_method=peptide_rollup_method,
    )
    return build_dia_protein_matrix_report(
        peptide_matrix,
        target_kind=target_kind,
        shared_peptide_policy=shared_peptide_policy,
        rollup_method=protein_rollup_method,
    )


def build_dia_peptide_matrix_report(
    precursor_matrix: DiaPrecursorMatrixReport,
    *,
    rollup_method: DiaPeptideRollupMethod = DiaPeptideRollupMethod.MAX,
) -> DiaPeptideMatrixReport:
    """Roll one DIA precursor matrix up to a peptide-by-sample matrix."""

    grouped: dict[str, list[DiaPrecursorMatrixRow]] = {}
    for row in precursor_matrix.rows:
        grouped.setdefault(_build_peptide_key(row), []).append(row)

    peptide_rows: list[DiaPeptideMatrixRow] = []
    observed_cell_count = 0
    missing_cell_count = 0
    shared_peptide_row_count = 0
    for peptide_key in sorted(grouped):
        precursor_rows = grouped[peptide_key]
        exemplar = precursor_rows[0]
        if len(exemplar.protein_refs) > 1:
            shared_peptide_row_count += 1
        sample_values: list[DiaPeptideMatrixValue] = []
        for sample_id in precursor_matrix.sample_ids:
            observations = _sample_observations(precursor_rows, sample_id)
            if not observations:
                missing_cell_count += 1
                sample_values.append(
                    DiaPeptideMatrixValue(
                        sample_id=sample_id,
                        contributing_precursor_count=0,
                        detected=False,
                    )
                )
                continue
            observed_cell_count += 1
            abundances = [
                observation.abundance
                for observation in observations
                if observation.abundance is not None
            ]
            abundance = None
            if abundances:
                abundance = (
                    max(abundances)
                    if rollup_method is DiaPeptideRollupMethod.MAX
                    else sum(abundances)
                )
            q_values = [
                observation.q_value
                for observation in observations
                if observation.q_value is not None
            ]
            sample_values.append(
                DiaPeptideMatrixValue(
                    sample_id=sample_id,
                    abundance=abundance,
                    q_value=min(q_values) if q_values else None,
                    contributing_precursor_count=sum(
                        observation.source_observation_count
                        for observation in observations
                    ),
                    source_precursor_keys=tuple(
                        sorted(
                            {
                                precursor_row.precursor_key
                                for precursor_row in precursor_rows
                                for value in precursor_row.values
                                if value.sample_id == sample_id and value.detected
                            }
                        )
                    ),
                    charge_states=tuple(sorted({row.charge for row in precursor_rows})),
                    detected=True,
                )
            )
        peptide_rows.append(
            DiaPeptideMatrixRow(
                peptide_key=peptide_key,
                peptide_sequence=exemplar.peptide_sequence,
                modified_peptide=exemplar.modified_peptide,
                canonical_peptide=exemplar.canonical_peptide,
                protein_group_id=exemplar.protein_group_id,
                protein_refs=exemplar.protein_refs,
                source_precursor_count=sum(
                    len(row.source_precursor_ids) for row in precursor_rows
                ),
                target_decoy_label=_combine_target_decoy_labels(
                    {row.target_decoy_label for row in precursor_rows}
                ),
                values=tuple(sample_values),
            )
        )

    return DiaPeptideMatrixReport(
        rollup_method=rollup_method,
        sample_ids=precursor_matrix.sample_ids,
        rows=tuple(peptide_rows),
        summary=DiaPeptideMatrixSummary(
            peptide_row_count=len(peptide_rows),
            sample_count=len(precursor_matrix.sample_ids),
            observed_cell_count=observed_cell_count,
            missing_cell_count=missing_cell_count,
            shared_peptide_row_count=shared_peptide_row_count,
        ),
        note=(
            "peptide matrix rolls sample-resolved precursor evidence up by modified peptide and protein group so peptide-level DIA review remains visible before protein aggregation"
        ),
    )


def build_dia_protein_matrix_report(
    peptide_matrix: DiaPeptideMatrixReport,
    *,
    target_kind: DiaProteinMatrixTargetKind = DiaProteinMatrixTargetKind.PROTEIN_GROUP,
    shared_peptide_policy: DiaSharedPeptidePolicy = DiaSharedPeptidePolicy.INCLUDE,
    rollup_method: DiaProteinRollupMethod = DiaProteinRollupMethod.SUM,
) -> DiaProteinMatrixReport:
    """Roll one DIA peptide matrix up to protein or protein-group targets."""

    grouped: dict[str, list[DiaPeptideMatrixRow]] = {}
    excluded_shared_peptide_count = 0
    for row in peptide_matrix.rows:
        is_shared = len(row.protein_refs) > 1
        if is_shared and shared_peptide_policy is DiaSharedPeptidePolicy.EXCLUDE:
            excluded_shared_peptide_count += 1
            continue
        target_ids = (
            row.protein_refs
            if target_kind is DiaProteinMatrixTargetKind.PROTEIN
            else (row.protein_group_id,)
        )
        for target_id in target_ids:
            grouped.setdefault(target_id, []).append(row)

    protein_rows: list[DiaProteinMatrixRow] = []
    observed_cell_count = 0
    missing_cell_count = 0
    shared_peptide_row_count = 0
    for entity_id in sorted(grouped):
        peptide_rows = grouped[entity_id]
        unique_peptides = sorted(
            {row.peptide_key for row in peptide_rows if len(row.protein_refs) == 1}
        )
        shared_peptides = sorted(
            {row.peptide_key for row in peptide_rows if len(row.protein_refs) > 1}
        )
        if shared_peptides:
            shared_peptide_row_count += 1
        protein_refs = (
            (entity_id,)
            if target_kind is DiaProteinMatrixTargetKind.PROTEIN
            else tuple(
                sorted(
                    {
                        protein_ref
                        for row in peptide_rows
                        for protein_ref in row.protein_refs
                    }
                )
            )
        )
        values: list[DiaProteinMatrixValue] = []
        for sample_id in peptide_matrix.sample_ids:
            observations = _sample_peptide_observations(peptide_rows, sample_id)
            if not observations:
                missing_cell_count += 1
                values.append(
                    DiaProteinMatrixValue(
                        sample_id=sample_id,
                        contributing_peptide_count=0,
                        detected=False,
                    )
                )
                continue
            observed_cell_count += 1
            abundances = [
                observation.abundance
                for observation in observations
                if observation.abundance is not None
            ]
            abundance = None
            if abundances:
                abundance = (
                    max(abundances)
                    if rollup_method is DiaProteinRollupMethod.MAX
                    else sum(abundances)
                )
            q_values = [
                observation.q_value
                for observation in observations
                if observation.q_value is not None
            ]
            values.append(
                DiaProteinMatrixValue(
                    sample_id=sample_id,
                    abundance=abundance,
                    q_value=min(q_values) if q_values else None,
                    contributing_peptide_count=len(observations),
                    detected=True,
                )
            )
        protein_rows.append(
            DiaProteinMatrixRow(
                entity_id=entity_id,
                target_kind=target_kind,
                protein_refs=protein_refs,
                peptide_count=len({row.peptide_key for row in peptide_rows}),
                unique_peptide_count=len(unique_peptides),
                shared_peptide_count=len(shared_peptides),
                contributing_peptides=tuple(
                    sorted({row.modified_peptide for row in peptide_rows})
                ),
                values=tuple(values),
            )
        )

    return DiaProteinMatrixReport(
        target_kind=target_kind,
        shared_peptide_policy=shared_peptide_policy,
        rollup_method=rollup_method,
        sample_ids=peptide_matrix.sample_ids,
        rows=tuple(protein_rows),
        summary=DiaProteinMatrixSummary(
            protein_row_count=len(protein_rows),
            sample_count=len(peptide_matrix.sample_ids),
            observed_cell_count=observed_cell_count,
            missing_cell_count=missing_cell_count,
            shared_peptide_row_count=shared_peptide_row_count,
            excluded_shared_peptide_count=excluded_shared_peptide_count,
        ),
        note=(
            "protein matrix preserves peptide-level DIA rollup and makes shared-peptide participation explicit before protein-level interpretation"
        ),
    )


def render_dia_peptide_matrix_summary_tsv(report: DiaPeptideMatrixReport) -> str:
    """Render a compact summary for one DIA peptide matrix."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "source_name",
            "rollup_method",
            "sample_count",
            "peptide_row_count",
            "observed_cell_count",
            "missing_cell_count",
            "shared_peptide_row_count",
            "note",
        ]
    )
    writer.writerow(
        [
            report.source_name,
            report.rollup_method.value,
            report.summary.sample_count,
            report.summary.peptide_row_count,
            report.summary.observed_cell_count,
            report.summary.missing_cell_count,
            report.summary.shared_peptide_row_count,
            report.note,
        ]
    )
    return buffer.getvalue()


def render_dia_peptide_quantity_matrix_tsv(report: DiaPeptideMatrixReport) -> str:
    """Render the DIA peptide-by-sample quantity matrix as a wide TSV."""

    return _render_dia_peptide_wide_matrix(
        report,
        value_getter=lambda value: (
            "" if value.abundance is None else f"{value.abundance:g}"
        ),
    )


def render_dia_peptide_q_value_matrix_tsv(report: DiaPeptideMatrixReport) -> str:
    """Render the DIA peptide-by-sample q-value matrix as a wide TSV."""

    return _render_dia_peptide_wide_matrix(
        report,
        value_getter=lambda value: (
            "" if value.q_value is None else f"{value.q_value:.6g}"
        ),
    )


def render_dia_protein_matrix_summary_tsv(report: DiaProteinMatrixReport) -> str:
    """Render a compact summary for one DIA protein matrix."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "source_name",
            "target_kind",
            "shared_peptide_policy",
            "rollup_method",
            "sample_count",
            "protein_row_count",
            "observed_cell_count",
            "missing_cell_count",
            "shared_peptide_row_count",
            "excluded_shared_peptide_count",
            "note",
        ]
    )
    writer.writerow(
        [
            report.source_name,
            report.target_kind.value,
            report.shared_peptide_policy.value,
            report.rollup_method.value,
            report.summary.sample_count,
            report.summary.protein_row_count,
            report.summary.observed_cell_count,
            report.summary.missing_cell_count,
            report.summary.shared_peptide_row_count,
            report.summary.excluded_shared_peptide_count,
            report.note,
        ]
    )
    return buffer.getvalue()


def render_dia_protein_quantity_matrix_tsv(report: DiaProteinMatrixReport) -> str:
    """Render the DIA protein-by-sample quantity matrix as a wide TSV."""

    return _render_dia_protein_wide_matrix(
        report,
        value_getter=lambda value: (
            "" if value.abundance is None else f"{value.abundance:g}"
        ),
    )


def render_dia_protein_q_value_matrix_tsv(report: DiaProteinMatrixReport) -> str:
    """Render the DIA protein-by-sample q-value matrix as a wide TSV."""

    return _render_dia_protein_wide_matrix(
        report,
        value_getter=lambda value: (
            "" if value.q_value is None else f"{value.q_value:.6g}"
        ),
    )


def export_dia_peptide_matrix_summary_tsv(
    report: DiaPeptideMatrixReport,
    path: Path,
) -> None:
    path.write_text(render_dia_peptide_matrix_summary_tsv(report), encoding="utf-8")


def export_dia_peptide_quantity_matrix_tsv(
    report: DiaPeptideMatrixReport,
    path: Path,
) -> None:
    path.write_text(render_dia_peptide_quantity_matrix_tsv(report), encoding="utf-8")


def export_dia_peptide_q_value_matrix_tsv(
    report: DiaPeptideMatrixReport,
    path: Path,
) -> None:
    path.write_text(render_dia_peptide_q_value_matrix_tsv(report), encoding="utf-8")


def export_dia_protein_matrix_summary_tsv(
    report: DiaProteinMatrixReport,
    path: Path,
) -> None:
    path.write_text(render_dia_protein_matrix_summary_tsv(report), encoding="utf-8")


def export_dia_protein_quantity_matrix_tsv(
    report: DiaProteinMatrixReport,
    path: Path,
) -> None:
    path.write_text(render_dia_protein_quantity_matrix_tsv(report), encoding="utf-8")


def export_dia_protein_q_value_matrix_tsv(
    report: DiaProteinMatrixReport,
    path: Path,
) -> None:
    path.write_text(render_dia_protein_q_value_matrix_tsv(report), encoding="utf-8")


def _build_peptide_key(row: DiaPrecursorMatrixRow) -> str:
    return f"{row.modified_peptide}|{row.protein_group_id}"


def _sample_observations(
    precursor_rows: list[DiaPrecursorMatrixRow],
    sample_id: str,
) -> list[DiaPrecursorMatrixValue]:
    return [
        value
        for row in precursor_rows
        for value in row.values
        if value.sample_id == sample_id and value.detected
    ]


def _sample_peptide_observations(
    peptide_rows: list[DiaPeptideMatrixRow],
    sample_id: str,
) -> list[DiaPeptideMatrixValue]:
    return [
        value
        for row in peptide_rows
        for value in row.values
        if value.sample_id == sample_id and value.detected
    ]


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


def _render_dia_peptide_wide_matrix(
    report: DiaPeptideMatrixReport,
    *,
    value_getter: Callable[[DiaPeptideMatrixValue], str],
) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "peptide_key",
            "peptide_sequence",
            "modified_peptide",
            "canonical_peptide",
            "protein_group_id",
            "protein_refs",
            "source_precursor_count",
            "target_decoy_label",
            *report.sample_ids,
        ]
    )
    for row in report.rows:
        value_lookup = {value.sample_id: value for value in row.values}
        writer.writerow(
            [
                row.peptide_key,
                row.peptide_sequence,
                row.modified_peptide,
                row.canonical_peptide,
                row.protein_group_id,
                ";".join(row.protein_refs),
                row.source_precursor_count,
                row.target_decoy_label.value,
                *[
                    value_getter(value_lookup[sample_id])
                    for sample_id in report.sample_ids
                ],
            ]
        )
    return buffer.getvalue()


def _render_dia_protein_wide_matrix(
    report: DiaProteinMatrixReport,
    *,
    value_getter: Callable[[DiaProteinMatrixValue], str],
) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "entity_id",
            "target_kind",
            "protein_refs",
            "peptide_count",
            "unique_peptide_count",
            "shared_peptide_count",
            "contributing_peptides",
            *report.sample_ids,
        ]
    )
    for row in report.rows:
        value_lookup = {value.sample_id: value for value in row.values}
        writer.writerow(
            [
                row.entity_id,
                row.target_kind.value,
                ";".join(row.protein_refs),
                row.peptide_count,
                row.unique_peptide_count,
                row.shared_peptide_count,
                ";".join(row.contributing_peptides),
                *[
                    value_getter(value_lookup[sample_id])
                    for sample_id in report.sample_ids
                ],
            ]
        )
    return buffer.getvalue()
