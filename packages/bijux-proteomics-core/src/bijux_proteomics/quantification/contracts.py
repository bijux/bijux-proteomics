# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Label-free quantification and differential abundance contracts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
import hashlib
import math
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics.chemistry import (
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.domain.records import (
    MissingValueState as CanonicalMissingValueState,
    QuantEntityKind as CanonicalQuantEntityKind,
    QuantMatrix as CanonicalQuantMatrix,
    QuantMeasureKind as CanonicalQuantMeasureKind,
)
from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    ExperimentalDesignSampleRole,
)
from bijux_proteomics.quantification.core_matrix import (
    build_numeric_quant_matrix,
    iter_quant_matrix_cells,
    quant_matrix_to_dense_array,
    rebuild_quant_matrix_from_dense_array,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.study.sample_run_identity import SampleRunAnalysisPolicy


class QuantEntityLevel(StrEnum):
    """Supported quantification aggregation levels."""

    PEPTIDE = "peptide"
    PROTEIN = "protein"


class QuantMeasureKind(StrEnum):
    """Supported quantification measurement kinds."""

    INTENSITY = "intensity"
    SPECTRAL_COUNT = "spectral_count"


class MissingValueKind(StrEnum):
    """Stable distinction between absent, zero, and filtered quant values."""

    OBSERVED = "observed"
    ZERO = "zero"
    NOT_OBSERVED = "missing_not_observed"
    FILTERED = "filtered"


class QuantRollupMethod(StrEnum):
    """Supported peptide-to-protein quant rollup policies."""

    SUM = "sum"
    MEDIAN = "median"
    TOP_N = "top_n"


class NormalizationMethod(StrEnum):
    """Supported label-free normalization methods."""

    NONE = "none"
    TIC = "tic"
    MEDIAN = "median"
    QUANTILE = "quantile"
    LOG2_MEDIAN_CENTERING = "log2_median_centering"
    VSN_LIKE = "vsn_like"


class ImputationMethod(StrEnum):
    """Supported label-free missing-value imputation methods."""

    NONE = "none"
    LOW_INTENSITY = "low_intensity"
    GROUP_AWARE_LOW_INTENSITY = "group_aware_low_intensity"
    KNN = "knn"


class QuantAssessmentDisposition(StrEnum):
    """Whether a quantification report changes behavior or remains advisory."""

    ENFORCED = "ENFORCED"
    ADVISORY = "ADVISORY"


class MissingValueCorrectionPolicy(StrEnum):
    """Deterministic remapping policy for missing-value summary categories."""

    PRESERVE = "preserve"
    TREAT_AS_NOT_OBSERVED = "treat_as_not_observed"


class MissingChannelPolicy(StrEnum):
    """Policy for expected multiplex channels that are absent from a run."""

    PRESERVE = "preserve"
    TREAT_AS_MISSING = "treat_as_missing"
    ERROR = "error"


class LabelBasedChannelRole(StrEnum):
    """Stable role classification for multiplex quantification channels."""

    SAMPLE = "sample"
    CARRIER = "carrier"
    REFERENCE = "reference"
    QC_BRIDGE = "qc_bridge"


class Ms1FeatureColumnMapping(JsonModel):
    """User-supplied mapping from feature-table columns to the quant contract."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    intensity: str = Field(..., min_length=1)
    protein_refs: str | None = None
    feature_id: str | None = None
    charge: str | None = None
    mz: str | None = None
    retention_time_seconds: str | None = None
    missing_reason: str | None = None
    protein_separator: str = ";"


class QuantValidationIssue(JsonModel):
    """One validation issue while parsing feature quantification input."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=2)


class RejectedMs1FeatureRow(JsonModel):
    """One rejected MS1 feature row with stable issue details."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[QuantValidationIssue, ...] = Field(default_factory=tuple)


class Ms1FeatureRecord(JsonModel):
    """One normalized MS1 feature quantification row."""

    model_config = ConfigDict(extra="forbid")

    feature_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    intensity: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    charge: int | None = Field(default=None, ge=1)
    mz: float | None = Field(default=None, gt=0.0)
    retention_time_seconds: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind = MissingValueKind.OBSERVED
    missing_reason: str | None = None
    provenance: ImportedEvidenceProvenance | None = None

    @field_validator(
        "feature_id",
        "sample_id",
        "peptide",
        "canonical_peptide",
        "missing_reason",
        mode="before",
    )
    @classmethod
    def _strip_text(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("protein_refs", mode="before")
    @classmethod
    def _normalize_protein_refs(cls, value: object) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        if isinstance(value, str):
            refs: tuple[str, ...] = (value,)
        else:
            if not isinstance(value, Iterable):
                raise ValueError("protein references must be iterable")
            refs = tuple(str(token) for token in value)
        normalized = tuple(token.strip() for token in refs if token.strip())
        return tuple(dict.fromkeys(normalized))


class Ms1FeatureParseReport(JsonModel):
    """Stable parse report for one MS1 feature quantification table."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[Ms1FeatureRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedMs1FeatureRow, ...] = Field(default_factory=tuple)
    column_mapping: Ms1FeatureColumnMapping


class PrecursorIntensityColumnMapping(JsonModel):
    """User-supplied mapping from precursor-quant columns to the quant contract."""

    model_config = ConfigDict(extra="forbid")

    peptide: str = Field(..., min_length=1)
    intensity: str = Field(..., min_length=1)
    sample_id: str | None = "sample_id"
    run_id: str | None = "run_id"
    modified_peptide: str | None = None
    protein_refs: str | None = None
    precursor_id: str | None = None
    charge: str | None = None
    missing_reason: str | None = None
    protein_separator: str = ";"

    @model_validator(mode="after")
    def _require_sample_or_run_column(self) -> PrecursorIntensityColumnMapping:
        if self.sample_id is None and self.run_id is None:
            raise ValueError("precursor intensity mapping requires sample_id or run_id")
        return self


class RejectedPrecursorIntensityRow(JsonModel):
    """One rejected precursor-intensity row with stable issue details."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[QuantValidationIssue, ...] = Field(default_factory=tuple)


class PrecursorIntensityRecord(JsonModel):
    """One normalized precursor-intensity quantification row."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    run_id: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    modified_peptide: str | None = None
    canonical_peptide: str = Field(..., min_length=1)
    intensity: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    charge: int | None = Field(default=None, ge=1)
    missing_value_kind: MissingValueKind = MissingValueKind.OBSERVED
    missing_reason: str | None = None
    provenance: ImportedEvidenceProvenance | None = None

    @field_validator(
        "precursor_id",
        "sample_id",
        "run_id",
        "peptide_sequence",
        "modified_peptide",
        "canonical_peptide",
        "missing_reason",
        mode="before",
    )
    @classmethod
    def _strip_precursor_text(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("protein_refs", mode="before")
    @classmethod
    def _normalize_precursor_protein_refs(cls, value: object) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        if isinstance(value, str):
            refs: tuple[str, ...] = (value,)
        else:
            if not isinstance(value, Iterable):
                raise ValueError("protein references must be iterable")
            refs = tuple(str(token) for token in value)
        normalized = tuple(token.strip() for token in refs if token.strip())
        return tuple(dict.fromkeys(normalized))


class PrecursorIntensityParseReport(JsonModel):
    """Stable parse report for one precursor-intensity quantification table."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[PrecursorIntensityRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedPrecursorIntensityRow, ...] = Field(
        default_factory=tuple
    )
    column_mapping: PrecursorIntensityColumnMapping


class QuantValue(JsonModel):
    """One matrix cell in a stable quantification table."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    entity_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    source_feature_count: int = Field(..., ge=0)
    value_provenance: QuantValueProvenance | None = None
    imputation_provenance: QuantCellImputationProvenance | None = None


class QuantCellImputationProvenance(JsonModel):
    """Per-cell provenance for an imputed quantification abundance."""

    model_config = ConfigDict(extra="forbid")

    method: ImputationMethod
    original_missing_value_kind: MissingValueKind
    strategy: str = Field(..., min_length=1)
    reference_group: str | None = None
    donor_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    donor_entity_ids: tuple[str, ...] = Field(default_factory=tuple)


class QuantValueOrigin(StrEnum):
    """Whether a quantification cell is observed, still missing, or imputed."""

    OBSERVED = "observed"
    MISSING = "missing"
    IMPUTED = "imputed"


class QuantValueContributorKind(StrEnum):
    """Stable contributor categories that can support one quantification value."""

    FEATURE = "feature"
    PRECURSOR = "precursor"


class QuantValueSourceContributor(JsonModel):
    """One selected raw contributor that directly supports a quant value."""

    model_config = ConfigDict(extra="forbid")

    contributor_id: str = Field(..., min_length=1)
    contributor_kind: QuantValueContributorKind
    canonical_peptide: str | None = None
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    imported_provenance: ImportedEvidenceProvenance | None = None


class QuantValueExcludedContributor(JsonModel):
    """One raw contributor excluded from a quant value plus the exclusion reason."""

    model_config = ConfigDict(extra="forbid")

    contributor: QuantValueSourceContributor
    reason_code: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class QuantValueProvenance(JsonModel):
    """Stable per-cell provenance that explains one matrix value back to raw support."""

    model_config = ConfigDict(extra="forbid")

    aggregation_method: QuantRollupMethod
    value_origin: QuantValueOrigin
    source_feature_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_peptides: tuple[str, ...] = Field(default_factory=tuple)
    source_precursor_ids: tuple[str, ...] = Field(default_factory=tuple)
    selected_contributors: tuple[QuantValueSourceContributor, ...] = Field(
        default_factory=tuple
    )
    excluded_contributors: tuple[QuantValueExcludedContributor, ...] = Field(
        default_factory=tuple
    )


class LabelBasedChannelPolicyEntry(JsonModel):
    """One expected multiplex channel role inside a label-based assay policy."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    channel_role: LabelBasedChannelRole


class LabelBasedQuantPolicy(JsonModel):
    """Explicit channel-role and missing-channel policy for multiplex assays."""

    model_config = ConfigDict(extra="forbid")

    missing_channel_policy: MissingChannelPolicy = MissingChannelPolicy.ERROR
    channel_entries: tuple[LabelBasedChannelPolicyEntry, ...] = Field(
        default_factory=tuple
    )


class LabelBasedChannelStateEntry(JsonModel):
    """One observed or expected multiplex channel inside a label-based workflow."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    sample_id: str | None = None
    condition: str | None = None
    sample_role: ExperimentalDesignSampleRole | None = None
    channel_role: LabelBasedChannelRole
    present_in_design: bool
    present_in_table: bool
    note: str = Field(..., min_length=1)


class MissingMultiplexChannelEntry(JsonModel):
    """One missing multiplex channel handled under an explicit policy."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    expected_role: LabelBasedChannelRole
    policy: MissingChannelPolicy
    message: str = Field(..., min_length=1)


class LabelBasedQuantBundle(JsonModel):
    """Reviewable channel-level manifest for one label-based quantification table."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    normalization_method: NormalizationMethod
    policy: LabelBasedQuantPolicy
    channels: tuple[LabelBasedChannelStateEntry, ...] = Field(default_factory=tuple)
    missing_channels: tuple[MissingMultiplexChannelEntry, ...] = Field(
        default_factory=tuple
    )


class MultiplexNormalizationPolicy(JsonModel):
    """Normalization and balance settings for multiplex quantification groups."""

    model_config = ConfigDict(extra="forbid")

    method: NormalizationMethod = NormalizationMethod.MEDIAN
    balance_ratio_threshold: float = Field(default=1.5, ge=1.0)


class MultiplexChannelBalanceEntry(JsonModel):
    """One multiplex-channel abundance balance row within a single plex group."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    channel_role: LabelBasedChannelRole
    total_abundance: float = Field(..., ge=0.0)
    ratio_to_group_median: float = Field(..., ge=0.0)
    flagged: bool


class MultiplexChannelBalanceReport(JsonModel):
    """Governed channel-balance report across multiplex assay groups."""

    model_config = ConfigDict(extra="forbid")

    policy: MultiplexNormalizationPolicy
    entries: tuple[MultiplexChannelBalanceEntry, ...] = Field(default_factory=tuple)


class ProteinQuantAssignmentPolicy(StrEnum):
    """Shared-peptide handling policies for protein-level quant rollups."""

    INFERENCE_INCLUSIVE = "inference_inclusive"
    QUANT_UNIQUE_ONLY = "quant_unique_only"
    QUANT_SPLIT_SHARED = "quant_split_shared"


class ProteinQuantPolicyValue(JsonModel):
    """One protein/sample abundance under one explicit assignment policy."""

    model_config = ConfigDict(extra="forbid")

    assignment_policy: ProteinQuantAssignmentPolicy
    abundance: float | None = Field(default=None, ge=0.0)
    contributing_peptides: tuple[str, ...] = Field(default_factory=tuple)
    shared_peptide_count: int = Field(..., ge=0)


class ProteinQuantPolicyComparisonEntry(JsonModel):
    """One explicit policy comparison for a protein/sample quant rollup."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    policy_values: tuple[ProteinQuantPolicyValue, ...] = Field(default_factory=tuple)
    max_abundance_difference: float = Field(..., ge=0.0)


class ProteinQuantPolicyComparisonReport(JsonModel):
    """Comparison of protein-level quant outcomes across assignment policies."""

    model_config = ConfigDict(extra="forbid")

    policies: tuple[ProteinQuantAssignmentPolicy, ...] = Field(default_factory=tuple)
    entries: tuple[ProteinQuantPolicyComparisonEntry, ...] = Field(
        default_factory=tuple
    )


class StudyScaleReplicateSampleEntry(JsonModel):
    """Per-sample correlation summary for larger replicate studies."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    within_condition_pairs: int = Field(..., ge=0)
    between_condition_pairs: int = Field(..., ge=0)
    mean_within_condition_correlation: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
    )
    mean_between_condition_correlation: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
    )


class StudyScaleReplicateCorrelationReport(JsonModel):
    """Compact replicate-correlation summary for realistic study sizes."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    sample_summaries: tuple[StudyScaleReplicateSampleEntry, ...] = Field(
        default_factory=tuple
    )
    weakest_within_condition_pairs: tuple[ReplicateCorrelationEntry, ...] = Field(
        default_factory=tuple
    )
    strongest_between_condition_pairs: tuple[ReplicateCorrelationEntry, ...] = Field(
        default_factory=tuple
    )


class StudyScaleBatchEffectEntry(JsonModel):
    """Batch-level compact summary for larger quantification studies."""

    model_config = ConfigDict(extra="forbid")

    batch_id: str = Field(..., min_length=1)
    sample_count: int = Field(..., ge=1)
    flagged: bool
    median_shift_from_global: float


class StudyScaleBatchEffectReport(JsonModel):
    """Compact batch-effect summary that stays reviewable at study scale."""

    model_config = ConfigDict(extra="forbid")

    disposition: QuantAssessmentDisposition = QuantAssessmentDisposition.ADVISORY
    entries: tuple[StudyScaleBatchEffectEntry, ...] = Field(default_factory=tuple)
    flagged_batch_count: int = Field(..., ge=0)
    batch_variance_proxy: float = Field(..., ge=0.0, le=1.0)
    batch_correction_blocked: bool


class QcOutlierSampleEntry(JsonModel):
    """One sample flagged as an outlier from replicate or batch QC context."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    batch: str | None = None
    instrument: str | None = None
    spectra_file: str = Field(..., min_length=1)
    reasons: tuple[str, ...] = Field(default_factory=tuple)


class ReplicateAndBatchQcReport(JsonModel):
    """Integrated replicate and batch QC report for quantification outputs."""

    model_config = ConfigDict(extra="forbid")

    batch_effect_report: BatchEffectAdvisoryReport
    replicate_correlation_report: ReplicateCorrelationReport
    replicate_cv_report: ReplicateCvReport
    replicate_correlation_count: int = Field(..., ge=0)
    flagged_batch_count: int = Field(..., ge=0)
    sample_pca_report: SamplePcaReport | None = None
    condition_clustering_report: ConditionClusteringReport | None = None
    outlier_samples: tuple[QcOutlierSampleEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class SampleReliabilityQcStatus(StrEnum):
    """Stable sample-QC status classes that can affect quantitative weighting."""

    PASS = "pass"
    CAUTION = "caution"
    FAIL = "fail"


class SampleReliabilityQcEntry(JsonModel):
    """One explicit sample-QC posture used for replicate reliability weighting."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    qc_status: SampleReliabilityQcStatus
    blocked: bool = False
    status_reason_codes: tuple[str, ...] = Field(default_factory=tuple)


class SampleReliabilityWeightEntry(JsonModel):
    """One sample-level reliability weight carried into downstream statistics."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    reliability_weight: float = Field(..., ge=0.0, le=1.0)
    low_weight_reasons: tuple[str, ...] = Field(default_factory=tuple)


class SampleReliabilityWeightReport(JsonModel):
    """Stable report over sample-level replicate reliability weights."""

    model_config = ConfigDict(extra="forbid")

    sample_count: int = Field(..., ge=0)
    low_weight_threshold: float = Field(..., ge=0.0, le=1.0)
    exclusion_weight_threshold: float = Field(..., ge=0.0, le=1.0)
    low_weight_sample_count: int = Field(..., ge=0)
    excluded_sample_count: int = Field(..., ge=0)
    entries: tuple[SampleReliabilityWeightEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class ReplicateCvConditionEntry(JsonModel):
    """Condition-level coefficient-of-variation summary over shared entities."""

    model_config = ConfigDict(extra="forbid")

    condition: str = Field(..., min_length=1)
    replicate_count: int = Field(..., ge=1)
    evaluated_entity_count: int = Field(..., ge=0)
    mean_entity_cv: float | None = Field(default=None, ge=0.0)
    median_entity_cv: float | None = Field(default=None, ge=0.0)
    high_cv_entity_count: int = Field(..., ge=0)
    flagged: bool


class ReplicateCvReport(JsonModel):
    """Replicate-spread summary that makes within-condition variance explicit."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    high_cv_threshold: float = Field(..., ge=0.0)
    entries: tuple[ReplicateCvConditionEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class SamplePcaEntry(JsonModel):
    """One sample projected into a compact principal-component QC space."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    batch: str | None = None
    pc1: float
    pc2: float
    distance_from_global_centroid: float = Field(..., ge=0.0)
    distance_from_condition_centroid: float = Field(..., ge=0.0)
    global_centroid_outlier: bool = False
    condition_centroid_outlier: bool = False
    outlier_reasons: tuple[str, ...] = Field(default_factory=tuple)
    outlier: bool


class SamplePcaReport(JsonModel):
    """Principal-component view over replicate structure and sample outliers."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    explained_variance_ratio_pc1: float = Field(..., ge=0.0, le=1.0)
    explained_variance_ratio_pc2: float = Field(..., ge=0.0, le=1.0)
    entries: tuple[SamplePcaEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class ConditionClusteringReport(JsonModel):
    """Condition-separation summary over sample-level QC space."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    condition_count: int = Field(..., ge=0)
    nearest_same_condition_fraction: float = Field(..., ge=0.0, le=1.0)
    mean_within_condition_distance: float | None = Field(default=None, ge=0.0)
    mean_between_condition_distance: float | None = Field(default=None, ge=0.0)
    clustered_by_condition: bool
    note: str = Field(..., min_length=1)


class QuantReproducibilityManifest(JsonModel):
    """Stable manifest proving one quant table can be reproduced exactly."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    normalization_method: NormalizationMethod
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    entity_ids: tuple[str, ...] = Field(default_factory=tuple)
    value_count: int = Field(..., ge=0)
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)


class NormalizationStrategySummaryEntry(JsonModel):
    """One normalization method summarized across sample-balance metrics."""

    model_config = ConfigDict(extra="forbid")

    method: NormalizationMethod
    total_abundance_cv: float = Field(..., ge=0.0)
    median_abundance_cv: float = Field(..., ge=0.0)
    interquartile_range_cv: float = Field(..., ge=0.0)
    balance_score: float = Field(..., ge=0.0)


class NormalizationStrategyComparisonReport(JsonModel):
    """Explicit comparison of normalization methods on one quant table."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    entries: tuple[NormalizationStrategySummaryEntry, ...] = Field(
        default_factory=tuple
    )
    recommended_method: NormalizationMethod


class MissingDataMechanism(StrEnum):
    """Heuristic label for one entity-level missingness pattern."""

    NO_MISSING_VALUES = "no_missing_values"
    CONDITION_SPECIFIC_ABSENCE = "condition_specific_absence"
    LIKELY_TECHNICAL_FAILURE = "likely_technical_failure"
    BATCH_OR_CHANNEL_ISSUE = "batch_or_channel_issue"
    MISSING_COMPLETELY_AT_RANDOM = "missing_completely_at_random"
    MIXED_OR_UNRESOLVED = "mixed_or_unresolved"


class MissingDataMechanismEntry(JsonModel):
    """One entity classified under an explicit missing-data mechanism heuristic."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    mechanism: MissingDataMechanism
    observed_conditions: tuple[str, ...] = Field(default_factory=tuple)
    missing_conditions: tuple[str, ...] = Field(default_factory=tuple)
    missing_samples: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class MissingDataMechanismReport(JsonModel):
    """Mechanism summary over entity-level quant missingness patterns."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    entries: tuple[MissingDataMechanismEntry, ...] = Field(default_factory=tuple)
    summary_counts: dict[MissingDataMechanism, int] = Field(default_factory=dict)


class MissingnessClassifierReport(JsonModel):
    """Owned missingness classifier that bundles table summaries and mechanisms."""

    model_config = ConfigDict(extra="forbid")

    sample_summary: MissingValueSummaryReport
    entity_summary: MissingnessEntitySummaryReport
    condition_summary: MissingnessConditionSummaryReport
    intensity_dependence: MissingnessIntensityDependenceReport
    mechanism_report: MissingDataMechanismReport


class QuantArtifactBundle(JsonModel):
    """Review-ready quantification artifact bundle independent of runtime logs."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    matrix_export: QuantMatrixExport
    missing_value_summary: MissingValueSummaryReport
    imputation_report: ImputationReport | None = None
    imputation_sensitivity_report: ImputationSensitivityReport | None = None
    missingness_entity_summary: MissingnessEntitySummaryReport | None = None
    missingness_condition_summary: MissingnessConditionSummaryReport | None = None
    missingness_intensity_dependence: MissingnessIntensityDependenceReport | None = None
    missingness_mechanism_report: MissingDataMechanismReport | None = None
    replicate_qc_report: ReplicateAndBatchQcReport | None = None
    reproducibility_manifest: QuantReproducibilityManifest
    normalization_comparison_report: NormalizationComparisonReport | None = None
    normalization_strategy_report: NormalizationStrategyComparisonReport | None = None
    limma_compatible_package: object | None = None
    msstats_compatible_input_report: object | None = None
    design_matrix_report: QuantDesignMatrixReport | None = None
    design_model_fit_report: QuantDesignModelFitReport | None = None
    differential_abundance_report: DifferentialAbundanceReport | None = None
    differential_abundance_multi_condition_report: (
        MultiConditionDifferentialAbundanceReport | None
    ) = None
    time_course_differential_report: TimeCourseDifferentialReport | None = None


class LabelFreeQuantTable(JsonModel):
    """Sample-by-entity quantification matrix with stable cell semantics."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    normalization_method: NormalizationMethod = NormalizationMethod.NONE
    imputation_method: ImputationMethod = ImputationMethod.NONE
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    entity_ids: tuple[str, ...] = Field(default_factory=tuple)
    values: tuple[QuantValue, ...] = Field(default_factory=tuple)
    quant_matrix: CanonicalQuantMatrix | None = None
    normalization_factors: dict[str, float] = Field(default_factory=dict)
    entity_protein_refs: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    entity_member_peptides: dict[str, tuple[str, ...]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _bind_canonical_quant_matrix(self) -> LabelFreeQuantTable:
        resolved_values: list[QuantValue] = []
        values_changed = False
        for value in self.values:
            resolved_provenance = _resolve_quant_value_provenance(
                value=value,
                entity_level=self.entity_level,
                aggregation_method=self.aggregation_method,
                entity_member_peptides=self.entity_member_peptides,
            )
            if resolved_provenance != value.value_provenance:
                value = value.model_copy(
                    update={"value_provenance": resolved_provenance}
                )
                values_changed = True
            resolved_values.append(value)
        if values_changed:
            self.values = tuple(resolved_values)
        quant_matrix = self.quant_matrix
        if quant_matrix is None:
            quant_matrix = self._build_canonical_quant_matrix()
            self.quant_matrix = quant_matrix
        elif quant_matrix.entity_ids != self.entity_ids:
            raise ValueError("quant_matrix entity_ids must match entity_ids")
        elif quant_matrix.sample_ids != self.sample_ids:
            raise ValueError("quant_matrix sample_ids must match sample_ids")
        return self

    def _build_canonical_quant_matrix(self) -> CanonicalQuantMatrix:
        return build_numeric_quant_matrix(
            matrix_id=f"{self.entity_level.value}_{self.measure_kind.value}_table",
            entity_kind=_canonical_entity_kind(self.entity_level),
            measure_kind=_canonical_measure_kind(self.measure_kind),
            entity_ids=self.entity_ids,
            sample_ids=self.sample_ids,
            value_lookup={
                (value.entity_id, value.sample_id): value.abundance for value in self.values
            },
            missing_state_lookup={
                (value.entity_id, value.sample_id): _canonical_missing_value_state(
                    value.missing_value_kind
                )
                for value in self.values
            },
            support_count_lookup={
                (value.entity_id, value.sample_id): value.source_feature_count
                for value in self.values
            },
            row_metadata_lookup={
                entity_id: {
                    "protein_refs": ";".join(self.entity_protein_refs.get(entity_id, ())),
                    "member_peptides": ";".join(
                        self.entity_member_peptides.get(entity_id, ())
                    ),
                }
                for entity_id in self.entity_ids
            },
            transformation_history=(
                f"entity_level:{self.entity_level.value}",
                f"measure_kind:{self.measure_kind.value}",
                f"aggregation_method:{self.aggregation_method.value}",
                f"normalization_method:{self.normalization_method.value}",
                f"imputation_method:{self.imputation_method.value}",
            ),
            metadata={
                "normalization_method": self.normalization_method.value,
                "imputation_method": self.imputation_method.value,
            },
        )

    def to_quant_matrix(self) -> CanonicalQuantMatrix:
        """Return the canonical numeric matrix that backs this quant table."""

        assert self.quant_matrix is not None
        return self.quant_matrix

    @classmethod
    def from_quant_matrix(
        cls,
        matrix: CanonicalQuantMatrix,
        *,
        entity_level: QuantEntityLevel,
        aggregation_method: QuantRollupMethod,
        normalization_method: NormalizationMethod = NormalizationMethod.NONE,
        imputation_method: ImputationMethod = ImputationMethod.NONE,
        normalization_factors: dict[str, float] | None = None,
        entity_protein_refs: dict[str, tuple[str, ...]] | None = None,
        entity_member_peptides: dict[str, tuple[str, ...]] | None = None,
    ) -> LabelFreeQuantTable:
        """Build one label-free table from a canonical numeric matrix."""

        row_metadata_lookup = {
            entity_id: matrix.row_metadata[index]
            for index, entity_id in enumerate(matrix.entity_ids)
        }
        resolved_protein_refs = (
            entity_protein_refs
            if entity_protein_refs is not None
            else {
                entity_id: _split_row_metadata_values(
                    row_metadata_lookup.get(entity_id, {}).get("protein_refs", "")
                )
                for entity_id in matrix.entity_ids
            }
        )
        resolved_member_peptides = (
            entity_member_peptides
            if entity_member_peptides is not None
            else {
                entity_id: _split_row_metadata_values(
                    row_metadata_lookup.get(entity_id, {}).get("member_peptides", "")
                )
                for entity_id in matrix.entity_ids
            }
        )
        values = tuple(
            QuantValue(
                entity_id=entity_id,
                sample_id=sample_id,
                abundance=abundance,
                missing_value_kind=_missing_value_kind_from_canonical(state),
                source_feature_count=support_count,
            )
            for entity_id, sample_id, abundance, state, support_count in _iter_label_free_quant_cells(
                matrix
            )
        )
        return cls(
            entity_level=entity_level,
            measure_kind=_quant_measure_kind_from_canonical(matrix.measure_kind),
            aggregation_method=aggregation_method,
            normalization_method=normalization_method,
            imputation_method=imputation_method,
            sample_ids=matrix.sample_ids,
            entity_ids=matrix.entity_ids,
            values=values,
            quant_matrix=matrix,
            normalization_factors=(
                dict.fromkeys(matrix.sample_ids, 1.0)
                if normalization_factors is None
                else normalization_factors
            ),
            entity_protein_refs=resolved_protein_refs,
            entity_member_peptides=resolved_member_peptides,
        )


class QuantSampleMetadataEntry(JsonModel):
    """Stable sample metadata attached to exported quantification matrices."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str | None = None
    replicate: int | None = Field(default=None, ge=1)
    fraction: int | None = Field(default=None, ge=1)
    batch: str | None = None
    instrument: str | None = None
    search_engine: str | None = None


class QuantNormalizationProvenance(JsonModel):
    """Normalization context preserved alongside exported quant matrices."""

    model_config = ConfigDict(extra="forbid")

    normalization_method: NormalizationMethod
    normalization_factors: dict[str, float] = Field(default_factory=dict)
    note: str = Field(..., min_length=1)


class QuantImputationProvenance(JsonModel):
    """Imputation context preserved alongside exported quant matrices."""

    model_config = ConfigDict(extra="forbid")

    imputation_method: ImputationMethod = ImputationMethod.NONE
    imputed_value_count: int = Field(default=0, ge=0)
    note: str = Field(..., min_length=1)


class QuantMatrixExportRow(JsonModel):
    """One stable export row from a quantification matrix."""

    model_config = ConfigDict(extra="forbid")

    sample_metadata: QuantSampleMetadataEntry
    entity_id: str = Field(..., min_length=1)
    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    source_feature_count: int = Field(..., ge=0)
    value_provenance: QuantValueProvenance | None = None
    imputation_provenance: QuantCellImputationProvenance | None = None
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    member_peptides: tuple[str, ...] = Field(default_factory=tuple)


class QuantMatrixExport(JsonModel):
    """Export-ready quantification matrix with metadata and provenance."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    rows: tuple[QuantMatrixExportRow, ...] = Field(default_factory=tuple)
    normalization_provenance: QuantNormalizationProvenance
    imputation_provenance: QuantImputationProvenance


class ProteinQuantRollupEvidenceEntry(JsonModel):
    """One protein/sample rollup with explicit contributing peptide and feature evidence."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    aggregation_method: QuantRollupMethod
    abundance: float | None = Field(default=None, ge=0.0)
    contributing_feature_ids: tuple[str, ...] = Field(default_factory=tuple)
    contributing_peptides: tuple[str, ...] = Field(default_factory=tuple)
    missing_value_kind: MissingValueKind


class NormalizationSampleSnapshot(JsonModel):
    """Per-sample totals, medians, and spread for a quant table snapshot."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    total_abundance: float = Field(..., ge=0.0)
    median_abundance: float = Field(..., ge=0.0)
    interquartile_range: float = Field(..., ge=0.0)


class NormalizationDistributionSnapshot(JsonModel):
    """Per-sample distribution summary before or after normalization."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    observed_count: int = Field(..., ge=0)
    zero_count: int = Field(..., ge=0)
    negative_count: int = Field(..., ge=0)
    min_abundance: float | None = Field(default=None, ge=0.0)
    lower_quartile_abundance: float | None = Field(default=None, ge=0.0)
    median_abundance: float | None = Field(default=None, ge=0.0)
    upper_quartile_abundance: float | None = Field(default=None, ge=0.0)
    max_abundance: float | None = Field(default=None, ge=0.0)


class NormalizationLogTransformPreparation(JsonModel):
    """Explicit per-sample handling of nonpositive values before log transform."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    zero_count: int = Field(..., ge=0)
    negative_count: int = Field(..., ge=0)
    positive_count: int = Field(..., ge=0)
    handling_strategy: str = Field(..., min_length=1)
    pseudocount: float | None = Field(default=None, gt=0.0)


class NormalizationComparisonReport(JsonModel):
    """Before/after report for one normalization operation."""

    model_config = ConfigDict(extra="forbid")

    method: NormalizationMethod
    normalization_factors: dict[str, float] = Field(default_factory=dict)
    before: tuple[NormalizationSampleSnapshot, ...] = Field(default_factory=tuple)
    after: tuple[NormalizationSampleSnapshot, ...] = Field(default_factory=tuple)
    before_distributions: tuple[NormalizationDistributionSnapshot, ...] = Field(
        default_factory=tuple
    )
    after_distributions: tuple[NormalizationDistributionSnapshot, ...] = Field(
        default_factory=tuple
    )
    log_transform_preparation: tuple[NormalizationLogTransformPreparation, ...] = (
        Field(default_factory=tuple)
    )


class ImputationEntry(JsonModel):
    """One imputed abundance with explicit source missingness context."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    original_missing_value_kind: MissingValueKind
    imputed_abundance: float = Field(..., ge=0.0)
    neighbor_entity_ids: tuple[str, ...] = Field(default_factory=tuple)
    donor_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    reference_group: str | None = None
    strategy: str = Field(..., min_length=1)


class ImputationReport(JsonModel):
    """Explicit ledger of values introduced by one imputation method."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    method: ImputationMethod
    entries: tuple[ImputationEntry, ...] = Field(default_factory=tuple)
    imputed_value_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class ImputationSensitivityEntry(JsonModel):
    """Downstream DA summary for one imputation policy."""

    model_config = ConfigDict(extra="forbid")

    method: ImputationMethod
    supported: bool
    imputed_value_count: int = Field(..., ge=0)
    significant_entity_count: int = Field(default=0, ge=0)
    top_entity_id: str | None = None
    top_entity_direction: str | None = None
    top_entity_effect_size: float | None = None
    note: str = Field(..., min_length=1)


class ImputationSensitivityOverlapEntry(JsonModel):
    """Pairwise overlap of significant hits across imputation methods."""

    model_config = ConfigDict(extra="forbid")

    method_a: ImputationMethod
    method_b: ImputationMethod
    significant_entity_count_a: int = Field(..., ge=0)
    significant_entity_count_b: int = Field(..., ge=0)
    overlapping_significant_entity_count: int = Field(..., ge=0)
    method_a_only_count: int = Field(..., ge=0)
    method_b_only_count: int = Field(..., ge=0)
    jaccard_index: float = Field(..., ge=0.0, le=1.0)


class ImputationSensitivityChangedSignificanceEntry(JsonModel):
    """One entity whose significance changes between two imputation methods."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    reference_method: ImputationMethod
    compared_method: ImputationMethod
    reference_significant: bool
    compared_significant: bool
    reference_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    compared_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    reference_log2_fold_change: float | None = None
    compared_log2_fold_change: float | None = None
    note: str = Field(..., min_length=1)


class ImputationDependentHitEntry(JsonModel):
    """One entity that becomes significant only after imputation."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    baseline_method: ImputationMethod
    imputation_methods: tuple[ImputationMethod, ...] = Field(default_factory=tuple)
    baseline_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    best_imputation_method: ImputationMethod
    best_imputation_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    best_imputation_log2_fold_change: float | None = None
    note: str = Field(..., min_length=1)


class ImputationSensitivityReport(JsonModel):
    """Comparison of downstream DA behavior across imputation methods."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    baseline_method: ImputationMethod = ImputationMethod.NONE
    significance_threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    entries: tuple[ImputationSensitivityEntry, ...] = Field(default_factory=tuple)
    overlap_entries: tuple[ImputationSensitivityOverlapEntry, ...] = Field(
        default_factory=tuple
    )
    changed_significance_entries: tuple[
        ImputationSensitivityChangedSignificanceEntry, ...
    ] = Field(default_factory=tuple)
    imputation_dependent_hits: tuple[ImputationDependentHitEntry, ...] = Field(
        default_factory=tuple
    )
    primary_narrative_changed: bool


class DifferentialImputationSignificanceChangeReason(StrEnum):
    """How one differential result changes between no-impute and imputed analysis."""

    NOT_IMPUTED = "not_imputed"
    STABLE_SIGNIFICANT = "stable_significant"
    STABLE_NON_SIGNIFICANT = "stable_non_significant"
    SIGNIFICANT_ONLY_AFTER_IMPUTATION = "significant_only_after_imputation"
    SIGNIFICANCE_LOST_AFTER_IMPUTATION = "significance_lost_after_imputation"


class MissingValueSummaryEntry(JsonModel):
    """Missing-value counts for one sample within a quant table."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    observed_count: int = Field(..., ge=0)
    zero_count: int = Field(..., ge=0)
    not_observed_count: int = Field(..., ge=0)
    filtered_count: int = Field(..., ge=0)


class MissingValueSummaryPolicy(JsonModel):
    """Correction and filtering rules applied before missing-value summarization."""

    model_config = ConfigDict(extra="forbid")

    zero_policy: MissingValueCorrectionPolicy = MissingValueCorrectionPolicy.PRESERVE
    filtered_policy: MissingValueCorrectionPolicy = (
        MissingValueCorrectionPolicy.PRESERVE
    )
    min_observed_samples_per_entity: int = Field(default=0, ge=0)


class MissingValueSummaryReport(JsonModel):
    """Stable missing-value summary over a quantification matrix."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    policy: MissingValueSummaryPolicy
    entries: tuple[MissingValueSummaryEntry, ...] = Field(default_factory=tuple)
    included_entity_ids: tuple[str, ...] = Field(default_factory=tuple)
    excluded_entity_ids: tuple[str, ...] = Field(default_factory=tuple)


class MissingnessEntitySummaryEntry(JsonModel):
    """Missingness burden for one quantified entity across all samples."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    observed_sample_count: int = Field(..., ge=0)
    zero_sample_count: int = Field(..., ge=0)
    not_observed_sample_count: int = Field(..., ge=0)
    filtered_sample_count: int = Field(..., ge=0)
    missing_fraction: float = Field(..., ge=0.0, le=1.0)


class MissingnessEntitySummaryReport(JsonModel):
    """Entity-level missingness summary over one quantification table."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    entries: tuple[MissingnessEntitySummaryEntry, ...] = Field(default_factory=tuple)


class MissingnessConditionSummaryEntry(JsonModel):
    """Missingness burden for one experimental condition."""

    model_config = ConfigDict(extra="forbid")

    condition: str = Field(..., min_length=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    observed_value_count: int = Field(..., ge=0)
    zero_value_count: int = Field(..., ge=0)
    not_observed_value_count: int = Field(..., ge=0)
    filtered_value_count: int = Field(..., ge=0)
    missing_fraction: float = Field(..., ge=0.0, le=1.0)
    condition_specific_absence_entity_ids: tuple[str, ...] = Field(default_factory=tuple)


class MissingnessConditionSummaryReport(JsonModel):
    """Condition-level missingness summary with condition-specific absence signals."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    entries: tuple[MissingnessConditionSummaryEntry, ...] = Field(default_factory=tuple)


class MissingnessIntensityPoint(JsonModel):
    """One entity-level point for missingness-versus-intensity plotting."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    mean_log2_observed_abundance: float
    missing_fraction: float = Field(..., ge=0.0, le=1.0)


class MissingnessIntensityBinEntry(JsonModel):
    """One intensity bin summarizing mean missingness burden."""

    model_config = ConfigDict(extra="forbid")

    lower_log2_abundance: float
    upper_log2_abundance: float
    entity_count: int = Field(..., ge=0)
    mean_missing_fraction: float = Field(..., ge=0.0, le=1.0)


class MissingnessIntensityDependenceReport(JsonModel):
    """Intensity-dependent missingness profile suitable for plotting and review."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    plot_points: tuple[MissingnessIntensityPoint, ...] = Field(default_factory=tuple)
    bins: tuple[MissingnessIntensityBinEntry, ...] = Field(default_factory=tuple)
    trend_correlation: float | None = Field(default=None, ge=-1.0, le=1.0)
    intensity_dependent_missingness_detected: bool


class BatchEffectBatchEntry(JsonModel):
    """One batch-level median-shift advisory row."""

    model_config = ConfigDict(extra="forbid")

    batch_id: str = Field(..., min_length=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    median_log2_abundance: float
    shift_from_global: float
    flagged: bool


class BatchAssociatedPrincipalComponentEntry(JsonModel):
    """One principal component annotated for batch association strength."""

    model_config = ConfigDict(extra="forbid")

    component_index: int = Field(..., ge=1)
    component_label: str = Field(..., min_length=1)
    explained_variance_ratio: float = Field(..., ge=0.0, le=1.0)
    batch_association_ratio: float = Field(..., ge=0.0, le=1.0)
    associated_with_batch: bool


class BatchEffectAdvisoryReport(JsonModel):
    """Owned batch-effect estimator over quantification samples."""

    model_config = ConfigDict(extra="forbid")

    disposition: QuantAssessmentDisposition = QuantAssessmentDisposition.ADVISORY
    batch_field: str = Field(..., min_length=1)
    global_median_log2_abundance: float
    batches: tuple[BatchEffectBatchEntry, ...] = Field(default_factory=tuple)
    batch_variance_proxy: float = Field(..., ge=0.0, le=1.0)
    principal_components: tuple[BatchAssociatedPrincipalComponentEntry, ...] = Field(
        default_factory=tuple
    )
    batch_associated_component_count: int = Field(..., ge=0)
    fully_confounded_with_condition: bool
    batch_correction_blocked: bool
    batch_warning: str | None = None
    note: str = Field(..., min_length=1)


class ReplicateCorrelationEntry(JsonModel):
    """One sample-pair replicate correlation row."""

    model_config = ConfigDict(extra="forbid")

    sample_a: str = Field(..., min_length=1)
    sample_b: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    correlation: float = Field(..., ge=-1.0, le=1.0)
    shared_entity_count: int = Field(..., ge=2)


class ReplicateCorrelationReport(JsonModel):
    """Pairwise replicate-correlation report over a quantification matrix."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    entries: tuple[ReplicateCorrelationEntry, ...] = Field(default_factory=tuple)
    within_condition_mean: float | None = Field(default=None, ge=-1.0, le=1.0)
    between_condition_mean: float | None = Field(default=None, ge=-1.0, le=1.0)


class DifferentialReplicatePolicy(JsonModel):
    """Minimum replicate policy for differential abundance comparisons."""

    model_config = ConfigDict(extra="forbid")

    min_replicates_per_condition: int = Field(default=2, ge=1)
    disposition: QuantAssessmentDisposition = QuantAssessmentDisposition.ENFORCED


class DifferentialAbundanceTestType(StrEnum):
    """Supported inferential engines for differential abundance results."""

    WELCH_T_TEST = "welch_t_test"
    LINEAR_MODEL_CONTRAST = "linear_model_contrast"
    PAIRED_T_TEST = "paired_t_test"


class BrokenPairDisposition(StrEnum):
    """Policies for broken design pairs during paired differential testing."""

    EXCLUDE = "exclude"
    BLOCK = "block"


class PairedDifferentialPolicy(JsonModel):
    """Pair completeness policy for paired differential abundance testing."""

    model_config = ConfigDict(extra="forbid")

    pair_id_field: str = Field(default="pair_id", min_length=1)
    minimum_complete_pairs: int = Field(default=2, ge=1)
    broken_pair_disposition: BrokenPairDisposition = BrokenPairDisposition.EXCLUDE


class DifferentialBrokenPairEntry(JsonModel):
    """One design pair excluded or blocked during paired testing."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    pair_id: str | None = None
    sample_ids_a: tuple[str, ...] = Field(default_factory=tuple)
    sample_ids_b: tuple[str, ...] = Field(default_factory=tuple)
    reason_code: str = Field(..., min_length=1)
    detail: str = Field(..., min_length=1)


class DifferentialAbundanceAssumptionReport(JsonModel):
    """Test and correction assumptions carried by a differential abundance report."""

    model_config = ConfigDict(extra="forbid")

    test_type: DifferentialAbundanceTestType
    variance_assumption: str = Field(..., min_length=1)
    multiple_testing_scope: str = Field(..., min_length=1)
    replicate_policy: DifferentialReplicatePolicy
    sample_weighting: str = Field(default="unweighted", min_length=1)
    contrast_name: str | None = None
    paired_policy: PairedDifferentialPolicy | None = None


class DifferentialResultRobustnessQcStatus(StrEnum):
    """Stable QC severity carried onto differential-result rows."""

    PASS = "pass"
    CAUTION = "caution"
    FAIL = "fail"


class DifferentialResultRobustnessReasonCode(StrEnum):
    """Stable downgrade reasons for one differential-result robustness score."""

    LOW_EFFECT_SIZE = "low_effect_size"
    ELEVATED_FDR = "elevated_fdr"
    HIGH_MISSINGNESS = "high_missingness"
    IMPUTATION_HEAVY = "imputation_heavy"
    IMPUTATION_DEPENDENT_SIGNIFICANCE = "imputation_dependent_significance"
    LOW_PEPTIDE_SUPPORT = "low_peptide_support"
    REPLICATE_INCONSISTENCY = "replicate_inconsistency"
    CAUTION_QC = "caution_qc"
    FAILED_QC = "failed_qc"


class DifferentialAbundanceEntry(JsonModel):
    """One entity-level two-condition differential abundance result."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    observations_a: int = Field(..., ge=0)
    observations_b: int = Field(..., ge=0)
    complete_pair_count: int = Field(default=0, ge=0)
    zero_values_a: int = Field(default=0, ge=0)
    zero_values_b: int = Field(default=0, ge=0)
    not_observed_values_a: int = Field(default=0, ge=0)
    not_observed_values_b: int = Field(default=0, ge=0)
    filtered_values_a: int = Field(default=0, ge=0)
    filtered_values_b: int = Field(default=0, ge=0)
    mean_log2_abundance_a: float
    mean_log2_abundance_b: float
    log2_fold_change: float
    p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    standard_error: float | None = Field(default=None, ge=0.0)
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    effect_size_cohens_d: float | None = None
    no_impute_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    no_impute_log2_fold_change: float | None = None
    imputed_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    imputed_log2_fold_change: float | None = None
    imputation_significance_change_reason: (
        DifferentialImputationSignificanceChangeReason | None
    ) = None
    imputation_dependent_hit: bool = False
    robustness_score: float | None = Field(default=None, ge=0.0, le=1.0)
    robustness_qc_status: DifferentialResultRobustnessQcStatus | None = None
    robustness_reason_codes: tuple[DifferentialResultRobustnessReasonCode, ...] = (
        Field(default_factory=tuple)
    )
    robustness_note: str | None = None
    uncertainty_note: str | None = None


class DifferentialAbundanceReport(JsonModel):
    """Stable two-condition differential abundance report."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    normalization_method: NormalizationMethod
    imputation_method: ImputationMethod = ImputationMethod.NONE
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    contrast_name: str | None = None
    replicate_policy: DifferentialReplicatePolicy = Field(
        default_factory=DifferentialReplicatePolicy
    )
    assumption_report: DifferentialAbundanceAssumptionReport
    entries: tuple[DifferentialAbundanceEntry, ...] = Field(default_factory=tuple)
    broken_pairs: tuple[DifferentialBrokenPairEntry, ...] = Field(default_factory=tuple)


class DifferentialAbundanceContrast(JsonModel):
    """One named condition contrast preserved inside a DA collection."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    contrast_name: str | None = None


class MultiConditionDifferentialAbundanceReport(JsonModel):
    """Pairwise differential-abundance collection over a multi-condition study."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    normalization_method: NormalizationMethod
    imputation_method: ImputationMethod = ImputationMethod.NONE
    condition_count: int = Field(..., ge=2)
    replicate_policy: DifferentialReplicatePolicy = Field(
        default_factory=DifferentialReplicatePolicy
    )
    contrasts: tuple[DifferentialAbundanceContrast, ...] = Field(default_factory=tuple)
    reports: tuple[DifferentialAbundanceReport, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class TimeCourseTestingPolicy(JsonModel):
    """Ordered-timepoint policy for one time-course differential analysis."""

    model_config = ConfigDict(extra="forbid")

    timepoint_field: str = Field(default="timepoint", min_length=1)
    ordered_timepoints: tuple[str, ...] = Field(default_factory=tuple)
    batch_field: str | None = None
    pairing_field: str | None = None
    covariate_fields: tuple[str, ...] = Field(default_factory=tuple)


class TimeCourseDifferentialEntry(JsonModel):
    """One entity-level time-course effect row for one condition."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    reference_condition: str = Field(..., min_length=1)
    observed_sample_count: int = Field(..., ge=0)
    observed_timepoint_count: int = Field(..., ge=0)
    slope_per_timepoint: float
    slope_standard_error: float | None = Field(default=None, ge=0.0)
    slope_confidence_interval_low: float | None = None
    slope_confidence_interval_high: float | None = None
    time_effect_p_value: float = Field(..., ge=0.0, le=1.0)
    time_effect_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    interaction_effect: float | None = None
    interaction_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    interaction_adjusted_p_value: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    no_impute_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    no_impute_log2_fold_change: float | None = None
    imputed_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    imputed_log2_fold_change: float | None = None
    imputation_significance_change_reason: (
        DifferentialImputationSignificanceChangeReason | None
    ) = None
    imputation_dependent_hit: bool = False
    robustness_score: float | None = Field(default=None, ge=0.0, le=1.0)
    robustness_qc_status: DifferentialResultRobustnessQcStatus | None = None
    robustness_reason_codes: tuple[DifferentialResultRobustnessReasonCode, ...] = (
        Field(default_factory=tuple)
    )
    robustness_note: str | None = None
    note: str | None = None


class TimeCourseDifferentialReport(JsonModel):
    """Time-course differential report over ordered study timepoints."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    normalization_method: NormalizationMethod
    imputation_method: ImputationMethod = ImputationMethod.NONE
    reference_condition: str = Field(..., min_length=1)
    condition_count: int = Field(..., ge=1)
    ordered_timepoints: tuple[str, ...] = Field(default_factory=tuple)
    timepoint_positions: dict[str, float] = Field(default_factory=dict)
    policy: TimeCourseTestingPolicy
    entries: tuple[TimeCourseDifferentialEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class QuantDesignMatrixColumnKind(StrEnum):
    """Durable ownership categories for design-matrix columns."""

    INTERCEPT = "intercept"
    CONDITION = "condition"
    BATCH = "batch"
    TIMEPOINT = "timepoint"
    INTERACTION = "interaction"
    COVARIATE = "covariate"
    PAIRING = "pairing"


class QuantDesignMatrixColumnEncoding(StrEnum):
    """Encoding applied to one design-matrix column."""

    BINARY = "binary"
    CATEGORICAL_ONE_HOT = "categorical_one_hot"
    NUMERIC = "numeric"


class QuantDesignMatrixColumn(JsonModel):
    """One explicit design-matrix column with stable ownership metadata."""

    model_config = ConfigDict(extra="forbid")

    column_name: str = Field(..., min_length=1)
    kind: QuantDesignMatrixColumnKind
    encoding: QuantDesignMatrixColumnEncoding
    source_field: str = Field(..., min_length=1)
    level: str | None = None
    reference_level: str | None = None


class QuantDesignMatrixSampleRow(JsonModel):
    """One sample row plus encoded matrix values and preserved design metadata."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    batch: str | None = None
    pair_id: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    column_values: tuple[float, ...] = Field(default_factory=tuple)


class QuantDesignContrast(JsonModel):
    """One named condition contrast expressed against design-matrix columns."""

    model_config = ConfigDict(extra="forbid")

    contrast_name: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    coefficient_weights: dict[str, float] = Field(default_factory=dict)
    coefficient_vector: tuple[float, ...] = Field(default_factory=tuple)


class QuantDesignMatrixReport(JsonModel):
    """Stable design-matrix report over conditions, batches, covariates, and pairs."""

    model_config = ConfigDict(extra="forbid")

    sample_count: int = Field(..., ge=1)
    column_count: int = Field(..., ge=1)
    condition_field: str = Field(..., min_length=1)
    batch_field: str | None = None
    pairing_field: str | None = None
    timepoint_field: str | None = None
    covariate_fields: tuple[str, ...] = Field(default_factory=tuple)
    columns: tuple[QuantDesignMatrixColumn, ...] = Field(default_factory=tuple)
    rows: tuple[QuantDesignMatrixSampleRow, ...] = Field(default_factory=tuple)
    contrasts: tuple[QuantDesignContrast, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class QuantDesignModelCoefficientEntry(JsonModel):
    """One per-entity coefficient estimated from the owned design matrix."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    coefficient_name: str = Field(..., min_length=1)
    estimate: float
    observed_sample_count: int = Field(..., ge=1)
    design_rank: int = Field(..., ge=1)
    residual_degrees_of_freedom: int = Field(..., ge=0)


class QuantDesignContrastEstimateEntry(JsonModel):
    """One per-entity estimate for a named condition contrast."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    contrast_name: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    estimate: float


class QuantDesignModelFitReport(JsonModel):
    """Least-squares coefficient report over a quantification table and design matrix."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    normalization_method: NormalizationMethod
    imputation_method: ImputationMethod = ImputationMethod.NONE
    design_matrix: QuantDesignMatrixReport
    fitted_entity_count: int = Field(..., ge=0)
    skipped_entity_count: int = Field(..., ge=0)
    coefficient_entries: tuple[QuantDesignModelCoefficientEntry, ...] = Field(
        default_factory=tuple
    )
    contrast_estimates: tuple[QuantDesignContrastEstimateEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class LabelFreeFeatureProvenanceEntry(JsonModel):
    """Feature-level provenance preserved inside an LFQ workflow bundle."""

    model_config = ConfigDict(extra="forbid")

    feature_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    intensity: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind


class LabelFreePeptideProvenanceEntry(JsonModel):
    """Peptide-level LFQ abundance plus contributing raw features."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    contributing_feature_ids: tuple[str, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)


class LabelFreeProvenanceBundle(JsonModel):
    """Reviewable LFQ provenance across features, peptides, and proteins."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    aggregation_method: QuantRollupMethod
    normalization_method: NormalizationMethod
    feature_entries: tuple[LabelFreeFeatureProvenanceEntry, ...] = Field(
        default_factory=tuple
    )
    peptide_entries: tuple[LabelFreePeptideProvenanceEntry, ...] = Field(
        default_factory=tuple
    )
    protein_entries: tuple[ProteinQuantRollupEvidenceEntry, ...] = Field(
        default_factory=tuple
    )


@dataclass(frozen=True)
class _QuantAccumulator:
    values: tuple[float, ...]
    feature_count: int
    missing_kinds: tuple[MissingValueKind, ...]


_STABLE_DOCUMENT_TIME = datetime(1970, 1, 1, tzinfo=UTC)


def _detect_delimiter(first_line: str) -> str:
    return "\t" if "\t" in first_line else ","


def _parse_protein_refs(raw_value: str | None, separator: str) -> tuple[str, ...]:
    if raw_value in (None, ""):
        return ()
    text = raw_value.strip() if raw_value is not None else ""
    refs = tuple(token.strip() for token in text.split(separator) if token.strip())
    return tuple(dict.fromkeys(refs))


def _row_issue(code: str, message: str, row_number: int) -> QuantValidationIssue:
    return QuantValidationIssue(code=code, message=message, row_number=row_number)


def _canonical_entity_kind(
    entity_level: QuantEntityLevel,
) -> CanonicalQuantEntityKind:
    if entity_level is QuantEntityLevel.PEPTIDE:
        return CanonicalQuantEntityKind.PEPTIDE
    return CanonicalQuantEntityKind.PROTEIN


def _canonical_measure_kind(
    measure_kind: QuantMeasureKind,
) -> CanonicalQuantMeasureKind:
    if measure_kind is QuantMeasureKind.SPECTRAL_COUNT:
        return CanonicalQuantMeasureKind.SPECTRAL_COUNT
    return CanonicalQuantMeasureKind.INTENSITY


def _quant_measure_kind_from_canonical(
    measure_kind: CanonicalQuantMeasureKind,
) -> QuantMeasureKind:
    if measure_kind is CanonicalQuantMeasureKind.SPECTRAL_COUNT:
        return QuantMeasureKind.SPECTRAL_COUNT
    return QuantMeasureKind.INTENSITY


def _canonical_missing_value_state(
    missing_value_kind: MissingValueKind,
) -> CanonicalMissingValueState:
    return CanonicalMissingValueState(missing_value_kind.value)


def _missing_value_kind_from_canonical(
    missing_value_state: CanonicalMissingValueState,
) -> MissingValueKind:
    return MissingValueKind(missing_value_state.value)


def _split_row_metadata_values(value: str) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(token for token in value.split(";") if token)


def _iter_label_free_quant_cells(
    matrix: CanonicalQuantMatrix,
) -> tuple[tuple[str, str, float | None, CanonicalMissingValueState, int], ...]:
    base_cells = iter_quant_matrix_cells(matrix)
    rows: list[tuple[str, str, float | None, CanonicalMissingValueState, int]] = []
    for row_index, cell in enumerate(base_cells):
        entity_id, sample_id, abundance, state = cell
        support_row_index = row_index // len(matrix.sample_ids)
        support_column_index = row_index % len(matrix.sample_ids)
        support_count = (
            0
            if not matrix.support_counts
            else matrix.support_counts[support_row_index][support_column_index]
        )
        rows.append((entity_id, sample_id, abundance, state, support_count))
    return tuple(rows)


def _quant_matrix_setting(
    matrix: CanonicalQuantMatrix,
    key: str,
    default: str,
) -> str:
    if key in matrix.metadata:
        return matrix.metadata[key]
    prefix = f"{key}:"
    for entry in matrix.transformation_history:
        if entry.startswith(prefix):
            return entry.removeprefix(prefix)
    return default


def coerce_label_free_quant_table(
    table: LabelFreeQuantTable | CanonicalQuantMatrix,
) -> LabelFreeQuantTable:
    """Accept one canonical matrix wherever label-free table semantics are needed."""

    if isinstance(table, LabelFreeQuantTable):
        return table
    if table.entity_kind is CanonicalQuantEntityKind.PEPTIDE:
        entity_level = QuantEntityLevel.PEPTIDE
    elif table.entity_kind is CanonicalQuantEntityKind.PROTEIN:
        entity_level = QuantEntityLevel.PROTEIN
    else:
        raise ValueError(
            "label-free quantification requires peptide or protein entity matrices"
        )
    return LabelFreeQuantTable.from_quant_matrix(
        table,
        entity_level=entity_level,
        aggregation_method=QuantRollupMethod(
            _quant_matrix_setting(table, "aggregation_method", QuantRollupMethod.SUM.value)
        ),
        normalization_method=NormalizationMethod(
            _quant_matrix_setting(
                table,
                "normalization_method",
                NormalizationMethod.NONE.value,
            )
        ),
        imputation_method=ImputationMethod(
            _quant_matrix_setting(
                table,
                "imputation_method",
                ImputationMethod.NONE.value,
            )
        ),
        normalization_factors=dict.fromkeys(table.sample_ids, 1.0),
    )


def _matrix_value_index(
    table: LabelFreeQuantTable,
) -> dict[tuple[str, str], QuantValue]:
    return {(value.entity_id, value.sample_id): value for value in table.values}


def _condition_lookup(entries: tuple[ExperimentalDesignEntry, ...]) -> dict[str, str]:
    return {entry.sample_id: entry.condition for entry in entries}


def _batch_lookup(entries: tuple[ExperimentalDesignEntry, ...]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for entry in entries:
        if entry.batch:
            mapping[entry.sample_id] = entry.batch
        elif entry.instrument:
            mapping[entry.sample_id] = entry.instrument
    return mapping


def _sample_metadata_lookup(
    entries: tuple[ExperimentalDesignEntry, ...],
) -> dict[str, QuantSampleMetadataEntry]:
    return {
        entry.sample_id: QuantSampleMetadataEntry(
            sample_id=entry.sample_id,
            condition=entry.condition,
            replicate=entry.replicate,
            fraction=entry.fraction,
            batch=entry.batch,
            instrument=entry.instrument,
            search_engine=entry.search_engine,
        )
        for entry in entries
    }


def _default_label_channel_role(
    entry: ExperimentalDesignEntry,
) -> LabelBasedChannelRole:
    if entry.sample_role is ExperimentalDesignSampleRole.POOLED_REFERENCE:
        return LabelBasedChannelRole.REFERENCE
    if entry.sample_role is ExperimentalDesignSampleRole.QC_BRIDGE:
        return LabelBasedChannelRole.QC_BRIDGE
    return LabelBasedChannelRole.SAMPLE


def _multiplex_channel_lookup(
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> dict[str, tuple[str, str, LabelBasedChannelRole]]:
    lookup: dict[str, tuple[str, str, LabelBasedChannelRole]] = {}
    for entry in design_entries:
        if not entry.multiplex_group or not entry.multiplex_channel:
            continue
        lookup[entry.sample_id] = (
            entry.multiplex_group,
            entry.multiplex_channel,
            _default_label_channel_role(entry),
        )
    return lookup


def _feature_entity_ids(
    record: Ms1FeatureRecord,
    *,
    entity_level: QuantEntityLevel,
) -> tuple[str, ...]:
    if entity_level is QuantEntityLevel.PEPTIDE:
        return (record.canonical_peptide,)
    if record.protein_refs:
        return record.protein_refs
    return ()


def _aggregate_missing_kind(kinds: tuple[MissingValueKind, ...]) -> MissingValueKind:
    if any(
        kind in (MissingValueKind.OBSERVED, MissingValueKind.ZERO) for kind in kinds
    ):
        if any(kind is MissingValueKind.ZERO for kind in kinds) and not any(
            kind is MissingValueKind.OBSERVED for kind in kinds
        ):
            return MissingValueKind.ZERO
        return MissingValueKind.OBSERVED
    if any(kind is MissingValueKind.FILTERED for kind in kinds):
        return MissingValueKind.FILTERED
    return MissingValueKind.NOT_OBSERVED


def _aggregate_abundance(
    values: tuple[float, ...],
    *,
    measure_kind: QuantMeasureKind,
    aggregation_method: QuantRollupMethod,
    top_n: int,
) -> float:
    if measure_kind is QuantMeasureKind.SPECTRAL_COUNT:
        return float(len(values))
    if aggregation_method is QuantRollupMethod.SUM:
        return float(sum(values))
    if aggregation_method is QuantRollupMethod.MEDIAN:
        return float(np.median(np.array(values, dtype=float)))
    sorted_values = sorted(values, reverse=True)
    return float(sum(sorted_values[:top_n]))


def _quant_value_origin(
    *,
    abundance: float | None,
    imputation_provenance: QuantCellImputationProvenance | None,
) -> QuantValueOrigin:
    if imputation_provenance is not None:
        return QuantValueOrigin.IMPUTED
    if abundance is None:
        return QuantValueOrigin.MISSING
    return QuantValueOrigin.OBSERVED


def _quant_value_source_contributor(
    record: Ms1FeatureRecord,
) -> QuantValueSourceContributor:
    return QuantValueSourceContributor(
        contributor_id=record.feature_id,
        contributor_kind=QuantValueContributorKind.FEATURE,
        canonical_peptide=record.canonical_peptide,
        protein_refs=record.protein_refs,
        abundance=None if record.intensity is None else float(record.intensity),
        missing_value_kind=record.missing_value_kind,
        imported_provenance=record.provenance,
    )


def _quant_value_exclusion_reason(
    *,
    record: Ms1FeatureRecord,
    reason_code: str,
) -> str:
    if reason_code == "excluded_by_top_n_rollup":
        return "contributor falls outside the selected top-n rollup window"
    if reason_code == "missing_value_filtered":
        return "contributor was marked filtered before matrix aggregation"
    if reason_code == "missing_value_not_observed":
        return "contributor was not observed in this sample before matrix aggregation"
    return f"contributor was excluded from the quant value: {record.feature_id}"


def _build_quant_value_provenance(
    *,
    aggregation_method: QuantRollupMethod,
    abundance: float | None,
    selected_records: tuple[Ms1FeatureRecord, ...],
    excluded_records: tuple[tuple[Ms1FeatureRecord, str], ...],
    imputation_provenance: QuantCellImputationProvenance | None = None,
) -> QuantValueProvenance:
    selected_contributors = tuple(
        _quant_value_source_contributor(record) for record in selected_records
    )
    excluded_contributors = tuple(
        QuantValueExcludedContributor(
            contributor=_quant_value_source_contributor(record),
            reason_code=reason_code,
            reason=_quant_value_exclusion_reason(
                record=record,
                reason_code=reason_code,
            ),
        )
        for record, reason_code in excluded_records
    )
    return QuantValueProvenance(
        aggregation_method=aggregation_method,
        value_origin=_quant_value_origin(
            abundance=abundance,
            imputation_provenance=imputation_provenance,
        ),
        source_feature_ids=tuple(
            contributor.contributor_id
            for contributor in selected_contributors
            if contributor.contributor_kind is QuantValueContributorKind.FEATURE
        ),
        source_peptides=tuple(
            dict.fromkeys(
                contributor.canonical_peptide
                for contributor in selected_contributors
                if contributor.canonical_peptide is not None
            )
        ),
        source_precursor_ids=tuple(
            contributor.contributor_id
            for contributor in selected_contributors
            if contributor.contributor_kind is QuantValueContributorKind.PRECURSOR
        ),
        selected_contributors=selected_contributors,
        excluded_contributors=excluded_contributors,
    )


def _fallback_quant_value_provenance(
    *,
    value: QuantValue,
    entity_level: QuantEntityLevel,
    aggregation_method: QuantRollupMethod,
    entity_member_peptides: dict[str, tuple[str, ...]],
) -> QuantValueProvenance:
    source_peptides = (
        (value.entity_id,)
        if entity_level is QuantEntityLevel.PEPTIDE
        else entity_member_peptides.get(value.entity_id, ())
    )
    return QuantValueProvenance(
        aggregation_method=aggregation_method,
        value_origin=_quant_value_origin(
            abundance=value.abundance,
            imputation_provenance=value.imputation_provenance,
        ),
        source_peptides=source_peptides,
    )


def _resolve_quant_value_provenance(
    *,
    value: QuantValue,
    entity_level: QuantEntityLevel,
    aggregation_method: QuantRollupMethod,
    entity_member_peptides: dict[str, tuple[str, ...]],
) -> QuantValueProvenance:
    provenance = value.value_provenance or _fallback_quant_value_provenance(
        value=value,
        entity_level=entity_level,
        aggregation_method=aggregation_method,
        entity_member_peptides=entity_member_peptides,
    )
    updates: dict[str, object] = {}
    if provenance.aggregation_method is not aggregation_method:
        updates["aggregation_method"] = aggregation_method
    resolved_origin = _quant_value_origin(
        abundance=value.abundance,
        imputation_provenance=value.imputation_provenance,
    )
    if provenance.value_origin is not resolved_origin:
        updates["value_origin"] = resolved_origin
    if (
        not provenance.source_peptides
        and entity_level is QuantEntityLevel.PEPTIDE
        and value.entity_id
    ):
        updates["source_peptides"] = (value.entity_id,)
    if updates:
        return provenance.model_copy(update=updates)
    return provenance


def _build_table(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    entity_level: QuantEntityLevel,
    measure_kind: QuantMeasureKind,
    aggregation_method: QuantRollupMethod,
    top_n: int,
) -> LabelFreeQuantTable:
    sample_ids = tuple(sorted({record.sample_id for record in records}))
    grouped: dict[tuple[str, str], list[float]] = {}
    records_by_key: dict[tuple[str, str], list[Ms1FeatureRecord]] = {}
    feature_counts: dict[tuple[str, str], int] = {}
    missing_kinds: dict[tuple[str, str], list[MissingValueKind]] = {}
    protein_refs_by_entity: dict[str, tuple[str, ...]] = {}
    peptides_by_entity: dict[str, set[str]] = {}

    for record in records:
        entity_ids = _feature_entity_ids(record, entity_level=entity_level)
        if not entity_ids:
            continue
        for entity_id in entity_ids:
            key = (entity_id, record.sample_id)
            records_by_key.setdefault(key, []).append(record)
            missing_kinds.setdefault(key, []).append(record.missing_value_kind)
            peptides_by_entity.setdefault(entity_id, set()).add(
                record.canonical_peptide
            )
            if entity_level is QuantEntityLevel.PEPTIDE:
                protein_refs_by_entity.setdefault(entity_id, record.protein_refs)
            else:
                protein_refs_by_entity.setdefault(entity_id, (entity_id,))
            if record.missing_value_kind in (
                MissingValueKind.OBSERVED,
                MissingValueKind.ZERO,
            ):
                grouped.setdefault(key, []).append(float(record.intensity or 0.0))
                feature_counts[key] = feature_counts.get(key, 0) + 1

    entity_ids = tuple(sorted(peptides_by_entity))
    values: list[QuantValue] = []
    for entity_id in entity_ids:
        for sample_id in sample_ids:
            key = (entity_id, sample_id)
            observed_values = tuple(grouped.get(key, ()))
            bucket = tuple(
                sorted(
                    records_by_key.get(key, ()),
                    key=lambda record: (
                        -(record.intensity or 0.0),
                        record.canonical_peptide,
                        record.feature_id,
                    ),
                )
            )
            candidate_records = tuple(
                record
                for record in bucket
                if record.missing_value_kind
                in (MissingValueKind.OBSERVED, MissingValueKind.ZERO)
            )
            kinds = tuple(missing_kinds.get(key, (MissingValueKind.NOT_OBSERVED,)))
            missing_kind = _aggregate_missing_kind(kinds)
            abundance: float | None
            count = feature_counts.get(key, 0)
            if observed_values:
                abundance = _aggregate_abundance(
                    observed_values,
                    measure_kind=measure_kind,
                    aggregation_method=aggregation_method,
                    top_n=top_n,
                )
                if abundance == 0.0 and missing_kind is not MissingValueKind.OBSERVED:
                    missing_kind = MissingValueKind.ZERO
            else:
                abundance = None
            selected_records = candidate_records
            excluded_records: list[tuple[Ms1FeatureRecord, str]] = []
            if (
                measure_kind is QuantMeasureKind.INTENSITY
                and aggregation_method is QuantRollupMethod.TOP_N
                and len(candidate_records) > top_n
            ):
                selected_records = candidate_records[:top_n]
                excluded_records.extend(
                    (record, "excluded_by_top_n_rollup")
                    for record in candidate_records[top_n:]
                )
            excluded_records.extend(
                (record, "missing_value_filtered")
                for record in bucket
                if record.missing_value_kind is MissingValueKind.FILTERED
            )
            excluded_records.extend(
                (record, "missing_value_not_observed")
                for record in bucket
                if record.missing_value_kind is MissingValueKind.NOT_OBSERVED
            )
            values.append(
                QuantValue(
                    sample_id=sample_id,
                    entity_id=entity_id,
                    abundance=abundance,
                    missing_value_kind=missing_kind,
                    source_feature_count=count,
                    value_provenance=_build_quant_value_provenance(
                        aggregation_method=aggregation_method,
                        abundance=abundance,
                        selected_records=selected_records,
                        excluded_records=tuple(excluded_records),
                    ),
                )
            )

    return LabelFreeQuantTable(
        entity_level=entity_level,
        measure_kind=measure_kind,
        aggregation_method=aggregation_method,
        normalization_method=NormalizationMethod.NONE,
        sample_ids=sample_ids,
        entity_ids=entity_ids,
        values=tuple(values),
        entity_protein_refs=protein_refs_by_entity,
        entity_member_peptides={
            entity_id: tuple(sorted(peptides))
            for entity_id, peptides in sorted(peptides_by_entity.items())
        },
    )


def _table_matrix(
    table: LabelFreeQuantTable,
) -> tuple[np.ndarray, list[tuple[str, str]]]:
    matrix = quant_matrix_to_dense_array(table.to_quant_matrix())
    rows = list(table.entity_ids)
    cols = list(table.sample_ids)
    return matrix, [(entity_id, sample_id) for entity_id in rows for sample_id in cols]


def _rebuild_table_from_matrix(
    table: LabelFreeQuantTable,
    matrix: np.ndarray,
    *,
    normalization_method: NormalizationMethod,
    normalization_factors: dict[str, float],
) -> LabelFreeQuantTable:
    sample_index = {
        sample_id: index for index, sample_id in enumerate(table.sample_ids)
    }
    entity_index = {
        entity_id: index for index, entity_id in enumerate(table.entity_ids)
    }
    values: list[QuantValue] = []
    for value in table.values:
        rebuilt = value
        if value.abundance is not None:
            abundance = float(
                matrix[entity_index[value.entity_id], sample_index[value.sample_id]]
            )
            rebuilt = value.model_copy(update={"abundance": max(abundance, 0.0)})
        values.append(rebuilt)
    canonical_matrix = rebuild_quant_matrix_from_dense_array(
        table.to_quant_matrix(),
        matrix,
        transformation_step=f"normalization:{normalization_method.value}",
        metadata_updates={"normalization_method": normalization_method.value},
    )
    return table.model_copy(
        update={
            "values": tuple(values),
            "quant_matrix": canonical_matrix,
            "normalization_method": normalization_method,
            "normalization_factors": normalization_factors,
        }
    )


def build_quant_matrix_export(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...] = (),
) -> QuantMatrixExport:
    """Build a stable quant matrix export with sample metadata and normalization context."""
    metadata_lookup = _sample_metadata_lookup(design_entries)
    rows: list[QuantMatrixExportRow] = []
    for value in table.values:
        sample_metadata = metadata_lookup.get(
            value.sample_id,
            QuantSampleMetadataEntry(sample_id=value.sample_id),
        )
        rows.append(
            QuantMatrixExportRow(
                sample_metadata=sample_metadata,
                entity_id=value.entity_id,
                entity_level=table.entity_level,
                measure_kind=table.measure_kind,
                aggregation_method=table.aggregation_method,
                abundance=value.abundance,
                missing_value_kind=value.missing_value_kind,
                source_feature_count=value.source_feature_count,
                value_provenance=value.value_provenance,
                imputation_provenance=value.imputation_provenance,
                protein_refs=table.entity_protein_refs.get(value.entity_id, ()),
                member_peptides=table.entity_member_peptides.get(value.entity_id, ()),
            )
        )
    note = (
        "table is unnormalized"
        if table.normalization_method is NormalizationMethod.NONE
        else "table preserves explicit sample normalization factors"
    )
    imputation_note = (
        "table preserves only observed abundances"
        if table.imputation_method is ImputationMethod.NONE
        else "table includes explicit imputed abundances for downstream statistical use"
    )
    imputed_value_count = sum(
        1 for value in table.values if value.imputation_provenance is not None
    )
    return QuantMatrixExport(
        entity_level=table.entity_level,
        measure_kind=table.measure_kind,
        aggregation_method=table.aggregation_method,
        rows=tuple(
            sorted(
                rows,
                key=lambda row: (row.entity_id, row.sample_metadata.sample_id),
            )
        ),
        normalization_provenance=QuantNormalizationProvenance(
            normalization_method=table.normalization_method,
            normalization_factors=table.normalization_factors,
            note=note,
        ),
        imputation_provenance=QuantImputationProvenance(
            imputation_method=table.imputation_method,
            imputed_value_count=imputed_value_count,
            note=imputation_note,
        ),
    )


def build_label_based_quant_bundle(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    policy: LabelBasedQuantPolicy,
) -> LabelBasedQuantBundle:
    """Build a stable multiplex-channel manifest over a label-based quant table."""
    multiplex_entries = tuple(
        entry
        for entry in design_entries
        if entry.multiplex_group and entry.multiplex_channel
    )
    if not multiplex_entries:
        raise ValueError("label-based quantification requires multiplex design entries")
    if not policy.channel_entries:
        raise ValueError(
            "label-based quantification requires explicit expected channel policy entries"
        )

    design_lookup = {
        (entry.multiplex_group or "", entry.multiplex_channel or ""): entry
        for entry in multiplex_entries
    }
    table_sample_ids = set(table.sample_ids)
    channel_policy_lookup = {
        (entry.multiplex_group, entry.multiplex_channel): entry.channel_role
        for entry in policy.channel_entries
    }

    channels: list[LabelBasedChannelStateEntry] = []
    missing_channels: list[MissingMultiplexChannelEntry] = []

    seen_keys = sorted(set(design_lookup) | set(channel_policy_lookup))
    for multiplex_group, multiplex_channel in seen_keys:
        design_entry = design_lookup.get((multiplex_group, multiplex_channel))
        channel_role = channel_policy_lookup.get(
            (multiplex_group, multiplex_channel),
            _default_label_channel_role(design_entry)
            if design_entry is not None
            else LabelBasedChannelRole.SAMPLE,
        )
        present_in_design = design_entry is not None
        present_in_table = (
            design_entry.sample_id in table_sample_ids
            if design_entry is not None
            else False
        )
        if not present_in_design or not present_in_table:
            missing_channels.append(
                MissingMultiplexChannelEntry(
                    multiplex_group=multiplex_group,
                    multiplex_channel=multiplex_channel,
                    expected_role=channel_role,
                    policy=policy.missing_channel_policy,
                    message=(
                        "expected multiplex channel is absent from the design table"
                        if not present_in_design
                        else "design channel is present but has no quantification values in the table"
                    ),
                )
            )
            if policy.missing_channel_policy is MissingChannelPolicy.ERROR:
                raise ValueError(
                    "label-based quantification missing expected multiplex channel "
                    f"{multiplex_group}:{multiplex_channel}"
                )
        if (
            not present_in_design
            and policy.missing_channel_policy is MissingChannelPolicy.PRESERVE
        ):
            channels.append(
                LabelBasedChannelStateEntry(
                    multiplex_group=multiplex_group,
                    multiplex_channel=multiplex_channel,
                    sample_id=None,
                    condition=None,
                    sample_role=None,
                    channel_role=channel_role,
                    present_in_design=False,
                    present_in_table=False,
                    note="expected channel is preserved in the manifest even though it was not observed",
                )
            )
            continue
        if design_entry is None:
            continue
        if (
            not present_in_table
            and policy.missing_channel_policy is MissingChannelPolicy.PRESERVE
        ):
            note = "design channel is preserved even though no quantification values were observed"
        elif not present_in_table:
            note = (
                "design channel is represented as missing in the quantification table"
            )
        elif channel_role is LabelBasedChannelRole.CARRIER:
            note = "carrier channel remains explicit and is not silently treated as a biological sample"
        else:
            note = "observed multiplex channel is represented explicitly in the review manifest"
        channels.append(
            LabelBasedChannelStateEntry(
                multiplex_group=multiplex_group,
                multiplex_channel=multiplex_channel,
                sample_id=design_entry.sample_id,
                condition=design_entry.condition,
                sample_role=design_entry.sample_role,
                channel_role=channel_role,
                present_in_design=True,
                present_in_table=present_in_table,
                note=note,
            )
        )

    bundle = LabelBasedQuantBundle(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="label_based_quant_bundle",
            package_name="bijux-proteomics-core",
            status="generated",
        ),
        entity_level=table.entity_level,
        measure_kind=table.measure_kind,
        normalization_method=table.normalization_method,
        policy=policy,
        channels=tuple(
            sorted(
                channels,
                key=lambda entry: (entry.multiplex_group, entry.multiplex_channel),
            )
        ),
        missing_channels=tuple(
            sorted(
                missing_channels,
                key=lambda entry: (entry.multiplex_group, entry.multiplex_channel),
            )
        ),
    )
    return bundle.model_copy(
        update={
            "document_schema": bundle.document_schema.with_content_hash(
                bundle.to_dict()
            )
        }
    )


def normalize_multiplex_quant_table(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    policy: MultiplexNormalizationPolicy | None = None,
) -> LabelFreeQuantTable:
    """Normalize a multiplex quant table independently within each plex group."""
    if table.measure_kind is not QuantMeasureKind.INTENSITY:
        raise ValueError("multiplex normalization only applies to intensity tables")
    active_policy = policy or MultiplexNormalizationPolicy()
    multiplex_lookup = _multiplex_channel_lookup(design_entries)
    if not multiplex_lookup:
        raise ValueError("multiplex normalization requires multiplex design metadata")
    if active_policy.method is NormalizationMethod.NONE:
        quant_matrix = rebuild_quant_matrix_from_dense_array(
            table.to_quant_matrix(),
            quant_matrix_to_dense_array(table.to_quant_matrix()),
            transformation_step="normalization:none",
            metadata_updates={"normalization_method": NormalizationMethod.NONE.value},
        )
        return table.model_copy(
            update={
                "quant_matrix": quant_matrix,
                "normalization_method": NormalizationMethod.NONE,
                "normalization_factors": dict.fromkeys(table.sample_ids, 1.0),
            }
        )

    matrix, _ = _table_matrix(table)
    sample_index = {
        sample_id: index for index, sample_id in enumerate(table.sample_ids)
    }
    grouped_samples: dict[str, list[str]] = {}
    for sample_id in table.sample_ids:
        if sample_id not in multiplex_lookup:
            continue
        grouped_samples.setdefault(multiplex_lookup[sample_id][0], []).append(sample_id)
    if not grouped_samples:
        raise ValueError(
            "multiplex normalization requires at least one multiplex sample in the table"
        )

    normalized = matrix.copy()
    factors = dict.fromkeys(table.sample_ids, 1.0)
    for group_sample_ids in grouped_samples.values():
        if active_policy.method is NormalizationMethod.MEDIAN:
            sample_medians = {
                sample_id: float(np.nanmedian(matrix[:, sample_index[sample_id]]))
                if np.any(~np.isnan(matrix[:, sample_index[sample_id]]))
                else float("nan")
                for sample_id in group_sample_ids
            }
            finite_medians = [
                median
                for median in sample_medians.values()
                if math.isfinite(median) and median > 0
            ]
            group_median = (
                float(np.median(np.array(finite_medians, dtype=float)))
                if finite_medians
                else 1.0
            )
            for sample_id in group_sample_ids:
                sample_median = sample_medians[sample_id]
                factor = (
                    group_median / sample_median
                    if math.isfinite(sample_median) and sample_median > 0
                    else 1.0
                )
                factors[sample_id] = factor
                normalized[:, sample_index[sample_id]] = (
                    normalized[:, sample_index[sample_id]] * factor
                )
            continue
        raise ValueError(
            "multiplex normalization currently supports only explicit none or group-wise median normalization"
        )
    return _rebuild_table_from_matrix(
        table,
        normalized,
        normalization_method=active_policy.method,
        normalization_factors=factors,
    )


def build_multiplex_channel_balance_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    policy: MultiplexNormalizationPolicy | None = None,
) -> MultiplexChannelBalanceReport:
    """Build a channel-balance report over multiplex groups."""
    active_policy = policy or MultiplexNormalizationPolicy()
    multiplex_lookup = _multiplex_channel_lookup(design_entries)
    grouped_entries: dict[str, list[tuple[str, str, LabelBasedChannelRole, float]]] = {}
    for sample_id in table.sample_ids:
        multiplex_entry = multiplex_lookup.get(sample_id)
        if multiplex_entry is None:
            continue
        multiplex_group, multiplex_channel, channel_role = multiplex_entry
        total_abundance = float(
            sum(
                value.abundance or 0.0
                for value in table.values
                if value.sample_id == sample_id and value.abundance is not None
            )
        )
        grouped_entries.setdefault(multiplex_group, []).append(
            (sample_id, multiplex_channel, channel_role, total_abundance)
        )
    entries: list[MultiplexChannelBalanceEntry] = []
    for multiplex_group, bucket in sorted(grouped_entries.items()):
        totals = np.array([entry[3] for entry in bucket], dtype=float)
        group_median = float(np.median(totals)) if totals.size else 0.0
        for sample_id, multiplex_channel, channel_role, total_abundance in sorted(
            bucket,
            key=lambda entry: entry[1],
        ):
            ratio = (total_abundance / group_median) if group_median > 0 else 0.0
            entries.append(
                MultiplexChannelBalanceEntry(
                    multiplex_group=multiplex_group,
                    multiplex_channel=multiplex_channel,
                    sample_id=sample_id,
                    channel_role=channel_role,
                    total_abundance=total_abundance,
                    ratio_to_group_median=ratio,
                    flagged=(
                        ratio > active_policy.balance_ratio_threshold
                        or ratio < 1.0 / active_policy.balance_ratio_threshold
                    ),
                )
            )
    return MultiplexChannelBalanceReport(
        policy=active_policy,
        entries=tuple(
            sorted(
                entries,
                key=lambda entry: (entry.multiplex_group, entry.multiplex_channel),
            )
        ),
    )


def _protein_quant_assignment_targets(
    record: Ms1FeatureRecord,
    *,
    assignment_policy: ProteinQuantAssignmentPolicy,
) -> tuple[tuple[str, float], ...]:
    if not record.protein_refs or record.intensity is None:
        return ()
    if assignment_policy is ProteinQuantAssignmentPolicy.INFERENCE_INCLUSIVE:
        return tuple(
            (protein_ref, float(record.intensity))
            for protein_ref in record.protein_refs
        )
    if assignment_policy is ProteinQuantAssignmentPolicy.QUANT_UNIQUE_ONLY:
        if len(record.protein_refs) == 1:
            return ((record.protein_refs[0], float(record.intensity)),)
        return ()
    split_intensity = float(record.intensity) / len(record.protein_refs)
    return tuple((protein_ref, split_intensity) for protein_ref in record.protein_refs)


def build_protein_quant_policy_comparison_report(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    policies: tuple[ProteinQuantAssignmentPolicy, ...] = (
        ProteinQuantAssignmentPolicy.INFERENCE_INCLUSIVE,
        ProteinQuantAssignmentPolicy.QUANT_UNIQUE_ONLY,
        ProteinQuantAssignmentPolicy.QUANT_SPLIT_SHARED,
    ),
) -> ProteinQuantPolicyComparisonReport:
    """Compare protein-level quant results under explicit shared-peptide policies."""
    per_policy: dict[
        ProteinQuantAssignmentPolicy,
        dict[tuple[str, str], list[tuple[Ms1FeatureRecord, float]]],
    ] = {}
    proteins: set[str] = set()
    sample_ids: set[str] = set()
    for policy in policies:
        grouped: dict[tuple[str, str], list[tuple[Ms1FeatureRecord, float]]] = (
            defaultdict(list)
        )
        for record in records:
            sample_ids.add(record.sample_id)
            for protein_ref, intensity in _protein_quant_assignment_targets(
                record,
                assignment_policy=policy,
            ):
                proteins.add(protein_ref)
                grouped[(protein_ref, record.sample_id)].append((record, intensity))
        per_policy[policy] = grouped

    entries: list[ProteinQuantPolicyComparisonEntry] = []
    for protein_ref in sorted(proteins):
        for sample_id in sorted(sample_ids):
            values: list[ProteinQuantPolicyValue] = []
            abundances: list[float] = []
            for policy in policies:
                bucket = sorted(
                    per_policy[policy].get((protein_ref, sample_id), ()),
                    key=lambda item: (item[0].canonical_peptide, item[0].feature_id),
                )
                abundance = (
                    float(sum(intensity for _, intensity in bucket)) if bucket else None
                )
                if abundance is not None:
                    abundances.append(abundance)
                values.append(
                    ProteinQuantPolicyValue(
                        assignment_policy=policy,
                        abundance=abundance,
                        contributing_peptides=tuple(
                            dict.fromkeys(
                                record.canonical_peptide for record, _ in bucket
                            )
                        ),
                        shared_peptide_count=sum(
                            1 for record, _ in bucket if len(record.protein_refs) > 1
                        ),
                    )
                )
            entries.append(
                ProteinQuantPolicyComparisonEntry(
                    protein_ref=protein_ref,
                    sample_id=sample_id,
                    policy_values=tuple(values),
                    max_abundance_difference=(
                        max(abundances) - min(abundances) if abundances else 0.0
                    ),
                )
            )
    return ProteinQuantPolicyComparisonReport(
        policies=policies,
        entries=tuple(entries),
    )


def build_protein_quant_rollup_evidence(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    top_n: int = 3,
) -> tuple[ProteinQuantRollupEvidenceEntry, ...]:
    """Build explicit protein rollup evidence from contributing peptide features."""
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    entries: list[ProteinQuantRollupEvidenceEntry] = []
    value_lookup = _matrix_value_index(table)
    for protein_ref in table.entity_ids:
        for sample_id in table.sample_ids:
            value = value_lookup[(protein_ref, sample_id)]
            entries.append(
                ProteinQuantRollupEvidenceEntry(
                    protein_ref=protein_ref,
                    sample_id=sample_id,
                    aggregation_method=aggregation_method,
                    abundance=value.abundance,
                    contributing_feature_ids=(
                        ()
                        if value.value_provenance is None
                        else value.value_provenance.source_feature_ids
                    ),
                    contributing_peptides=(
                        ()
                        if value.value_provenance is None
                        else value.value_provenance.source_peptides
                    ),
                    missing_value_kind=value.missing_value_kind,
                )
            )
    return tuple(
        sorted(
            entries,
            key=lambda entry: (entry.protein_ref, entry.sample_id),
        )
    )


def build_label_free_provenance_bundle(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    normalization_method: NormalizationMethod = NormalizationMethod.NONE,
    top_n: int = 3,
) -> LabelFreeProvenanceBundle:
    """Build peptide-level and feature-level provenance for an LFQ workflow."""
    peptide_table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    protein_table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    if normalization_method is not NormalizationMethod.NONE:
        peptide_table = normalize_label_free_table(
            peptide_table,
            method=normalization_method,
        )
        protein_table = normalize_label_free_table(
            protein_table,
            method=normalization_method,
        )
    peptide_value_lookup = _matrix_value_index(peptide_table)
    protein_value_lookup = _matrix_value_index(protein_table)

    grouped_features: dict[tuple[str, str], list[Ms1FeatureRecord]] = defaultdict(list)
    for record in records:
        grouped_features[(record.canonical_peptide, record.sample_id)].append(record)

    peptide_entries: list[LabelFreePeptideProvenanceEntry] = []
    for canonical_peptide in peptide_table.entity_ids:
        for sample_id in peptide_table.sample_ids:
            value = peptide_value_lookup[(canonical_peptide, sample_id)]
            features = sorted(
                grouped_features.get((canonical_peptide, sample_id), ()),
                key=lambda record: record.feature_id,
            )
            peptide_entries.append(
                LabelFreePeptideProvenanceEntry(
                    sample_id=sample_id,
                    canonical_peptide=canonical_peptide,
                    abundance=value.abundance,
                    missing_value_kind=value.missing_value_kind,
                    contributing_feature_ids=tuple(
                        record.feature_id for record in features
                    ),
                    protein_refs=tuple(
                        dict.fromkeys(
                            protein_ref
                            for record in features
                            for protein_ref in record.protein_refs
                        )
                    ),
                )
            )

    protein_entries = []
    for entry in build_protein_quant_rollup_evidence(
        records,
        aggregation_method=aggregation_method,
        top_n=top_n,
    ):
        protein_entries.append(
            entry.model_copy(
                update={
                    "abundance": protein_value_lookup[
                        (entry.protein_ref, entry.sample_id)
                    ].abundance,
                    "missing_value_kind": protein_value_lookup[
                        (entry.protein_ref, entry.sample_id)
                    ].missing_value_kind,
                }
            )
        )

    bundle = LabelFreeProvenanceBundle(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="label_free_provenance_bundle",
            package_name="bijux-proteomics-core",
            status="generated",
        ),
        aggregation_method=aggregation_method,
        normalization_method=normalization_method,
        feature_entries=tuple(
            LabelFreeFeatureProvenanceEntry(
                feature_id=record.feature_id,
                sample_id=record.sample_id,
                canonical_peptide=record.canonical_peptide,
                protein_refs=record.protein_refs,
                intensity=record.intensity,
                missing_value_kind=record.missing_value_kind,
            )
            for record in sorted(
                records,
                key=lambda record: (
                    record.sample_id,
                    record.canonical_peptide,
                    record.feature_id,
                ),
            )
        ),
        peptide_entries=tuple(
            sorted(
                peptide_entries,
                key=lambda entry: (entry.canonical_peptide, entry.sample_id),
            )
        ),
        protein_entries=tuple(
            sorted(
                protein_entries,
                key=lambda entry: (entry.protein_ref, entry.sample_id),
            )
        ),
    )
    return bundle.model_copy(
        update={
            "document_schema": bundle.document_schema.with_content_hash(
                bundle.to_dict()
            )
        }
    )


def export_label_free_provenance_bundle(
    bundle: LabelFreeProvenanceBundle,
    path: Path,
) -> None:
    """Write a stable JSON bundle for LFQ provenance review."""
    path.write_text(bundle.to_stable_json() + "\n", encoding="utf-8")


def export_quant_matrix_tsv(
    matrix_export: QuantMatrixExport,
    path: Path,
) -> None:
    """Write one stable TSV export for a quantification matrix."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "sample_id",
                "condition",
                "replicate",
                "fraction",
                "batch",
                "instrument",
                "search_engine",
                "entity_id",
                "entity_level",
                "measure_kind",
                "aggregation_method",
                "abundance",
                "missing_value_kind",
                "value_origin",
                "source_feature_count",
                "source_feature_ids",
                "source_peptides",
                "source_precursor_ids",
                "excluded_contributor_ids",
                "exclusion_reason_codes",
                "imputation_method",
                "imputation_strategy",
                "imputation_reference_group",
                "imputation_donor_sample_ids",
                "imputation_donor_entity_ids",
                "original_missing_value_kind",
                "protein_refs",
                "member_peptides",
                "normalization_method",
                "normalization_factor",
            ]
        )
        for row in matrix_export.rows:
            writer.writerow(
                [
                    row.sample_metadata.sample_id,
                    row.sample_metadata.condition or "",
                    row.sample_metadata.replicate or "",
                    row.sample_metadata.fraction or "",
                    row.sample_metadata.batch or "",
                    row.sample_metadata.instrument or "",
                    row.sample_metadata.search_engine or "",
                    row.entity_id,
                    row.entity_level.value,
                    row.measure_kind.value,
                    row.aggregation_method.value,
                    "" if row.abundance is None else row.abundance,
                    row.missing_value_kind.value,
                    (
                        ""
                        if row.value_provenance is None
                        else row.value_provenance.value_origin.value
                    ),
                    row.source_feature_count,
                    (
                        ""
                        if row.value_provenance is None
                        else ";".join(row.value_provenance.source_feature_ids)
                    ),
                    (
                        ""
                        if row.value_provenance is None
                        else ";".join(row.value_provenance.source_peptides)
                    ),
                    (
                        ""
                        if row.value_provenance is None
                        else ";".join(row.value_provenance.source_precursor_ids)
                    ),
                    (
                        ""
                        if row.value_provenance is None
                        else ";".join(
                            excluded.contributor.contributor_id
                            for excluded in row.value_provenance.excluded_contributors
                        )
                    ),
                    (
                        ""
                        if row.value_provenance is None
                        else ";".join(
                            excluded.reason_code
                            for excluded in row.value_provenance.excluded_contributors
                        )
                    ),
                    (
                        ""
                        if row.imputation_provenance is None
                        else row.imputation_provenance.method.value
                    ),
                    (
                        ""
                        if row.imputation_provenance is None
                        else row.imputation_provenance.strategy
                    ),
                    (
                        ""
                        if row.imputation_provenance is None
                        or row.imputation_provenance.reference_group is None
                        else row.imputation_provenance.reference_group
                    ),
                    (
                        ""
                        if row.imputation_provenance is None
                        else ";".join(row.imputation_provenance.donor_sample_ids)
                    ),
                    (
                        ""
                        if row.imputation_provenance is None
                        else ";".join(row.imputation_provenance.donor_entity_ids)
                    ),
                    (
                        ""
                        if row.imputation_provenance is None
                        else row.imputation_provenance.original_missing_value_kind.value
                    ),
                    ";".join(row.protein_refs),
                    ";".join(row.member_peptides),
                    matrix_export.normalization_provenance.normalization_method.value,
                    matrix_export.normalization_provenance.normalization_factors.get(
                        row.sample_metadata.sample_id,
                        1.0,
                    ),
                ]
            )


def build_quant_reproducibility_manifest(
    table: LabelFreeQuantTable,
) -> QuantReproducibilityManifest:
    """Build a stable reproducibility manifest for one quantification table."""
    payload = [
        table.entity_level.value,
        table.measure_kind.value,
        table.aggregation_method.value,
        table.normalization_method.value,
        tuple(table.sample_ids),
        tuple(table.entity_ids),
        tuple(sorted(table.normalization_factors.items())),
        tuple(
            (
                value.entity_id,
                value.sample_id,
                value.abundance,
                value.missing_value_kind.value,
                value.source_feature_count,
                None
                if value.value_provenance is None
                else (
                    value.value_provenance.aggregation_method.value,
                    value.value_provenance.value_origin.value,
                    tuple(value.value_provenance.source_feature_ids),
                    tuple(value.value_provenance.source_peptides),
                    tuple(value.value_provenance.source_precursor_ids),
                    tuple(
                        (
                            contributor.contributor_id,
                            contributor.contributor_kind.value,
                            contributor.canonical_peptide,
                            tuple(contributor.protein_refs),
                            contributor.abundance,
                            contributor.missing_value_kind.value,
                        )
                        for contributor in value.value_provenance.selected_contributors
                    ),
                    tuple(
                        (
                            excluded.contributor.contributor_id,
                            excluded.contributor.contributor_kind.value,
                            excluded.reason_code,
                        )
                        for excluded in value.value_provenance.excluded_contributors
                    ),
                ),
                None
                if value.imputation_provenance is None
                else (
                    value.imputation_provenance.method.value,
                    value.imputation_provenance.original_missing_value_kind.value,
                    value.imputation_provenance.strategy,
                    value.imputation_provenance.reference_group,
                    tuple(value.imputation_provenance.donor_sample_ids),
                    tuple(value.imputation_provenance.donor_entity_ids),
                ),
            )
            for value in sorted(
                table.values,
                key=lambda entry: (entry.entity_id, entry.sample_id),
            )
        ),
    ]
    reproducibility_hash = hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()
    manifest = QuantReproducibilityManifest(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="quant_reproducibility_manifest",
            package_name="bijux-proteomics-core",
            status="generated",
            created_at=_STABLE_DOCUMENT_TIME,
            updated_at=_STABLE_DOCUMENT_TIME,
        ),
        entity_level=table.entity_level,
        measure_kind=table.measure_kind,
        aggregation_method=table.aggregation_method,
        normalization_method=table.normalization_method,
        sample_ids=table.sample_ids,
        entity_ids=table.entity_ids,
        value_count=len(table.values),
        reproducibility_hash=reproducibility_hash,
    )
    return manifest.model_copy(
        update={
            "document_schema": manifest.document_schema.with_content_hash(
                manifest.to_dict()
            )
        }
    )


def export_quant_reproducibility_manifest(
    manifest: QuantReproducibilityManifest,
    path: Path,
) -> None:
    """Write a stable JSON reproducibility manifest for quantification outputs."""
    path.write_text(manifest.to_stable_json() + "\n", encoding="utf-8")


def build_quant_artifact_bundle(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...] = (),
    missing_value_policy: MissingValueSummaryPolicy | None = None,
    imputation_report: ImputationReport | None = None,
    imputation_sensitivity_report: ImputationSensitivityReport | None = None,
    missingness_entity_summary: MissingnessEntitySummaryReport | None = None,
    missingness_condition_summary: MissingnessConditionSummaryReport | None = None,
    missingness_intensity_dependence: MissingnessIntensityDependenceReport | None = None,
    missingness_mechanism_report: MissingDataMechanismReport | None = None,
    replicate_qc_report: ReplicateAndBatchQcReport | None = None,
    normalization_comparison_report: NormalizationComparisonReport | None = None,
    normalization_strategy_report: NormalizationStrategyComparisonReport | None = None,
    limma_compatible_package: object | None = None,
    msstats_compatible_input_report: object | None = None,
    design_matrix_report: QuantDesignMatrixReport | None = None,
    design_model_fit_report: QuantDesignModelFitReport | None = None,
    differential_abundance_report: DifferentialAbundanceReport | None = None,
    differential_abundance_multi_condition_report: (
        MultiConditionDifferentialAbundanceReport | None
    ) = None,
    time_course_differential_report: TimeCourseDifferentialReport | None = None,
) -> QuantArtifactBundle:
    """Bundle quant outputs so review can happen without workflow runtime logs."""
    bundle = QuantArtifactBundle(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="quant_artifact_bundle",
            package_name="bijux-proteomics-core",
            status="generated",
            created_at=_STABLE_DOCUMENT_TIME,
            updated_at=_STABLE_DOCUMENT_TIME,
        ),
        matrix_export=build_quant_matrix_export(table, design_entries=design_entries),
        missing_value_summary=summarize_missing_values(
            table,
            policy=missing_value_policy,
        ),
        imputation_report=imputation_report,
        imputation_sensitivity_report=imputation_sensitivity_report,
        missingness_entity_summary=missingness_entity_summary,
        missingness_condition_summary=missingness_condition_summary,
        missingness_intensity_dependence=missingness_intensity_dependence,
        missingness_mechanism_report=missingness_mechanism_report,
        replicate_qc_report=replicate_qc_report,
        reproducibility_manifest=build_quant_reproducibility_manifest(table),
        normalization_comparison_report=normalization_comparison_report,
        normalization_strategy_report=normalization_strategy_report,
        limma_compatible_package=limma_compatible_package,
        msstats_compatible_input_report=msstats_compatible_input_report,
        design_matrix_report=design_matrix_report,
        design_model_fit_report=design_model_fit_report,
        differential_abundance_report=differential_abundance_report,
        differential_abundance_multi_condition_report=(
            differential_abundance_multi_condition_report
        ),
        time_course_differential_report=time_course_differential_report,
    )
    return bundle.model_copy(
        update={
            "document_schema": bundle.document_schema.with_content_hash(
                bundle.to_dict()
            )
        }
    )


