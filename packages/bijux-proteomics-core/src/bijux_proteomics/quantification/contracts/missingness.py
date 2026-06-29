# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Label-free quantification and differential abundance contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
)
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    pass


from .input_models import (
    MissingValueCorrectionPolicy,
    QuantEntityLevel,
)
from .matrix_models import LabelFreeQuantTable


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


class MissingValueSummaryEntry(JsonModel):
    """Missing-value counts for one sample within a quant table."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    observed_count: int = Field(..., ge=0)
    zero_count: int = Field(..., ge=0)
    not_observed_count: int = Field(..., ge=0)
    filtered_count: int = Field(..., ge=0)
    imputed_count: int = Field(default=0, ge=0)
    censored_count: int = Field(default=0, ge=0)
    excluded_count: int = Field(default=0, ge=0)
    not_applicable_count: int = Field(default=0, ge=0)


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
    imputed_sample_count: int = Field(default=0, ge=0)
    censored_sample_count: int = Field(default=0, ge=0)
    excluded_sample_count: int = Field(default=0, ge=0)
    not_applicable_sample_count: int = Field(default=0, ge=0)
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
    imputed_value_count: int = Field(default=0, ge=0)
    censored_value_count: int = Field(default=0, ge=0)
    excluded_value_count: int = Field(default=0, ge=0)
    not_applicable_value_count: int = Field(default=0, ge=0)
    missing_fraction: float = Field(..., ge=0.0, le=1.0)
    condition_specific_absence_entity_ids: tuple[str, ...] = Field(
        default_factory=tuple
    )


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
