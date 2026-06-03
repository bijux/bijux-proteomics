# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Label-free quantification and differential abundance contracts."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
)
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.study.sample_run_identity import SampleRunAnalysisPolicy


from .input_models import ImputationMethod, NormalizationMethod, QuantEntityLevel
from .matrix_models import LabelFreeQuantTable

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

def build_quant_design_matrix_report(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    batch_field: str | None = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
    timepoint_field: str | None = None,
    condition_field: str = "condition",
    sample_run_policy: "SampleRunAnalysisPolicy | None" = None,
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
