# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Threshold policies, assessments, and review renderers for laboratory QC."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.lab.protocol_context import (
    AcquisitionType,
    DepletionMode,
    EnrichmentType,
    FractionationMode,
    LabelingMethod,
    LabProtocolContextEntry,
)
from bijux_proteomics.lab.qc.models import (
    InstrumentBatchQcReport,
    LcmsRunQcReport,
    QcAssessmentDisposition,
    QcAssessmentProvenance,
    QcAssessmentSeverity,
    QcBatchAssessmentReport,
    QcContaminantSummary,
    QcDigestionSpecificity,
    QcMassErrorSummary,
    QcMetricAssessment,
    QcQuantSummary,
    QcRetentionTimeSummary,
    QcRunAnomalyCategory,
    QcRunAnomalyEntry,
    QcRunAssessmentReport,
    QcStatus,
    QcStatusReasonEntry,
    QcStatusReasonSource,
    QcThresholdPolicy,
    QcThresholdPolicyProfile,
    QcThresholdRule,
    QcUnknownStateReason,
)
from bijux_proteomics.lab.qc.support import (
    build_document_schema,
    metadata_reference_values,
    stable_sha256,
)


def _severity_rank(severity: QcAssessmentSeverity) -> int:
    return {
        QcAssessmentSeverity.PASSED: 0,
        QcAssessmentSeverity.NOT_ASSESSED: 1,
        QcAssessmentSeverity.WARNING: 2,
        QcAssessmentSeverity.FAILED: 3,
    }[severity]


def _status_rank(status: QcStatus) -> int:
    return {
        QcStatus.PASSED: 0,
        QcStatus.CAUTION: 1,
        QcStatus.FAIL: 2,
    }[status]


def _status_from_severity(severity: QcAssessmentSeverity) -> QcStatus:
    if severity is QcAssessmentSeverity.FAILED:
        return QcStatus.FAIL
    if severity in (QcAssessmentSeverity.WARNING, QcAssessmentSeverity.NOT_ASSESSED):
        return QcStatus.CAUTION
    return QcStatus.PASSED


def _metric_status_reason(assessment: QcMetricAssessment) -> QcStatusReasonEntry | None:
    status = _status_from_severity(assessment.severity)
    if status is QcStatus.PASSED:
        return None
    return QcStatusReasonEntry(
        code=assessment.metric_key,
        status=status,
        source=QcStatusReasonSource.METRIC,
        message=assessment.message,
    )


