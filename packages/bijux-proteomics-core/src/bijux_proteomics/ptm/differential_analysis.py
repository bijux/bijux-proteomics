# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned PTM site differential-analysis surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
import math
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.ptm.site_quantification import (
    PtmSiteQuantRow,
    PtmSiteQuantificationReport,
)
from bijux_proteomics.ptm.peptide_parser import parse_modified_peptide
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceTestType,
    DifferentialBrokenPairEntry,
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
    Ms1FeatureRecord,
    NormalizationComparisonReport,
    NormalizationMethod,
    PairedDifferentialPolicy,
    QuantDesignMatrixReport,
    QuantDesignModelFitReport,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    QuantValue,
    build_label_free_intensity_table,
)
from bijux_proteomics.quantification.design_matrix import (
    build_quant_design_matrix_report,
    fit_quant_design_matrix_model,
)
from bijux_proteomics.quantification.differential_abundance import (
    build_differential_abundance_report,
)
from bijux_proteomics.quantification.normalization import (
    build_normalization_comparison_report,
    normalize_label_free_table,
)
from bijux_proteomics_foundation import JsonModel


class PtmSiteDifferentialEntry(JsonModel):
    """One PTM site-level two-condition differential result."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    ambiguous: bool = False
    shared_peptide: bool = False
    localized_peptides: tuple[str, ...] = Field(default_factory=tuple)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    observations_a: int = Field(..., ge=0)
    observations_b: int = Field(..., ge=0)
    complete_pair_count: int = Field(default=0, ge=0)
    mean_log2_abundance_a: float
    mean_log2_abundance_b: float
    log2_fold_change: float
    p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    standard_error: float | None = Field(default=None, ge=0.0)
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    effect_size_cohens_d: float | None = None
    protein_log2_fold_change: float | None = None
    protein_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    corrected_log2_fold_change: float | None = None
    protein_correction_status: str = Field(..., min_length=1)
    uncertainty_note: str | None = None


class PtmSiteDifferentialReport(JsonModel):
    """Stable PTM site differential report over one explicit contrast."""

    model_config = ConfigDict(extra="forbid")

    normalization_method: NormalizationMethod
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    entries: tuple[PtmSiteDifferentialEntry, ...] = Field(default_factory=tuple)
    broken_pairs: tuple[DifferentialBrokenPairEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class PtmProteinCorrectionMode(StrEnum):
    """Protein-level correction policies for PTM differential review."""

    NONE = "none"
    SUBTRACT_UNMODIFIED_PROTEIN = "subtract_unmodified_protein"


class PtmProteinCorrectionStatus(StrEnum):
    """Correction availability status for one PTM site differential row."""

    NOT_REQUESTED = "not_requested"
    CORRECTED = "corrected"
    MISSING_PROTEIN_BASELINE = "missing_protein_baseline"


class PtmDifferentialVolcanoPoint(JsonModel):
    """One PTM site point for volcano-plot review."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    raw_log2_fold_change: float
    corrected_log2_fold_change: float | None = None
    plotted_log2_fold_change: float
    raw_p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float = Field(..., ge=0.0, le=1.0)
    negative_log10_adjusted_p_value: float = Field(..., ge=0.0)
    highlighted: bool = False
    protein_correction_status: str = Field(..., min_length=1)


