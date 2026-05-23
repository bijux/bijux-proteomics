# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned DIA differential-analysis inputs over sample-resolved DIA matrices."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from itertools import combinations
import math
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.dia.protein_matrix import (
    DiaPeptideRollupMethod,
    DiaProteinMatrixReport,
    DiaProteinMatrixTargetKind,
    DiaProteinRollupMethod,
    DiaSharedPeptidePolicy,
    build_diann_protein_matrix_report,
    build_spectronaut_protein_matrix_report,
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
    render_differential_abundance_tsv,
    render_multi_condition_differential_abundance_tsv,
)
from bijux_proteomics.quantification.normalization import (
    build_normalization_comparison_report,
    normalize_label_free_table,
)
from bijux_proteomics.study import (
    ExperimentDesignAnalysisFamily,
    ExperimentDesign,
    coerce_experiment_design,
    require_feasible_experiment_design_for_analysis,
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


class DiaDifferentialQcSummary(JsonModel):
    """Compact QC summary over one owned DIA differential-analysis report."""

    model_config = ConfigDict(extra="forbid")

    source_kind: DiaDifferentialSourceKind
    source_name: str = Field(..., min_length=1)
    normalization_method: NormalizationMethod
    entity_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    observed_raw_cell_count: int = Field(..., ge=0)
    missing_raw_cell_count: int = Field(..., ge=0)
    observed_normalized_cell_count: int = Field(..., ge=0)
    missing_normalized_cell_count: int = Field(..., ge=0)
    design_sample_count: int = Field(..., ge=0)
    design_column_count: int = Field(..., ge=0)
    fitted_entity_count: int = Field(..., ge=0)
    contrast_count: int = Field(..., ge=0)
    differential_entry_count: int = Field(..., ge=0)
    significant_entry_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class DiaDifferentialAnalysisReport(JsonModel):
    """Normalization, design, and differential results over one DIA input packet."""

    model_config = ConfigDict(extra="forbid")

    input_report: DiaDifferentialInputReport
    normalized_table: LabelFreeQuantTable
    normalization_comparison: NormalizationComparisonReport
    design_matrix: QuantDesignMatrixReport
    design_model_fit: QuantDesignModelFitReport
    qc_summary: DiaDifferentialQcSummary
    normalization_balance_plot: DiaNormalizationBalancePlot
    volcano_plot: DiaDifferentialVolcanoPlot | None = None
    differential_abundance_report: DifferentialAbundanceReport | None = None
    differential_abundance_multi_condition_report: (
        MultiConditionDifferentialAbundanceReport | None
    ) = None
    note: str = Field(..., min_length=1)


class DiaNormalizationBalancePoint(JsonModel):
    """One sample point for before/after DIA normalization plotting."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    stage: str = Field(..., min_length=1)
    total_abundance: float = Field(..., ge=0.0)
    median_abundance: float = Field(..., ge=0.0)
    interquartile_range: float = Field(..., ge=0.0)


class DiaNormalizationBalancePlot(JsonModel):
    """Plot-ready before/after DIA sample-balance payload."""

    model_config = ConfigDict(extra="forbid")

    method: NormalizationMethod
    points: tuple[DiaNormalizationBalancePoint, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class DiaDifferentialVolcanoPoint(JsonModel):
    """One entity point for DIA differential volcano plotting."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    log2_fold_change: float
    raw_p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float = Field(..., ge=0.0, le=1.0)
    negative_log10_adjusted_p_value: float = Field(..., ge=0.0)
    highlighted: bool


class DiaDifferentialVolcanoPlot(JsonModel):
    """Plot-ready volcano payload for one DIA differential contrast."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    significant_point_count: int = Field(..., ge=0)
    points: tuple[DiaDifferentialVolcanoPoint, ...] = Field(default_factory=tuple)
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
    peptide_rollup_method: DiaPeptideRollupMethod = DiaPeptideRollupMethod.MAX,
    target_kind: DiaProteinMatrixTargetKind = DiaProteinMatrixTargetKind.PROTEIN_GROUP,
    shared_peptide_policy: DiaSharedPeptidePolicy = DiaSharedPeptidePolicy.INCLUDE,
    protein_rollup_method: DiaProteinRollupMethod = DiaProteinRollupMethod.SUM,
) -> DiaDifferentialInputReport:
    """Build a DIA-native quantification input packet from one Spectronaut report."""

    protein_matrix = build_spectronaut_protein_matrix_report(
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
        source_kind=DiaDifferentialSourceKind.SPECTRONAUT,
        note=(
            "dia differential input preserves one protein-level sample matrix over governed Spectronaut rollup evidence"
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


def build_dia_protein_matrix_differential_analysis_report(
    protein_matrix: DiaProteinMatrixReport,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    source_kind: DiaDifferentialSourceKind,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
    note: str | None = None,
) -> DiaDifferentialAnalysisReport:
    """Run owned DIA differential analysis directly from one DIA protein matrix."""

    input_report = build_dia_differential_input_report(
        protein_matrix,
        source_kind=source_kind,
        note=note
        or (
            f"dia differential input preserves one protein-level sample matrix over governed {protein_matrix.source_name} rollup evidence"
        ),
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


def build_dia_differential_analysis_report(
    input_report: DiaDifferentialInputReport,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
) -> DiaDifferentialAnalysisReport:
    """Normalize one DIA-native matrix, build the design, and run differential testing."""

    experiment_design = coerce_experiment_design(design_entries)
    selected_contrast = _resolve_selected_contrast(
        experiment_design.entries,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    feasibility_report = require_feasible_experiment_design_for_analysis(
        experiment_design,
        chosen_analysis_family=(
            ExperimentDesignAnalysisFamily.PAIRWISE_DIFFERENTIAL
            if selected_contrast is not None
            else ExperimentDesignAnalysisFamily.MULTI_CONDITION_DIFFERENTIAL
        ),
        condition_a=(
            selected_contrast[0] if selected_contrast is not None else condition_a
        ),
        condition_b=(
            selected_contrast[1] if selected_contrast is not None else condition_b
        ),
        batch_field=batch_field if batch_field else None,
        pairing_field=pairing_field,
    )
    design_entries = feasibility_report.experiment_design.entries
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
    differential_abundance_report: DifferentialAbundanceReport | None = None
    differential_abundance_multi_condition_report: (
        MultiConditionDifferentialAbundanceReport | None
    ) = None
    volcano_plot: DiaDifferentialVolcanoPlot | None = None
    if selected_contrast is not None:
        differential_abundance_report = apply_benjamini_hochberg(
            build_differential_abundance_report(
                normalized_table,
                design_entries,
                condition_a=selected_contrast[0],
                condition_b=selected_contrast[1],
            )
        )
        volcano_plot = build_dia_differential_volcano_plot(
            differential_abundance_report,
            protein_refs_by_entity=normalized_table.entity_protein_refs,
        )
    else:
        differential_abundance_multi_condition_report = (
            build_multi_condition_differential_abundance_report(
                normalized_table,
                design_entries,
                contrasts=tuple(combinations(_condition_names(design_entries), 2)),
            )
        )
    qc_summary = _build_dia_differential_qc_summary(
        input_report,
        normalized_table=normalized_table,
        design_matrix=design_matrix,
        design_model_fit=design_model_fit,
        differential_abundance_report=differential_abundance_report,
        differential_abundance_multi_condition_report=(
            differential_abundance_multi_condition_report
        ),
    )
    return DiaDifferentialAnalysisReport(
        input_report=input_report,
        normalized_table=normalized_table,
        normalization_comparison=normalization_comparison,
        design_matrix=design_matrix,
        design_model_fit=design_model_fit,
        qc_summary=qc_summary,
        normalization_balance_plot=build_dia_normalization_balance_plot(
            normalization_comparison
        ),
        volcano_plot=volcano_plot,
        differential_abundance_report=differential_abundance_report,
        differential_abundance_multi_condition_report=(
            differential_abundance_multi_condition_report
        ),
        note=(
            "dia differential analysis preserves normalization, explicit design encoding, benjamini-hochberg-corrected differential results, and qc summary counts"
        ),
    )


def _build_dia_differential_qc_summary(
    input_report: DiaDifferentialInputReport,
    *,
    normalized_table: LabelFreeQuantTable,
    design_matrix: QuantDesignMatrixReport,
    design_model_fit: QuantDesignModelFitReport,
    differential_abundance_report: DifferentialAbundanceReport | None,
    differential_abundance_multi_condition_report: (
        MultiConditionDifferentialAbundanceReport | None
    ),
) -> DiaDifferentialQcSummary:
    contrast_count = 0
    differential_entry_count = 0
    significant_entry_count = 0
    if differential_abundance_report is not None:
        contrast_count = 1
        differential_entry_count = len(differential_abundance_report.entries)
        significant_entry_count = _count_significant_differential_entries(
            differential_abundance_report.entries
        )
    elif differential_abundance_multi_condition_report is not None:
        contrast_count = len(differential_abundance_multi_condition_report.reports)
        differential_entry_count = sum(
            len(report.entries)
            for report in differential_abundance_multi_condition_report.reports
        )
        significant_entry_count = sum(
            _count_significant_differential_entries(report.entries)
            for report in differential_abundance_multi_condition_report.reports
        )
    return DiaDifferentialQcSummary(
        source_kind=input_report.source_kind,
        source_name=input_report.source_name,
        normalization_method=normalized_table.normalization_method,
        entity_count=len(input_report.table.entity_ids),
        sample_count=len(input_report.table.sample_ids),
        observed_raw_cell_count=sum(
            1 for value in input_report.table.values if value.abundance is not None
        ),
        missing_raw_cell_count=sum(
            1 for value in input_report.table.values if value.abundance is None
        ),
        observed_normalized_cell_count=sum(
            1 for value in normalized_table.values if value.abundance is not None
        ),
        missing_normalized_cell_count=sum(
            1 for value in normalized_table.values if value.abundance is None
        ),
        design_sample_count=design_matrix.sample_count,
        design_column_count=design_matrix.column_count,
        fitted_entity_count=design_model_fit.fitted_entity_count,
        contrast_count=contrast_count,
        differential_entry_count=differential_entry_count,
        significant_entry_count=significant_entry_count,
        note=(
            "dia differential qc summary preserves matrix completeness, design size, fitted entities, and significant differential counts"
        ),
    )


def _count_significant_differential_entries(
    entries: tuple[object, ...],
    *,
    adjusted_p_value_threshold: float = 0.05,
) -> int:
    return sum(
        1
        for entry in entries
        if getattr(entry, "adjusted_p_value", None) is not None
        and getattr(entry, "adjusted_p_value") <= adjusted_p_value_threshold
    )


def build_diann_differential_analysis_report(
    result_tsv_path: Path,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
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

    experiment_design = coerce_experiment_design(design_entries)
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
    return build_dia_protein_matrix_differential_analysis_report(
        protein_matrix,
        experiment_design,
        source_kind=DiaDifferentialSourceKind.DIANN,
        normalization_method=normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
        batch_field=batch_field,
        covariate_fields=covariate_fields,
        pairing_field=pairing_field,
    )


def build_spectronaut_differential_analysis_report(
    result_tsv_path: Path,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
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
    """Build Spectronaut normalization, design, and differential results in one path."""

    experiment_design = coerce_experiment_design(design_entries)
    protein_matrix = build_spectronaut_protein_matrix_report(
        result_tsv_path,
        config_path=config_path,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
        peptide_rollup_method=peptide_rollup_method,
        target_kind=target_kind,
        shared_peptide_policy=shared_peptide_policy,
        protein_rollup_method=protein_rollup_method,
    )
    return build_dia_protein_matrix_differential_analysis_report(
        protein_matrix,
        experiment_design,
        source_kind=DiaDifferentialSourceKind.SPECTRONAUT,
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


def build_dia_normalization_balance_plot(
    comparison: NormalizationComparisonReport,
) -> DiaNormalizationBalancePlot:
    """Build one before/after sample-balance plot payload from normalization review."""

    points = tuple(
        [
            *[
                DiaNormalizationBalancePoint(
                    sample_id=entry.sample_id,
                    stage="before",
                    total_abundance=entry.total_abundance,
                    median_abundance=entry.median_abundance,
                    interquartile_range=entry.interquartile_range,
                )
                for entry in comparison.before
            ],
            *[
                DiaNormalizationBalancePoint(
                    sample_id=entry.sample_id,
                    stage="after",
                    total_abundance=entry.total_abundance,
                    median_abundance=entry.median_abundance,
                    interquartile_range=entry.interquartile_range,
                )
                for entry in comparison.after
            ],
        ]
    )
    return DiaNormalizationBalancePlot(
        method=comparison.method,
        points=tuple(sorted(points, key=lambda entry: (entry.sample_id, entry.stage))),
        note=(
            "sample-balance plot preserves before-and-after totals, medians, and spread for DIA normalization review"
        ),
    )


def build_dia_differential_volcano_plot(
    report: DifferentialAbundanceReport,
    *,
    protein_refs_by_entity: dict[str, tuple[str, ...]],
    adjusted_p_value_threshold: float = 0.1,
    absolute_log2_fold_change_threshold: float = 1.0,
) -> DiaDifferentialVolcanoPlot:
    """Build one volcano payload over a BH-corrected DIA differential report."""

    points: list[DiaDifferentialVolcanoPoint] = []
    for entry in report.entries:
        adjusted_p_value = entry.adjusted_p_value or entry.p_value
        highlighted = (
            adjusted_p_value <= adjusted_p_value_threshold
            and abs(entry.log2_fold_change) >= absolute_log2_fold_change_threshold
        )
        points.append(
            DiaDifferentialVolcanoPoint(
                entity_id=entry.entity_id,
                protein_refs=protein_refs_by_entity.get(entry.entity_id, ()),
                log2_fold_change=entry.log2_fold_change,
                raw_p_value=entry.p_value,
                adjusted_p_value=adjusted_p_value,
                negative_log10_adjusted_p_value=_negative_log10(adjusted_p_value),
                highlighted=highlighted,
            )
        )
    return DiaDifferentialVolcanoPlot(
        condition_a=report.condition_a,
        condition_b=report.condition_b,
        significant_point_count=sum(1 for point in points if point.highlighted),
        points=tuple(
            sorted(
                points,
                key=lambda point: (
                    -point.negative_log10_adjusted_p_value,
                    -abs(point.log2_fold_change),
                    point.entity_id,
                ),
            )
        ),
        note=(
            "volcano plot preserves fold change and adjusted significance for one explicit DIA contrast"
        ),
    )


def render_dia_differential_matrix_tsv(table: LabelFreeQuantTable) -> str:
    """Render one DIA differential matrix as a stable wide TSV table."""

    sample_ids = list(table.sample_ids)
    value_lookup = {(value.entity_id, value.sample_id): value for value in table.values}
    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "protein_refs",
            "member_peptides",
            *sample_ids,
        )
    )
    for entity_id in table.entity_ids:
        writer.writerow(
            (
                entity_id,
                ";".join(table.entity_protein_refs.get(entity_id, ())),
                ";".join(table.entity_member_peptides.get(entity_id, ())),
                *[
                    ""
                    if (value := value_lookup[(entity_id, sample_id)]).abundance is None
                    else f"{value.abundance:g}"
                    for sample_id in sample_ids
                ],
            )
        )
    return handle.getvalue()


def render_dia_differential_results_tsv(
    report: DiaDifferentialAnalysisReport,
) -> str:
    """Render one DIA differential result surface as TSV."""

    if report.differential_abundance_report is not None:
        return render_differential_abundance_tsv(report.differential_abundance_report)
    if report.differential_abundance_multi_condition_report is not None:
        return render_multi_condition_differential_abundance_tsv(
            report.differential_abundance_multi_condition_report
        )
    raise ValueError("dia differential analysis report does not contain differential results")


def render_dia_differential_qc_summary_tsv(
    report: DiaDifferentialAnalysisReport,
) -> str:
    """Render one DIA differential QC summary as a stable TSV ledger."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("source_kind", report.qc_summary.source_kind.value),
        ("source_name", report.qc_summary.source_name),
        ("normalization_method", report.qc_summary.normalization_method.value),
        ("entity_count", report.qc_summary.entity_count),
        ("sample_count", report.qc_summary.sample_count),
        ("observed_raw_cell_count", report.qc_summary.observed_raw_cell_count),
        ("missing_raw_cell_count", report.qc_summary.missing_raw_cell_count),
        ("observed_normalized_cell_count", report.qc_summary.observed_normalized_cell_count),
        ("missing_normalized_cell_count", report.qc_summary.missing_normalized_cell_count),
        ("design_sample_count", report.qc_summary.design_sample_count),
        ("design_column_count", report.qc_summary.design_column_count),
        ("fitted_entity_count", report.qc_summary.fitted_entity_count),
        ("contrast_count", report.qc_summary.contrast_count),
        ("differential_entry_count", report.qc_summary.differential_entry_count),
        ("significant_entry_count", report.qc_summary.significant_entry_count),
        ("note", report.qc_summary.note),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def render_dia_normalization_balance_plot_tsv(
    plot: DiaNormalizationBalancePlot,
) -> str:
    """Render one normalization-balance plot payload as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "sample_id",
            "stage",
            "total_abundance",
            "median_abundance",
            "interquartile_range",
        )
    )
    for point in plot.points:
        writer.writerow(
            (
                point.sample_id,
                point.stage,
                f"{point.total_abundance:g}",
                f"{point.median_abundance:g}",
                f"{point.interquartile_range:g}",
            )
        )
    return handle.getvalue()


def render_dia_differential_volcano_plot_tsv(
    plot: DiaDifferentialVolcanoPlot,
) -> str:
    """Render one DIA volcano plot payload as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "protein_refs",
            "log2_fold_change",
            "raw_p_value",
            "adjusted_p_value",
            "negative_log10_adjusted_p_value",
            "highlighted",
        )
    )
    for point in plot.points:
        writer.writerow(
            (
                point.entity_id,
                ";".join(point.protein_refs),
                f"{point.log2_fold_change:.6g}",
                f"{point.raw_p_value:.6g}",
                f"{point.adjusted_p_value:.6g}",
                f"{point.negative_log10_adjusted_p_value:.6g}",
                str(point.highlighted).lower(),
            )
        )
    return handle.getvalue()