def _build_run_status_reasons(
    run_report: LcmsRunQcReport,
    metric_assessments: tuple[QcMetricAssessment, ...],
) -> tuple[QcStatusReasonEntry, ...]:
    reasons: list[QcStatusReasonEntry] = []
    reasons.extend(
        reason
        for reason in (
            _metric_status_reason(assessment) for assessment in metric_assessments
        )
        if reason is not None
    )

    specificity_lookup = {
        entry.specificity: entry.fraction for entry in run_report.digestion_specificity
    }
    non_specific_fraction = specificity_lookup.get(
        QcDigestionSpecificity.NON_SPECIFIC, 0.0
    )
    if run_report.missed_cleavage_rate >= 0.2 or non_specific_fraction >= 0.15:
        reasons.append(
            QcStatusReasonEntry(
                code="digestion_inefficiency",
                status=(
                    QcStatus.FAIL
                    if run_report.missed_cleavage_rate >= 0.35
                    or non_specific_fraction >= 0.25
                    else QcStatus.CAUTION
                ),
                source=QcStatusReasonSource.LAB,
                message=(
                    "missed-cleavage rate "
                    f"{run_report.missed_cleavage_rate:.4g} and non-specific fraction "
                    f"{non_specific_fraction:.4g} indicate weak digestion efficiency"
                ),
            )
        )

    contamination_fraction = (
        run_report.contaminant_summary.contaminant_intensity_fraction
    )
    if (
        contamination_fraction >= 0.05
        or run_report.contaminant_summary.contaminant_psm_fraction >= 0.1
    ):
        reasons.append(
            QcStatusReasonEntry(
                code="contamination_burden",
                status=QcStatus.FAIL
                if contamination_fraction >= 0.15
                else QcStatus.CAUTION,
                source=QcStatusReasonSource.LAB,
                message=(
                    "contaminant intensity fraction "
                    f"{contamination_fraction:.4g} indicates meaningful contamination burden"
                ),
            )
        )

    carryover_refs = metadata_reference_values(
        run_report.design_metadata, "carryover_marker_refs"
    )
    carryover_hits = tuple(
        sorted(
            ref
            for ref in carryover_refs
            if run_report.protein_psm_counts.get(ref, 0) > 0
        )
    )
    if carryover_hits:
        reasons.append(
            QcStatusReasonEntry(
                code="carryover_suspected",
                status=QcStatus.CAUTION,
                source=QcStatusReasonSource.LAB,
                message="carryover markers were observed: " + ", ".join(carryover_hits),
            )
        )

    expected_species_refs = metadata_reference_values(
        run_report.design_metadata, "expected_species_marker_refs"
    )
    expected_species_hits = tuple(
        sorted(
            ref
            for ref in expected_species_refs
            if run_report.protein_psm_counts.get(ref, 0) > 0
        )
    )
    forbidden_species_hits = tuple(
        sorted(
            ref
            for ref in metadata_reference_values(
                run_report.design_metadata, "forbidden_species_marker_refs"
            )
            if run_report.protein_psm_counts.get(ref, 0) > 0
        )
    )
    if forbidden_species_hits or (expected_species_refs and not expected_species_hits):
        reasons.append(
            QcStatusReasonEntry(
                code="species_marker_mismatch",
                status=QcStatus.FAIL if forbidden_species_hits else QcStatus.CAUTION,
                source=QcStatusReasonSource.LAB,
                message=(
                    "species marker posture did not match the expected sample metadata"
                    if not forbidden_species_hits
                    else "forbidden species markers were observed: "
                    + ", ".join(forbidden_species_hits)
                ),
            )
        )

    expected_sex_refs = metadata_reference_values(
        run_report.design_metadata, "expected_sex_marker_refs"
    )
    expected_sex_hits = tuple(
        sorted(
            ref
            for ref in expected_sex_refs
            if run_report.protein_psm_counts.get(ref, 0) > 0
        )
    )
    forbidden_sex_hits = tuple(
        sorted(
            ref
            for ref in metadata_reference_values(
                run_report.design_metadata, "forbidden_sex_marker_refs"
            )
            if run_report.protein_psm_counts.get(ref, 0) > 0
        )
    )
    if forbidden_sex_hits or (expected_sex_refs and not expected_sex_hits):
        reasons.append(
            QcStatusReasonEntry(
                code="sex_marker_mismatch",
                status=QcStatus.FAIL if forbidden_sex_hits else QcStatus.CAUTION,
                source=QcStatusReasonSource.LAB,
                message=(
                    "sex marker posture did not match the expected sample metadata"
                    if not forbidden_sex_hits
                    else "forbidden sex markers were observed: "
                    + ", ".join(forbidden_sex_hits)
                ),
            )
        )

    if forbidden_species_hits or forbidden_sex_hits:
        reasons.append(
            QcStatusReasonEntry(
                code="sample_swap_suspected",
                status=QcStatus.CAUTION,
                source=QcStatusReasonSource.LAB,
                message=(
                    "marker evidence conflicts with the expected sample identity and suggests a sample swap"
                ),
            )
        )

    expected_enrichment_refs = metadata_reference_values(
        run_report.design_metadata, "enrichment_marker_refs"
    )
    enrichment_hits = tuple(
        sorted(
            ref
            for ref in expected_enrichment_refs
            if run_report.protein_psm_counts.get(ref, 0) > 0
        )
    )
    if expected_enrichment_refs and not enrichment_hits:
        reasons.append(
            QcStatusReasonEntry(
                code="enrichment_inefficiency",
                status=QcStatus.CAUTION,
                source=QcStatusReasonSource.LAB,
                message="expected enrichment markers were not observed",
            )
        )

    depletion_hits = tuple(
        sorted(
            ref
            for ref in metadata_reference_values(
                run_report.design_metadata, "depletion_marker_refs"
            )
            if run_report.protein_psm_counts.get(ref, 0) > 0
        )
    )
    if depletion_hits:
        reasons.append(
            QcStatusReasonEntry(
                code="depletion_inefficiency",
                status=QcStatus.CAUTION,
                source=QcStatusReasonSource.LAB,
                message="depletion markers remained visible: "
                + ", ".join(depletion_hits),
            )
        )

    unique_reasons: dict[tuple[str, str], QcStatusReasonEntry] = {}
    for reason in reasons:
        key = (reason.code, reason.message)
        incumbent = unique_reasons.get(key)
        if incumbent is None or _status_rank(reason.status) > _status_rank(
            incumbent.status
        ):
            unique_reasons[key] = reason
    return tuple(
        sorted(
            unique_reasons.values(),
            key=lambda entry: (
                _status_rank(entry.status),
                entry.source.value,
                entry.code,
            ),
            reverse=True,
        )
    )