class PtmDifferentialVolcanoPlot(JsonModel):
    """Plot-ready PTM site differential volcano payload for one contrast."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    protein_correction_mode: PtmProteinCorrectionMode
    significant_point_count: int = Field(..., ge=0)
    points: tuple[PtmDifferentialVolcanoPoint, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class PtmDifferentialAnalysisReport(JsonModel):
    """PTM site differential analysis over one governed site-quant matrix."""

    model_config = ConfigDict(extra="forbid")

    site_quantification: PtmSiteQuantificationReport
    site_quant_table: LabelFreeQuantTable
    normalized_site_quant_table: LabelFreeQuantTable
    normalization_comparison: NormalizationComparisonReport
    design_matrix: QuantDesignMatrixReport
    design_model_fit: QuantDesignModelFitReport
    protein_correction_mode: PtmProteinCorrectionMode
    differential_report: PtmSiteDifferentialReport
    volcano_plot: PtmDifferentialVolcanoPlot
    note: str = Field(..., min_length=1)


def build_ptm_differential_analysis_report(
    site_quantification: PtmSiteQuantificationReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    feature_records: tuple[Ms1FeatureRecord, ...] | None = None,
    protein_correction_mode: PtmProteinCorrectionMode = PtmProteinCorrectionMode.NONE,
    batch_field: str = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
) -> PtmDifferentialAnalysisReport:
    """Normalize PTM site intensities and test one explicit two-condition contrast."""

    effective_pairing_field = pairing_field
    if effective_pairing_field is None and all(
        entry.pair_id not in (None, "") for entry in design_entries
    ):
        effective_pairing_field = "pair_id"
    site_quant_table = _build_label_free_table_from_site_quantification(site_quantification)
    normalization_reference_table = _build_label_free_table_from_site_quantification(
        site_quantification,
        include_ambiguity_groups=True,
    )
    normalized_reference_table = normalize_label_free_table(
        normalization_reference_table,
        method=normalization_method,
    )
    normalized_table = _project_label_free_table_entities(
        normalized_reference_table,
        entity_ids=site_quant_table.entity_ids,
    )
    normalization_comparison = build_normalization_comparison_report(
        site_quant_table,
        normalized_table,
    )
    design_matrix = build_quant_design_matrix_report(
        design_entries,
        batch_field=batch_field,
        covariate_fields=tuple(dict.fromkeys(covariate_fields)),
        pairing_field=effective_pairing_field,
    )
    design_model_fit = fit_quant_design_matrix_model(
        normalized_table,
        design_matrix,
    )
    resolved_condition_a, resolved_condition_b = _resolve_selected_contrast(
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    paired_policy = (
        PairedDifferentialPolicy(pair_id_field=effective_pairing_field)
        if effective_pairing_field is not None
        else None
    )
    differential = build_differential_abundance_report(
        normalized_table,
        design_entries,
        condition_a=resolved_condition_a,
        condition_b=resolved_condition_b,
        test_type=(
            DifferentialAbundanceTestType.PAIRED_T_TEST
            if paired_policy is not None
            else DifferentialAbundanceTestType.WELCH_T_TEST
        ),
        paired_policy=paired_policy,
    )
    protein_differential_lookup = _build_protein_differential_lookup(
        design_entries,
        normalization_method=normalization_method,
        condition_a=resolved_condition_a,
        condition_b=resolved_condition_b,
        feature_records=feature_records,
        protein_correction_mode=protein_correction_mode,
        pairing_field=effective_pairing_field,
    )
    differential_report = _build_ptm_site_differential_report(
        differential,
        site_quantification.rows,
        protein_differential_lookup=protein_differential_lookup,
        protein_correction_mode=protein_correction_mode,
    )
    volcano_plot = build_ptm_differential_volcano_plot(differential_report)
    return PtmDifferentialAnalysisReport(
        site_quantification=site_quantification,
        site_quant_table=site_quant_table,
        normalized_site_quant_table=normalized_table,
        normalization_comparison=normalization_comparison,
        design_matrix=design_matrix,
        design_model_fit=design_model_fit,
        protein_correction_mode=protein_correction_mode,
        differential_report=differential_report,
        volcano_plot=volcano_plot,
        note=(
            "ptm differential analysis normalizes exact-site testing against one non-duplicated PTM signal matrix, preserves explicit design encoding, and emits benjamini-hochberg-corrected site testing"
        ),
    )


def build_ptm_differential_volcano_plot(
    report: PtmSiteDifferentialReport,
    *,
    adjusted_p_value_threshold: float = 0.1,
    absolute_log2_fold_change_threshold: float = 1.0,
) -> PtmDifferentialVolcanoPlot:
    """Build one volcano payload over one governed PTM site differential report."""

    points: list[PtmDifferentialVolcanoPoint] = []
    for entry in report.entries:
        adjusted_p_value = entry.adjusted_p_value or entry.p_value
        plotted_log2_fold_change = (
            entry.corrected_log2_fold_change
            if entry.corrected_log2_fold_change is not None
            else entry.log2_fold_change
        )
        highlighted = (
            adjusted_p_value <= adjusted_p_value_threshold
            and abs(plotted_log2_fold_change) >= absolute_log2_fold_change_threshold
        )
        points.append(
            PtmDifferentialVolcanoPoint(
                site_key=entry.site_key,
                protein_ref=entry.protein_ref,
                residue=entry.residue,
                position=entry.position,
                modification_name=entry.modification_name,
                raw_log2_fold_change=entry.log2_fold_change,
                corrected_log2_fold_change=entry.corrected_log2_fold_change,
                plotted_log2_fold_change=plotted_log2_fold_change,
                raw_p_value=entry.p_value,
                adjusted_p_value=adjusted_p_value,
                negative_log10_adjusted_p_value=_negative_log10(adjusted_p_value),
                highlighted=highlighted,
                protein_correction_status=entry.protein_correction_status,
            )
        )
    return PtmDifferentialVolcanoPlot(
        condition_a=report.condition_a,
        condition_b=report.condition_b,
        protein_correction_mode=(
            PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN
            if any(
                entry.protein_correction_status
                == PtmProteinCorrectionStatus.CORRECTED.value
                for entry in report.entries
            )
            else PtmProteinCorrectionMode.NONE
        ),
        significant_point_count=sum(1 for point in points if point.highlighted),
        points=tuple(
            sorted(
                points,
                key=lambda point: (
                    -point.negative_log10_adjusted_p_value,
                    -abs(point.plotted_log2_fold_change),
                    point.site_key,
                ),
            )
        ),
        note=(
            "ptm volcano plot preserves site fold change and adjusted significance for one explicit contrast"
        ),
    )


def _build_label_free_table_from_site_quantification(
    report: PtmSiteQuantificationReport,
    *,
    include_ambiguity_groups: bool = False,
) -> LabelFreeQuantTable:
    values: list[QuantValue] = []
    entity_protein_refs: dict[str, tuple[str, ...]] = {}
    entity_member_peptides: dict[str, tuple[str, ...]] = {}
    entity_ids: list[str] = []
    for row in report.rows:
        entity_ids.append(row.site_key)
        entity_protein_refs[row.site_key] = (row.protein_ref,)
        entity_member_peptides[row.site_key] = row.localized_peptides
        for value in row.values:
            values.append(
                QuantValue(
                    sample_id=value.sample_id,
                    entity_id=row.site_key,
                    abundance=value.abundance,
                    missing_value_kind=value.missing_value_kind,
                    source_feature_count=value.contributing_feature_count,
                )
            )
    if include_ambiguity_groups and report.ambiguous_group_quantification is not None:
        for row in report.ambiguous_group_quantification.rows:
            entity_ids.append(row.group_key)
            entity_protein_refs[row.group_key] = (row.protein_ref,)
            entity_member_peptides[row.group_key] = row.localized_peptides
            for value in row.values:
                values.append(
                    QuantValue(
                        sample_id=value.sample_id,
                        entity_id=row.group_key,
                        abundance=value.abundance,
                        missing_value_kind=value.missing_value_kind,
                        source_feature_count=value.contributing_feature_count,
                    )
                )
    return LabelFreeQuantTable(
        entity_level=QuantEntityLevel.PEPTIDE,
        measure_kind=QuantMeasureKind.INTENSITY,
        aggregation_method=QuantRollupMethod.SUM,
        normalization_method=NormalizationMethod.NONE,
        sample_ids=report.sample_ids,
        entity_ids=tuple(entity_ids),
        values=tuple(values),
        entity_protein_refs=entity_protein_refs,
        entity_member_peptides=entity_member_peptides,
    )


def _project_label_free_table_entities(
    table: LabelFreeQuantTable,
    *,
    entity_ids: tuple[str, ...],
) -> LabelFreeQuantTable:
    entity_id_set = set(entity_ids)
    return LabelFreeQuantTable(
        entity_level=table.entity_level,
        measure_kind=table.measure_kind,
        aggregation_method=table.aggregation_method,
        normalization_method=table.normalization_method,
        sample_ids=table.sample_ids,
        entity_ids=entity_ids,
        values=tuple(value for value in table.values if value.entity_id in entity_id_set),
        entity_protein_refs={
            entity_id: table.entity_protein_refs[entity_id]
            for entity_id in entity_ids
            if entity_id in table.entity_protein_refs
        },
        entity_member_peptides={
            entity_id: table.entity_member_peptides[entity_id]
            for entity_id in entity_ids
            if entity_id in table.entity_member_peptides
        },
    )


def _build_ptm_site_differential_report(
    differential: DifferentialAbundanceReport,
    site_rows: tuple[PtmSiteQuantRow, ...],
    *,
    protein_differential_lookup: dict[str, PtmProteinDifferentialReference],
    protein_correction_mode: PtmProteinCorrectionMode,
) -> PtmSiteDifferentialReport:
    row_by_site = {row.site_key: row for row in site_rows}
    entries: list[PtmSiteDifferentialEntry] = []
    for entry in differential.entries:
        row = row_by_site[entry.entity_id]
        correction_reference = protein_differential_lookup.get(row.protein_ref)
        protein_log2_fold_change = None
        protein_adjusted_p_value = None
        corrected_log2_fold_change = None
        correction_status = PtmProteinCorrectionStatus.NOT_REQUESTED
        if protein_correction_mode is PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN:
            if correction_reference is None:
                correction_status = PtmProteinCorrectionStatus.MISSING_PROTEIN_BASELINE
            else:
                protein_log2_fold_change = correction_reference.log2_fold_change
                protein_adjusted_p_value = correction_reference.adjusted_p_value
                corrected_log2_fold_change = (
                    entry.log2_fold_change - correction_reference.log2_fold_change
                )
                correction_status = PtmProteinCorrectionStatus.CORRECTED
        entries.append(
            PtmSiteDifferentialEntry(
                site_key=row.site_key,
                protein_ref=row.protein_ref,
                residue=row.residue,
                position=row.position,
                modification_name=row.modification_name,
                ambiguous=row.ambiguous,
                shared_peptide=row.shared_peptide,
                localized_peptides=row.localized_peptides,
                condition_a=entry.condition_a,
                condition_b=entry.condition_b,
                observations_a=entry.observations_a,
                observations_b=entry.observations_b,
                complete_pair_count=entry.complete_pair_count,
                mean_log2_abundance_a=entry.mean_log2_abundance_a,
                mean_log2_abundance_b=entry.mean_log2_abundance_b,
                log2_fold_change=entry.log2_fold_change,
                p_value=entry.p_value,
                adjusted_p_value=entry.adjusted_p_value,
                standard_error=entry.standard_error,
                confidence_interval_low=entry.confidence_interval_low,
                confidence_interval_high=entry.confidence_interval_high,
                effect_size_cohens_d=entry.effect_size_cohens_d,
                protein_log2_fold_change=protein_log2_fold_change,
                protein_adjusted_p_value=protein_adjusted_p_value,
                corrected_log2_fold_change=corrected_log2_fold_change,
                protein_correction_status=correction_status.value,
                uncertainty_note=entry.uncertainty_note,
            )
        )
    return PtmSiteDifferentialReport(
        normalization_method=differential.normalization_method,
        condition_a=differential.condition_a,
        condition_b=differential.condition_b,
        entries=tuple(entries),
        broken_pairs=differential.broken_pairs,
        note=(
            "ptm site differential report preserves protein-mapped site identity alongside one benjamini-hochberg-corrected contrast"
        ),
    )


class PtmProteinDifferentialReference(JsonModel):
    """Protein-level differential reference used for optional PTM site correction."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    log2_fold_change: float
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)


