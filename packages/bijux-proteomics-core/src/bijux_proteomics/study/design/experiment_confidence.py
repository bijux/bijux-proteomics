# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned experiment-level confidence scoring over study, QC, and final-result evidence."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.domain import ConfidenceTier
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import MissingnessConditionSummaryReport
from bijux_proteomics.quantification.power_estimation import PowerEstimationReport
from bijux_proteomics.study.design.design_validity import (
    ExperimentDesignValidityReport,
    build_experiment_design_validity_report,
)
from bijux_proteomics.study.design.experiment_design import (
    ExperimentDesign,
    coerce_experiment_design,
)
from bijux_proteomics.study.design.experiment_feasibility import (
    ExperimentFeasibilityReport,
    build_experiment_feasibility_report,
)
from bijux_proteomics.lab.protocol_consistency import (
    ProtocolConsistencyReport,
)
from bijux_proteomics.lab.qc import (
    LcmsRunQcReport,
    QcRunAssessmentReport,
    QcStatus,
)
from bijux_proteomics_foundation import JsonModel


class ExperimentConfidenceComponentKind(StrEnum):
    """Stable experiment-confidence component kinds."""

    METADATA_VALIDITY = "metadata_validity"
    RUN_QC = "run_qc"
    SAMPLE_BALANCE = "sample_balance"
    MISSINGNESS = "missingness"
    CONTAMINATION = "contamination"
    STATISTICAL_POWER = "statistical_power"
    EVIDENCE_CONSISTENCY = "evidence_consistency"


ExperimentConfidenceTier = ConfidenceTier


class ExperimentConfidenceComponent(JsonModel):
    """One decomposed experiment-confidence component with explicit reasons."""

    model_config = ConfigDict(extra="forbid")

    component: ExperimentConfidenceComponentKind
    score: float = Field(..., ge=0.0, le=1.0)
    tier: ExperimentConfidenceTier
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    message: str = Field(..., min_length=1)


class ExperimentConfidenceSummary(JsonModel):
    """Compact experiment-level confidence summary."""

    model_config = ConfigDict(extra="forbid")

    overall_score: float = Field(..., ge=0.0, le=1.0)
    overall_tier: ExperimentConfidenceTier
    component_count: int = Field(..., ge=0)
    low_confidence_component_count: int = Field(..., ge=0)
    metadata_issue_count: int = Field(..., ge=0)
    caution_run_count: int = Field(..., ge=0)
    failed_run_count: int = Field(..., ge=0)


class ExperimentConfidenceReport(JsonModel):
    """Owned experiment-confidence report with decomposed component reasons."""

    model_config = ConfigDict(extra="forbid")

    experiment_design: ExperimentDesign
    validity_report: ExperimentDesignValidityReport
    feasibility_report: ExperimentFeasibilityReport
    missingness_condition_summary_report: MissingnessConditionSummaryReport
    power_estimation_report: PowerEstimationReport
    protocol_consistency_report: ProtocolConsistencyReport | None = None
    components: tuple[ExperimentConfidenceComponent, ...] = Field(default_factory=tuple)
    summary: ExperimentConfidenceSummary
    note: str = Field(..., min_length=1)