def _status_from_reasons(
    reasons: tuple[QcStatusReasonEntry, ...],
    overall_severity: QcAssessmentSeverity,
) -> QcStatus:
    if reasons:
        return max(reasons, key=lambda entry: _status_rank(entry.status)).status
    return _status_from_severity(overall_severity)


def _build_batch_status_reasons(
    metric_assessments: tuple[QcMetricAssessment, ...],
) -> tuple[QcStatusReasonEntry, ...]:
    return tuple(
        reason
        for reason in (
            _metric_status_reason(assessment) for assessment in metric_assessments
        )
        if reason is not None
    )


def _assessment_message(
    rule: QcThresholdRule,
    severity: QcAssessmentSeverity,
    observed_value: float | None,
    unknown_state_reason: QcUnknownStateReason | None = None,
) -> str:
    if observed_value is None:
        if unknown_state_reason is not None:
            return (
                f"{rule.metric_label} was not assessed because "
                f"{unknown_state_reason.value.replace('_', ' ')}"
            )
        return f"{rule.metric_label} was not assessed"
    value_text = f"{observed_value:.4f}".rstrip("0").rstrip(".")
    unit = f" {rule.unit}" if rule.unit else ""
    if severity is QcAssessmentSeverity.PASSED:
        return f"{rule.metric_label} is within policy at {value_text}{unit}"
    if severity is QcAssessmentSeverity.WARNING:
        return f"{rule.metric_label} breached advisory threshold at {value_text}{unit}"
    return f"{rule.metric_label} breached fail threshold at {value_text}{unit}"


