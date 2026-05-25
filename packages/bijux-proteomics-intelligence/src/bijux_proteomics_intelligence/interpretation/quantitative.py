# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Quantitative missingness, outlier, and QC integration owners."""

from __future__ import annotations

from collections import Counter, defaultdict
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    LabelFreeQuantTable,
    MissingValueKind,
    ReplicateCorrelationReport,
)
from bijux_proteomics.lab.qc import (
    InstrumentBatchQcReport,
    QcRunAssessmentReport,
)
from bijux_proteomics_foundation import JsonModel


class MissingnessPatternLabel(StrEnum):
    """Advisory pattern labels for missing-value structure."""

    MOSTLY_OBSERVED = "mostly_observed"
    CONDITION_LINKED = "condition_linked_missingness"
    MNAR_LIKE_LOW_SIGNAL = "mnar_like_low_signal"
    FILTER_DOMINATED = "filter_dominated"
    MAR_LIKE = "mar_like_random"
    MIXED = "mixed"


class OutlierInterpretationClass(StrEnum):
    """Classification of whether an outlier looks technical or biological."""

    TECHNICAL_ANOMALY = "technical_anomaly"
    PLAUSIBLE_BIOLOGICAL_EFFECT = "plausible_biological_effect"
    MIXED_SIGNAL = "mixed_signal"


class MissingnessPatternEntry(JsonModel):
    """Pattern summary for one quantified entity."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    label: MissingnessPatternLabel
    observed_count: int = Field(..., ge=0)
    missing_count: int = Field(..., ge=0)
    condition_missing_counts: dict[str, int] = Field(default_factory=dict)
    note: str = Field(..., min_length=1)


class MissingnessPatternAnalysis(JsonModel):
    """Advisory classification of missingness behavior."""

    model_config = ConfigDict(extra="forbid")

    entity_level: str = Field(..., min_length=1)
    overall_label: MissingnessPatternLabel
    entries: tuple[MissingnessPatternEntry, ...] = Field(default_factory=tuple)
    interpretation_summary: str = Field(..., min_length=1)


class OutlierSampleExplanation(JsonModel):
    """Explanation for a sample or run flagged as an outlier."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    batch_id: str | None = None
    classification: OutlierInterpretationClass
    reasons: tuple[str, ...] = Field(default_factory=tuple)
    technical_reasons: tuple[str, ...] = Field(default_factory=tuple)
    biological_reasons: tuple[str, ...] = Field(default_factory=tuple)
    supporting_metrics: dict[str, float] = Field(default_factory=dict)
    recommended_follow_up: str = Field(..., min_length=1)
    interpretation_summary: str = Field(..., min_length=1)


class QuantQcEvidenceIntegrationReport(JsonModel):
    """Joint missingness, outlier, and QC interpretation over one quant surface."""

    model_config = ConfigDict(extra="forbid")

    entity_level: str = Field(..., min_length=1)
    missingness: MissingnessPatternAnalysis
    outliers: tuple[OutlierSampleExplanation, ...] = Field(default_factory=tuple)
    blocked_run_ids: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


