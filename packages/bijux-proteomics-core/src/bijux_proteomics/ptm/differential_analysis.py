# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned PTM site differential-analysis surfaces."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.ptm.site_quantification import (
    PtmSiteQuantRow,
    PtmSiteQuantificationReport,
)
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
    NormalizationComparisonReport,
    NormalizationMethod,
    QuantDesignMatrixReport,
    QuantDesignModelFitReport,
    QuantEntityLevel,
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
    mean_log2_abundance_a: float
    mean_log2_abundance_b: float
    log2_fold_change: float
    p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    standard_error: float | None = Field(default=None, ge=0.0)
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    effect_size_cohens_d: float | None = None
    uncertainty_note: str | None = None


class PtmSiteDifferentialReport(JsonModel):
    """Stable PTM site differential report over one explicit contrast."""

    model_config = ConfigDict(extra="forbid")

    normalization_method: NormalizationMethod
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    entries: tuple[PtmSiteDifferentialEntry, ...] = Field(default_factory=tuple)
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
    differential_report: PtmSiteDifferentialReport
    note: str = Field(..., min_length=1)


def build_ptm_differential_analysis_report(
    site_quantification: PtmSiteQuantificationReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
) -> PtmDifferentialAnalysisReport:
    """Normalize PTM site intensities and test one explicit two-condition contrast."""

    site_quant_table = _build_label_free_table_from_site_quantification(site_quantification)
    normalized_table = normalize_label_free_table(
        site_quant_table,
        method=normalization_method,
    )
    normalization_comparison = build_normalization_comparison_report(
        site_quant_table,
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
    resolved_condition_a, resolved_condition_b = _resolve_selected_contrast(
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    differential = apply_benjamini_hochberg(
        build_differential_abundance_report(
            normalized_table,
            design_entries,
            condition_a=resolved_condition_a,
            condition_b=resolved_condition_b,
        )
    )
    differential_report = _build_ptm_site_differential_report(
        differential,
        site_quantification.rows,
    )
    return PtmDifferentialAnalysisReport(
        site_quantification=site_quantification,
        site_quant_table=site_quant_table,
        normalized_site_quant_table=normalized_table,
        normalization_comparison=normalization_comparison,
        design_matrix=design_matrix,
        design_model_fit=design_model_fit,
        differential_report=differential_report,
        note=(
            "ptm differential analysis preserves one site-level quantification matrix, explicit design encoding, and benjamini-hochberg-corrected site testing"
        ),
    )


def _build_label_free_table_from_site_quantification(
    report: PtmSiteQuantificationReport,
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


def _build_ptm_site_differential_report(
    differential: DifferentialAbundanceReport,
    site_rows: tuple[PtmSiteQuantRow, ...],
) -> PtmSiteDifferentialReport:
    row_by_site = {row.site_key: row for row in site_rows}
    entries: list[PtmSiteDifferentialEntry] = []
    for entry in differential.entries:
        row = row_by_site[entry.entity_id]
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
                mean_log2_abundance_a=entry.mean_log2_abundance_a,
                mean_log2_abundance_b=entry.mean_log2_abundance_b,
                log2_fold_change=entry.log2_fold_change,
                p_value=entry.p_value,
                adjusted_p_value=entry.adjusted_p_value,
                standard_error=entry.standard_error,
                confidence_interval_low=entry.confidence_interval_low,
                confidence_interval_high=entry.confidence_interval_high,
                effect_size_cohens_d=entry.effect_size_cohens_d,
                uncertainty_note=entry.uncertainty_note,
            )
        )
    return PtmSiteDifferentialReport(
        normalization_method=differential.normalization_method,
        condition_a=differential.condition_a,
        condition_b=differential.condition_b,
        entries=tuple(entries),
        note=(
            "ptm site differential report preserves protein-mapped site identity alongside one benjamini-hochberg-corrected contrast"
        ),
    )


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