def build_run_anomalies(
    *,
    identification_rate: float,
    mass_error_summary: QcMassErrorSummary,
    retention_summary: QcRetentionTimeSummary,
    quant_summary: QcQuantSummary | None,
    contaminant_summary: QcContaminantSummary,
) -> tuple[QcRunAnomalyEntry, ...]:
    """Build operator-facing anomaly entries from one run report summary."""
    anomalies: list[QcRunAnomalyEntry] = []
    if (
        retention_summary.spectra_with_retention_time == 0
        or retention_summary.identified_span_seconds is not None
        and retention_summary.identified_span_seconds < 120.0
    ):
        anomalies.append(
            QcRunAnomalyEntry(
                category=QcRunAnomalyCategory.CHROMATOGRAPHY,
                code="limited_retention_coverage",
                message="retention-time coverage is limited for identified spectra",
                severity=QcAssessmentSeverity.WARNING,
            )
        )
    if identification_rate < 0.5 or (
        mass_error_summary.median_abs_ppm is not None
        and mass_error_summary.median_abs_ppm > 10.0
    ):
        anomalies.append(
            QcRunAnomalyEntry(
                category=QcRunAnomalyCategory.IDENTIFICATION,
                code="weak_identification_signal",
                message="identification evidence is weak or precursor error is elevated",
                severity=QcAssessmentSeverity.WARNING
                if identification_rate >= 0.3
                else QcAssessmentSeverity.FAILED,
            )
        )
    if quant_summary is None or quant_summary.missing_fraction > 0.4:
        anomalies.append(
            QcRunAnomalyEntry(
                category=QcRunAnomalyCategory.QUANTIFICATION,
                code="sparse_quant_signal",
                message="quantification coverage is sparse or absent for this run",
                severity=QcAssessmentSeverity.WARNING,
            )
        )
    if (
        contaminant_summary.contaminant_psm_fraction > 0.1
        or contaminant_summary.contaminant_intensity_fraction > 0.1
    ):
        anomalies.append(
            QcRunAnomalyEntry(
                category=QcRunAnomalyCategory.CONTAMINATION,
                code="elevated_contaminant_fraction",
                message="contaminant evidence burden exceeds the expected background range",
                severity=QcAssessmentSeverity.WARNING,
            )
        )
    return tuple(anomalies)


def _evaluate_rule(
    rule: QcThresholdRule,
    observed_value: float | None,
    *,
    policy_name: str,
    policy_version: str,
    policy_sha256: str,
    unknown_state_reason: QcUnknownStateReason | None = None,
) -> QcMetricAssessment:
    triggered_threshold = None
    if observed_value is None:
        severity = QcAssessmentSeverity.NOT_ASSESSED
    else:
        severity = QcAssessmentSeverity.PASSED
        if (
            rule.lower_fail is not None
            and observed_value < rule.lower_fail
            or rule.upper_fail is not None
            and observed_value > rule.upper_fail
        ):
            severity = QcAssessmentSeverity.FAILED
            triggered_threshold = (
                "lower_fail"
                if rule.lower_fail is not None and observed_value < rule.lower_fail
                else "upper_fail"
            )
        elif (
            rule.lower_warn is not None
            and observed_value < rule.lower_warn
            or rule.upper_warn is not None
            and observed_value > rule.upper_warn
        ):
            severity = QcAssessmentSeverity.WARNING
            triggered_threshold = (
                "lower_warn"
                if rule.lower_warn is not None and observed_value < rule.lower_warn
                else "upper_warn"
            )
    return QcMetricAssessment(
        metric_key=rule.metric_key,
        metric_label=rule.metric_label,
        observed_value=observed_value,
        unit=rule.unit,
        severity=severity,
        disposition=rule.disposition,
        threshold_rule=rule,
        provenance=QcAssessmentProvenance(
            policy_name=policy_name,
            policy_version=policy_version,
            policy_sha256=policy_sha256,
            rule_sha256=stable_sha256(rule),
            triggered_threshold=triggered_threshold,
            lower_warn=rule.lower_warn,
            lower_fail=rule.lower_fail,
            upper_warn=rule.upper_warn,
            upper_fail=rule.upper_fail,
        ),
        unknown_state_reason=unknown_state_reason,
        message=_assessment_message(
            rule,
            severity,
            observed_value,
            unknown_state_reason=unknown_state_reason,
        ),
        enforced_violation=severity is QcAssessmentSeverity.FAILED
        and rule.disposition is QcAssessmentDisposition.ENFORCED,
    )


