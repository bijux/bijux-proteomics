# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned DIA run-level QC surfaces over DIA-NN import evidence."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.identification.diann_import import (
        DiaNnBundleImportReport,
        DiaNnPrecursorReviewEntry,
        DiaNnProteinGroupReviewEntry,
    )


class DiaRunQcRunEntry(JsonModel):
    """One DIA run summarized at precursor and protein identity level."""

    model_config = ConfigDict(extra="forbid")

    run_name: str = Field(..., min_length=1)
    sample_name: str = Field(..., min_length=1)
    precursor_id_count: int = Field(..., ge=0)
    precursor_key_count: int = Field(..., ge=0)
    protein_group_id_count: int = Field(..., ge=0)
    protein_id_count: int = Field(..., ge=0)
    observed_precursor_quantity_count: int = Field(..., ge=0)
    observed_protein_quantity_count: int = Field(..., ge=0)
    flagged: bool = False


class DiaRunQcSummary(JsonModel):
    """Compact summary over one DIA run-QC report."""

    model_config = ConfigDict(extra="forbid")

    run_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    union_precursor_key_count: int = Field(..., ge=0)
    union_protein_group_id_count: int = Field(..., ge=0)
    union_protein_id_count: int = Field(..., ge=0)
    flagged_run_count: int = Field(..., ge=0)


class DiaRunQcReport(JsonModel):
    """Owned DIA run QC report over imported precursor and protein-group rows."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(default="DIA-NN", min_length=1)
    run_entries: tuple[DiaRunQcRunEntry, ...] = Field(default_factory=tuple)
    summary: DiaRunQcSummary
    note: str = Field(..., min_length=1)


def build_dia_run_qc_report(
    import_report: DiaNnBundleImportReport,
    *,
    include_decoys: bool = False,
    max_q_value: float | None = None,
) -> DiaRunQcReport:
    """Build DIA run-level QC over imported DIA-NN evidence."""

    precursor_rows = _filtered_precursor_rows(
        import_report.precursor_rows,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
    )
    protein_rows = _filtered_protein_rows(
        import_report.protein_group_rows,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
    )
    run_names = sorted({row.run_name for row in precursor_rows})
    union_precursor_keys = {_stable_precursor_key(row) for row in precursor_rows}
    union_protein_group_ids = {row.protein_group_id for row in protein_rows}
    union_protein_ids = {
        protein_ref for row in protein_rows for protein_ref in row.protein_refs
    }
    run_entries: list[DiaRunQcRunEntry] = []
    for run_name in run_names:
        run_precursors = [row for row in precursor_rows if row.run_name == run_name]
        run_proteins = [row for row in protein_rows if row.run_name == run_name]
        sample_names = sorted({row.sample_name for row in run_precursors})
        run_entries.append(
            DiaRunQcRunEntry(
                run_name=run_name,
                sample_name=sample_names[0] if sample_names else "unknown",
                precursor_id_count=len({row.precursor_id for row in run_precursors}),
                precursor_key_count=len(
                    {_stable_precursor_key(row) for row in run_precursors}
                ),
                protein_group_id_count=len(
                    {row.protein_group_id for row in run_proteins}
                ),
                protein_id_count=len(
                    {
                        protein_ref
                        for row in run_proteins
                        for protein_ref in row.protein_refs
                    }
                ),
                observed_precursor_quantity_count=sum(
                    row.precursor_quantity is not None for row in run_precursors
                ),
                observed_protein_quantity_count=sum(
                    row.protein_group_quantity is not None for row in run_proteins
                ),
            )
        )
    sample_count = len({entry.sample_name for entry in run_entries})
    return DiaRunQcReport(
        run_entries=tuple(sorted(run_entries, key=lambda entry: entry.run_name)),
        summary=DiaRunQcSummary(
            run_count=len(run_entries),
            sample_count=sample_count,
            union_precursor_key_count=len(union_precursor_keys),
            union_protein_group_id_count=len(union_protein_group_ids),
            union_protein_id_count=len(union_protein_ids),
            flagged_run_count=0,
        ),
        note=(
            "run qc keeps precursor and protein identity burden visible per run before higher-order missingness, correlation, and outlier review are applied"
        ),
    )


def build_diann_run_qc_report(
    result_tsv_path: Path,
    *,
    config_path: Path | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = None,
) -> DiaRunQcReport:
    """Build DIA run-level QC directly from one DIA-NN report."""

    from bijux_proteomics.identification.diann_import import build_diann_import_report

    return build_dia_run_qc_report(
        build_diann_import_report(result_tsv_path, config_path=config_path),
        include_decoys=include_decoys,
        max_q_value=max_q_value,
    )


def _filtered_precursor_rows(
    rows: tuple[DiaNnPrecursorReviewEntry, ...],
    *,
    include_decoys: bool,
    max_q_value: float | None,
) -> tuple[DiaNnPrecursorReviewEntry, ...]:
    filtered: list[DiaNnPrecursorReviewEntry] = []
    for row in rows:
        if not include_decoys and row.target_decoy_label is TargetDecoyLabel.DECOY:
            continue
        if max_q_value is not None and row.q_value > max_q_value:
            continue
        filtered.append(row)
    return tuple(filtered)


def _filtered_protein_rows(
    rows: tuple[DiaNnProteinGroupReviewEntry, ...],
    *,
    include_decoys: bool,
    max_q_value: float | None,
) -> tuple[DiaNnProteinGroupReviewEntry, ...]:
    filtered: list[DiaNnProteinGroupReviewEntry] = []
    for row in rows:
        if not include_decoys and row.target_decoy_label is TargetDecoyLabel.DECOY:
            continue
        if max_q_value is not None and row.q_value > max_q_value:
            continue
        filtered.append(row)
    return tuple(filtered)


def _stable_precursor_key(row: DiaNnPrecursorReviewEntry) -> str:
    return f"{row.modified_peptide}|z{row.charge}|{row.protein_group_id}"
