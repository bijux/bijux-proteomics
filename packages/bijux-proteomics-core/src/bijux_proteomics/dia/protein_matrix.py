# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned DIA peptide and protein matrix surfaces over precursor matrices."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.dia.precursor_matrix import (
    DiaPrecursorMatrixReport,
    DiaPrecursorMatrixRow,
    DiaPrecursorMatrixValue,
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