def _resolve_selected_contrast(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None,
    condition_b: str | None,
) -> tuple[str, str]:
    conditions = tuple(sorted({entry.condition for entry in design_entries if entry.condition}))
    if condition_a is not None and condition_b is not None:
        return condition_a, condition_b
    if len(conditions) != 2:
        raise ValueError(
            "ptm differential analysis requires exactly two conditions or explicit condition names"
        )
    return conditions


def _negative_log10(value: float) -> float:
    bounded = max(value, 1e-300)
    return -math.log10(bounded)


def render_ptm_site_differential_tsv(report: PtmSiteDifferentialReport) -> str:
    """Render one PTM site differential report as a stable TSV ledger."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "site_key",
            "protein_ref",
            "residue",
            "position",
            "modification_name",
            "ambiguous",
            "shared_peptide",
            "localized_peptides",
            "condition_a",
            "condition_b",
            "observations_a",
            "observations_b",
            "complete_pair_count",
            "mean_log2_abundance_a",
            "mean_log2_abundance_b",
            "log2_fold_change",
            "protein_log2_fold_change",
            "corrected_log2_fold_change",
            "p_value",
            "adjusted_p_value",
            "standard_error",
            "confidence_interval_low",
            "confidence_interval_high",
            "effect_size_cohens_d",
            "protein_correction_status",
            "uncertainty_note",
        )
    )
    for entry in sort_rows_by_fields(report.entries, "site_key"):
        writer.writerow(
            (
                entry.site_key,
                entry.protein_ref,
                entry.residue,
                entry.position,
                entry.modification_name,
                str(entry.ambiguous).lower(),
                str(entry.shared_peptide).lower(),
                ";".join(sort_strings(entry.localized_peptides)),
                entry.condition_a,
                entry.condition_b,
                entry.observations_a,
                entry.observations_b,
                entry.complete_pair_count,
                f"{entry.mean_log2_abundance_a:g}",
                f"{entry.mean_log2_abundance_b:g}",
                f"{entry.log2_fold_change:g}",
                "" if entry.protein_log2_fold_change is None else f"{entry.protein_log2_fold_change:g}",
                ""
                if entry.corrected_log2_fold_change is None
                else f"{entry.corrected_log2_fold_change:g}",
                f"{entry.p_value:g}",
                "" if entry.adjusted_p_value is None else f"{entry.adjusted_p_value:g}",
                "" if entry.standard_error is None else f"{entry.standard_error:g}",
                ""
                if entry.confidence_interval_low is None
                else f"{entry.confidence_interval_low:g}",
                ""
                if entry.confidence_interval_high is None
                else f"{entry.confidence_interval_high:g}",
                ""
                if entry.effect_size_cohens_d is None
                else f"{entry.effect_size_cohens_d:g}",
                entry.protein_correction_status,
                entry.uncertainty_note or "",
            )
        )
    return handle.getvalue()


def export_ptm_site_differential_tsv(
    report: PtmSiteDifferentialReport,
    path: Path,
) -> None:
    """Write one PTM site differential report to a stable TSV artifact."""

    path.write_text(render_ptm_site_differential_tsv(report), encoding="utf-8")


def render_ptm_site_differential_broken_pairs_tsv(
    report: PtmSiteDifferentialReport,
) -> str:
    """Render one PTM paired-design broken-pair ledger as a stable TSV artifact."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "condition_a",
            "condition_b",
            "pair_id",
            "sample_ids_a",
            "sample_ids_b",
            "reason_code",
            "detail",
        )
    )
    for entry in report.broken_pairs:
        writer.writerow(
            (
                entry.condition_a,
                entry.condition_b,
                entry.pair_id or "",
                ";".join(entry.sample_ids_a),
                ";".join(entry.sample_ids_b),
                entry.reason_code,
                entry.detail,
            )
        )
    return handle.getvalue()


