# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned DIA precursor-matrix surfaces over DIA-NN precursor evidence."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.identification.diann_import import DiaNnPrecursorReviewEntry


class DiaPrecursorMatrixValue(JsonModel):
    """One sample-specific DIA precursor matrix cell."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    run_names: tuple[str, ...] = Field(default_factory=tuple)
    source_precursor_ids: tuple[str, ...] = Field(default_factory=tuple)
    abundance: float | None = Field(default=None, ge=0.0)
    q_value: float | None = Field(default=None, ge=0.0, le=1.0)
    source_observation_count: int = Field(..., ge=0)
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


class DiaPrecursorMatrixReport(JsonModel):
    """Owned DIA precursor matrix retaining source precursor IDs and q-values."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(default="DIA-NN", min_length=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    run_names: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[DiaPrecursorMatrixRow, ...] = Field(default_factory=tuple)
    summary: DiaPrecursorMatrixSummary
    note: str = Field(..., min_length=1)


def build_dia_precursor_matrix_report(
    rows: tuple[DiaNnPrecursorReviewEntry, ...],
    *,
    include_decoys: bool = False,
    max_q_value: float | None = None,
) -> DiaPrecursorMatrixReport:
    """Build a DIA precursor-by-sample matrix from normalized DIA-NN precursor rows."""

    if max_q_value is not None and not 0.0 <= max_q_value <= 1.0:
        raise ValueError("max_q_value must be between 0.0 and 1.0")

    sample_ids = tuple(sorted({row.sample_name for row in rows}))
    run_names = tuple(sorted({row.run_name for row in rows}))
    excluded_decoy_count = 0
    excluded_q_value_count = 0

    grouped: dict[
        str,
        dict[str, object],
    ] = {}
    for row in rows:
        if (
            not include_decoys
            and row.target_decoy_label is TargetDecoyLabel.DECOY
        ):
            excluded_decoy_count += 1
            continue
        if max_q_value is not None and row.q_value > max_q_value:
            excluded_q_value_count += 1
            continue
        precursor_key = _build_precursor_key(row)
        group = grouped.setdefault(
            precursor_key,
            {
                "peptide_sequence": row.peptide_sequence,
                "modified_peptide": row.modified_peptide,
                "canonical_peptide": row.canonical_peptide,
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
    observed_cell_count = 0
    missing_cell_count = 0
    target_row_count = 0
    decoy_row_count = 0
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
        for sample_id in sample_ids:
            observations = sample_rows.get(sample_id, [])
            if not observations:
                missing_cell_count += 1
                values.append(
                    DiaPrecursorMatrixValue(
                        sample_id=sample_id,
                        source_observation_count=0,
                        detected=False,
                    )
                )
                continue
            observed_cell_count += 1
            best_quantity = max(
                (
                    observation.precursor_quantity
                    for observation in observations
                    if observation.precursor_quantity is not None
                ),
                default=None,
            )
            best_q_value = min(observation.q_value for observation in observations)
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
                    abundance=best_quantity,
                    q_value=best_q_value,
                    source_observation_count=len(observations),
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

    return DiaPrecursorMatrixReport(
        sample_ids=sample_ids,
        run_names=run_names,
        rows=tuple(matrix_rows),
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
        ),
        note=(
            "precursor matrix groups DIA-NN evidence by modified peptide, charge, and protein group while preserving sample-specific source precursor identifiers because exported precursor ids may be run-scoped"
        ),
    )


def build_diann_precursor_matrix_report(
    result_tsv_path: Path,
    *,
    config_path: Path | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = None,
) -> DiaPrecursorMatrixReport:
    """Build a DIA precursor-by-sample matrix directly from a DIA-NN report."""

    from bijux_proteomics.identification.diann_import import build_diann_import_report

    report = build_diann_import_report(result_tsv_path, config_path=config_path)
    return build_dia_precursor_matrix_report(
        report.precursor_rows,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
    )


def _build_precursor_key(row: DiaNnPrecursorReviewEntry) -> str:
    return f"{row.modified_peptide}|z{row.charge}|{row.protein_group_id}"


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
