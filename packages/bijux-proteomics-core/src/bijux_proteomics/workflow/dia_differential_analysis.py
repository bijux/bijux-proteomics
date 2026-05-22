# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned DIA differential-analysis inputs over sample-resolved DIA matrices."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.dia.protein_matrix import (
    DiaPeptideRollupMethod,
    DiaProteinMatrixReport,
    DiaProteinMatrixTargetKind,
    DiaProteinRollupMethod,
    DiaSharedPeptidePolicy,
    build_diann_protein_matrix_report,
)
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    MissingValueKind,
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    QuantValue,
)
from bijux_proteomics_foundation import JsonModel


class DiaDifferentialSourceKind(StrEnum):
    """Owned DIA evidence sources that can drive downstream statistics."""

    DIANN = "diann"
    SPECTRONAUT = "spectronaut"


class DiaDifferentialMatrixSummary(JsonModel):
    """Compact summary over one DIA-native sample matrix prepared for statistics."""

    model_config = ConfigDict(extra="forbid")

    source_kind: DiaDifferentialSourceKind
    source_name: str = Field(..., min_length=1)
    entity_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    observed_cell_count: int = Field(..., ge=0)
    missing_cell_count: int = Field(..., ge=0)


class DiaDifferentialInputReport(JsonModel):
    """Governed DIA-native input packet for downstream normalization and modeling."""

    model_config = ConfigDict(extra="forbid")

    source_kind: DiaDifferentialSourceKind
    source_name: str = Field(..., min_length=1)
    matrix_summary: DiaDifferentialMatrixSummary
    table: LabelFreeQuantTable
    note: str = Field(..., min_length=1)


def build_diann_differential_input_report(
    result_tsv_path: Path,
    *,
    config_path: Path | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = 0.01,
    peptide_rollup_method: DiaPeptideRollupMethod = DiaPeptideRollupMethod.MAX,
    target_kind: DiaProteinMatrixTargetKind = DiaProteinMatrixTargetKind.PROTEIN_GROUP,
    shared_peptide_policy: DiaSharedPeptidePolicy = DiaSharedPeptidePolicy.INCLUDE,
    protein_rollup_method: DiaProteinRollupMethod = DiaProteinRollupMethod.SUM,
) -> DiaDifferentialInputReport:
    """Build a DIA-native quantification input packet directly from one DIA-NN report."""

    protein_matrix = build_diann_protein_matrix_report(
        result_tsv_path,
        config_path=config_path,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
        peptide_rollup_method=peptide_rollup_method,
        target_kind=target_kind,
        shared_peptide_policy=shared_peptide_policy,
        protein_rollup_method=protein_rollup_method,
    )
    return build_dia_differential_input_report(
        protein_matrix,
        source_kind=DiaDifferentialSourceKind.DIANN,
        note=(
            "dia differential input preserves one protein-level sample matrix over governed DIA-NN rollup evidence"
        ),
    )


def build_dia_differential_input_report(
    protein_matrix: DiaProteinMatrixReport,
    *,
    source_kind: DiaDifferentialSourceKind,
    note: str,
) -> DiaDifferentialInputReport:
    """Convert one DIA protein matrix into the owned quant-table contract."""

    table = _build_label_free_table_from_protein_matrix(protein_matrix)
    matrix_summary = DiaDifferentialMatrixSummary(
        source_kind=source_kind,
        source_name=protein_matrix.source_name,
        entity_count=len(table.entity_ids),
        sample_count=len(table.sample_ids),
        observed_cell_count=sum(1 for value in table.values if value.abundance is not None),
        missing_cell_count=sum(1 for value in table.values if value.abundance is None),
    )
    return DiaDifferentialInputReport(
        source_kind=source_kind,
        source_name=protein_matrix.source_name,
        matrix_summary=matrix_summary,
        table=table,
        note=note,
    )


def _build_label_free_table_from_protein_matrix(
    protein_matrix: DiaProteinMatrixReport,
) -> LabelFreeQuantTable:
    values: list[QuantValue] = []
    entity_protein_refs: dict[str, tuple[str, ...]] = {}
    entity_member_peptides: dict[str, tuple[str, ...]] = {}
    for row in protein_matrix.rows:
        entity_protein_refs[row.entity_id] = row.protein_refs
        entity_member_peptides[row.entity_id] = row.contributing_peptides
        for value in row.values:
            values.append(
                QuantValue(
                    sample_id=value.sample_id,
                    entity_id=row.entity_id,
                    abundance=value.abundance,
                    missing_value_kind=(
                        MissingValueKind.OBSERVED
                        if value.detected and value.abundance is not None
                        else MissingValueKind.NOT_OBSERVED
                    ),
                    source_feature_count=value.contributing_peptide_count,
                )
            )
    return LabelFreeQuantTable(
        entity_level=QuantEntityLevel.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        aggregation_method=QuantRollupMethod.SUM,
        normalization_method=NormalizationMethod.NONE,
        sample_ids=protein_matrix.sample_ids,
        entity_ids=tuple(row.entity_id for row in protein_matrix.rows),
        values=tuple(values),
        entity_protein_refs=entity_protein_refs,
        entity_member_peptides=entity_member_peptides,
    )