def default_qc_threshold_policy() -> QcThresholdPolicy:
    """Return a durable default QC threshold policy for run diagnostics."""
    return QcThresholdPolicy(
        document_schema=build_document_schema("qc_threshold_policy"),
        policy_name="default-lcms-qc",
        version="1.0.0",
        rules=(
            QcThresholdRule(
                metric_key="spectrum_count",
                metric_label="Spectrum count",
                lower_warn=1000.0,
                lower_fail=500.0,
                disposition=QcAssessmentDisposition.ADVISORY,
            ),
            QcThresholdRule(
                metric_key="identification_rate",
                metric_label="Identification rate",
                unit="fraction",
                lower_warn=0.2,
                lower_fail=0.1,
                disposition=QcAssessmentDisposition.ENFORCED,
            ),
            QcThresholdRule(
                metric_key="median_abs_mass_error_ppm",
                metric_label="Median absolute precursor error",
                unit="ppm",
                upper_warn=10.0,
                upper_fail=20.0,
                disposition=QcAssessmentDisposition.ENFORCED,
            ),
            QcThresholdRule(
                metric_key="contaminant_psm_fraction",
                metric_label="Contaminant PSM fraction",
                unit="fraction",
                upper_warn=0.1,
                upper_fail=0.2,
                disposition=QcAssessmentDisposition.ADVISORY,
            ),
            QcThresholdRule(
                metric_key="missed_cleavage_rate",
                metric_label="Missed-cleavage rate",
                unit="fraction",
                upper_warn=0.2,
                upper_fail=0.35,
                disposition=QcAssessmentDisposition.ADVISORY,
            ),
            QcThresholdRule(
                metric_key="non_specific_fraction",
                metric_label="Non-specific peptide fraction",
                unit="fraction",
                upper_warn=0.15,
                upper_fail=0.3,
                disposition=QcAssessmentDisposition.ADVISORY,
            ),
        ),
    )


def build_protocol_aware_qc_threshold_policy(
    protocol_context: LabProtocolContextEntry,
    *,
    base_policy: QcThresholdPolicy | None = None,
) -> QcThresholdPolicy:
    """Adapt run-QC thresholds to one governed lab protocol context."""
    thresholds_by_metric: dict[str, dict[str, float]] = {}

    def _set(metric_key: str, **updates: float) -> None:
        thresholds_by_metric.setdefault(metric_key, {}).update(updates)

    if protocol_context.acquisition_type is AcquisitionType.DIA:
        _set("spectrum_count", lower_warn=700.0, lower_fail=350.0)
        _set("identification_rate", lower_warn=0.12, lower_fail=0.06)
    if protocol_context.acquisition_type is AcquisitionType.TARGETED:
        _set("spectrum_count", lower_warn=200.0, lower_fail=100.0)
        _set("identification_rate", lower_warn=0.05, lower_fail=0.02)
        _set("contaminant_psm_fraction", upper_warn=0.08, upper_fail=0.16)
    if protocol_context.labeling_method is LabelingMethod.TMT:
        _set("missed_cleavage_rate", upper_warn=0.25, upper_fail=0.4)
        _set("non_specific_fraction", upper_warn=0.2, upper_fail=0.35)
    if protocol_context.enrichment_type is not EnrichmentType.NONE:
        _set("spectrum_count", lower_warn=600.0, lower_fail=300.0)
        _set("identification_rate", lower_warn=0.1, lower_fail=0.05)
        _set("missed_cleavage_rate", upper_warn=0.28, upper_fail=0.45)
    if protocol_context.fractionation_mode is not FractionationMode.NONE:
        _set("spectrum_count", lower_warn=500.0, lower_fail=250.0)
    if protocol_context.depletion_mode is DepletionMode.PLASMA_HIGH_ABUNDANCE:
        _set("contaminant_psm_fraction", upper_warn=0.12, upper_fail=0.24)

    active_policy = base_policy or default_qc_threshold_policy()
    return active_policy.model_copy(
        update={
            "policy_name": (
                f"{active_policy.policy_name}:{protocol_context.protocol_id}"
            ),
            "rules": tuple(
                rule.model_copy(update=thresholds_by_metric.get(rule.metric_key, {}))
                for rule in active_policy.rules
            ),
        }
    )


