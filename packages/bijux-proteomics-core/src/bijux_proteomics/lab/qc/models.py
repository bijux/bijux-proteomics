# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable QC contracts for laboratory-facing run and batch review."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.domain.reason_codes import (
    ReasonCodeCategory,
    require_registered_reason_code,
)
from bijux_proteomics.lab.protocol_context import (
    AcquisitionType,
    DepletionMode,
    EnrichmentType,
    FractionationMode,
    LabelingMethod,
)
from bijux_proteomics.quantification.contracts import QuantEntityLevel
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class QcDigestionSpecificity(StrEnum):
    """Stable digestion-specificity classes for identified peptides."""

    ENZYMATIC = "enzymatic"
    SEMI_SPECIFIC = "semi_specific"
    NON_SPECIFIC = "non_specific"


class QcChargeStateEntry(JsonModel):
    """One charge-state count and fraction."""

    model_config = ConfigDict(extra="forbid")

    charge_label: str = Field(..., min_length=1)
    count: int = Field(..., ge=0)
    fraction: float = Field(..., ge=0.0, le=1.0)


class QcMassErrorSummary(JsonModel):
    """Stable summary over precursor mass-error evidence."""

    model_config = ConfigDict(extra="forbid")

    matched_psm_count: int = Field(..., ge=0)
    mean_ppm: float | None = None
    median_ppm: float | None = None
    median_abs_ppm: float | None = Field(default=None, ge=0.0)
    p95_abs_ppm: float | None = Field(default=None, ge=0.0)
    max_abs_ppm: float | None = Field(default=None, ge=0.0)


class QcRetentionTimeSummary(JsonModel):
    """Stable retention-time coverage summary for one run."""

    model_config = ConfigDict(extra="forbid")

    spectra_with_retention_time: int = Field(..., ge=0)
    identified_with_retention_time: int = Field(..., ge=0)
    min_retention_time_seconds: float | None = Field(default=None, ge=0.0)
    max_retention_time_seconds: float | None = Field(default=None, ge=0.0)
    span_seconds: float | None = Field(default=None, ge=0.0)
    identified_min_retention_time_seconds: float | None = Field(default=None, ge=0.0)
    identified_max_retention_time_seconds: float | None = Field(default=None, ge=0.0)
    identified_span_seconds: float | None = Field(default=None, ge=0.0)
    identified_median_retention_time_seconds: float | None = Field(default=None, ge=0.0)


class QcContaminantSummary(JsonModel):
    """Stable contaminant burden summary for one run."""

    model_config = ConfigDict(extra="forbid")

    contaminant_psm_count: int = Field(..., ge=0)
    contaminant_psm_fraction: float = Field(..., ge=0.0, le=1.0)
    contaminant_peptide_count: int = Field(..., ge=0)
    contaminant_protein_count: int = Field(..., ge=0)
    contaminant_intensity: float = Field(..., ge=0.0)
    total_psm_intensity: float = Field(..., ge=0.0)
    contaminant_intensity_fraction: float = Field(..., ge=0.0, le=1.0)
    contaminant_protein_counts: dict[str, int] = Field(default_factory=dict)


class QcInstrumentSummary(JsonModel):
    """Stable instrument-facing summary for one LC-MS run."""

    model_config = ConfigDict(extra="forbid")

    instrument: str | None = None
    spectrum_count: int = Field(..., ge=0)
    spectra_with_precursor_charge: int = Field(..., ge=0)
    spectra_with_retention_time: int = Field(..., ge=0)
    acquisition_span_seconds: float | None = Field(default=None, ge=0.0)
    dominant_charge_label: str | None = None


class QcIdentificationSummary(JsonModel):
    """Stable identification-facing summary for one LC-MS run."""

    model_config = ConfigDict(extra="forbid")

    identified_spectrum_count: int = Field(..., ge=0)
    psm_count: int = Field(..., ge=0)
    identification_rate: float = Field(..., ge=0.0, le=1.0)
    matched_mass_error_psm_count: int = Field(..., ge=0)
    median_abs_mass_error_ppm: float | None = Field(default=None, ge=0.0)
    contaminant_psm_fraction: float = Field(..., ge=0.0, le=1.0)
    missed_cleavage_rate: float = Field(..., ge=0.0, le=1.0)


