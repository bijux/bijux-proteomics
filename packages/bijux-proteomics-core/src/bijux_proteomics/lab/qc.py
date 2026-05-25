# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""LC-MS run quality-control and batch-diagnostic contracts."""

from __future__ import annotations

from collections import Counter
from enum import StrEnum
import hashlib
from pathlib import Path
from statistics import median

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.domain.reason_codes import (
    ReasonCodeCategory,
    require_registered_reason_code,
)
from bijux_proteomics.chemistry import calculate_peptide_mz
from bijux_proteomics.identification.contaminant_evidence import (
    build_contaminant_evidence_report,
)
from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.io.spectra import SpectrumModel, calculate_precursor_mass_error
from bijux_proteomics.quantification import (
    LabelFreeQuantTable,
    MissingValueKind,
    QuantEntityLevel,
)
from bijux_proteomics.lab.protocol_context import (
    AcquisitionType,
    DepletionMode,
    EnrichmentType,
    FractionationMode,
    LabProtocolContextEntry,
    LabelingMethod,
)
from bijux_proteomics.sequences.digestion import (
    ProteaseCleavageMode,
    ProteaseRule,
    count_missed_cleavages as count_sequence_missed_cleavages,
    get_protease_rule,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel, hash_model


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

    PASS = "pass"
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


def _build_document_schema(document_kind: str) -> DocumentSchema:
    return DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind=document_kind,
        package_name="bijux-proteomics-core",
        status="generated",
    )


def _stable_sha256(payload: JsonModel) -> str:
    return hash_model(payload)


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve_run_id(
    run_id: str | None, design_entry: ExperimentalDesignEntry | None
) -> str:
    if run_id:
        return run_id
    if design_entry and design_entry.spectra_file:
        return Path(design_entry.spectra_file).stem
    if design_entry and design_entry.sample_id:
        return f"{design_entry.sample_id}-run"
    return "run"


def _quantile(sorted_values: list[float], fraction: float) -> float:
    if not sorted_values:
        raise ValueError("cannot calculate a quantile for an empty sequence")
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * fraction
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    interpolation = position - lower_index
    return sorted_values[lower_index] + (
        (sorted_values[upper_index] - sorted_values[lower_index]) * interpolation
    )


def _fraction(count: int, total: int) -> float:
    return 0.0 if total == 0 else count / total