def build_qc_threshold_profile(policy: QcThresholdPolicy) -> QcThresholdPolicyProfile:
    """Build an explicit advisory/enforced rule split from one QC policy."""
    advisory_rules = tuple(
        rule
        for rule in policy.rules
        if rule.disposition is QcAssessmentDisposition.ADVISORY
    )
    enforced_rules = tuple(
        rule
        for rule in policy.rules
        if rule.disposition is QcAssessmentDisposition.ENFORCED
    )
    return QcThresholdPolicyProfile(
        policy_name=policy.policy_name,
        policy_version=policy.version,
        advisory_rules=advisory_rules,
        enforced_rules=enforced_rules,
    )


def load_qc_threshold_policy(path: Path) -> QcThresholdPolicy:
    """Load a QC threshold policy from JSON."""
    return QcThresholdPolicy.model_validate_json(path.read_text(encoding="utf-8"))


def build_run_qc_assessment(
    run_report: LcmsRunQcReport,
    *,
    policy: QcThresholdPolicy,
) -> QcRunAssessmentReport:
    """Assess one run-level QC report against a threshold policy."""
    specificity_lookup = {
        entry.specificity: entry.fraction for entry in run_report.digestion_specificity
    }
    policy_sha256 = stable_sha256(policy)
    observed_metrics = {
        "spectrum_count": float(run_report.spectrum_count),
        "identification_rate": run_report.identification_rate,
        "median_abs_mass_error_ppm": run_report.mass_error.median_abs_ppm,
        "contaminant_psm_fraction": run_report.contaminant_summary.contaminant_psm_fraction,
        "missed_cleavage_rate": run_report.missed_cleavage_rate,
        "non_specific_fraction": specificity_lookup.get(
            QcDigestionSpecificity.NON_SPECIFIC, 0.0
        ),
    }
    unknown_reasons = {
        "median_abs_mass_error_ppm": (
            QcUnknownStateReason.NO_MATCHED_PSMS
            if run_report.mass_error.matched_psm_count == 0
            else QcUnknownStateReason.NO_MASS_ERROR_EVIDENCE
        )
    }
    assessments = tuple(
        _evaluate_rule(
            rule,
            observed_metrics.get(rule.metric_key),
            policy_name=policy.policy_name,
            policy_version=policy.version,
            policy_sha256=policy_sha256,
            unknown_state_reason=unknown_reasons.get(rule.metric_key)
            if observed_metrics.get(rule.metric_key) is None
            else None,
        )
        for rule in policy.rules
    )
    threshold_profile = build_qc_threshold_profile(policy)
    advisory_failure_metric_keys = tuple(
        assessment.metric_key
        for assessment in assessments
        if assessment.severity
        in (QcAssessmentSeverity.WARNING, QcAssessmentSeverity.FAILED)
        and assessment.disposition is QcAssessmentDisposition.ADVISORY
    )
    enforced_failure_metric_keys = tuple(
        assessment.metric_key
        for assessment in assessments
        if assessment.severity is QcAssessmentSeverity.FAILED
        and assessment.disposition is QcAssessmentDisposition.ENFORCED
    )
    overall = max(
        assessments, key=lambda entry: _severity_rank(entry.severity), default=None
    )
    overall_severity = (
        QcAssessmentSeverity.PASSED if overall is None else overall.severity
    )
    status_reasons = _build_run_status_reasons(run_report, assessments)
    return QcRunAssessmentReport(
        document_schema=build_document_schema("qc_run_assessment_report"),
        run_id=run_report.run_id,
        sample_id=run_report.sample_id,
        policy_name=policy.policy_name,
        policy_version=policy.version,
        policy_sha256=policy_sha256,
        threshold_profile=threshold_profile,
        overall_severity=overall_severity,
        qc_status=_status_from_reasons(status_reasons, overall_severity),
        blocked=any(entry.enforced_violation for entry in assessments),
        advisory_failure_metric_keys=advisory_failure_metric_keys,
        enforced_failure_metric_keys=enforced_failure_metric_keys,
        status_reasons=status_reasons,
        metric_assessments=assessments,
    )


