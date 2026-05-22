# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned labeled-proteomics report bundles over TMT and SILAC workflows."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.isotope_labeling import TmtValidationReport, build_tmt_validation_report
from bijux_proteomics.multiplex import (
    TmtNormalizationMethod,
    TmtNormalizationPolicy,
    TmtNormalizationReport,
    TmtRatioReport,
    TmtReporterChannelColumn,
    TmtReporterColumnMapping,
    TmtReporterMatrixReport,
    TmtSearchResultSourceKind,
    build_tmt_normalization_report,
    build_tmt_ratio_report,
    build_tmt_reporter_feature_bundle,
    build_tmt_reporter_matrix_report,
    parse_tmt_reporter_table,
)
from bijux_proteomics.quantification import NormalizationMethod
from bijux_proteomics.workflow.label_based_differential_analysis import (
    LabelBasedDifferentialAnalysisReport,
    LabelBasedDifferentialSourceKind,
    build_tmt_differential_analysis_report,
)
from bijux_proteomics_foundation import JsonModel


class LabelBasedReportSampleQcEntry(JsonModel):
    """One labeled sample-QC row carried by the owned reporting surface."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class LabelBasedReportSummary(JsonModel):
    """Compact summary over one labeled experiment report bundle."""

    model_config = ConfigDict(extra="forbid")

    source_kind: LabelBasedDifferentialSourceKind
    sample_count: int = Field(..., ge=0)
    quality_entry_count: int = Field(..., ge=0)
    protein_ratio_count: int = Field(..., ge=0)
    differential_result_count: int = Field(..., ge=0)
    sample_qc_entry_count: int = Field(..., ge=0)


class LabelBasedReportBundle(JsonModel):
    """Owned labeled experiment report bundle over TMT or SILAC workflows."""

    model_config = ConfigDict(extra="forbid")

    source_kind: LabelBasedDifferentialSourceKind
    source_name: str = Field(..., min_length=1)
    tmt_matrix_report: TmtReporterMatrixReport | None = None
    tmt_normalization_report: TmtNormalizationReport | None = None
    tmt_ratio_report: TmtRatioReport | None = None
    tmt_validation_report: TmtValidationReport | None = None
    differential_analysis_report: LabelBasedDifferentialAnalysisReport
    sample_qc_entries: tuple[LabelBasedReportSampleQcEntry, ...] = Field(
        default_factory=tuple
    )
    summary: LabelBasedReportSummary
    note: str = Field(..., min_length=1)


def build_tmt_label_based_report_bundle(
    result_tsv_path,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    control_channel: str,
    source_kind: TmtSearchResultSourceKind = TmtSearchResultSourceKind.MAXQUANT,
    mapping: TmtReporterColumnMapping | None = None,
    channel_columns: tuple[TmtReporterChannelColumn, ...] = (),
    channel_normalization_method: TmtNormalizationMethod = TmtNormalizationMethod.MEDIAN,
    differential_normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
) -> LabelBasedReportBundle:
    """Build one owned labeled report bundle over governed TMT workflows."""

    import_report = parse_tmt_reporter_table(
        result_tsv_path,
        source_kind=source_kind,
        mapping=mapping,
        channel_columns=channel_columns,
    )
    feature_bundle = build_tmt_reporter_feature_bundle(
        import_report,
        design_entries=design_entries,
    )
    matrix_report = build_tmt_reporter_matrix_report(feature_bundle)
    normalization_policy = TmtNormalizationPolicy(method=channel_normalization_method)
    normalization_report = build_tmt_normalization_report(
        feature_bundle,
        policy=normalization_policy,
    )
    ratio_report = build_tmt_ratio_report(
        feature_bundle,
        control_channel=control_channel,
        normalization_policy=normalization_policy,
    )
    validation_report = build_tmt_validation_report(feature_bundle)
    differential_report = build_tmt_differential_analysis_report(
        result_tsv_path,
        design_entries,
        source_kind=source_kind,
        mapping=mapping,
        channel_columns=channel_columns,
        normalization_method=differential_normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
        batch_field=batch_field,
        covariate_fields=tuple(dict.fromkeys(covariate_fields)),
        pairing_field=pairing_field,
    )
    return LabelBasedReportBundle(
        source_kind=LabelBasedDifferentialSourceKind.TMT,
        source_name=source_kind.value,
        tmt_matrix_report=matrix_report,
        tmt_normalization_report=normalization_report,
        tmt_ratio_report=ratio_report,
        tmt_validation_report=validation_report,
        differential_analysis_report=differential_report,
        summary=LabelBasedReportSummary(
            source_kind=LabelBasedDifferentialSourceKind.TMT,
            sample_count=matrix_report.protein_matrix.summary.sample_count,
            quality_entry_count=len(validation_report.channel_entries),
            protein_ratio_count=len(ratio_report.protein_ratios),
            differential_result_count=_differential_result_count(differential_report),
            sample_qc_entry_count=0,
        ),
        note=(
            "labeled reporting assembles governed tmt channel totals, normalization review, protein ratios, and differential results into one owned bundle"
        ),
    )


def _differential_result_count(report: LabelBasedDifferentialAnalysisReport) -> int:
    if report.differential_abundance_report is not None:
        return len(report.differential_abundance_report.entries)
    if report.differential_abundance_multi_condition_report is not None:
        return sum(
            len(contrast.report.entries)
            for contrast in report.differential_abundance_multi_condition_report.contrasts
        )
    return 0
