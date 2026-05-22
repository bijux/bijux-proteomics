# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned DIA differential-analysis inputs over sample-resolved DIA matrices."""

from __future__ import annotations

from enum import StrEnum
from itertools import combinations
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
from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics.identification.spectronaut_import import (
    SpectronautImportReport,
    SpectronautPrecursorReviewEntry,
    SpectronautProteinGroupReviewEntry,
    build_spectronaut_import_report,
)
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
    MissingValueKind,
    MultiConditionDifferentialAbundanceReport,
    NormalizationMethod,
    NormalizationComparisonReport,
    QuantEntityLevel,
    QuantDesignMatrixReport,
    QuantDesignModelFitReport,
    QuantMeasureKind,
    QuantRollupMethod,
    QuantValue,
)
from bijux_proteomics.quantification.design_matrix import (
    build_quant_design_matrix_report,
    fit_quant_design_matrix_model,
)
from bijux_proteomics.quantification.differential_abundance import (
    apply_benjamini_hochberg,
    build_differential_abundance_report,
    build_multi_condition_differential_abundance_report,
)
from bijux_proteomics.quantification.normalization import (
    build_normalization_comparison_report,
    normalize_label_free_table,
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


class DiaDifferentialAnalysisReport(JsonModel):
    """Normalization, design, and differential results over one DIA input packet."""

    model_config = ConfigDict(extra="forbid")

    input_report: DiaDifferentialInputReport
    normalized_table: LabelFreeQuantTable
    normalization_comparison: NormalizationComparisonReport
    design_matrix: QuantDesignMatrixReport
    design_model_fit: QuantDesignModelFitReport
    differential_abundance_report: DifferentialAbundanceReport | None = None
    differential_abundance_multi_condition_report: (
        MultiConditionDifferentialAbundanceReport | None
    ) = None
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


def build_spectronaut_differential_input_report(
    result_tsv_path: Path,
    *,
    config_path: Path | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = 0.01,
) -> DiaDifferentialInputReport:
    """Build a DIA-native quantification input packet from one Spectronaut report."""

    import_report = build_spectronaut_import_report(
        result_tsv_path,
        config_path=config_path,
    )
    table = _build_label_free_table_from_spectronaut_report(
        import_report,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
    )
    matrix_summary = DiaDifferentialMatrixSummary(
        source_kind=DiaDifferentialSourceKind.SPECTRONAUT,
        source_name="Spectronaut",
        entity_count=len(table.entity_ids),
        sample_count=len(table.sample_ids),
        observed_cell_count=sum(1 for value in table.values if value.abundance is not None),
        missing_cell_count=sum(1 for value in table.values if value.abundance is None),
    )
    return DiaDifferentialInputReport(
        source_kind=DiaDifferentialSourceKind.SPECTRONAUT,
        source_name="Spectronaut",
        matrix_summary=matrix_summary,
        table=table,
        note=(
            "dia differential input preserves one protein-group sample matrix over governed Spectronaut report evidence"
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


def build_dia_differential_analysis_report(
    input_report: DiaDifferentialInputReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
) -> DiaDifferentialAnalysisReport:
    """Normalize one DIA-native matrix, build the design, and run differential testing."""

    normalized_table = normalize_label_free_table(
        input_report.table,
        method=normalization_method,
    )
    normalization_comparison = build_normalization_comparison_report(
        input_report.table,
        normalized_table,
    )
    design_matrix = build_quant_design_matrix_report(
        design_entries,
        batch_field=batch_field,
        covariate_fields=tuple(dict.fromkeys(covariate_fields)),
        pairing_field=pairing_field,
    )
    design_model_fit = fit_quant_design_matrix_model(
        normalized_table,
        design_matrix,
    )
    selected_contrast = _resolve_selected_contrast(
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    differential_abundance_report: DifferentialAbundanceReport | None = None
    differential_abundance_multi_condition_report: (
        MultiConditionDifferentialAbundanceReport | None
    ) = None
    if selected_contrast is not None:
        differential_abundance_report = apply_benjamini_hochberg(
            build_differential_abundance_report(
                normalized_table,
                design_entries,
                condition_a=selected_contrast[0],
                condition_b=selected_contrast[1],
            )
        )
    else:
        differential_abundance_multi_condition_report = (
            build_multi_condition_differential_abundance_report(
                normalized_table,
                design_entries,
                contrasts=tuple(combinations(_condition_names(design_entries), 2)),
            )
        )
    return DiaDifferentialAnalysisReport(
        input_report=input_report,
        normalized_table=normalized_table,
        normalization_comparison=normalization_comparison,
        design_matrix=design_matrix,
        design_model_fit=design_model_fit,
        differential_abundance_report=differential_abundance_report,
        differential_abundance_multi_condition_report=(
            differential_abundance_multi_condition_report
        ),
        note=(
            "dia differential analysis preserves normalization, explicit design encoding, and benjamini-hochberg-corrected differential results"
        ),
    )


def build_diann_differential_analysis_report(
    result_tsv_path: Path,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    config_path: Path | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = 0.01,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    peptide_rollup_method: DiaPeptideRollupMethod = DiaPeptideRollupMethod.MAX,
    target_kind: DiaProteinMatrixTargetKind = DiaProteinMatrixTargetKind.PROTEIN_GROUP,
    shared_peptide_policy: DiaSharedPeptidePolicy = DiaSharedPeptidePolicy.INCLUDE,
    protein_rollup_method: DiaProteinRollupMethod = DiaProteinRollupMethod.SUM,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
) -> DiaDifferentialAnalysisReport:
    """Build DIA-NN normalization, design, and differential results in one path."""

    input_report = build_diann_differential_input_report(
        result_tsv_path,
        config_path=config_path,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
        peptide_rollup_method=peptide_rollup_method,
        target_kind=target_kind,
        shared_peptide_policy=shared_peptide_policy,
        protein_rollup_method=protein_rollup_method,
    )
    return build_dia_differential_analysis_report(
        input_report,
        design_entries,
        normalization_method=normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
        batch_field=batch_field,
        covariate_fields=covariate_fields,
        pairing_field=pairing_field,
    )


def build_spectronaut_differential_analysis_report(
    result_tsv_path: Path,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    config_path: Path | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = 0.01,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
) -> DiaDifferentialAnalysisReport:
    """Build Spectronaut normalization, design, and differential results in one path."""

    input_report = build_spectronaut_differential_input_report(
        result_tsv_path,
        config_path=config_path,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
    )
    return build_dia_differential_analysis_report(
        input_report,
        design_entries,
        normalization_method=normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
        batch_field=batch_field,
        covariate_fields=covariate_fields,
        pairing_field=pairing_field,
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


def _build_label_free_table_from_spectronaut_report(
    import_report: SpectronautImportReport,
    *,
    include_decoys: bool,
    max_q_value: float | None,
) -> LabelFreeQuantTable:
    sample_ids = tuple(sorted({row.sample_name for row in import_report.protein_group_rows}))
    precursor_lookup = _spectronaut_precursor_lookup(
        import_report.precursor_rows,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
    )
    grouped_rows: dict[tuple[str, str], list[SpectronautProteinGroupReviewEntry]] = {}
    protein_refs_by_entity: dict[str, tuple[str, ...]] = {}
    for row in import_report.protein_group_rows:
        if not include_decoys and row.target_decoy_label is TargetDecoyLabel.DECOY:
            continue
        if max_q_value is not None and row.q_value > max_q_value:
            continue
        grouped_rows.setdefault((row.protein_group_id, row.sample_name), []).append(row)
        protein_refs_by_entity[row.protein_group_id] = row.protein_refs

    entity_ids = tuple(sorted(protein_refs_by_entity))
    values: list[QuantValue] = []
    entity_member_peptides = {
        entity_id: precursor_lookup.get(entity_id, ())
        for entity_id in entity_ids
    }
    for entity_id in entity_ids:
        for sample_id in sample_ids:
            observations = grouped_rows.get((entity_id, sample_id), [])
            abundances = [
                observation.protein_group_quantity
                for observation in observations
                if observation.protein_group_quantity is not None
            ]
            abundance = max(abundances) if abundances else None
            values.append(
                QuantValue(
                    sample_id=sample_id,
                    entity_id=entity_id,
                    abundance=abundance,
                    missing_value_kind=(
                        MissingValueKind.OBSERVED
                        if abundance is not None
                        else MissingValueKind.NOT_OBSERVED
                    ),
                    source_feature_count=sum(
                        observation.source_precursor_count for observation in observations
                    ),
                )
            )
    return LabelFreeQuantTable(
        entity_level=QuantEntityLevel.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        aggregation_method=QuantRollupMethod.SUM,
        normalization_method=NormalizationMethod.NONE,
        sample_ids=sample_ids,
        entity_ids=entity_ids,
        values=tuple(values),
        entity_protein_refs=protein_refs_by_entity,
        entity_member_peptides=entity_member_peptides,
    )


def _spectronaut_precursor_lookup(
    rows: tuple[SpectronautPrecursorReviewEntry, ...],
    *,
    include_decoys: bool,
    max_q_value: float | None,
) -> dict[str, tuple[str, ...]]:
    grouped: dict[str, set[str]] = {}
    for row in rows:
        if not include_decoys and row.target_decoy_label is TargetDecoyLabel.DECOY:
            continue
        if max_q_value is not None and row.q_value > max_q_value:
            continue
        grouped.setdefault(row.protein_group_id, set()).add(row.modified_peptide)
    return {
        protein_group_id: tuple(sorted(peptides))
        for protein_group_id, peptides in sorted(grouped.items())
    }


def _condition_names(
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[str, ...]:
    return tuple(sorted({entry.condition for entry in design_entries if entry.condition}))


def _resolve_selected_contrast(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None,
    condition_b: str | None,
) -> tuple[str, str] | None:
    conditions = _condition_names(design_entries)
    if condition_a is not None or condition_b is not None:
        if not condition_a or not condition_b:
            raise ValueError("both condition_a and condition_b are required together")
        return (condition_a, condition_b)
    if len(conditions) == 2:
        return (conditions[0], conditions[1])
    return None