class QcQuantSummary(JsonModel):
    """Stable quantification-facing summary attached to one run-level QC bundle."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    entity_level: QuantEntityLevel
    observed_entity_count: int = Field(..., ge=0)
    zero_entity_count: int = Field(..., ge=0)
    filtered_entity_count: int = Field(..., ge=0)
    not_observed_entity_count: int = Field(..., ge=0)
    total_entity_count: int = Field(..., ge=0)
    observed_fraction: float = Field(..., ge=0.0, le=1.0)
    missing_fraction: float = Field(..., ge=0.0, le=1.0)
    median_observed_abundance: float | None = Field(default=None, ge=0.0)
    normalization_method: str = Field(..., min_length=1)


class QcDigestionSpecificityEntry(JsonModel):
    """One digestion-specificity bucket for identified peptides."""

    model_config = ConfigDict(extra="forbid")

    specificity: QcDigestionSpecificity
    count: int = Field(..., ge=0)
    fraction: float = Field(..., ge=0.0, le=1.0)


class QcContaminantPolicy(JsonModel):
    """Stable policy for contaminant classification from protein references."""

    model_config = ConfigDict(extra="forbid")

    prefixes: tuple[str, ...] = ("CON__",)
    substrings: tuple[str, ...] = ("KERATIN", "CONTAMINANT", "CRAP")


class QcAssessmentDisposition(StrEnum):
    """Whether a QC rule is advisory or enforced."""

    ADVISORY = "ADVISORY"
    ENFORCED = "ENFORCED"


class QcAssessmentSeverity(StrEnum):
    """Stable QC outcome severity."""

    PASSED = "PASS"
    WARNING = "WARN"
    FAILED = "FAIL"
    NOT_ASSESSED = "NOT_ASSESSED"


class QcStatus(StrEnum):
    """Operator-facing QC status for laboratory review and handoff."""

    PASSED = "pass"
    CAUTION = "caution"
    FAIL = "fail"


class QcStatusReasonSource(StrEnum):
    """Stable provenance for one operator-facing QC reason code."""

    METRIC = "metric"
    LAB = "lab"


class QcStatusReasonEntry(JsonModel):
    """One operator-facing non-pass reason with a stable code and message."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    status: QcStatus
    source: QcStatusReasonSource
    message: str = Field(..., min_length=1)

    @field_validator("code")
    @classmethod
    def _validate_code(cls, value: str) -> str:
        return require_registered_reason_code(
            value,
            ReasonCodeCategory.QC_REASON,
        )


class QcRunAnomalyCategory(StrEnum):
    """Stable anomaly categories for run-level QC summaries."""

    CHROMATOGRAPHY = "chromatography"
    IDENTIFICATION = "identification"
    QUANTIFICATION = "quantification"
    CONTAMINATION = "contamination"


class QcUnknownStateReason(StrEnum):
    """Stable reasons for QC metrics that cannot be computed."""

    NO_MATCHED_PSMS = "no_matched_psms"
    NO_BATCH_PEERS = "no_batch_peers"
    NO_MASS_ERROR_EVIDENCE = "no_mass_error_evidence"
    NO_RETENTION_TIME_EVIDENCE = "no_retention_time_evidence"


class QcThresholdRule(JsonModel):
    """One named threshold rule over a numeric QC metric."""

    model_config = ConfigDict(extra="forbid")

    metric_key: str = Field(..., min_length=1)
    metric_label: str = Field(..., min_length=1)
    unit: str | None = None
    lower_warn: float | None = None
    lower_fail: float | None = None
    upper_warn: float | None = None
    upper_fail: float | None = None
    disposition: QcAssessmentDisposition = QcAssessmentDisposition.ADVISORY
    description: str = ""


