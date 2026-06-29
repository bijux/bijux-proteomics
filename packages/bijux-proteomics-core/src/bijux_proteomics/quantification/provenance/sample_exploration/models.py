# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Typed contracts and internal state for sample exploration ownership."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from pydantic import ConfigDict, Field

from bijux_proteomics.quantification.contracts.input_models import (
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
)
from bijux_proteomics.quantification.contracts.study_qc import (
    ConditionClusteringReport,
    SamplePcaEntry,
    SamplePcaReport,
)
from bijux_proteomics_foundation import JsonModel


@dataclass(frozen=True)
class SampleSpaceDecomposition:
    """Centered sample-space decomposition over one quantification table."""

    sample_ids: tuple[str, ...]
    feature_count: int
    condition_by_sample: dict[str, str]
    batch_by_sample: dict[str, str | None]
    matrix: np.ndarray
    centered_matrix: np.ndarray
    scores: np.ndarray
    eigenvalues: np.ndarray
    total_variance: float


@dataclass(frozen=True)
class SampleClusterState:
    """Active cluster membership over one deterministic merge sequence."""

    member_indexes: tuple[int, ...]


class SamplePcaVarianceEntry(JsonModel):
    """Explained-variance payload for one principal component."""

    model_config = ConfigDict(extra="forbid")

    component_index: int = Field(..., ge=1)
    component_label: str = Field(..., min_length=1)
    explained_variance_ratio: float = Field(..., ge=0.0, le=1.0)
    cumulative_explained_variance_ratio: float = Field(..., ge=0.0, le=1.0)


class SamplePcaVarianceReport(JsonModel):
    """Explained-variance report over one sample PCA decomposition."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    entries: tuple[SamplePcaVarianceEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class SampleDistanceEntry(JsonModel):
    """One pairwise sample distance in centered feature space."""

    model_config = ConfigDict(extra="forbid")

    sample_id_a: str = Field(..., min_length=1)
    sample_id_b: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    batch_a: str | None = None
    batch_b: str | None = None
    euclidean_distance: float = Field(..., ge=0.0)
    same_condition: bool
    same_batch: bool


class SampleDistanceReport(JsonModel):
    """Pairwise sample-distance report over one quantification table."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    sample_count: int = Field(..., ge=0)
    entries: tuple[SampleDistanceEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class SampleCorrelationEntry(JsonModel):
    """One pairwise sample correlation across the filled feature matrix."""

    model_config = ConfigDict(extra="forbid")

    sample_id_a: str = Field(..., min_length=1)
    sample_id_b: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    batch_a: str | None = None
    batch_b: str | None = None
    pearson_correlation: float = Field(..., ge=-1.0, le=1.0)
    same_condition: bool
    same_batch: bool


class SampleCorrelationReport(JsonModel):
    """Pairwise sample-correlation report over one quantification table."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    sample_count: int = Field(..., ge=0)
    entries: tuple[SampleCorrelationEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class SampleClusterEntry(JsonModel):
    """One average-linkage merge row in a deterministic sample cluster table."""

    model_config = ConfigDict(extra="forbid")

    merge_order: int = Field(..., ge=1)
    member_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    left_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    right_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    member_conditions: tuple[str, ...] = Field(default_factory=tuple)
    member_batches: tuple[str, ...] = Field(default_factory=tuple)
    member_count: int = Field(..., ge=2)
    average_linkage_distance: float = Field(..., ge=0.0)


class SampleClusterReport(JsonModel):
    """Deterministic average-linkage cluster table over study samples."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    sample_count: int = Field(..., ge=0)
    entries: tuple[SampleClusterEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class SampleOutlierEntry(JsonModel):
    """One outlier sample with the metric labels that triggered it."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    batch: str | None = None
    outlier_reasons: tuple[str, ...] = Field(default_factory=tuple)
    distance_from_global_centroid: float = Field(..., ge=0.0)
    distance_from_condition_centroid: float = Field(..., ge=0.0)


class SampleOutlierReport(JsonModel):
    """Explicit outlier ledger over the sample exploration space."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    entries: tuple[SampleOutlierEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class SampleExplorationSummary(JsonModel):
    """Compact study-space summary for one sample exploration run."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    normalization_method: str = Field(..., min_length=1)
    sample_count: int = Field(..., ge=0)
    feature_count: int = Field(..., ge=0)
    pairwise_correlation_count: int = Field(..., ge=0)
    pairwise_distance_count: int = Field(..., ge=0)
    cluster_merge_count: int = Field(..., ge=0)
    outlier_sample_count: int = Field(..., ge=0)
    clustered_by_condition: bool


class SampleExplorationReport(JsonModel):
    """Integrated sample-level exploratory analysis over one quant table."""

    model_config = ConfigDict(extra="forbid")

    summary: SampleExplorationSummary
    sample_pca_report: SamplePcaReport
    explained_variance_report: SamplePcaVarianceReport
    condition_clustering_report: ConditionClusteringReport
    sample_correlation_report: SampleCorrelationReport
    sample_distance_report: SampleDistanceReport
    sample_cluster_report: SampleClusterReport
    sample_outlier_report: SampleOutlierReport
    note: str = Field(..., min_length=1)


__all__ = [
    "ConditionClusteringReport",
    "SampleClusterEntry",
    "SampleClusterReport",
    "SampleClusterState",
    "SampleCorrelationEntry",
    "SampleCorrelationReport",
    "SampleDistanceEntry",
    "SampleDistanceReport",
    "SampleExplorationReport",
    "SampleExplorationSummary",
    "SampleOutlierEntry",
    "SampleOutlierReport",
    "SamplePcaEntry",
    "SamplePcaReport",
    "SamplePcaVarianceEntry",
    "SamplePcaVarianceReport",
    "SampleSpaceDecomposition",
]