def export_ptm_site_differential_broken_pairs_tsv(
    report: PtmSiteDifferentialReport,
    path: Path,
) -> None:
    """Write one PTM paired-design broken-pair ledger to a stable TSV artifact."""

    path.write_text(
        render_ptm_site_differential_broken_pairs_tsv(report),
        encoding="utf-8",
    )


def render_ptm_differential_volcano_tsv(plot: PtmDifferentialVolcanoPlot) -> str:
    """Render one PTM volcano payload as a stable TSV ledger."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "site_key",
            "protein_ref",
            "residue",
            "position",
            "modification_name",
            "raw_log2_fold_change",
            "corrected_log2_fold_change",
            "plotted_log2_fold_change",
            "raw_p_value",
            "adjusted_p_value",
            "negative_log10_adjusted_p_value",
            "highlighted",
            "protein_correction_status",
        )
    )
    for point in sort_rows_by_fields(plot.points, "site_key"):
        writer.writerow(
            (
                point.site_key,
                point.protein_ref,
                point.residue,
                point.position,
                point.modification_name,
                f"{point.raw_log2_fold_change:g}",
                ""
                if point.corrected_log2_fold_change is None
                else f"{point.corrected_log2_fold_change:g}",
                f"{point.plotted_log2_fold_change:g}",
                f"{point.raw_p_value:g}",
                f"{point.adjusted_p_value:g}",
                f"{point.negative_log10_adjusted_p_value:g}",
                str(point.highlighted).lower(),
                point.protein_correction_status,
            )
        )
    return handle.getvalue()


def export_ptm_differential_volcano_tsv(
    plot: PtmDifferentialVolcanoPlot,
    path: Path,
) -> None:
    """Write one PTM differential volcano payload to a stable TSV artifact."""

    path.write_text(render_ptm_differential_volcano_tsv(plot), encoding="utf-8")


def _build_protein_differential_lookup(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    normalization_method: NormalizationMethod,
    condition_a: str,
    condition_b: str,
    feature_records: tuple[Ms1FeatureRecord, ...] | None,
    protein_correction_mode: PtmProteinCorrectionMode,
    pairing_field: str | None,
) -> dict[str, PtmProteinDifferentialReference]:
    if protein_correction_mode is PtmProteinCorrectionMode.NONE:
        return {}
    if feature_records is None:
        raise ValueError(
            "protein-level correction requires feature records so unmodified protein evidence can be modeled"
        )
    unmodified_records = tuple(
        record
        for record in feature_records
        if record.peptide == parse_modified_peptide(record.peptide).sequence
        and len(record.protein_refs) == 1
    )
    if not unmodified_records:
        return {}
    protein_table = build_label_free_intensity_table(
        unmodified_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    normalized_protein_table = (
        protein_table
        if len(protein_table.entity_ids) <= 1
        else normalize_label_free_table(
            protein_table,
            method=normalization_method,
        )
    )
    paired_policy = (
        PairedDifferentialPolicy(pair_id_field=pairing_field)
        if pairing_field is not None
        else None
    )
    protein_differential = build_differential_abundance_report(
        normalized_protein_table,
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
        test_type=(
            DifferentialAbundanceTestType.PAIRED_T_TEST
            if paired_policy is not None
            else DifferentialAbundanceTestType.WELCH_T_TEST
        ),
        paired_policy=paired_policy,
    )
    return {
        entry.entity_id: PtmProteinDifferentialReference(
            protein_ref=entry.entity_id,
            log2_fold_change=entry.log2_fold_change,
            adjusted_p_value=entry.adjusted_p_value,
        )
        for entry in protein_differential.entries
    }