class QcThresholdPolicy(JsonModel):
    """Stable QC threshold policy document."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    policy_name: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    rules: tuple[QcThresholdRule, ...] = Field(default_factory=tuple)


class QcThresholdPolicyProfile(JsonModel):
    """Explicit separation of advisory and enforced QC policy rules."""

    model_config = ConfigDict(extra="forbid")

    policy_name: str = Field(..., min_length=1)
    policy_version: str = Field(..., min_length=1)
    advisory_rules: tuple[QcThresholdRule, ...] = Field(default_factory=tuple)
    enforced_rules: tuple[QcThresholdRule, ...] = Field(default_factory=tuple)


class QcMetricAssessment(JsonModel):
    """One measured QC metric evaluated against a threshold rule."""

    model_config = ConfigDict(extra="forbid")

    metric_key: str = Field(..., min_length=1)
    metric_label: str = Field(..., min_length=1)
    observed_value: float | None = None
    unit: str | None = None
    severity: QcAssessmentSeverity
    disposition: QcAssessmentDisposition
    threshold_rule: QcThresholdRule | None = None
    provenance: QcAssessmentProvenance | None = None
    unknown_state_reason: QcUnknownStateReason | None = None
    message: str = Field(..., min_length=1)
    enforced_violation: bool = False


class QcAssessmentProvenance(JsonModel):
    """Exact threshold provenance for one QC metric decision."""

    model_config = ConfigDict(extra="forbid")

    policy_name: str = Field(..., min_length=1)
    policy_version: str = Field(..., min_length=1)
    policy_sha256: str = Field(..., min_length=64, max_length=64)
    rule_sha256: str = Field(..., min_length=64, max_length=64)
    triggered_threshold: str | None = None
    lower_warn: float | None = None
    lower_fail: float | None = None
    upper_warn: float | None = None
    upper_fail: float | None = None


class QcRunAnomalyEntry(JsonModel):
    """One categorized run-level anomaly."""

    model_config = ConfigDict(extra="forbid")

    category: QcRunAnomalyCategory
    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    severity: QcAssessmentSeverity


class QcRunAssessmentReport(JsonModel):
    """Stable assessment payload for one run-level QC report."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    run_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    policy_name: str = Field(..., min_length=1)
    policy_version: str = Field(..., min_length=1)
    policy_sha256: str = Field(..., min_length=64, max_length=64)
    threshold_profile: QcThresholdPolicyProfile
    overall_severity: QcAssessmentSeverity
    qc_status: QcStatus
    blocked: bool = False
    advisory_failure_metric_keys: tuple[str, ...] = Field(default_factory=tuple)
    enforced_failure_metric_keys: tuple[str, ...] = Field(default_factory=tuple)
    status_reasons: tuple[QcStatusReasonEntry, ...] = Field(default_factory=tuple)
    metric_assessments: tuple[QcMetricAssessment, ...] = Field(default_factory=tuple)


class QcBatchAssessmentReport(JsonModel):
    """Stable assessment payload for one batch-level QC report."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    batch_id: str | None = None
    instrument: str | None = None
    policy_name: str = Field(..., min_length=1)
    policy_version: str = Field(..., min_length=1)
    policy_sha256: str = Field(..., min_length=64, max_length=64)
    threshold_profile: QcThresholdPolicyProfile
    overall_severity: QcAssessmentSeverity
    qc_status: QcStatus
    blocked: bool = False
    advisory_failure_metric_keys: tuple[str, ...] = Field(default_factory=tuple)
    enforced_failure_metric_keys: tuple[str, ...] = Field(default_factory=tuple)
    status_reasons: tuple[QcStatusReasonEntry, ...] = Field(default_factory=tuple)
    metric_assessments: tuple[QcMetricAssessment, ...] = Field(default_factory=tuple)


class QcEvidenceInputFile(JsonModel):
    """Stable source-file record for a QC evidence manifest."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=64, max_length=64)
    role: str = Field(..., min_length=1)


class ProteomicsPerformanceOperation(JsonModel):
    """One benchmarked operation within a production snapshot."""

    model_config = ConfigDict(extra="forbid")

    operation: str = Field(..., min_length=1)
    elapsed_seconds: float = Field(..., ge=0.0)
    item_count: int | None = Field(default=None, ge=0)
    throughput_per_second: float | None = Field(default=None, ge=0.0)


