# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Data models for labeled differential workflow assembly and review."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.quantification.contracts.design import (
    QuantDesignMatrixReport,
    QuantDesignModelFitReport,
)
from bijux_proteomics.quantification.contracts.differential import (
    DifferentialAbundanceReport,
    MultiConditionDifferentialAbundanceReport,
)
from bijux_proteomics.quantification.contracts.input_models import (
    MissingValueKind,
    NormalizationMethod,
)
from bijux_proteomics_foundation import JsonModel


class LabelBasedDifferentialSourceKind(StrEnum):
    """Owned labeled quantification sources that can drive differential analysis."""

    TMT = "tmt"
    SILAC = "silac"


class LabelBasedMeasurementKind(StrEnum):
    """Whether a labeled workflow contributes intensities or explicit ratios."""

    INTENSITY = "intensity"
    RATIO = "ratio"


class LabelBasedDifferentialMatrixValue(JsonModel):
    """One sample-specific value inside a labeled differential matrix."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind = MissingValueKind.OBSERVED
    source_feature_count: int = Field(..., ge=0)


class LabelBasedDifferentialMatrixRow(JsonModel):
    """One protein-level row inside a labeled differential matrix."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    member_peptides: tuple[str, ...] = Field(default_factory=tuple)
    values: tuple[LabelBasedDifferentialMatrixValue, ...] = Field(default_factory=tuple)


class LabelBasedDifferentialMatrixSummary(JsonModel):
    """Compact summary over one labeled differential matrix."""

    model_config = ConfigDict(extra="forbid")

    source_kind: LabelBasedDifferentialSourceKind
    measurement_kind: LabelBasedMeasurementKind
    entity_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    observed_cell_count: int = Field(..., ge=0)
    missing_cell_count: int = Field(..., ge=0)


class LabelBasedDifferentialInputReport(JsonModel):
    """Governed labeled differential input packet before normalization and statistics."""

    model_config = ConfigDict(extra="forbid")

    source_kind: LabelBasedDifferentialSourceKind
    source_name: str = Field(..., min_length=1)
    measurement_kind: LabelBasedMeasurementKind
    summary: LabelBasedDifferentialMatrixSummary
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[LabelBasedDifferentialMatrixRow, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class LabelBasedNormalizationBalancePoint(JsonModel):
    """One sample point for labeled before/after normalization review."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    stage: str = Field(..., min_length=1)
    total_abundance: float = Field(..., ge=0.0)
    median_abundance: float = Field(..., ge=0.0)
    interquartile_range: float = Field(..., ge=0.0)


class LabelBasedNormalizationBalancePlot(JsonModel):
    """Plot-ready before/after balance payload for labeled differential analysis."""

    model_config = ConfigDict(extra="forbid")

    method: NormalizationMethod
    points: tuple[LabelBasedNormalizationBalancePoint, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class LabelBasedDifferentialVolcanoPoint(JsonModel):
    """One point for labeled differential volcano review."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    log2_fold_change: float
    raw_p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float = Field(..., ge=0.0, le=1.0)
    negative_log10_adjusted_p_value: float = Field(..., ge=0.0)
    highlighted: bool


class LabelBasedDifferentialVolcanoPlot(JsonModel):
    """Plot-ready volcano payload for one labeled differential contrast."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    significant_point_count: int = Field(..., ge=0)
    points: tuple[LabelBasedDifferentialVolcanoPoint, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class LabelBasedDifferentialAnalysisReport(JsonModel):
    """Normalization, design, and differential results over labeled protein matrices."""

    model_config = ConfigDict(extra="forbid")

    input_report: LabelBasedDifferentialInputReport
    normalization_method: NormalizationMethod
    normalization_factors: dict[str, float] = Field(default_factory=dict)
    normalized_matrix: LabelBasedDifferentialInputReport
    normalization_balance_plot: LabelBasedNormalizationBalancePlot
    design_matrix: QuantDesignMatrixReport
    design_model_fit: QuantDesignModelFitReport
    differential_abundance_report: DifferentialAbundanceReport | None = None
    differential_abundance_multi_condition_report: (
        MultiConditionDifferentialAbundanceReport | None
    ) = None
    volcano_plot: LabelBasedDifferentialVolcanoPlot | None = None
    note: str = Field(..., min_length=1)


__all__ = [
    "LabelBasedDifferentialAnalysisReport",
    "LabelBasedDifferentialInputReport",
    "LabelBasedDifferentialMatrixRow",
    "LabelBasedDifferentialMatrixSummary",
    "LabelBasedDifferentialMatrixValue",
    "LabelBasedDifferentialSourceKind",
    "LabelBasedDifferentialVolcanoPlot",
    "LabelBasedDifferentialVolcanoPoint",
    "LabelBasedMeasurementKind",
    "LabelBasedNormalizationBalancePlot",
    "LabelBasedNormalizationBalancePoint",
]
