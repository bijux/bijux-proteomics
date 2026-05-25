# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Label-free quantification and differential abundance contracts."""

from __future__ import annotations

from collections import defaultdict
from enum import StrEnum
import math
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.domain.reason_codes import (
    ReasonCodeCategory,
    require_registered_reason_codes,
)
from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
)
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    pass


from .input_models import QuantAssessmentDisposition, QuantEntityLevel
from .matrix_building import _condition_lookup, _matrix_value_index
from .matrix_models import LabelFreeQuantTable

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

    @field_validator("status_reason_codes")
    @classmethod
    def _validate_status_reason_codes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_registered_reason_codes(
            value,
            ReasonCodeCategory.QC_REASON,
        )

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
