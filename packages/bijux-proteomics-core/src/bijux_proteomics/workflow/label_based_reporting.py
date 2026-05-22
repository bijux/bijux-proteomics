# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned labeled-proteomics report bundles over TMT and SILAC workflows."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.isotope_labeling import (
    SilacColumnMapping,
    SilacQuantificationPolicy,
    SilacRatioReport,
    SilacValidationPolicy,
    SilacValidationReport,
    TmtValidationReport,
    build_silac_ratio_report,
    build_silac_validation_report,
    build_tmt_validation_report,
    parse_silac_feature_table,
)
from bijux_proteomics.multiplex import (
    TmtDistributionStage,
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
    build_silac_differential_analysis_report,
    build_tmt_differential_analysis_report,
)
from bijux_proteomics_foundation import JsonModel


class LabelBasedReportSampleQcEntry(JsonModel):
    """One labeled sample-QC row carried by the owned reporting surface."""

    model_config = ConfigDict(extra="forbid")

    source_kind: LabelBasedDifferentialSourceKind
    sample_id: str = Field(..., min_length=1)
    condition: str | None = None
    sample_role: str | None = None
    multiplex_group: str | None = None
    assay_axis: str = Field(..., min_length=1)
    total_signal: float = Field(..., ge=0.0)
    before_balance_ratio: float | None = Field(default=None, ge=0.0)
    after_balance_ratio: float | None = Field(default=None, ge=0.0)
    missing_measurement_count: int = Field(..., ge=0)
    weak_measurement_count: int = Field(..., ge=0)
    abnormal_distribution_count: int = Field(..., ge=0)
    flagged: bool
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
    silac_ratio_report: SilacRatioReport | None = None
    silac_validation_report: SilacValidationReport | None = None
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
    sample_qc_entries = _build_tmt_sample_qc_entries(
        validation_report,
        normalization_report=normalization_report,
    )
    return LabelBasedReportBundle(
        source_kind=LabelBasedDifferentialSourceKind.TMT,
        source_name=source_kind.value,
        tmt_matrix_report=matrix_report,
        tmt_normalization_report=normalization_report,
        tmt_ratio_report=ratio_report,
        tmt_validation_report=validation_report,
        differential_analysis_report=differential_report,
        sample_qc_entries=sample_qc_entries,
        summary=LabelBasedReportSummary(
            source_kind=LabelBasedDifferentialSourceKind.TMT,
            sample_count=matrix_report.protein_matrix.summary.sample_count,
            quality_entry_count=len(validation_report.channel_entries),
            protein_ratio_count=len(ratio_report.protein_ratios),
            differential_result_count=_differential_result_count(differential_report),
            sample_qc_entry_count=len(sample_qc_entries),
        ),
        note=(
            "labeled reporting assembles governed tmt channel totals, normalization review, protein ratios, differential results, and sample qc into one owned bundle"
        ),
    )


def build_silac_label_based_report_bundle(
    feature_tsv_path,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    mapping: SilacColumnMapping | None = None,
    quantification_policy: SilacQuantificationPolicy | None = None,
    validation_policy: SilacValidationPolicy | None = None,
    differential_normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
) -> LabelBasedReportBundle:
    """Build one owned labeled report bundle over governed SILAC workflows."""

    import_report = parse_silac_feature_table(
        feature_tsv_path,
        mapping=mapping,
    )
    ratio_report = build_silac_ratio_report(
        import_report,
        policy=quantification_policy,
    )
    validation_report = build_silac_validation_report(
        import_report,
        policy=validation_policy,
    )
    differential_report = build_silac_differential_analysis_report(
        feature_tsv_path,
        design_entries,
        mapping=mapping,
        quantification_policy=quantification_policy,
        normalization_method=differential_normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
        batch_field=batch_field,
        covariate_fields=tuple(dict.fromkeys(covariate_fields)),
        pairing_field=pairing_field,
    )
    sample_qc_entries = _build_silac_sample_qc_entries(
        validation_report,
        differential_report=differential_report,
        design_entries=design_entries,
    )
    return LabelBasedReportBundle(
        source_kind=LabelBasedDifferentialSourceKind.SILAC,
        source_name="silac",
        silac_ratio_report=ratio_report,
        silac_validation_report=validation_report,
        differential_analysis_report=differential_report,
        sample_qc_entries=sample_qc_entries,
        summary=LabelBasedReportSummary(
            source_kind=LabelBasedDifferentialSourceKind.SILAC,
            sample_count=ratio_report.summary.sample_count,
            quality_entry_count=len(validation_report.label_entries),
            protein_ratio_count=len(ratio_report.protein_ratios),
            differential_result_count=_differential_result_count(differential_report),
            sample_qc_entry_count=len(sample_qc_entries),
        ),
        note=(
            "labeled reporting assembles governed silac protein ratios, label validation, differential results, and sample qc into one owned bundle"
        ),
    )