def build_experiment_confidence_report(
    design: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    missingness_condition_summary_report: MissingnessConditionSummaryReport,
    power_estimation_report: PowerEstimationReport,
    validity_report: ExperimentDesignValidityReport | None = None,
    feasibility_report: ExperimentFeasibilityReport | None = None,
    run_qc_reports: tuple[LcmsRunQcReport, ...] = (),
    run_qc_assessments: tuple[QcRunAssessmentReport, ...] = (),
    protocol_consistency_report: ProtocolConsistencyReport | None = None,
    warning_card_count: int = 0,
    protein_card_count: int = 0,
) -> ExperimentConfidenceReport:
    """Score one experiment from metadata, QC, balance, missingness, power, and evidence consistency."""

    experiment_design = coerce_experiment_design(design)
    resolved_validity_report = validity_report or build_experiment_design_validity_report(
        experiment_design
    )
    resolved_feasibility_report = feasibility_report or build_experiment_feasibility_report(
        experiment_design
    )
    components = (
        _metadata_validity_component(
            resolved_validity_report,
            resolved_feasibility_report,
        ),
        _run_qc_component(run_qc_assessments),
        _sample_balance_component(resolved_feasibility_report),
        _missingness_component(missingness_condition_summary_report),
        _contamination_component(run_qc_reports),
        _statistical_power_component(power_estimation_report),
        _evidence_consistency_component(
            protocol_consistency_report=protocol_consistency_report,
            warning_card_count=warning_card_count,
            protein_card_count=protein_card_count,
        ),
    )
    overall_score = _weighted_score(components)
    low_confidence_component_count = sum(
        1
        for component in components
        if component.tier is ExperimentConfidenceTier.LOW_CONFIDENCE
    )
    caution_run_count = sum(
        1
        for assessment in run_qc_assessments
        if assessment.qc_status is QcStatus.CAUTION
    )
    failed_run_count = sum(
        1
        for assessment in run_qc_assessments
        if assessment.qc_status is QcStatus.FAIL
    )
    return ExperimentConfidenceReport(
        experiment_design=experiment_design,
        validity_report=resolved_validity_report,
        feasibility_report=resolved_feasibility_report,
        missingness_condition_summary_report=missingness_condition_summary_report,
        power_estimation_report=power_estimation_report,
        protocol_consistency_report=protocol_consistency_report,
        components=components,
        summary=ExperimentConfidenceSummary(
            overall_score=overall_score,
            overall_tier=_tier(overall_score),
            component_count=len(components),
            low_confidence_component_count=low_confidence_component_count,
            metadata_issue_count=resolved_validity_report.summary.issue_count
            + resolved_feasibility_report.summary.missing_metadata_count,
            caution_run_count=caution_run_count,
            failed_run_count=failed_run_count,
        ),
        note=(
            "experiment confidence combines metadata validity, run qc, sample balance, "
            "missingness burden, contamination, statistical power, and evidence consistency "
            "into one decomposed study-level confidence report with explicit reasons"
        ),
    )


def render_experiment_confidence_summary_tsv(
    report: ExperimentConfidenceReport,
) -> str:
    """Render a compact experiment-confidence summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("overall_score", f"{report.summary.overall_score:.4f}"))
    writer.writerow(("overall_tier", report.summary.overall_tier.value))
    writer.writerow(("component_count", report.summary.component_count))
    writer.writerow(
        ("low_confidence_component_count", report.summary.low_confidence_component_count)
    )
    writer.writerow(("metadata_issue_count", report.summary.metadata_issue_count))
    writer.writerow(("caution_run_count", report.summary.caution_run_count))
    writer.writerow(("failed_run_count", report.summary.failed_run_count))
    writer.writerow(("note", report.note))
    return buffer.getvalue()


def render_experiment_confidence_component_tsv(
    report: ExperimentConfidenceReport,
) -> str:
    """Render decomposed experiment-confidence components as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("component", "score", "tier", "reason_codes", "message"))
    for component in report.components:
        writer.writerow(
            (
                component.component.value,
                f"{component.score:.4f}",
                component.tier.value,
                ";".join(component.reason_codes),
                component.message,
            )
        )
    return buffer.getvalue()


def _metadata_validity_component(
    validity_report: ExperimentDesignValidityReport,
    feasibility_report: ExperimentFeasibilityReport,
) -> ExperimentConfidenceComponent:
    reason_codes = tuple(
        sorted(
            {
                *(issue.code for issue in validity_report.issues),
                *(issue.code for issue in feasibility_report.missing_metadata),
            }
        )
    )
    issue_count = validity_report.summary.issue_count + feasibility_report.summary.missing_metadata_count
    score = max(0.0, 1.0 - (0.2 * issue_count))
    if not validity_report.summary.valid_for_differential_analysis:
        score = min(score, 0.25)
    if not reason_codes:
        return ExperimentConfidenceComponent(
            component=ExperimentConfidenceComponentKind.METADATA_VALIDITY,
            score=1.0,
            tier=ExperimentConfidenceTier.HIGH_CONFIDENCE,
            reason_codes=(),
            message="study metadata is internally valid and complete for downstream analysis",
        )
    return ExperimentConfidenceComponent(
        component=ExperimentConfidenceComponentKind.METADATA_VALIDITY,
        score=score,
        tier=_tier(score),
        reason_codes=reason_codes,
        message=(
            "study metadata carries blocking validity issues or missing feasibility fields "
            "that weaken experiment-level confidence"
        ),
    )