def export_dia_differential_matrix_tsv(table: LabelFreeQuantTable, path: Path) -> None:
    """Write one DIA differential matrix to a stable TSV artifact."""

    path.write_text(render_dia_differential_matrix_tsv(table), encoding="utf-8")


def export_dia_differential_results_tsv(
    report: DiaDifferentialAnalysisReport,
    path: Path,
) -> None:
    """Write one DIA differential result surface to a stable TSV artifact."""

    path.write_text(render_dia_differential_results_tsv(report), encoding="utf-8")


def export_dia_differential_qc_summary_tsv(
    report: DiaDifferentialAnalysisReport,
    path: Path,
) -> None:
    """Write one DIA differential QC summary to a stable TSV artifact."""

    path.write_text(render_dia_differential_qc_summary_tsv(report), encoding="utf-8")


def export_dia_normalization_balance_plot_tsv(
    plot: DiaNormalizationBalancePlot,
    path: Path,
) -> None:
    """Write one normalization-balance plot payload to a stable TSV artifact."""

    path.write_text(render_dia_normalization_balance_plot_tsv(plot), encoding="utf-8")


def export_dia_differential_volcano_plot_tsv(
    plot: DiaDifferentialVolcanoPlot,
    path: Path,
) -> None:
    """Write one DIA volcano plot payload to a stable TSV artifact."""

    path.write_text(render_dia_differential_volcano_plot_tsv(plot), encoding="utf-8")


def _condition_names(
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
) -> tuple[str, ...]:
    return coerce_experiment_design(design_entries).conditions


def _resolve_selected_contrast(
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
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


def _negative_log10(value: float) -> float:
    bounded = max(value, 1e-300)
    return -math.log10(bounded)