class ProteomicsPerformanceSnapshot(JsonModel):
    """Stable benchmark artifact over production-facing proteomics operations."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    run_id: str = Field(..., min_length=1)
    operations: tuple[ProteomicsPerformanceOperation, ...] = Field(
        default_factory=tuple
    )
    total_elapsed_seconds: float = Field(..., ge=0.0)


class QcEvidenceManifest(JsonModel):
    """Stable evidence manifest for one QC assessment run."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    run_id: str = Field(..., min_length=1)
    batch_id: str | None = None
    policy_name: str = Field(..., min_length=1)
    policy_version: str = Field(..., min_length=1)
    input_files: tuple[QcEvidenceInputFile, ...] = Field(default_factory=tuple)
    run_report_sha256: str = Field(..., min_length=64, max_length=64)
    run_assessment_sha256: str = Field(..., min_length=64, max_length=64)
    batch_report_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    batch_assessment_sha256: str | None = Field(
        default=None, min_length=64, max_length=64
    )
    benchmark_sha256: str | None = Field(default=None, min_length=64, max_length=64)


class LcmsRunQcReport(JsonModel):
    """Run-level LC-MS QC summary built from spectra and identifications."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    run_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    condition: str | None = None
    replicate: int | None = Field(default=None, ge=1)
    fraction: int | None = Field(default=None, ge=1)
    batch: str | None = None
    instrument: str | None = None
    design_metadata: dict[str, str] = Field(default_factory=dict)
    instrument_summary: QcInstrumentSummary
    identification_summary: QcIdentificationSummary
    quant_summary: QcQuantSummary | None = None
    run_anomalies: tuple[QcRunAnomalyEntry, ...] = Field(default_factory=tuple)
    spectrum_count: int = Field(..., ge=0)
    identified_spectrum_count: int = Field(..., ge=0)
    psm_count: int = Field(..., ge=0)
    identification_rate: float = Field(..., ge=0.0, le=1.0)
    spectrum_charge_distribution: tuple[QcChargeStateEntry, ...] = Field(
        default_factory=tuple
    )
    identified_charge_distribution: tuple[QcChargeStateEntry, ...] = Field(
        default_factory=tuple
    )
    mass_error: QcMassErrorSummary
    retention_time: QcRetentionTimeSummary
    missed_cleavage_count: int = Field(..., ge=0)
    missed_cleavage_rate: float = Field(..., ge=0.0, le=1.0)
    contaminant_summary: QcContaminantSummary
    protein_psm_counts: dict[str, int] = Field(default_factory=dict)
    digestion_specificity: tuple[QcDigestionSpecificityEntry, ...] = Field(
        default_factory=tuple
    )


class InstrumentBatchQcRunEntry(JsonModel):
    """One run scored against its batch peers."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    batch: str | None = None
    instrument: str | None = None
    spectrum_count: int = Field(..., ge=0)
    identification_rate: float = Field(..., ge=0.0, le=1.0)
    median_abs_mass_error_ppm: float | None = Field(default=None, ge=0.0)
    identified_retention_time_span_seconds: float | None = Field(default=None, ge=0.0)
    retention_time_shift_seconds: float | None = None
    outlier_reasons: tuple[str, ...] = Field(default_factory=tuple)