def _run_qc_component(
    run_qc_assessments: tuple[QcRunAssessmentReport, ...],
) -> ExperimentConfidenceComponent:
    if not run_qc_assessments:
        return ExperimentConfidenceComponent(
            component=ExperimentConfidenceComponentKind.RUN_QC,
            score=0.5,
            tier=ExperimentConfidenceTier.MODERATE_CONFIDENCE,
            reason_codes=("run_qc_not_available",),
            message="no run-level qc assessment was available for experiment confidence scoring",
        )
    total = len(run_qc_assessments)
    weighted = sum(
        1.0
        if assessment.qc_status is QcStatus.PASS
        else 0.5
        if assessment.qc_status is QcStatus.CAUTION
        else 0.0
        for assessment in run_qc_assessments
    )
    reason_codes = tuple(
        sorted(
            {
                "failed_run_qc" if assessment.qc_status is QcStatus.FAIL else "caution_run_qc"
                for assessment in run_qc_assessments
                if assessment.qc_status is not QcStatus.PASS
            }
        )
    )
    score = weighted / total
    return ExperimentConfidenceComponent(
        component=ExperimentConfidenceComponentKind.RUN_QC,
        score=score,
        tier=_tier(score),
        reason_codes=reason_codes,
        message=(
            "run-level qc reflects the fraction of runs that pass cleanly versus "
            "those that require caution or fail"
        ),
    )


def _sample_balance_component(
    feasibility_report: ExperimentFeasibilityReport,
) -> ExperimentConfidenceComponent:
    counts = tuple(
        entry.effective_statistical_unit_count for entry in feasibility_report.group_sizes
    )
    if not counts:
        return ExperimentConfidenceComponent(
            component=ExperimentConfidenceComponentKind.SAMPLE_BALANCE,
            score=0.0,
            tier=ExperimentConfidenceTier.LOW_CONFIDENCE,
            reason_codes=("no_condition_structure",),
            message="sample balance cannot be assessed without condition-level statistical units",
        )
    minimum = min(counts)
    maximum = max(counts)
    balance_ratio = 0.0 if maximum == 0 else minimum / maximum
    score = balance_ratio
    reason_codes: list[str] = []
    if any(entry.underpowered for entry in feasibility_report.group_sizes):
        score *= 0.6
        reason_codes.append("underpowered_condition")
    if maximum - minimum > 1:
        reason_codes.append("imbalanced_condition_sizes")
    if not reason_codes:
        return ExperimentConfidenceComponent(
            component=ExperimentConfidenceComponentKind.SAMPLE_BALANCE,
            score=1.0,
            tier=ExperimentConfidenceTier.HIGH_CONFIDENCE,
            reason_codes=(),
            message="condition-level statistical units are balanced across the experiment",
        )
    return ExperimentConfidenceComponent(
        component=ExperimentConfidenceComponentKind.SAMPLE_BALANCE,
        score=score,
        tier=_tier(score),
        reason_codes=tuple(sorted(reason_codes)),
        message=(
            "condition-level statistical units are imbalanced or underpowered for "
            "stable experiment-level conclusions"
        ),
    )