def analyze_missingness_patterns(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> MissingnessPatternAnalysis:
    """Classify missingness patterns from a quantification matrix and design."""
    condition_lookup = {entry.sample_id: entry.condition for entry in design_entries}
    entity_values: dict[str, list[tuple[str, MissingValueKind, float | None]]] = (
        defaultdict(list)
    )
    observed_values: list[float] = []
    for value in table.values:
        entity_values[value.entity_id].append(
            (value.sample_id, value.missing_value_kind, value.abundance)
        )
        if value.abundance is not None:
            observed_values.append(value.abundance)
    abundance_median = (
        sorted(observed_values)[len(observed_values) // 2] if observed_values else 0.0
    )
    entries: list[MissingnessPatternEntry] = []
    label_counts: Counter[MissingnessPatternLabel] = Counter()
    for entity_id, values in sorted(entity_values.items()):
        observed_count = sum(
            1
            for _, kind, _ in values
            if kind in {MissingValueKind.OBSERVED, MissingValueKind.ZERO}
        )
        missing_count = len(values) - observed_count
        condition_missing_counts: Counter[str] = Counter()
        filtered_count = 0
        observed_abundances = [
            abundance
            for _, kind, abundance in values
            if kind is MissingValueKind.OBSERVED and abundance is not None
        ]
        for sample_id, kind, _ in values:
            if kind in {MissingValueKind.NOT_OBSERVED, MissingValueKind.FILTERED}:
                condition_missing_counts[
                    condition_lookup.get(sample_id, sample_id)
                ] += 1
            if kind is MissingValueKind.FILTERED:
                filtered_count += 1
        if missing_count == 0:
            label = MissingnessPatternLabel.MOSTLY_OBSERVED
            note = "entity is observed across all samples"
        elif filtered_count == missing_count and missing_count > 0:
            label = MissingnessPatternLabel.FILTER_DOMINATED
            note = "missingness is dominated by feature-level filtering"
        elif (
            len([count for count in condition_missing_counts.values() if count > 0])
            == 1
        ):
            label = MissingnessPatternLabel.CONDITION_LINKED
            note = "missingness is concentrated in one condition"
        elif observed_abundances and max(observed_abundances) <= abundance_median:
            label = MissingnessPatternLabel.MNAR_LIKE_LOW_SIGNAL
            note = "missingness follows low-abundance behavior and looks MNAR-like"
        elif missing_count > 0:
            label = MissingnessPatternLabel.MAR_LIKE
            note = "missingness is spread across conditions without a dominant low-signal pattern"
        else:
            label = MissingnessPatternLabel.MIXED
            note = "mixed missingness pattern"
        label_counts[label] += 1
        entries.append(
            MissingnessPatternEntry(
                entity_id=entity_id,
                label=label,
                observed_count=observed_count,
                missing_count=missing_count,
                condition_missing_counts=dict(condition_missing_counts),
                note=note,
            )
        )
    if not label_counts:
        overall = MissingnessPatternLabel.MIXED
    else:
        non_observed_counts = {
            label: count
            for label, count in label_counts.items()
            if label is not MissingnessPatternLabel.MOSTLY_OBSERVED
        }
        if not non_observed_counts:
            overall = MissingnessPatternLabel.MOSTLY_OBSERVED
        elif label_counts[MissingnessPatternLabel.MOSTLY_OBSERVED] > 0:
            overall = MissingnessPatternLabel.MIXED
        else:
            overall = max(
                non_observed_counts.items(),
                key=lambda item: (item[1], item[0].value),
            )[0]
    return MissingnessPatternAnalysis(
        entity_level=table.entity_level.value,
        overall_label=overall,
        entries=tuple(entries),
        interpretation_summary=f"{label_counts[overall]} entities primarily show {overall.value}.",
    )


def explain_outlier_samples(
    batch_report: InstrumentBatchQcReport,
    replicate_report: ReplicateCorrelationReport,
    *,
    low_correlation_threshold: float = 0.85,
) -> tuple[OutlierSampleExplanation, ...]:
    """Explain outlier samples from batch QC and replicate-correlation signals."""
    within_condition_correlations: dict[str, list[float]] = defaultdict(list)
    between_condition_correlations: dict[str, list[float]] = defaultdict(list)
    for entry in replicate_report.entries:
        target_map = (
            within_condition_correlations
            if entry.condition_a == entry.condition_b
            else between_condition_correlations
        )
        target_map[entry.sample_a].append(entry.correlation)
        target_map[entry.sample_b].append(entry.correlation)
    explanations: list[OutlierSampleExplanation] = []
    technical_reason_codes = {
        "low_identification_rate",
        "high_mass_error",
        "retention_time_shift",
        "low_replicate_correlation",
    }
    for run in batch_report.runs:
        reasons = list(run.outlier_reasons)
        supporting_metrics = {
            "spectrum_count": float(run.spectrum_count),
            "identification_rate": run.identification_rate,
        }
        if run.median_abs_mass_error_ppm is not None:
            supporting_metrics["median_abs_mass_error_ppm"] = (
                run.median_abs_mass_error_ppm
            )
        sample_id = run.sample_id or run.run_id
        within_condition = within_condition_correlations.get(sample_id, [])
        between_condition = between_condition_correlations.get(sample_id, [])
        if within_condition and min(within_condition) < low_correlation_threshold:
            reasons.append("low_replicate_correlation")
            supporting_metrics["min_replicate_correlation"] = min(within_condition)
        technical_reasons = {
            reason for reason in reasons if reason in technical_reason_codes
        }
        biological_reasons: set[str] = set()
        batch_median_abs_mass_error_ppm = batch_report.median_abs_mass_error_ppm
        if (
            not technical_reasons
            and between_condition
            and min(between_condition) < low_correlation_threshold
            and run.run_id in batch_report.outlier_run_ids
            and run.identification_rate >= batch_report.median_identification_rate
            and (
                run.median_abs_mass_error_ppm is None
                or batch_median_abs_mass_error_ppm is None
                or run.median_abs_mass_error_ppm <= batch_median_abs_mass_error_ppm
            )
        ):
            biological_reasons.add("condition_separation_without_qc_failure")
            supporting_metrics["min_between_condition_correlation"] = min(
                between_condition
            )
        if reasons:
            if technical_reasons and biological_reasons:
                classification = OutlierInterpretationClass.MIXED_SIGNAL
                follow_up = "repeat QC checks and verify whether the condition shift persists in orthogonal assays"
            elif technical_reasons:
                classification = OutlierInterpretationClass.TECHNICAL_ANOMALY
                follow_up = "treat the sample as a technical anomaly until acquisition or preparation issues are resolved"
            else:
                classification = OutlierInterpretationClass.PLAUSIBLE_BIOLOGICAL_EFFECT
                follow_up = "preserve the sample for biological follow-up and confirm the shift with orthogonal evidence"
            explanations.append(
                OutlierSampleExplanation(
                    sample_id=sample_id,
                    batch_id=run.batch,
                    classification=classification,
                    reasons=tuple(dict.fromkeys(reasons)),
                    technical_reasons=tuple(sorted(technical_reasons)),
                    biological_reasons=tuple(sorted(biological_reasons)),
                    supporting_metrics=supporting_metrics,
                    recommended_follow_up=follow_up,
                    interpretation_summary=(
                        f"{sample_id} is classified as {classification.value} because "
                        + ", ".join(dict.fromkeys(reasons or biological_reasons))
                    ),
                )
            )
        elif biological_reasons:
            explanations.append(
                OutlierSampleExplanation(
                    sample_id=sample_id,
                    batch_id=run.batch,
                    classification=OutlierInterpretationClass.PLAUSIBLE_BIOLOGICAL_EFFECT,
                    reasons=tuple(sorted(biological_reasons)),
                    technical_reasons=(),
                    biological_reasons=tuple(sorted(biological_reasons)),
                    supporting_metrics=supporting_metrics,
                    recommended_follow_up=(
                        "preserve the sample for biological follow-up and confirm the shift with orthogonal evidence"
                    ),
                    interpretation_summary=(
                        f"{sample_id} separates by condition without a matching QC failure."
                    ),
                )
            )
    return tuple(explanations)


def integrate_quant_qc_evidence(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    batch_report: InstrumentBatchQcReport,
    replicate_report: ReplicateCorrelationReport,
    *,
    run_assessments: tuple[QcRunAssessmentReport, ...] = (),
) -> QuantQcEvidenceIntegrationReport:
    """Integrate quant missingness and QC outlier evidence into one report."""
    missingness = analyze_missingness_patterns(table, design_entries)
    outliers = explain_outlier_samples(batch_report, replicate_report)
    blocked_run_ids = tuple(
        sorted(
            assessment.run_id for assessment in run_assessments if assessment.blocked
        )
    )
    notes: list[str] = []
    if outliers:
        technical_count = sum(
            1
            for outlier in outliers
            if outlier.classification is OutlierInterpretationClass.TECHNICAL_ANOMALY
        )
        biological_count = sum(
            1
            for outlier in outliers
            if outlier.classification
            is OutlierInterpretationClass.PLAUSIBLE_BIOLOGICAL_EFFECT
        )
        notes.append(f"{len(outliers)} samples show QC-supported outlier behavior")
        if technical_count:
            notes.append(f"{technical_count} outliers look technical")
        if biological_count:
            notes.append(f"{biological_count} outliers may reflect biology")
    if missingness.overall_label is not MissingnessPatternLabel.MOSTLY_OBSERVED:
        notes.append(
            f"missingness remains {missingness.overall_label.value} at the {table.entity_level.value} level"
        )
    if blocked_run_ids:
        notes.append("blocked QC runs: " + ", ".join(blocked_run_ids))
    if not notes:
        notes.append(
            "quant and QC evidence are jointly consistent for this analysis surface"
        )
    return QuantQcEvidenceIntegrationReport(
        entity_level=table.entity_level.value,
        missingness=missingness,
        outliers=outliers,
        blocked_run_ids=blocked_run_ids,
        notes=tuple(notes),
    )