class InstrumentBatchQcReport(JsonModel):
    """Batch-level QC summary over multiple LC-MS runs."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    batch_id: str | None = None
    instrument: str | None = None
    run_count: int = Field(..., ge=0)
    median_spectrum_count: float = Field(..., ge=0.0)
    median_identification_rate: float = Field(..., ge=0.0, le=1.0)
    median_abs_mass_error_ppm: float | None = Field(default=None, ge=0.0)
    median_identified_retention_time_seconds: float | None = Field(default=None, ge=0.0)
    outlier_run_ids: tuple[str, ...] = Field(default_factory=tuple)
    runs: tuple[InstrumentBatchQcRunEntry, ...] = Field(default_factory=tuple)


class StudyQcConditionSummary(JsonModel):
    """Condition-level QC comparison summary within one study."""

    model_config = ConfigDict(extra="forbid")

    condition: str = Field(..., min_length=1)
    run_ids: tuple[str, ...] = Field(default_factory=tuple)
    median_identification_rate: float = Field(..., ge=0.0, le=1.0)
    median_spectrum_count: float = Field(..., ge=0.0)
    median_abs_mass_error_ppm: float | None = Field(default=None, ge=0.0)


class StudyQcBatchSummary(JsonModel):
    """Batch-level QC comparison summary within one study."""

    model_config = ConfigDict(extra="forbid")

    batch_id: str = Field(..., min_length=1)
    run_ids: tuple[str, ...] = Field(default_factory=tuple)
    median_identification_rate: float = Field(..., ge=0.0, le=1.0)
    median_spectrum_count: float = Field(..., ge=0.0)
    outlier_run_ids: tuple[str, ...] = Field(default_factory=tuple)


class StudyQcSummaryReport(JsonModel):
    """Study-level QC summary that compares runs across conditions and batches."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    study_id: str = Field(..., min_length=1)
    run_count: int = Field(..., ge=0)
    condition_summaries: tuple[StudyQcConditionSummary, ...] = Field(
        default_factory=tuple
    )
    batch_summaries: tuple[StudyQcBatchSummary, ...] = Field(default_factory=tuple)
    overall_identification_rate_span: float = Field(..., ge=0.0)
    overall_spectrum_count_span: float = Field(..., ge=0.0)


class QcRunBundleSummary(JsonModel):
    """Coherent run bundle summary joining QC, assessment, and evidence metadata."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    run_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    batch_id: str | None = None
    policy_name: str = Field(..., min_length=1)
    policy_version: str = Field(..., min_length=1)
    overall_severity: QcAssessmentSeverity
    qc_status: QcStatus
    blocked: bool = False
    identification_rate: float = Field(..., ge=0.0, le=1.0)
    contaminant_psm_fraction: float = Field(..., ge=0.0, le=1.0)
    quant_observed_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    anomaly_codes: tuple[str, ...] = Field(default_factory=tuple)
    status_reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    evidence_file_roles: tuple[str, ...] = Field(default_factory=tuple)
    evidence_file_paths: tuple[str, ...] = Field(default_factory=tuple)
    manifest_sha256s: dict[str, str] = Field(default_factory=dict)


class QcPublicationDecision(JsonModel):
    """Explicit publication or promotion gate derived from QC assessments."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    publish_allowed: bool = False
    promote_allowed: bool = False
    blocking_metric_keys: tuple[str, ...] = Field(default_factory=tuple)
    reason: str = Field(..., min_length=1)
    advisory_metric_keys: tuple[str, ...] = Field(default_factory=tuple)


__all__ = [
    "AcquisitionType",
    "DepletionMode",
    "EnrichmentType",
    "FractionationMode",
    "InstrumentBatchQcReport",
    "InstrumentBatchQcRunEntry",
    "LabelingMethod",
    "LcmsRunQcReport",
    "ProteomicsPerformanceOperation",
    "ProteomicsPerformanceSnapshot",
    "QcAssessmentDisposition",
    "QcAssessmentProvenance",
    "QcAssessmentSeverity",
    "QcBatchAssessmentReport",
    "QcChargeStateEntry",
    "QcContaminantPolicy",
    "QcContaminantSummary",
    "QcDigestionSpecificity",
    "QcDigestionSpecificityEntry",
    "QcEvidenceInputFile",
    "QcEvidenceManifest",
    "QcIdentificationSummary",
    "QcInstrumentSummary",
    "QcMassErrorSummary",
    "QcMetricAssessment",
    "QcPublicationDecision",
    "QcQuantSummary",
    "QcRetentionTimeSummary",
    "QcRunAnomalyCategory",
    "QcRunAnomalyEntry",
    "QcRunAssessmentReport",
    "QcRunBundleSummary",
    "QcStatus",
    "QcStatusReasonEntry",
    "QcStatusReasonSource",
    "QcThresholdPolicy",
    "QcThresholdPolicyProfile",
    "QcThresholdRule",
    "QcUnknownStateReason",
    "StudyQcBatchSummary",
    "StudyQcConditionSummary",
    "StudyQcSummaryReport",
]