def _build_charge_distribution(
    counts: Counter[str], total: int
) -> tuple[QcChargeStateEntry, ...]:
    return tuple(
        QcChargeStateEntry(
            charge_label=label, count=count, fraction=_fraction(count, total)
        )
        for label, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _build_quant_summary(
    table: LabelFreeQuantTable | None,
    *,
    sample_id: str | None,
) -> QcQuantSummary | None:
    if table is None or sample_id is None or sample_id not in table.sample_ids:
        return None
    sample_values = [value for value in table.values if value.sample_id == sample_id]
    if not sample_values:
        return None
    observed_values = [
        float(value.abundance)
        for value in sample_values
        if value.abundance is not None
        and value.missing_value_kind
        in (MissingValueKind.OBSERVED, MissingValueKind.ZERO)
    ]
    zero_count = sum(
        1
        for value in sample_values
        if value.missing_value_kind is MissingValueKind.ZERO
    )
    filtered_count = sum(
        1
        for value in sample_values
        if value.missing_value_kind is MissingValueKind.FILTERED
    )
    not_observed_count = sum(
        1
        for value in sample_values
        if value.missing_value_kind is MissingValueKind.NOT_OBSERVED
    )
    observed_count = sum(
        1
        for value in sample_values
        if value.missing_value_kind
        in (MissingValueKind.OBSERVED, MissingValueKind.ZERO)
    )
    total_count = len(sample_values)
    return QcQuantSummary(
        sample_id=sample_id,
        entity_level=table.entity_level,
        observed_entity_count=observed_count,
        zero_entity_count=zero_count,
        filtered_entity_count=filtered_count,
        not_observed_entity_count=not_observed_count,
        total_entity_count=total_count,
        observed_fraction=_fraction(observed_count, total_count),
        missing_fraction=_fraction(filtered_count + not_observed_count, total_count),
        median_observed_abundance=None
        if not observed_values
        else median(observed_values),
        normalization_method=table.normalization_method.value,
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
        QcStatus.PASS: 0,
        QcStatus.CAUTION: 1,
        QcStatus.FAIL: 2,
    }[status]


def _status_from_severity(severity: QcAssessmentSeverity) -> QcStatus:
    if severity is QcAssessmentSeverity.FAILED:
        return QcStatus.FAIL
    if severity in (QcAssessmentSeverity.WARNING, QcAssessmentSeverity.NOT_ASSESSED):
        return QcStatus.CAUTION
    return QcStatus.PASS


def _metadata_reference_values(metadata: dict[str, str], key: str) -> tuple[str, ...]:
    value = metadata.get(key, "").strip()
    if not value:
        return ()
    return tuple(sorted({token.strip() for token in value.split(";") if token.strip()}))


def _metric_status_reason(assessment: QcMetricAssessment) -> QcStatusReasonEntry | None:
    status = _status_from_severity(assessment.severity)
    if status is QcStatus.PASS:
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
    non_specific_fraction = specificity_lookup.get(QcDigestionSpecificity.NON_SPECIFIC, 0.0)
    if run_report.missed_cleavage_rate >= 0.2 or non_specific_fraction >= 0.15:
        reasons.append(
            QcStatusReasonEntry(
                code="digestion_inefficiency",
                status=(
                    QcStatus.FAIL
                    if run_report.missed_cleavage_rate >= 0.35 or non_specific_fraction >= 0.25
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

    contamination_fraction = run_report.contaminant_summary.contaminant_intensity_fraction
    if contamination_fraction >= 0.05 or run_report.contaminant_summary.contaminant_psm_fraction >= 0.1:
        reasons.append(
            QcStatusReasonEntry(
                code="contamination_burden",
                status=QcStatus.FAIL if contamination_fraction >= 0.15 else QcStatus.CAUTION,
                source=QcStatusReasonSource.LAB,
                message=(
                    "contaminant intensity fraction "
                    f"{contamination_fraction:.4g} indicates meaningful contamination burden"
                ),
            )
        )

    carryover_refs = _metadata_reference_values(
        run_report.design_metadata, "carryover_marker_refs"
    )
    carryover_hits = tuple(
        sorted(ref for ref in carryover_refs if run_report.protein_psm_counts.get(ref, 0) > 0)
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

    expected_species_refs = _metadata_reference_values(
        run_report.design_metadata, "expected_species_marker_refs"
    )
    expected_species_hits = tuple(
        sorted(ref for ref in expected_species_refs if run_report.protein_psm_counts.get(ref, 0) > 0)
    )
    forbidden_species_hits = tuple(
        sorted(
            ref
            for ref in _metadata_reference_values(
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

    expected_sex_refs = _metadata_reference_values(
        run_report.design_metadata, "expected_sex_marker_refs"
    )
    expected_sex_hits = tuple(
        sorted(ref for ref in expected_sex_refs if run_report.protein_psm_counts.get(ref, 0) > 0)
    )
    forbidden_sex_hits = tuple(
        sorted(
            ref
            for ref in _metadata_reference_values(
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

    expected_enrichment_refs = _metadata_reference_values(
        run_report.design_metadata, "enrichment_marker_refs"
    )
    enrichment_hits = tuple(
        sorted(ref for ref in expected_enrichment_refs if run_report.protein_psm_counts.get(ref, 0) > 0)
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
            for ref in _metadata_reference_values(
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
                message="depletion markers remained visible: " + ", ".join(depletion_hits),
            )
        )

    unique_reasons: dict[tuple[str, str], QcStatusReasonEntry] = {}
    for reason in reasons:
        key = (reason.code, reason.message)
        incumbent = unique_reasons.get(key)
        if incumbent is None or _status_rank(reason.status) > _status_rank(incumbent.status):
            unique_reasons[key] = reason
    return tuple(
        sorted(
            unique_reasons.values(),
            key=lambda entry: (_status_rank(entry.status), entry.source.value, entry.code),
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


def _format_metric_value(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _build_run_anomalies(
    *,
    identification_rate: float,
    mass_error_summary: QcMassErrorSummary,
    retention_summary: QcRetentionTimeSummary,
    quant_summary: QcQuantSummary | None,
    contaminant_summary: QcContaminantSummary,
) -> tuple[QcRunAnomalyEntry, ...]:
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
            rule_sha256=_stable_sha256(rule),
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
        document_schema=_build_document_schema("qc_threshold_policy"),
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
                rule.model_copy(
                    update=thresholds_by_metric.get(rule.metric_key, {})
                )
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
    policy_sha256 = _stable_sha256(policy)
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
        document_schema=_build_document_schema("qc_run_assessment_report"),
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
    policy_sha256 = _stable_sha256(batch_policy)
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
        document_schema=_build_document_schema("qc_batch_assessment_report"),
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


def build_qc_evidence_manifest(
    *,
    run_report: LcmsRunQcReport,
    run_assessment: QcRunAssessmentReport,
    policy: QcThresholdPolicy,
    input_files: tuple[QcEvidenceInputFile, ...],
    batch_report: InstrumentBatchQcReport | None = None,
    batch_assessment: QcBatchAssessmentReport | None = None,
    benchmark: ProteomicsPerformanceSnapshot | None = None,
) -> QcEvidenceManifest:
    """Build a stable manifest binding QC outputs to input hashes and policy."""
    return QcEvidenceManifest(
        document_schema=_build_document_schema("qc_evidence_manifest"),
        run_id=run_report.run_id,
        batch_id=batch_report.batch_id if batch_report else run_report.batch,
        policy_name=policy.policy_name,
        policy_version=policy.version,
        input_files=input_files,
        run_report_sha256=_stable_sha256(run_report),
        run_assessment_sha256=_stable_sha256(run_assessment),
        batch_report_sha256=None
        if batch_report is None
        else _stable_sha256(batch_report),
        batch_assessment_sha256=None
        if batch_assessment is None
        else _stable_sha256(batch_assessment),
        benchmark_sha256=None if benchmark is None else _stable_sha256(benchmark),
    )


def build_qc_run_bundle_summary(
    *,
    run_report: LcmsRunQcReport,
    run_assessment: QcRunAssessmentReport,
    evidence_manifest: QcEvidenceManifest,
) -> QcRunBundleSummary:
    """Join run QC, assessment, and evidence metadata into one review summary."""
    manifest_sha256s = {
        "run_report": evidence_manifest.run_report_sha256,
        "run_assessment": evidence_manifest.run_assessment_sha256,
    }
    if evidence_manifest.batch_report_sha256:
        manifest_sha256s["batch_report"] = evidence_manifest.batch_report_sha256
    if evidence_manifest.batch_assessment_sha256:
        manifest_sha256s["batch_assessment"] = evidence_manifest.batch_assessment_sha256
    if evidence_manifest.benchmark_sha256:
        manifest_sha256s["benchmark"] = evidence_manifest.benchmark_sha256
    return QcRunBundleSummary(
        document_schema=_build_document_schema("qc_run_bundle_summary"),
        run_id=run_report.run_id,
        sample_id=run_report.sample_id,
        batch_id=evidence_manifest.batch_id or run_report.batch,
        policy_name=run_assessment.policy_name,
        policy_version=run_assessment.policy_version,
        overall_severity=run_assessment.overall_severity,
        qc_status=run_assessment.qc_status,
        blocked=run_assessment.blocked,
        identification_rate=run_report.identification_rate,
        contaminant_psm_fraction=run_report.contaminant_summary.contaminant_psm_fraction,
        quant_observed_fraction=None
        if run_report.quant_summary is None
        else run_report.quant_summary.observed_fraction,
        anomaly_codes=tuple(sorted(entry.code for entry in run_report.run_anomalies)),
        status_reason_codes=tuple(
            sorted({entry.code for entry in run_assessment.status_reasons})
        ),
        evidence_file_roles=tuple(
            sorted(entry.role for entry in evidence_manifest.input_files)
        ),
        evidence_file_paths=tuple(
            sorted(entry.path for entry in evidence_manifest.input_files)
        ),
        manifest_sha256s=manifest_sha256s,
    )


def build_qc_publication_decision(
    *,
    run_assessment: QcRunAssessmentReport,
    batch_assessment: QcBatchAssessmentReport | None = None,
) -> QcPublicationDecision:
    """Refuse publication or promotion when mandatory QC gates fail."""
    blocking_metric_keys = list(run_assessment.enforced_failure_metric_keys)
    advisory_metric_keys = list(run_assessment.advisory_failure_metric_keys)
    if batch_assessment is not None:
        blocking_metric_keys.extend(batch_assessment.enforced_failure_metric_keys)
        advisory_metric_keys.extend(batch_assessment.advisory_failure_metric_keys)
    blocking_metric_keys = sorted(set(blocking_metric_keys))
    advisory_metric_keys = sorted(set(advisory_metric_keys))
    if blocking_metric_keys:
        reason = "mandatory qc gates failed for metrics: " + ", ".join(
            blocking_metric_keys
        )
        return QcPublicationDecision(
            run_id=run_assessment.run_id,
            publish_allowed=False,
            promote_allowed=False,
            blocking_metric_keys=tuple(blocking_metric_keys),
            reason=reason,
            advisory_metric_keys=tuple(advisory_metric_keys),
        )
    return QcPublicationDecision(
        run_id=run_assessment.run_id,
        publish_allowed=True,
        promote_allowed=True,
        blocking_metric_keys=(),
        reason="mandatory qc gates passed",
        advisory_metric_keys=tuple(advisory_metric_keys),
    )


def build_performance_snapshot(
    run_id: str,
    *,
    operations: dict[str, tuple[float, int | None]],
) -> ProteomicsPerformanceSnapshot:
    """Build a stable performance snapshot from named elapsed operations."""
    entries: list[ProteomicsPerformanceOperation] = []
    total_elapsed_seconds = 0.0
    for operation_name, (elapsed_seconds, item_count) in sorted(operations.items()):
        total_elapsed_seconds += elapsed_seconds
        throughput = None
        if item_count is not None and elapsed_seconds > 0:
            throughput = item_count / elapsed_seconds
        entries.append(
            ProteomicsPerformanceOperation(
                operation=operation_name,
                elapsed_seconds=elapsed_seconds,
                item_count=item_count,
                throughput_per_second=throughput,
            )
        )
    return ProteomicsPerformanceSnapshot(
        document_schema=_build_document_schema("proteomics_performance_snapshot"),
        run_id=run_id,
        operations=tuple(entries),
        total_elapsed_seconds=total_elapsed_seconds,
    )


def render_qc_assessment_tsv(
    run_assessment: QcRunAssessmentReport,
    *,
    batch_assessment: QcBatchAssessmentReport | None = None,
) -> str:
    """Render QC assessment rows as a TSV string."""
    rows = [
        [
            "scope",
            "entity_id",
            "qc_status",
            "status_reason_codes",
            "metric_key",
            "metric_label",
            "observed_value",
            "unit",
            "severity",
            "disposition",
            "enforced_violation",
            "message",
        ]
    ]
    for assessment in run_assessment.metric_assessments:
        rows.append(
            [
                "run",
                run_assessment.run_id,
                run_assessment.qc_status.value,
                ";".join(reason.code for reason in run_assessment.status_reasons),
                assessment.metric_key,
                assessment.metric_label,
                _format_metric_value(assessment.observed_value),
                assessment.unit or "",
                assessment.severity.value,
                assessment.disposition.value,
                "true" if assessment.enforced_violation else "false",
                assessment.message,
            ]
        )
    if batch_assessment is not None:
        entity_id = batch_assessment.batch_id or "batch"
        for assessment in batch_assessment.metric_assessments:
            rows.append(
                [
                    "batch",
                    entity_id,
                    batch_assessment.qc_status.value,
                    ";".join(reason.code for reason in batch_assessment.status_reasons),
                    assessment.metric_key,
                    assessment.metric_label,
                    _format_metric_value(assessment.observed_value),
                    assessment.unit or "",
                    assessment.severity.value,
                    assessment.disposition.value,
                    "true" if assessment.enforced_violation else "false",
                    assessment.message,
                ]
            )
    return "\n".join("\t".join(row) for row in rows) + "\n"


def render_qc_assessment_html(
    run_report: LcmsRunQcReport,
    run_assessment: QcRunAssessmentReport,
    *,
    batch_report: InstrumentBatchQcReport | None = None,
    batch_assessment: QcBatchAssessmentReport | None = None,
) -> str:
    """Render a compact static HTML QC report."""
    rows = []
    for assessment in run_assessment.metric_assessments:
        rows.append(
            "<tr>"
            f"<td>run</td><td>{run_assessment.run_id}</td><td>{run_assessment.qc_status.value}</td><td>{'; '.join(reason.code for reason in run_assessment.status_reasons) or 'none'}</td><td>{assessment.metric_label}</td>"
            f"<td>{_format_metric_value(assessment.observed_value)}</td>"
            f"<td>{assessment.severity.value}</td><td>{assessment.disposition.value}</td><td>{assessment.message}</td>"
            "</tr>"
        )
    if batch_assessment is not None:
        entity_id = batch_assessment.batch_id or "batch"
        for assessment in batch_assessment.metric_assessments:
            rows.append(
                "<tr>"
                f"<td>batch</td><td>{entity_id}</td><td>{batch_assessment.qc_status.value}</td><td>{'; '.join(reason.code for reason in batch_assessment.status_reasons) or 'none'}</td><td>{assessment.metric_label}</td>"
                f"<td>{_format_metric_value(assessment.observed_value)}</td>"
                f"<td>{assessment.severity.value}</td><td>{assessment.disposition.value}</td><td>{assessment.message}</td>"
                "</tr>"
            )
    batch_summary = ""
    if batch_report is not None:
        batch_summary = (
            f"<p><strong>Batch</strong>: {batch_report.batch_id or 'n/a'} | "
            f"<strong>Instrument</strong>: {batch_report.instrument or 'n/a'} | "
            f"<strong>Outliers</strong>: {', '.join(batch_report.outlier_run_ids) or 'none'}</p>"
        )
    return (
        "<html><head><title>Bijux Proteomics QC Report</title></head><body>"
        f"<h1>QC report for {run_report.run_id}</h1>"
        f"<p><strong>Sample</strong>: {run_report.sample_id or 'n/a'} | "
        f"<strong>Overall</strong>: {run_assessment.overall_severity.value} | "
        f"<strong>Status</strong>: {run_assessment.qc_status.value} | "
        f"<strong>Blocked</strong>: {'yes' if run_assessment.blocked else 'no'}</p>"
        f"{batch_summary}"
        "<table border='1' cellspacing='0' cellpadding='4'>"
        "<thead><tr><th>Scope</th><th>Entity</th><th>Status</th><th>Reason codes</th><th>Metric</th><th>Observed</th><th>Severity</th><th>Disposition</th><th>Message</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        "</body></html>\n"
    )


def _is_contaminant_reference(reference: str, policy: QcContaminantPolicy) -> bool:
    normalized = reference.strip().upper()
    return normalized.startswith(
        tuple(prefix.upper() for prefix in policy.prefixes)
    ) or any(token.upper() in normalized for token in policy.substrings)


def _count_missed_cleavages(sequence: str, rule: ProteaseRule) -> int:
    return count_sequence_missed_cleavages(sequence, rule)


def _boundary_valid(
    protein_sequence: str,
    *,
    peptide_start: int,
    peptide_end: int,
    rule: ProteaseRule,
) -> tuple[bool, bool]:
    sequence_length = len(protein_sequence)
    if rule.cleavage_mode is ProteaseCleavageMode.C_TERMINAL:
        if peptide_start == 1:
            left_valid = True
        else:
            left_residue = protein_sequence[peptide_start - 2]
            first_peptide_residue = protein_sequence[peptide_start - 1]
            left_valid = (
                left_residue in rule.cleavage_residues
                and first_peptide_residue not in rule.blocked_by_next
            )
        if peptide_end == sequence_length:
            right_valid = True
        else:
            last_peptide_residue = protein_sequence[peptide_end - 1]
            right_neighbor = protein_sequence[peptide_end]
            right_valid = (
                last_peptide_residue in rule.cleavage_residues
                and right_neighbor not in rule.blocked_by_next
            )
        return left_valid, right_valid

    if peptide_start == 1:
        left_valid = True
    else:
        left_neighbor = protein_sequence[peptide_start - 2]
        first_peptide_residue = protein_sequence[peptide_start - 1]
        left_valid = (
            first_peptide_residue in rule.cleavage_residues
            and left_neighbor not in rule.blocked_by_previous
        )
    if peptide_end == sequence_length:
        right_valid = True
    else:
        last_peptide_residue = protein_sequence[peptide_end - 1]
        right_neighbor = protein_sequence[peptide_end]
        right_valid = (
            right_neighbor in rule.cleavage_residues
            and last_peptide_residue not in rule.blocked_by_previous
        )
    return left_valid, right_valid


def _classify_specificity(
    peptide_sequence: str,
    protein_refs: tuple[str, ...],
    protein_sequences: dict[str, str],
    rule: ProteaseRule,
) -> QcDigestionSpecificity:
    best = QcDigestionSpecificity.NON_SPECIFIC
    for protein_ref in protein_refs:
        protein_sequence = protein_sequences.get(protein_ref)
        if not protein_sequence:
            continue
        offset = protein_sequence.find(peptide_sequence)
        while offset != -1:
            start = offset + 1
            end = offset + len(peptide_sequence)
            left_valid, right_valid = _boundary_valid(
                protein_sequence,
                peptide_start=start,
                peptide_end=end,
                rule=rule,
            )
            if left_valid and right_valid:
                return QcDigestionSpecificity.ENZYMATIC
            if left_valid or right_valid:
                best = QcDigestionSpecificity.SEMI_SPECIFIC
            offset = protein_sequence.find(peptide_sequence, offset + 1)
    return best


def build_lcms_run_qc_report(
    spectra: tuple[SpectrumModel, ...],
    psm_records: tuple[PsmRecord, ...],
    *,
    design_entry: ExperimentalDesignEntry | None = None,
    protein_sequences: dict[str, str] | None = None,
    quant_table: LabelFreeQuantTable | None = None,
    protease: ProteaseRule | str = "trypsin",
    run_id: str | None = None,
    contaminant_policy: QcContaminantPolicy | None = None,
) -> LcmsRunQcReport:
    """Build a typed QC report for one LC-MS run."""
    active_rule = get_protease_rule(protease) if isinstance(protease, str) else protease
    active_contaminant_policy = contaminant_policy or QcContaminantPolicy()
    spectra_by_id = {spectrum.spectrum_id: spectrum for spectrum in spectra}
    identified_spectrum_ids = {record.spectrum_id for record in psm_records}

    spectrum_charge_counts: Counter[str] = Counter()
    for spectrum in spectra:
        label = (
            "unknown"
            if spectrum.precursor_charge is None
            else str(spectrum.precursor_charge)
        )
        spectrum_charge_counts[label] += 1

    identified_charge_counts: Counter[str] = Counter(
        str(record.charge) for record in psm_records
    )

    mass_errors_ppm: list[float] = []
    for record in psm_records:
        candidate_spectrum = spectra_by_id.get(record.spectrum_id)
        if candidate_spectrum is None:
            continue
        spectrum = candidate_spectrum
        theoretical_mz = calculate_peptide_mz(record.peptide, charge=record.charge)
        mass_error = calculate_precursor_mass_error(
            observed_mz=spectrum.precursor_mz,
            theoretical_mz=theoretical_mz,
        )
        mass_errors_ppm.append(mass_error.delta_ppm)

    sorted_abs_mass_errors = sorted(abs(value) for value in mass_errors_ppm)
    mass_error_summary = QcMassErrorSummary(
        matched_psm_count=len(mass_errors_ppm),
        mean_ppm=None
        if not mass_errors_ppm
        else sum(mass_errors_ppm) / len(mass_errors_ppm),
        median_ppm=None if not mass_errors_ppm else median(mass_errors_ppm),
        median_abs_ppm=None
        if not sorted_abs_mass_errors
        else median(sorted_abs_mass_errors),
        p95_abs_ppm=None
        if not sorted_abs_mass_errors
        else _quantile(sorted_abs_mass_errors, 0.95),
        max_abs_ppm=None if not sorted_abs_mass_errors else max(sorted_abs_mass_errors),
    )

    retention_times = sorted(
        spectrum.retention_time_seconds
        for spectrum in spectra
        if spectrum.retention_time_seconds is not None
    )
    identified_retention_times: list[float] = sorted(
        retention_time
        for record in psm_records
        for spectrum in [spectra_by_id.get(record.spectrum_id)]
        if spectrum is not None
        for retention_time in [spectrum.retention_time_seconds]
        if retention_time is not None
    )
    retention_summary = QcRetentionTimeSummary(
        spectra_with_retention_time=len(retention_times),
        identified_with_retention_time=len(identified_retention_times),
        min_retention_time_seconds=None if not retention_times else retention_times[0],
        max_retention_time_seconds=None if not retention_times else retention_times[-1],
        span_seconds=None
        if len(retention_times) < 2
        else retention_times[-1] - retention_times[0],
        identified_min_retention_time_seconds=None
        if not identified_retention_times
        else identified_retention_times[0],
        identified_max_retention_time_seconds=None
        if not identified_retention_times
        else identified_retention_times[-1],
        identified_span_seconds=None
        if len(identified_retention_times) < 2
        else identified_retention_times[-1] - identified_retention_times[0],
        identified_median_retention_time_seconds=None
        if not identified_retention_times
        else median(identified_retention_times),
    )

    missed_cleavage_count = sum(
        _count_missed_cleavages(record.canonical_peptide, active_rule)
        for record in psm_records
    )
    resolved_run_id = _resolve_run_id(run_id, design_entry)
    sample_id = design_entry.sample_id if design_entry else None
    qc_psm_records = tuple(
        record
        if record.run_id
        else record.model_copy(update={"run_id": resolved_run_id})
        for record in psm_records
    )

    contaminant_report = build_contaminant_evidence_report(
        qc_psm_records,
        contaminant_prefixes=active_contaminant_policy.prefixes,
        sample_id_by_run={} if sample_id is None else {resolved_run_id: sample_id},
    )
    run_burden = next(
        (
            entry
            for entry in contaminant_report.burden_entries
            if entry.run_id == resolved_run_id
        ),
        None,
    )
    contaminant_summary = QcContaminantSummary(
        contaminant_psm_count=0 if run_burden is None else run_burden.contaminant_psm_count,
        contaminant_psm_fraction=0.0
        if run_burden is None
        else run_burden.contaminant_psm_fraction,
        contaminant_peptide_count=0
        if run_burden is None
        else run_burden.contaminant_peptide_count,
        contaminant_protein_count=0
        if run_burden is None
        else run_burden.contaminant_protein_count,
        contaminant_intensity=0.0
        if run_burden is None
        else run_burden.contaminant_intensity,
        total_psm_intensity=0.0 if run_burden is None else run_burden.total_intensity,
        contaminant_intensity_fraction=0.0
        if run_burden is None
        else run_burden.contaminant_intensity_fraction,
        contaminant_protein_counts={
            entry.protein_ref: entry.psm_count for entry in contaminant_report.protein_entries
        },
    )

    specificity_counts: Counter[QcDigestionSpecificity] = Counter()
    sequence_lookup = protein_sequences or {}
    for record in psm_records:
        specificity = _classify_specificity(
            record.canonical_peptide,
            record.protein_refs,
            sequence_lookup,
            active_rule,
        )
        specificity_counts[specificity] += 1
    digestion_specificity = tuple(
        QcDigestionSpecificityEntry(
            specificity=specificity,
            count=specificity_counts.get(specificity, 0),
            fraction=_fraction(
                specificity_counts.get(specificity, 0), len(psm_records)
            ),
        )
        for specificity in (
            QcDigestionSpecificity.ENZYMATIC,
            QcDigestionSpecificity.SEMI_SPECIFIC,
            QcDigestionSpecificity.NON_SPECIFIC,
        )
    )

    instrument_summary = QcInstrumentSummary(
        instrument=design_entry.instrument if design_entry else None,
        spectrum_count=len(spectra),
        spectra_with_precursor_charge=sum(
            1 for spectrum in spectra if spectrum.precursor_charge is not None
        ),
        spectra_with_retention_time=len(retention_times),
        acquisition_span_seconds=retention_summary.span_seconds,
        dominant_charge_label=(
            max(
                spectrum_charge_counts.items(),
                key=lambda item: (item[1], item[0]),
            )[0]
            if spectrum_charge_counts
            else None
        ),
    )
    identified_spectrum_count = len(identified_spectrum_ids & set(spectra_by_id))
    identification_rate = _fraction(identified_spectrum_count, len(spectra))
    identification_summary = QcIdentificationSummary(
        identified_spectrum_count=identified_spectrum_count,
        psm_count=len(psm_records),
        identification_rate=identification_rate,
        matched_mass_error_psm_count=len(mass_errors_ppm),
        median_abs_mass_error_ppm=mass_error_summary.median_abs_ppm,
        contaminant_psm_fraction=contaminant_summary.contaminant_psm_fraction,
        missed_cleavage_rate=_fraction(missed_cleavage_count, len(psm_records)),
    )
    quant_summary = _build_quant_summary(quant_table, sample_id=sample_id)
    return LcmsRunQcReport(
        document_schema=_build_document_schema("lcms_run_qc_report"),
        run_id=resolved_run_id,
        sample_id=sample_id,
        condition=design_entry.condition if design_entry else None,
        replicate=design_entry.replicate if design_entry else None,
        fraction=design_entry.fraction if design_entry else None,
        batch=design_entry.batch if design_entry else None,
        instrument=design_entry.instrument if design_entry else None,
        design_metadata={} if design_entry is None else dict(sorted(design_entry.metadata.items())),
        instrument_summary=instrument_summary,
        identification_summary=identification_summary,
        quant_summary=quant_summary,
        run_anomalies=_build_run_anomalies(
            identification_rate=identification_rate,
            mass_error_summary=mass_error_summary,
            retention_summary=retention_summary,
            quant_summary=quant_summary,
            contaminant_summary=contaminant_summary,
        ),
        spectrum_count=len(spectra),
        identified_spectrum_count=identified_spectrum_count,
        psm_count=len(psm_records),
        identification_rate=identification_rate,
        spectrum_charge_distribution=_build_charge_distribution(
            spectrum_charge_counts, len(spectra)
        ),
        identified_charge_distribution=_build_charge_distribution(
            identified_charge_counts, len(psm_records)
        ),
        mass_error=mass_error_summary,
        retention_time=retention_summary,
        missed_cleavage_count=missed_cleavage_count,
        missed_cleavage_rate=_fraction(missed_cleavage_count, len(psm_records)),
        contaminant_summary=contaminant_summary,
        protein_psm_counts=dict(
            sorted(Counter(ref for record in psm_records for ref in record.protein_refs).items())
        ),
        digestion_specificity=digestion_specificity,
    )


def build_instrument_batch_qc_report(
    run_reports: tuple[LcmsRunQcReport, ...],
    *,
    batch_id: str | None = None,
    instrument: str | None = None,
    identification_rate_floor_ratio: float = 0.85,
    spectrum_count_floor_ratio: float = 0.8,
    median_abs_mass_error_multiplier: float = 2.0,
) -> InstrumentBatchQcReport:
    """Build a typed batch-level QC summary and outlier flags."""
    if not run_reports:
        raise ValueError("batch QC requires at least one run report")

    resolved_batch_id = batch_id
    if resolved_batch_id is None:
        batch_ids = {report.batch for report in run_reports if report.batch}
        resolved_batch_id = next(iter(batch_ids)) if len(batch_ids) == 1 else None
    resolved_instrument = instrument
    if resolved_instrument is None:
        instruments = {report.instrument for report in run_reports if report.instrument}
        resolved_instrument = next(iter(instruments)) if len(instruments) == 1 else None

    spectrum_count_values = [report.spectrum_count for report in run_reports]
    identification_rate_values = [report.identification_rate for report in run_reports]
    median_spectrum_count = float(median(spectrum_count_values))
    median_identification_rate = float(median(identification_rate_values))

    median_abs_mass_error_values = [
        report.mass_error.median_abs_ppm
        for report in run_reports
        if report.mass_error.median_abs_ppm is not None
    ]
    median_abs_mass_error_ppm = (
        None
        if not median_abs_mass_error_values
        else float(median(median_abs_mass_error_values))
    )
    identified_median_rt_values = [
        report.retention_time.identified_median_retention_time_seconds
        for report in run_reports
        if report.retention_time.identified_median_retention_time_seconds is not None
    ]
    median_identified_retention_time_seconds = (
        None
        if not identified_median_rt_values
        else float(median(identified_median_rt_values))
    )

    run_entries: list[InstrumentBatchQcRunEntry] = []
    outlier_run_ids: list[str] = []
    for report in sorted(run_reports, key=lambda item: item.run_id):
        reasons: list[str] = []
        if median_spectrum_count > 0 and report.spectrum_count < (
            median_spectrum_count * spectrum_count_floor_ratio
        ):
            reasons.append("low_spectrum_count")
        if median_identification_rate > 0 and report.identification_rate < (
            median_identification_rate * identification_rate_floor_ratio
        ):
            reasons.append("low_identification_rate")
        if (
            median_abs_mass_error_ppm is not None
            and report.mass_error.median_abs_ppm is not None
            and report.mass_error.median_abs_ppm
            > max(5.0, median_abs_mass_error_ppm * median_abs_mass_error_multiplier)
        ):
            reasons.append("high_mass_error")
        retention_time_shift_seconds = None
        if (
            median_identified_retention_time_seconds is not None
            and report.retention_time.identified_median_retention_time_seconds
            is not None
        ):
            retention_time_shift_seconds = (
                report.retention_time.identified_median_retention_time_seconds
                - median_identified_retention_time_seconds
            )
        if reasons:
            outlier_run_ids.append(report.run_id)
        run_entries.append(
            InstrumentBatchQcRunEntry(
                run_id=report.run_id,
                sample_id=report.sample_id,
                batch=report.batch,
                instrument=report.instrument,
                spectrum_count=report.spectrum_count,
                identification_rate=report.identification_rate,
                median_abs_mass_error_ppm=report.mass_error.median_abs_ppm,
                identified_retention_time_span_seconds=report.retention_time.identified_span_seconds,
                retention_time_shift_seconds=retention_time_shift_seconds,
                outlier_reasons=tuple(reasons),
            )
        )

    return InstrumentBatchQcReport(
        document_schema=_build_document_schema("instrument_batch_qc_report"),
        batch_id=resolved_batch_id,
        instrument=resolved_instrument,
        run_count=len(run_reports),
        median_spectrum_count=median_spectrum_count,
        median_identification_rate=median_identification_rate,
        median_abs_mass_error_ppm=median_abs_mass_error_ppm,
        median_identified_retention_time_seconds=median_identified_retention_time_seconds,
        outlier_run_ids=tuple(sorted(outlier_run_ids)),
        runs=tuple(run_entries),
    )


def build_study_qc_summary(
    run_reports: tuple[LcmsRunQcReport, ...],
    *,
    study_id: str = "study",
) -> StudyQcSummaryReport:
    """Build a study-level QC summary across conditions and batches."""
    if not run_reports:
        raise ValueError("study QC summary requires at least one run report")

    condition_groups: dict[str, list[LcmsRunQcReport]] = {}
    batch_groups: dict[str, list[LcmsRunQcReport]] = {}
    for report in run_reports:
        condition_groups.setdefault(report.condition or "unknown", []).append(report)
        batch_groups.setdefault(report.batch or "unbatched", []).append(report)

    condition_summaries = tuple(
        StudyQcConditionSummary(
            condition=condition,
            run_ids=tuple(sorted(report.run_id for report in reports)),
            median_identification_rate=float(
                median([report.identification_rate for report in reports])
            ),
            median_spectrum_count=float(
                median([report.spectrum_count for report in reports])
            ),
            median_abs_mass_error_ppm=(
                None
                if not [
                    report.mass_error.median_abs_ppm
                    for report in reports
                    if report.mass_error.median_abs_ppm is not None
                ]
                else float(
                    median(
                        [
                            report.mass_error.median_abs_ppm
                            for report in reports
                            if report.mass_error.median_abs_ppm is not None
                        ]
                    )
                )
            ),
        )
        for condition, reports in sorted(condition_groups.items())
    )

    batch_summaries = tuple(
        StudyQcBatchSummary(
            batch_id=batch_id,
            run_ids=tuple(sorted(report.run_id for report in reports)),
            median_identification_rate=float(
                median([report.identification_rate for report in reports])
            ),
            median_spectrum_count=float(
                median([report.spectrum_count for report in reports])
            ),
            outlier_run_ids=tuple(
                sorted(
                    build_instrument_batch_qc_report(
                        tuple(reports), batch_id=batch_id
                    ).outlier_run_ids
                )
            ),
        )
        for batch_id, reports in sorted(batch_groups.items())
    )

    identification_rates = [report.identification_rate for report in run_reports]
    spectrum_counts = [float(report.spectrum_count) for report in run_reports]
    return StudyQcSummaryReport(
        document_schema=_build_document_schema("study_qc_summary_report"),
        study_id=study_id,
        run_count=len(run_reports),
        condition_summaries=condition_summaries,
        batch_summaries=batch_summaries,
        overall_identification_rate_span=max(identification_rates)
        - min(identification_rates),
        overall_spectrum_count_span=max(spectrum_counts) - min(spectrum_counts),
    )