def export_quant_artifact_bundle(bundle: QuantArtifactBundle, path: Path) -> None:
    """Write a stable JSON artifact bundle for quant review."""
    path.write_text(bundle.to_stable_json() + "\n", encoding="utf-8")


def build_normalization_comparison_report(
    before: LabelFreeQuantTable,
    after: LabelFreeQuantTable,
) -> NormalizationComparisonReport:
    """Build a before/after normalization summary over sample totals and spread."""
    from bijux_proteomics.quantification.normalization import (
        build_normalization_comparison_report as _implementation,
    )

    return _implementation(before, after)


def build_normalization_strategy_comparison_report(
    table: LabelFreeQuantTable,
    *,
    methods: tuple[NormalizationMethod, ...] = (
        NormalizationMethod.NONE,
        NormalizationMethod.TIC,
        NormalizationMethod.MEDIAN,
        NormalizationMethod.QUANTILE,
        NormalizationMethod.VSN_LIKE,
    ),
) -> NormalizationStrategyComparisonReport:
    """Compare normalization methods using stable sample-balance summary metrics."""
    from bijux_proteomics.quantification.normalization import (
        build_normalization_strategy_comparison_report as _implementation,
    )

    return _implementation(table, methods=methods)


def _log2_values(table: LabelFreeQuantTable, sample_id: str) -> np.ndarray:
    lookup = _matrix_value_index(table)
    values: list[float] = []
    for entity_id in table.entity_ids:
        cell = lookup[(entity_id, sample_id)]
        if cell.abundance is None:
            continue
        values.append(math.log2(cell.abundance + 1.0))
    return np.array(values, dtype=float)