def _missingness_component(
    report: MissingnessConditionSummaryReport,
) -> ExperimentConfidenceComponent:
    if not report.entries:
        return ExperimentConfidenceComponent(
            component=ExperimentConfidenceComponentKind.MISSINGNESS,
            score=0.0,
            tier=ExperimentConfidenceTier.LOW_CONFIDENCE,
            reason_codes=("missingness_not_available",),
            message="missingness cannot be assessed without condition-level quantitative evidence",
        )
    maximum_missing_fraction = max(entry.missing_fraction for entry in report.entries)
    mean_missing_fraction = sum(entry.missing_fraction for entry in report.entries) / len(
        report.entries
    )
    condition_specific_absence_count = sum(
        len(entry.condition_specific_absence_entity_ids) for entry in report.entries
    )
    score = max(
        0.0,
        1.0 - (0.8 * mean_missing_fraction) - (0.7 * maximum_missing_fraction),
    )
    reason_codes: list[str] = []
    if maximum_missing_fraction >= 0.5:
        reason_codes.append("high_condition_missingness")
    elif maximum_missing_fraction >= 0.3:
        reason_codes.append("moderate_condition_missingness")
    if condition_specific_absence_count:
        score = max(0.0, score - 0.2)
        reason_codes.append("condition_specific_absence")
    if not reason_codes:
        return ExperimentConfidenceComponent(
            component=ExperimentConfidenceComponentKind.MISSINGNESS,
            score=1.0,
            tier=ExperimentConfidenceTier.HIGH_CONFIDENCE,
            reason_codes=(),
            message="condition-level quantitative evidence has low missingness burden",
        )
    return ExperimentConfidenceComponent(
        component=ExperimentConfidenceComponentKind.MISSINGNESS,
        score=score,
        tier=_tier(score),
        reason_codes=tuple(sorted(reason_codes)),
        message=(
            "missing quantitative evidence or condition-specific absence reduces the "
            "stability of experiment-level interpretation"
        ),
    )


def _contamination_component(
    run_qc_reports: tuple[LcmsRunQcReport, ...],
) -> ExperimentConfidenceComponent:
    if not run_qc_reports:
        return ExperimentConfidenceComponent(
            component=ExperimentConfidenceComponentKind.CONTAMINATION,
            score=0.5,
            tier=ExperimentConfidenceTier.MODERATE_CONFIDENCE,
            reason_codes=("contamination_not_available",),
            message="contamination burden could not be scored because no run-level qc report was available",
        )
    maximum_fraction = max(
        report.contaminant_summary.contaminant_psm_fraction for report in run_qc_reports
    )
    mean_fraction = sum(
        report.contaminant_summary.contaminant_psm_fraction for report in run_qc_reports
    ) / len(run_qc_reports)
    if maximum_fraction <= 0.05 and mean_fraction <= 0.03:
        score = 1.0
        reason_codes: tuple[str, ...] = ()
    elif maximum_fraction <= 0.1 and mean_fraction <= 0.08:
        score = 0.75
        reason_codes = ("elevated_contamination",)
    elif maximum_fraction <= 0.2:
        score = 0.4
        reason_codes = ("high_contamination",)
    else:
        score = 0.1
        reason_codes = ("severe_contamination",)
    return ExperimentConfidenceComponent(
        component=ExperimentConfidenceComponentKind.CONTAMINATION,
        score=score,
        tier=_tier(score),
        reason_codes=reason_codes,
        message=(
            "contamination confidence follows the observed contaminant psm burden across qc-scored runs"
        ),
    )


def _statistical_power_component(
    report: PowerEstimationReport,
) -> ExperimentConfidenceComponent:
    grid = report.effect_size_grid
    if not grid:
        return ExperimentConfidenceComponent(
            component=ExperimentConfidenceComponentKind.STATISTICAL_POWER,
            score=0.0,
            tier=ExperimentConfidenceTier.LOW_CONFIDENCE,
            reason_codes=("power_not_available",),
            message="statistical power could not be estimated from the quantitative evidence",
        )
    best_entry = grid[min(len(grid) - 1, 1)]
    detectable_effect = best_entry.median_detectable_log2_fold_change
    if detectable_effect <= 0.5:
        score = 1.0
        reason_codes: tuple[str, ...] = ()
    elif detectable_effect <= 1.0:
        score = 0.75
        reason_codes = ("moderate_detectable_effect",)
    elif detectable_effect <= 1.5:
        score = 0.5
        reason_codes = ("large_detectable_effect_required",)
    else:
        score = 0.2
        reason_codes = ("very_large_detectable_effect_required",)
    if report.summary.evaluated_entity_count < 25:
        score = min(score, 0.5)
        reason_codes = tuple(sorted((*reason_codes, "few_evaluable_entities")))
    return ExperimentConfidenceComponent(
        component=ExperimentConfidenceComponentKind.STATISTICAL_POWER,
        score=score,
        tier=_tier(score),
        reason_codes=reason_codes,
        message=(
            "statistical power follows the median detectable log2 fold-change across "
            "candidate replicate counts"
        ),
    )