def _build_tmt_sample_qc_entries(
    validation_report: TmtValidationReport,
    *,
    normalization_report: TmtNormalizationReport,
) -> tuple[LabelBasedReportSampleQcEntry, ...]:
    after_distribution_by_key = {
        (entry.multiplex_group, entry.multiplex_channel, entry.sample_id): entry
        for entry in normalization_report.channel_distributions
        if entry.stage is TmtDistributionStage.AFTER
    }
    before_distribution_by_key = {
        (entry.multiplex_group, entry.multiplex_channel, entry.sample_id): entry
        for entry in validation_report.distribution_entries
    }
    weak_counts_by_key: dict[tuple[str, str, str | None], int] = {}
    for entry in validation_report.weak_evidence:
        key = (entry.multiplex_group, entry.multiplex_channel, entry.sample_id)
        weak_counts_by_key[key] = weak_counts_by_key.get(key, 0) + 1
    rows: list[LabelBasedReportSampleQcEntry] = []
    for entry in validation_report.channel_entries:
        if entry.sample_id is None:
            continue
        key = (entry.multiplex_group, entry.multiplex_channel, entry.sample_id)
        before_distribution = before_distribution_by_key.get(key)
        after_distribution = after_distribution_by_key.get(key)
        weak_measurement_count = weak_counts_by_key.get(key, 0)
        abnormal_distribution_count = int(
            before_distribution is not None and before_distribution.abnormal_distribution
        ) + int(after_distribution is not None and after_distribution.flagged)
        notes: list[str] = []
        if not entry.present:
            notes.append("expected multiplex channel is missing or empty")
        if before_distribution is not None and before_distribution.abnormal_distribution:
            notes.append("channel total intensity falls outside the study-wide same-channel envelope")
        if after_distribution is not None and after_distribution.flagged:
            notes.append("normalized channel remains imbalanced within the multiplex group")
        if weak_measurement_count > 0:
            notes.append("weak channel evidence is present")
        rows.append(
            LabelBasedReportSampleQcEntry(
                source_kind=LabelBasedDifferentialSourceKind.TMT,
                sample_id=entry.sample_id,
                condition=entry.condition,
                sample_role=(
                    None if entry.channel_role is None else entry.channel_role.value
                ),
                multiplex_group=entry.multiplex_group,
                assay_axis=entry.multiplex_channel,
                total_signal=entry.total_intensity,
                before_balance_ratio=(
                    None
                    if before_distribution is None
                    else before_distribution.ratio_to_channel_median
                ),
                after_balance_ratio=(
                    None
                    if after_distribution is None
                    else after_distribution.ratio_to_group_median
                ),
                missing_measurement_count=entry.missing_row_count,
                weak_measurement_count=weak_measurement_count,
                abnormal_distribution_count=abnormal_distribution_count,
                flagged=bool(notes),
                note=(
                    "; ".join(notes)
                    if notes
                    else "channel quality, normalization balance, and weak-evidence review are all within the governed tmt envelope"
                ),
            )
        )
    return tuple(rows)


def _build_silac_sample_qc_entries(
    validation_report: SilacValidationReport,
    *,
    differential_report: LabelBasedDifferentialAnalysisReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[LabelBasedReportSampleQcEntry, ...]:
    design_by_sample = {entry.sample_id: entry for entry in design_entries}
    label_entries_by_sample: dict[str, list] = {}
    for entry in validation_report.label_entries:
        label_entries_by_sample.setdefault(entry.sample_id, []).append(entry)
    abnormal_distribution_count_by_sample: dict[str, int] = {}
    for entry in validation_report.distribution_entries:
        if entry.abnormal_distribution:
            abnormal_distribution_count_by_sample[entry.sample_id] = (
                abnormal_distribution_count_by_sample.get(entry.sample_id, 0) + 1
            )
    weak_count_by_sample: dict[str, int] = {}
    for entry in validation_report.weak_evidence:
        weak_count_by_sample[entry.sample_id] = (
            weak_count_by_sample.get(entry.sample_id, 0) + 1
        )
    balance_by_sample_stage = {
        (entry.sample_id, entry.stage.lower()): _ratio_or_none(
            entry.total_abundance,
            entry.median_abundance,
        )
        for entry in differential_report.normalization_balance_plot.points
    }
    rows: list[LabelBasedReportSampleQcEntry] = []
    for sample_id in sorted(label_entries_by_sample):
        label_entries = label_entries_by_sample[sample_id]
        design_entry = design_by_sample.get(sample_id)
        missing_measurement_count = sum(
            entry.missing_group_count for entry in label_entries
        )
        weak_measurement_count = weak_count_by_sample.get(sample_id, 0)
        abnormal_distribution_count = abnormal_distribution_count_by_sample.get(
            sample_id,
            0,
        )
        notes: list[str] = []
        if missing_measurement_count > 0:
            notes.append("one or more expected silac label groups are missing")
        if abnormal_distribution_count > 0:
            notes.append("label-intensity distribution falls outside the governed sample envelope")
        if weak_measurement_count > 0:
            notes.append("weak label evidence is present")
        rows.append(
            LabelBasedReportSampleQcEntry(
                source_kind=LabelBasedDifferentialSourceKind.SILAC,
                sample_id=sample_id,
                condition=None if design_entry is None else design_entry.condition,
                sample_role=(
                    None
                    if design_entry is None or design_entry.sample_role is None
                    else design_entry.sample_role.value
                ),
                assay_axis="silac",
                total_signal=sum(entry.total_intensity for entry in label_entries),
                before_balance_ratio=balance_by_sample_stage.get((sample_id, "before")),
                after_balance_ratio=balance_by_sample_stage.get((sample_id, "after")),
                missing_measurement_count=missing_measurement_count,
                weak_measurement_count=weak_measurement_count,
                abnormal_distribution_count=abnormal_distribution_count,
                flagged=bool(notes),
                note=(
                    "; ".join(notes)
                    if notes
                    else "label presence, intensity distribution, and ratio balance are all within the governed silac envelope"
                ),
            )
        )
    return tuple(rows)


def _ratio_or_none(numerator: float, denominator: float) -> float | None:
    if denominator <= 0.0:
        return None
    return float(numerator) / float(denominator)


def _differential_result_count(report: LabelBasedDifferentialAnalysisReport) -> int:
    if report.differential_abundance_report is not None:
        return len(report.differential_abundance_report.entries)
    if report.differential_abundance_multi_condition_report is not None:
        return sum(
            len(contrast.report.entries)
            for contrast in report.differential_abundance_multi_condition_report.contrasts
        )
    return 0