def build_batch_qc_assessment(
    batch_report: InstrumentBatchQcReport,
    *,
    policy: QcThresholdPolicy,
) -> QcBatchAssessmentReport:
    """Assess one batch-level QC report against a threshold policy."""
    metrics = {
        "median_spectrum_count": batch_report.median_spectrum_count,
        "median_identification_rate": batch_report.median_identification_rate,
        "median_abs_mass_error_ppm": batch_report.median_abs_mass_error_ppm,
        "outlier_run_count": float(len(batch_report.outlier_run_ids)),
    }
    unknown_reasons = {
        "median_abs_mass_error_ppm": QcUnknownStateReason.NO_MASS_ERROR_EVIDENCE
    }
    rules = []
    for rule in policy.rules:
        if rule.metric_key == "spectrum_count":
            rules.append(
                rule.model_copy(
                    update={
                        "metric_key": "median_spectrum_count",
                        "metric_label": "Median spectrum count",
                    }
                )
            )
        elif rule.metric_key == "identification_rate":
            rules.append(
                rule.model_copy(
                    update={
                        "metric_key": "median_identification_rate",
                        "metric_label": "Median identification rate",
                    }
                )
            )
        elif rule.metric_key == "median_abs_mass_error_ppm":
            rules.append(rule)
    rules.append(
        QcThresholdRule(
            metric_key="outlier_run_count",
            metric_label="Outlier run count",
            upper_warn=0.0,
            upper_fail=1.0,
            disposition=QcAssessmentDisposition.ADVISORY,
        )
    )
    batch_policy = QcThresholdPolicy(
        document_schema=policy.document_schema,
        policy_name=policy.policy_name,
        version=policy.version,
        rules=tuple(rules),
    )
    policy_sha256 = stable_sha256(batch_policy)
    assessments = tuple(
        _evaluate_rule(
            rule,
            metrics.get(rule.metric_key),
            policy_name=policy.policy_name,
            policy_version=policy.version,
            policy_sha256=policy_sha256,
            unknown_state_reason=unknown_reasons.get(rule.metric_key)
            if metrics.get(rule.metric_key) is None
            else None,
        )
        for rule in rules
    )
    threshold_profile = build_qc_threshold_profile(batch_policy)
    advisory_failure_metric_keys = tuple(
        assessment.metric_key
        for assessment in assessments
        if assessment.severity
        in (QcAssessmentSeverity.WARNING, QcAssessmentSeverity.FAILED)
        and assessment.disposition is QcAssessmentDisposition.ADVISORY
    )
    enforced_failure_metric_keys = tuple(
        assessment.metric_key
        for assessment in assessments
        if assessment.severity is QcAssessmentSeverity.FAILED
        and assessment.disposition is QcAssessmentDisposition.ENFORCED
    )
    overall = max(
        assessments, key=lambda entry: _severity_rank(entry.severity), default=None
    )
    overall_severity = (
        QcAssessmentSeverity.PASSED if overall is None else overall.severity
    )
    status_reasons = _build_batch_status_reasons(assessments)
    return QcBatchAssessmentReport(
        document_schema=build_document_schema("qc_batch_assessment_report"),
        batch_id=batch_report.batch_id,
        instrument=batch_report.instrument,
        policy_name=policy.policy_name,
        policy_version=policy.version,
        policy_sha256=policy_sha256,
        threshold_profile=threshold_profile,
        overall_severity=overall_severity,
        qc_status=_status_from_reasons(status_reasons, overall_severity),
        blocked=any(entry.enforced_violation for entry in assessments),
        advisory_failure_metric_keys=advisory_failure_metric_keys,
        enforced_failure_metric_keys=enforced_failure_metric_keys,
        status_reasons=status_reasons,
        metric_assessments=assessments,
    )


__all__ = [
    "build_batch_qc_assessment",
    "build_protocol_aware_qc_threshold_policy",
    "build_qc_threshold_profile",
    "build_run_anomalies",
    "build_run_qc_assessment",
    "default_qc_threshold_policy",
    "load_qc_threshold_policy",
]