def _betacf(a: float, b: float, x: float) -> float:
    max_iter = 200
    eps = 3.0e-7
    fpmin = 1.0e-30
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for step in range(1, max_iter + 1):
        step_twice = 2 * step
        aa = step * (b - step) * x / ((qam + step_twice) * (a + step_twice))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(a + step) * (qab + step) * x / ((a + step_twice) * (qap + step_twice))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _regularized_beta(x: float, a: float, b: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    log_beta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(log_beta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def _student_t_two_sided_p_value(
    t_statistic: float, degrees_of_freedom: float
) -> float:
    if (
        not math.isfinite(t_statistic)
        or not math.isfinite(degrees_of_freedom)
        or degrees_of_freedom <= 0
    ):
        return 1.0
    x = degrees_of_freedom / (degrees_of_freedom + t_statistic * t_statistic)
    return min(max(_regularized_beta(x, degrees_of_freedom / 2.0, 0.5), 0.0), 1.0)


def _welch_t_test(values_a: np.ndarray, values_b: np.ndarray) -> tuple[float, float]:
    if values_a.size < 2 or values_b.size < 2:
        return 0.0, 1.0
    mean_a = float(np.mean(values_a))
    mean_b = float(np.mean(values_b))
    var_a = float(np.var(values_a, ddof=1))
    var_b = float(np.var(values_b, ddof=1))
    if var_a == 0.0 and var_b == 0.0:
        return mean_b - mean_a, 1.0
    denominator = math.sqrt((var_a / values_a.size) + (var_b / values_b.size))
    if denominator == 0.0:
        return mean_b - mean_a, 1.0
    t_statistic = (mean_b - mean_a) / denominator
    numerator = (var_a / values_a.size + var_b / values_b.size) ** 2
    denominator_df = ((var_a / values_a.size) ** 2) / (values_a.size - 1) + (
        (var_b / values_b.size) ** 2
    ) / (values_b.size - 1)
    if denominator_df == 0.0:
        return mean_b - mean_a, 1.0
    degrees_of_freedom = numerator / denominator_df
    return mean_b - mean_a, _student_t_two_sided_p_value(
        abs(t_statistic), degrees_of_freedom
    )


def _effect_size_and_uncertainty(
    values_a: np.ndarray,
    values_b: np.ndarray,
    log2_fold_change: float,
) -> tuple[float | None, float | None, float | None, float | None, str | None]:
    if values_a.size < 2 or values_b.size < 2:
        return (
            None,
            None,
            None,
            None,
            "confidence intervals and effect sizes require at least two observations per condition",
        )
    variance_a = float(np.var(values_a, ddof=1))
    variance_b = float(np.var(values_b, ddof=1))
    standard_error = math.sqrt(
        variance_a / float(values_a.size) + variance_b / float(values_b.size)
    )
    interval_radius = 1.96 * standard_error
    pooled_variance_numerator = (values_a.size - 1) * variance_a + (
        values_b.size - 1
    ) * variance_b
    pooled_variance_denominator = values_a.size + values_b.size - 2
    pooled_sd = math.sqrt(pooled_variance_numerator / pooled_variance_denominator)
    cohens_d = (log2_fold_change / pooled_sd) if pooled_sd > 0 else None
    note = None
    if standard_error > 1.0:
        note = "uncertainty remains wide relative to the estimated fold change"
    return (
        standard_error,
        log2_fold_change - interval_radius,
        log2_fold_change + interval_radius,
        cohens_d,
        note,
    )


def parse_ms1_feature_table(
    path: Path,
    *,
    mapping: Ms1FeatureColumnMapping | None = None,
) -> Ms1FeatureParseReport:
    """Parse one MS1 feature quantification table into stable feature records."""
    active_mapping = mapping or Ms1FeatureColumnMapping(
        sample_id="sample_id",
        peptide="peptide",
        intensity="intensity",
        protein_refs="proteins",
        feature_id="feature_id",
        charge="charge",
        mz="mz",
        retention_time_seconds="retention_time_seconds",
        missing_reason="missing_reason",
    )

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return Ms1FeatureParseReport(total_rows=0, column_mapping=active_mapping)
    reader = csv.DictReader(lines, delimiter=_detect_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("MS1 feature table must include a header row")
    required_columns = {
        active_mapping.sample_id,
        active_mapping.peptide,
        active_mapping.intensity,
    }
    missing_columns = required_columns - set(reader.fieldnames)
    if missing_columns:
        raise ValueError(
            "MS1 feature table is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    accepted: list[Ms1FeatureRecord] = []
    rejected: list[RejectedMs1FeatureRow] = []
    for row_number, row in enumerate(reader, start=2):
        raw_fields = {
            str(key): str(value or "") for key, value in row.items() if key is not None
        }
        issues: list[QuantValidationIssue] = []
        sample_id = raw_fields.get(active_mapping.sample_id, "").strip()
        peptide = raw_fields.get(active_mapping.peptide, "").strip()
        intensity_token = raw_fields.get(active_mapping.intensity, "").strip()
        missing_reason = (
            raw_fields.get(active_mapping.missing_reason, "").strip()
            if active_mapping.missing_reason
            else ""
        )
        if not sample_id:
            issues.append(
                _row_issue("missing_sample_id", "missing sample identifier", row_number)
            )
        if not peptide:
            issues.append(
                _row_issue("missing_peptide", "missing peptide sequence", row_number)
            )
        canonical_peptide = peptide
        if peptide:
            try:
                canonical_peptide = canonicalize_modified_peptide(peptide)
            except ValueError as exc:
                issues.append(
                    _row_issue("invalid_peptide_notation", str(exc), row_number)
                )

        intensity: float | None
        missing_value_kind: MissingValueKind
        normalized_missing_reason = missing_reason.strip().lower()
        if not intensity_token:
            intensity = None
            if normalized_missing_reason == "filtered":
                missing_value_kind = MissingValueKind.FILTERED
            else:
                missing_value_kind = MissingValueKind.NOT_OBSERVED
        else:
            try:
                intensity = float(intensity_token)
            except ValueError:
                issues.append(
                    _row_issue(
                        "invalid_intensity", "invalid intensity value", row_number
                    )
                )
                intensity = None
            if intensity is not None and intensity < 0:
                issues.append(
                    _row_issue(
                        "negative_intensity",
                        "intensity must be non-negative",
                        row_number,
                    )
                )
            if intensity is not None and intensity == 0:
                missing_value_kind = MissingValueKind.ZERO
            else:
                missing_value_kind = MissingValueKind.OBSERVED

        charge: int | None = None
        if active_mapping.charge:
            charge_token = raw_fields.get(active_mapping.charge, "").strip()
            if charge_token:
                try:
                    charge = int(charge_token)
                    if charge < 1:
                        raise ValueError
                except ValueError:
                    issues.append(
                        _row_issue("invalid_charge", "invalid charge value", row_number)
                    )

        mz: float | None = None
        if active_mapping.mz:
            mz_token = raw_fields.get(active_mapping.mz, "").strip()
            if mz_token:
                try:
                    mz = float(mz_token)
                    if mz <= 0:
                        raise ValueError
                except ValueError:
                    issues.append(
                        _row_issue(
                            "invalid_mz", "invalid precursor m/z value", row_number
                        )
                    )

        retention_time_seconds: float | None = None
        if active_mapping.retention_time_seconds:
            rt_token = raw_fields.get(active_mapping.retention_time_seconds, "").strip()
            if rt_token:
                try:
                    retention_time_seconds = float(rt_token)
                    if retention_time_seconds < 0:
                        raise ValueError
                except ValueError:
                    issues.append(
                        _row_issue(
                            "invalid_retention_time",
                            "invalid retention time value",
                            row_number,
                        )
                    )

        protein_refs = _parse_protein_refs(
            raw_fields.get(active_mapping.protein_refs, "")
            if active_mapping.protein_refs
            else "",
            active_mapping.protein_separator,
        )

        if issues:
            rejected.append(
                RejectedMs1FeatureRow(
                    row_number=row_number,
                    raw_fields=raw_fields,
                    issues=tuple(issues),
                )
            )
            continue

        accepted.append(
            Ms1FeatureRecord(
                feature_id=(
                    raw_fields.get(active_mapping.feature_id, "").strip()
                    if active_mapping.feature_id
                    else f"feature-{row_number}"
                )
                or f"feature-{row_number}",
                sample_id=sample_id,
                peptide=peptide,
                canonical_peptide=canonical_peptide,
                intensity=intensity,
                protein_refs=protein_refs,
                charge=charge,
                mz=mz,
                retention_time_seconds=retention_time_seconds,
                missing_value_kind=missing_value_kind,
                missing_reason=missing_reason or None,
                provenance=ImportedEvidenceProvenance.from_single_row(
                    source_engine="ms1-feature-table",
                    source_file=str(path),
                    source_row_number=row_number,
                    original_identifiers={
                        "feature_id": (
                            raw_fields.get(active_mapping.feature_id, "").strip()
                            if active_mapping.feature_id
                            else f"feature-{row_number}"
                        )
                        or f"feature-{row_number}",
                        "sample_id": sample_id,
                        "peptide": peptide,
                    },
                ),
            )
        )

    accepted = sorted(
        accepted,
        key=lambda record: (
            record.sample_id,
            record.canonical_peptide,
            record.feature_id,
        ),
    )
    return Ms1FeatureParseReport(
        total_rows=len(accepted) + len(rejected),
        accepted_records=tuple(accepted),
        rejected_rows=tuple(rejected),
        column_mapping=active_mapping,
    )


def parse_precursor_intensity_table(
    path: Path,
    *,
    mapping: PrecursorIntensityColumnMapping | None = None,
) -> PrecursorIntensityParseReport:
    """Parse one precursor-intensity table into stable precursor records."""

    active_mapping = mapping or PrecursorIntensityColumnMapping(
        peptide="peptide",
        modified_peptide="modified_peptide",
        intensity="intensity",
        sample_id="sample_id",
        run_id="run_id",
        protein_refs="proteins",
        precursor_id="precursor_id",
        charge="charge",
        missing_reason="missing_reason",
    )

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return PrecursorIntensityParseReport(
            total_rows=0,
            column_mapping=active_mapping,
        )
    reader = csv.DictReader(lines, delimiter=_detect_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("precursor intensity table must include a header row")

    required_columns = {active_mapping.peptide, active_mapping.intensity}
    missing_columns = required_columns - set(reader.fieldnames)
    if missing_columns:
        raise ValueError(
            "precursor intensity table is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )
    sample_column_present = (
        active_mapping.sample_id is not None
        and active_mapping.sample_id in reader.fieldnames
    )
    run_column_present = (
        active_mapping.run_id is not None and active_mapping.run_id in reader.fieldnames
    )
    if not sample_column_present and not run_column_present:
        expected_columns = tuple(
            column
            for column in (active_mapping.sample_id, active_mapping.run_id)
            if column is not None
        )
        raise ValueError(
            "precursor intensity table is missing required sample or run column: "
            + ", ".join(expected_columns)
        )

    accepted: list[PrecursorIntensityRecord] = []
    rejected: list[RejectedPrecursorIntensityRow] = []
    for row_number, row in enumerate(reader, start=2):
        raw_fields = {
            str(key): str(value or "") for key, value in row.items() if key is not None
        }
        issues: list[QuantValidationIssue] = []
        sample_token = (
            raw_fields.get(active_mapping.sample_id, "").strip()
            if active_mapping.sample_id is not None
            else ""
        )
        run_token = (
            raw_fields.get(active_mapping.run_id, "").strip()
            if active_mapping.run_id is not None
            else ""
        )
        sample_id = sample_token or run_token
        if not sample_id:
            issues.append(
                _row_issue(
                    "missing_sample_or_run",
                    "missing sample or run identifier",
                    row_number,
                )
            )

        peptide_token = raw_fields.get(active_mapping.peptide, "").strip()
        modified_peptide_token = (
            raw_fields.get(active_mapping.modified_peptide, "").strip()
            if active_mapping.modified_peptide
            else ""
        )
        peptide_notation = modified_peptide_token or peptide_token
        if not peptide_notation:
            issues.append(
                _row_issue(
                    "missing_peptide",
                    "missing peptide or modified peptide identifier",
                    row_number,
                )
            )
            peptide_sequence = ""
            canonical_peptide = ""
        else:
            try:
                canonical_peptide = canonicalize_modified_peptide(peptide_notation)
                peptide_sequence = peptide_token or parse_modified_peptide(
                    canonical_peptide
                ).sequence
            except ValueError as exc:
                issues.append(
                    _row_issue("invalid_peptide_notation", str(exc), row_number)
                )
                peptide_sequence = peptide_token
                canonical_peptide = peptide_notation

        intensity_token = raw_fields.get(active_mapping.intensity, "").strip()
        missing_reason = (
            raw_fields.get(active_mapping.missing_reason, "").strip()
            if active_mapping.missing_reason
            else ""
        )
        normalized_missing_reason = missing_reason.strip().lower()
        intensity: float | None
        missing_value_kind: MissingValueKind
        if not intensity_token:
            intensity = None
            if normalized_missing_reason == "filtered":
                missing_value_kind = MissingValueKind.FILTERED
            else:
                missing_value_kind = MissingValueKind.NOT_OBSERVED
        else:
            try:
                intensity = float(intensity_token)
            except ValueError:
                issues.append(
                    _row_issue(
                        "invalid_intensity", "invalid intensity value", row_number
                    )
                )
                intensity = None
            if intensity is not None and intensity < 0:
                issues.append(
                    _row_issue(
                        "negative_intensity",
                        "intensity must be non-negative",
                        row_number,
                    )
                )
            if intensity is not None and intensity == 0.0:
                missing_value_kind = MissingValueKind.ZERO
            else:
                missing_value_kind = MissingValueKind.OBSERVED

        charge: int | None = None
        if active_mapping.charge:
            charge_token = raw_fields.get(active_mapping.charge, "").strip()
            if charge_token:
                try:
                    charge = int(charge_token)
                    if charge < 1:
                        raise ValueError
                except ValueError:
                    issues.append(
                        _row_issue("invalid_charge", "invalid charge value", row_number)
                    )

        protein_refs = _parse_protein_refs(
            raw_fields.get(active_mapping.protein_refs, "")
            if active_mapping.protein_refs
            else "",
            active_mapping.protein_separator,
        )

        precursor_id = (
            raw_fields.get(active_mapping.precursor_id, "").strip()
            if active_mapping.precursor_id
            else ""
        ) or f"precursor-{row_number}"
        if issues:
            rejected.append(
                RejectedPrecursorIntensityRow(
                    row_number=row_number,
                    raw_fields=raw_fields,
                    issues=tuple(issues),
                )
            )
            continue

        accepted.append(
            PrecursorIntensityRecord(
                precursor_id=precursor_id,
                sample_id=sample_id,
                run_id=run_token or None,
                peptide_sequence=peptide_sequence,
                modified_peptide=modified_peptide_token or None,
                canonical_peptide=canonical_peptide,
                intensity=intensity,
                protein_refs=protein_refs,
                charge=charge,
                missing_value_kind=missing_value_kind,
                missing_reason=missing_reason or None,
                provenance=ImportedEvidenceProvenance.from_single_row(
                    source_engine="precursor-intensity-table",
                    source_file=str(path),
                    source_row_number=row_number,
                    original_identifiers={
                        "precursor_id": precursor_id,
                        "sample_id": sample_id,
                        "run_id": run_token,
                        "peptide": peptide_sequence,
                        "modified_peptide": modified_peptide_token or peptide_sequence,
                    },
                ),
            )
        )

    accepted = sorted(
        accepted,
        key=lambda record: (
            record.sample_id,
            record.canonical_peptide,
            record.precursor_id,
        ),
    )
    return PrecursorIntensityParseReport(
        total_rows=len(accepted) + len(rejected),
        accepted_records=tuple(accepted),
        rejected_rows=tuple(rejected),
        column_mapping=active_mapping,
    )


def build_label_free_intensity_table(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    entity_level: QuantEntityLevel = QuantEntityLevel.PEPTIDE,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    top_n: int = 3,
) -> LabelFreeQuantTable:
    """Build a stable label-free intensity matrix from parsed MS1 features."""
    if top_n < 1:
        raise ValueError("top_n must be at least 1")
    return _build_table(
        records,
        entity_level=entity_level,
        measure_kind=QuantMeasureKind.INTENSITY,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )


def build_spectral_count_table(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    entity_level: QuantEntityLevel = QuantEntityLevel.PEPTIDE,
) -> LabelFreeQuantTable:
    """Build a stable spectral-count matrix from parsed MS1 features."""
    return _build_table(
        records,
        entity_level=entity_level,
        measure_kind=QuantMeasureKind.SPECTRAL_COUNT,
        aggregation_method=QuantRollupMethod.SUM,
        top_n=1,
    )


def summarize_missing_values(
    table: LabelFreeQuantTable,
    *,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingValueSummaryReport:
    """Summarize missing values with explicit correction and sparse-entity filters."""
    from bijux_proteomics.quantification.missingness import (
        summarize_missing_values as _implementation,
    )

    return _implementation(table, policy=policy)


def build_missing_data_mechanism_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> MissingDataMechanismReport:
    """Classify missingness patterns with explicit mechanism labels."""
    from bijux_proteomics.quantification.missingness import (
        build_missing_data_mechanism_report as _implementation,
    )

    return _implementation(table, design_entries)


def build_missingness_classifier_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    policy: MissingValueSummaryPolicy | None = None,
    bin_count: int = 4,
) -> MissingnessClassifierReport:
    """Bundle sample, entity, condition, intensity, and mechanism missingness views."""
    from bijux_proteomics.quantification.missingness import (
        build_missingness_classifier_report as _implementation,
    )

    return _implementation(
        table,
        design_entries=design_entries,
        policy=policy,
        bin_count=bin_count,
    )


def normalize_label_free_table(
    table: LabelFreeQuantTable,
    *,
    method: NormalizationMethod = NormalizationMethod.MEDIAN,
) -> LabelFreeQuantTable:
    """Normalize a label-free intensity table with one stable baseline method."""
    from bijux_proteomics.quantification.normalization import (
        normalize_label_free_table as _implementation,
    )

    return _implementation(table, method=method)


def build_batch_effect_estimator_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    batch_field: str = "batch",
    shift_threshold: float = 0.5,
    component_association_threshold: float = 0.35,
) -> BatchEffectAdvisoryReport:
    """Build a batch-effect estimator with shift, PC, and confounding diagnostics."""
    from bijux_proteomics.quantification.batch_effect import (
        build_batch_effect_estimator_report as _implementation,
    )

    return _implementation(
        table,
        design_entries,
        batch_field=batch_field,
        shift_threshold=shift_threshold,
        component_association_threshold=component_association_threshold,
    )


def build_batch_effect_advisory(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    batch_field: str = "batch",
    shift_threshold: float = 0.5,
    component_association_threshold: float = 0.35,
) -> BatchEffectAdvisoryReport:
    """Compatibility wrapper over the owned batch-effect estimator."""
    return build_batch_effect_estimator_report(
        table,
        design_entries,
        batch_field=batch_field,
        shift_threshold=shift_threshold,
        component_association_threshold=component_association_threshold,
    )


def render_batch_effect_summary_tsv(report: BatchEffectAdvisoryReport) -> str:
    """Render a stable one-row batch-effect summary table."""
    from bijux_proteomics.quantification.batch_effect import (
        render_batch_effect_summary_tsv as _implementation,
    )

    return _implementation(report)


def render_batch_effect_batches_tsv(report: BatchEffectAdvisoryReport) -> str:
    """Render stable batch-level median-shift rows for one batch-effect report."""
    from bijux_proteomics.quantification.batch_effect import (
        render_batch_effect_batches_tsv as _implementation,
    )

    return _implementation(report)


def render_batch_effect_principal_components_tsv(
    report: BatchEffectAdvisoryReport,
) -> str:
    """Render stable principal-component batch-association rows."""
    from bijux_proteomics.quantification.batch_effect import (
        render_batch_effect_principal_components_tsv as _implementation,
    )

    return _implementation(report)


def export_batch_effect_summary_tsv(
    report: BatchEffectAdvisoryReport,
    path: Path,
) -> None:
    """Write a stable batch-effect summary table."""
    from bijux_proteomics.quantification.batch_effect import (
        export_batch_effect_summary_tsv as _implementation,
    )

    _implementation(report, path)


def export_batch_effect_batches_tsv(
    report: BatchEffectAdvisoryReport,
    path: Path,
) -> None:
    """Write stable batch-level shift rows."""
    from bijux_proteomics.quantification.batch_effect import (
        export_batch_effect_batches_tsv as _implementation,
    )

    _implementation(report, path)


def export_batch_effect_principal_components_tsv(
    report: BatchEffectAdvisoryReport,
    path: Path,
) -> None:
    """Write stable principal-component batch-association rows."""
    from bijux_proteomics.quantification.batch_effect import (
        export_batch_effect_principal_components_tsv as _implementation,
    )

    _implementation(report, path)


def build_replicate_correlation_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> ReplicateCorrelationReport:
    """Build a replicate-correlation report over shared observed quant values."""
    condition_by_sample = _condition_lookup(design_entries)
    lookup = _matrix_value_index(table)
    entries: list[ReplicateCorrelationEntry] = []
    within_condition: list[float] = []
    between_condition: list[float] = []
    for index, sample_a in enumerate(table.sample_ids):
        for sample_b in table.sample_ids[index + 1 :]:
            vector_a: list[float] = []
            vector_b: list[float] = []
            for entity_id in table.entity_ids:
                cell_a = lookup[(entity_id, sample_a)]
                cell_b = lookup[(entity_id, sample_b)]
                if cell_a.abundance is None or cell_b.abundance is None:
                    continue
                vector_a.append(math.log2(cell_a.abundance + 1.0))
                vector_b.append(math.log2(cell_b.abundance + 1.0))
            if len(vector_a) < 2:
                continue
            correlation = float(np.corrcoef(vector_a, vector_b)[0, 1])
            entry = ReplicateCorrelationEntry(
                sample_a=sample_a,
                sample_b=sample_b,
                condition_a=condition_by_sample.get(sample_a, "unknown"),
                condition_b=condition_by_sample.get(sample_b, "unknown"),
                correlation=correlation,
                shared_entity_count=len(vector_a),
            )
            entries.append(entry)
            if entry.condition_a == entry.condition_b:
                within_condition.append(correlation)
            else:
                between_condition.append(correlation)
    return ReplicateCorrelationReport(
        entity_level=table.entity_level,
        entries=tuple(entries),
        within_condition_mean=float(np.mean(within_condition))
        if within_condition
        else None,
        between_condition_mean=float(np.mean(between_condition))
        if between_condition
        else None,
    )


def build_study_scale_replicate_correlation_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    top_pair_count: int = 5,
) -> StudyScaleReplicateCorrelationReport:
    """Summarize replicate correlations in a compact study-scale report."""
    pairwise = build_replicate_correlation_report(table, design_entries)
    per_sample_within: dict[str, list[float]] = defaultdict(list)
    per_sample_between: dict[str, list[float]] = defaultdict(list)
    condition_by_sample = _condition_lookup(design_entries)
    for entry in pairwise.entries:
        target = (
            per_sample_within
            if entry.condition_a == entry.condition_b
            else per_sample_between
        )
        target[entry.sample_a].append(entry.correlation)
        target[entry.sample_b].append(entry.correlation)

    sample_summaries = tuple(
        StudyScaleReplicateSampleEntry(
            sample_id=sample_id,
            condition=condition_by_sample.get(sample_id, "unknown"),
            within_condition_pairs=len(per_sample_within.get(sample_id, ())),
            between_condition_pairs=len(per_sample_between.get(sample_id, ())),
            mean_within_condition_correlation=(
                float(np.mean(per_sample_within[sample_id]))
                if per_sample_within.get(sample_id)
                else None
            ),
            mean_between_condition_correlation=(
                float(np.mean(per_sample_between[sample_id]))
                if per_sample_between.get(sample_id)
                else None
            ),
        )
        for sample_id in table.sample_ids
    )
    weakest_within = tuple(
        sorted(
            (
                entry
                for entry in pairwise.entries
                if entry.condition_a == entry.condition_b
            ),
            key=lambda entry: (entry.correlation, entry.sample_a, entry.sample_b),
        )[:top_pair_count]
    )
    strongest_between = tuple(
        sorted(
            (
                entry
                for entry in pairwise.entries
                if entry.condition_a != entry.condition_b
            ),
            key=lambda entry: (-entry.correlation, entry.sample_a, entry.sample_b),
        )[:top_pair_count]
    )
    return StudyScaleReplicateCorrelationReport(
        entity_level=table.entity_level,
        sample_summaries=sample_summaries,
        weakest_within_condition_pairs=weakest_within,
        strongest_between_condition_pairs=strongest_between,
    )


def build_study_scale_batch_effect_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    batch_field: str = "batch",
    shift_threshold: float = 0.5,
    component_association_threshold: float = 0.35,
) -> StudyScaleBatchEffectReport:
    """Summarize batch effects in a compact report for larger studies."""
    advisory = build_batch_effect_advisory(
        table,
        design_entries,
        batch_field=batch_field,
        shift_threshold=shift_threshold,
        component_association_threshold=component_association_threshold,
    )
    entries = tuple(
        StudyScaleBatchEffectEntry(
            batch_id=entry.batch_id,
            sample_count=len(entry.sample_ids),
            flagged=entry.flagged,
            median_shift_from_global=entry.shift_from_global,
        )
        for entry in advisory.batches
    )
    return StudyScaleBatchEffectReport(
        disposition=advisory.disposition,
        entries=entries,
        flagged_batch_count=sum(1 for entry in entries if entry.flagged),
        batch_variance_proxy=advisory.batch_variance_proxy,
        batch_correction_blocked=advisory.batch_correction_blocked,
    )


def build_differential_abundance_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None = None,
    condition_b: str | None = None,
    test_type: DifferentialAbundanceTestType = DifferentialAbundanceTestType.WELCH_T_TEST,
    design_matrix: QuantDesignMatrixReport | None = None,
    contrast_name: str | None = None,
    paired_policy: PairedDifferentialPolicy | None = None,
    replicate_policy: DifferentialReplicatePolicy | None = None,
    sample_run_policy: "SampleRunAnalysisPolicy" = None,
) -> DifferentialAbundanceReport:
    """Run one owned two-condition differential abundance engine."""
    from bijux_proteomics.quantification.differential_abundance import (
        build_differential_abundance_report as _implementation,
    )
    from bijux_proteomics.study.sample_run_identity import SampleRunAnalysisPolicy

    resolved_sample_run_policy = (
        sample_run_policy or SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS
    )

    return _implementation(
        table,
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
        test_type=test_type,
        design_matrix=design_matrix,
        contrast_name=contrast_name,
        paired_policy=paired_policy,
        replicate_policy=replicate_policy,
        sample_run_policy=resolved_sample_run_policy,
    )


def apply_benjamini_hochberg(
    report: DifferentialAbundanceReport,
) -> DifferentialAbundanceReport:
    """Apply Benjamini-Hochberg correction to one differential report."""
    from bijux_proteomics.quantification.differential_abundance import (
        apply_benjamini_hochberg as _implementation,
    )

    return _implementation(report)


def render_differential_abundance_tsv(
    report: DifferentialAbundanceReport,
) -> str:
    """Render one differential-abundance report as a stable TSV table."""
    from bijux_proteomics.quantification.differential_abundance import (
        render_differential_abundance_tsv as _implementation,
    )

    return _implementation(report)


def render_differential_broken_pairs_tsv(
    report: DifferentialAbundanceReport,
) -> str:
    """Render one broken-pair ledger for paired differential testing."""
    from bijux_proteomics.quantification.differential_abundance import (
        render_differential_broken_pairs_tsv as _implementation,
    )

    return _implementation(report)


def export_differential_broken_pairs_tsv(
    report: DifferentialAbundanceReport,
    path: Path,
) -> None:
    """Write one broken-pair ledger to a stable TSV artifact."""
    from bijux_proteomics.quantification.differential_abundance import (
        export_differential_broken_pairs_tsv as _implementation,
    )

    _implementation(report, path)


def export_differential_abundance_tsv(
    report: DifferentialAbundanceReport,
    path: Path,
) -> None:
    """Write one differential-abundance report to a stable TSV artifact."""
    from bijux_proteomics.quantification.differential_abundance import (
        export_differential_abundance_tsv as _implementation,
    )

    _implementation(report, path)


def render_multi_condition_differential_abundance_tsv(
    report: MultiConditionDifferentialAbundanceReport,
) -> str:
    """Render a multi-condition DA collection as one flattened TSV table."""
    from bijux_proteomics.quantification.differential_abundance import (
        render_multi_condition_differential_abundance_tsv as _implementation,
    )

    return _implementation(report)


def export_multi_condition_differential_abundance_tsv(
    report: MultiConditionDifferentialAbundanceReport,
    path: Path,
) -> None:
    """Write a multi-condition DA collection to one flattened TSV artifact."""
    from bijux_proteomics.quantification.differential_abundance import (
        export_multi_condition_differential_abundance_tsv as _implementation,
    )

    _implementation(report, path)


def build_time_course_differential_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    policy: TimeCourseTestingPolicy | None = None,
    sample_run_policy: "SampleRunAnalysisPolicy" = None,
) -> TimeCourseDifferentialReport:
    """Build one ordered time-course differential report over a quant table."""
    from bijux_proteomics.quantification.time_course_differential import (
        build_time_course_differential_report as _implementation,
    )
    from bijux_proteomics.study.sample_run_identity import SampleRunAnalysisPolicy

    resolved_sample_run_policy = (
        sample_run_policy or SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS
    )
    return _implementation(
        table,
        design_entries,
        policy=policy,
        sample_run_policy=resolved_sample_run_policy,
    )


def render_time_course_differential_tsv(
    report: TimeCourseDifferentialReport,
) -> str:
    """Render one time-course differential report as a stable TSV table."""
    from bijux_proteomics.quantification.time_course_differential import (
        render_time_course_differential_tsv as _implementation,
    )

    return _implementation(report)


def export_time_course_differential_tsv(
    report: TimeCourseDifferentialReport,
    path: Path,
) -> None:
    """Write one time-course differential report to a stable TSV artifact."""
    from bijux_proteomics.quantification.time_course_differential import (
        export_time_course_differential_tsv as _implementation,
    )

    _implementation(report, path)


def build_quant_design_matrix_report(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    batch_field: str | None = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
    timepoint_field: str | None = None,
    condition_field: str = "condition",
    sample_run_policy: "SampleRunAnalysisPolicy" = None,
) -> QuantDesignMatrixReport:
    """Build an explicit design matrix over one quantification study design."""
    from bijux_proteomics.quantification.design_matrix import (
        build_quant_design_matrix_report as _implementation,
    )
    from bijux_proteomics.study.sample_run_identity import SampleRunAnalysisPolicy

    resolved_sample_run_policy = (
        sample_run_policy or SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS
    )

    return _implementation(
        design_entries,
        batch_field=batch_field,
        covariate_fields=covariate_fields,
        pairing_field=pairing_field,
        timepoint_field=timepoint_field,
        condition_field=condition_field,
        sample_run_policy=resolved_sample_run_policy,
    )


def fit_quant_design_matrix_model(
    table: LabelFreeQuantTable,
    design_matrix: QuantDesignMatrixReport,
) -> QuantDesignModelFitReport:
    """Fit one coefficient report over a quantification table and design matrix."""
    from bijux_proteomics.quantification.design_matrix import (
        fit_quant_design_matrix_model as _implementation,
    )

    return _implementation(table, design_matrix)


def render_quant_design_matrix_tsv(
    report: QuantDesignMatrixReport,
) -> str:
    """Render a design matrix as a stable TSV table."""
    from bijux_proteomics.quantification.design_matrix import (
        render_quant_design_matrix_tsv as _implementation,
    )

    return _implementation(report)


def export_quant_design_matrix_tsv(
    report: QuantDesignMatrixReport,
    path: Path,
) -> None:
    """Write a design matrix to a stable TSV artifact."""
    from bijux_proteomics.quantification.design_matrix import (
        export_quant_design_matrix_tsv as _implementation,
    )

    _implementation(report, path)


def render_quant_design_model_coefficients_tsv(
    report: QuantDesignModelFitReport,
) -> str:
    """Render design-model coefficients as a stable TSV table."""
    from bijux_proteomics.quantification.design_matrix import (
        render_quant_design_model_coefficients_tsv as _implementation,
    )

    return _implementation(report)


def export_quant_design_model_coefficients_tsv(
    report: QuantDesignModelFitReport,
    path: Path,
) -> None:
    """Write design-model coefficients to a stable TSV artifact."""
    from bijux_proteomics.quantification.design_matrix import (
        export_quant_design_model_coefficients_tsv as _implementation,
    )

    _implementation(report, path)


def render_quant_design_contrast_estimates_tsv(
    report: QuantDesignModelFitReport,
) -> str:
    """Render condition-contrast estimates as a stable TSV table."""
    from bijux_proteomics.quantification.design_matrix import (
        render_quant_design_contrast_estimates_tsv as _implementation,
    )

    return _implementation(report)


def export_quant_design_contrast_estimates_tsv(
    report: QuantDesignModelFitReport,
    path: Path,
) -> None:
    """Write condition-contrast estimates to a stable TSV artifact."""
    from bijux_proteomics.quantification.design_matrix import (
        export_quant_design_contrast_estimates_tsv as _implementation,
    )

    _implementation(report, path)