def _evidence_consistency_component(
    *,
    protocol_consistency_report: ProtocolConsistencyReport | None,
    warning_card_count: int,
    protein_card_count: int,
) -> ExperimentConfidenceComponent:
    score = 1.0
    reason_codes: list[str] = []
    if protocol_consistency_report is not None:
        blocking = protocol_consistency_report.summary.blocking_diagnostic_count
        caution = protocol_consistency_report.summary.caution_diagnostic_count
        if blocking:
            score = min(score, 0.1)
            reason_codes.append("protocol_consistency_blocking")
        elif caution:
            score = min(score, 0.6)
            reason_codes.append("protocol_consistency_caution")
    else:
        score = min(score, 0.7)
        reason_codes.append("protocol_consistency_not_available")
    if protein_card_count > 0:
        warning_fraction = warning_card_count / protein_card_count
        if warning_fraction >= 0.5:
            score = max(0.0, score - 0.3)
            reason_codes.append("frequent_result_card_warnings")
        elif warning_fraction > 0.0:
            score = max(0.0, score - 0.1)
            reason_codes.append("result_card_warnings")
    if not reason_codes:
        return ExperimentConfidenceComponent(
            component=ExperimentConfidenceComponentKind.EVIDENCE_CONSISTENCY,
            score=1.0,
            tier=ExperimentConfidenceTier.HIGH_CONFIDENCE,
            reason_codes=(),
            message="protocol declarations and final-result evidence are internally consistent",
        )
    return ExperimentConfidenceComponent(
        component=ExperimentConfidenceComponentKind.EVIDENCE_CONSISTENCY,
        score=score,
        tier=_tier(score),
        reason_codes=tuple(sorted(reason_codes)),
        message=(
            "declared protocol mismatches or repeated final-result warnings reduce overall evidence consistency"
        ),
    )


def _weighted_score(
    components: tuple[ExperimentConfidenceComponent, ...],
) -> float:
    weights = {
        ExperimentConfidenceComponentKind.METADATA_VALIDITY: 0.2,
        ExperimentConfidenceComponentKind.RUN_QC: 0.15,
        ExperimentConfidenceComponentKind.SAMPLE_BALANCE: 0.15,
        ExperimentConfidenceComponentKind.MISSINGNESS: 0.15,
        ExperimentConfidenceComponentKind.CONTAMINATION: 0.1,
        ExperimentConfidenceComponentKind.STATISTICAL_POWER: 0.15,
        ExperimentConfidenceComponentKind.EVIDENCE_CONSISTENCY: 0.1,
    }
    weighted_total = sum(
        component.score * weights[component.component] for component in components
    )
    return max(0.0, min(1.0, weighted_total))


def _tier(score: float) -> ExperimentConfidenceTier:
    if score >= 0.8:
        return ExperimentConfidenceTier.HIGH_CONFIDENCE
    if score >= 0.55:
        return ExperimentConfidenceTier.MODERATE_CONFIDENCE
    return ExperimentConfidenceTier.LOW_CONFIDENCE


__all__ = [
    "ExperimentConfidenceComponent",
    "ExperimentConfidenceComponentKind",
    "ExperimentConfidenceReport",
    "ExperimentConfidenceSummary",
    "ExperimentConfidenceTier",
    "build_experiment_confidence_report",
    "render_experiment_confidence_component_tsv",
    "render_experiment_confidence_summary_tsv",
]
