# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned experiment-design type classification for statistical method routing."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    ExperimentalDesignSampleRole,
)
from bijux_proteomics.study.design.design_validity import (
    ExperimentDesignValidityReport,
    build_experiment_design_validity_report,
)
from bijux_proteomics.study.design.experiment_design import (
    ExperimentDesign,
    coerce_experiment_design,
)
from bijux_proteomics_foundation import JsonModel


class ExperimentDesignType(StrEnum):
    """Stable study-design types that govern downstream method choice."""

    TWO_GROUP = "two_group"
    MULTI_GROUP = "multi_group"
    PAIRED = "paired"
    LONGITUDINAL = "longitudinal"
    TMT_PLEXED = "tmt_plexed"
    BATCH_CONFOUNDED = "batch_confounded"
    TARGETED_VALIDATION = "targeted_validation"
    EXPLORATORY = "exploratory"


class ExperimentDesignAnalysisFamily(StrEnum):
    """Statistical or review families that must match classified study designs."""

    PAIRWISE_DIFFERENTIAL = "pairwise_differential"
    PAIRED_DIFFERENTIAL = "paired_differential"
    MULTI_CONDITION_DIFFERENTIAL = "multi_condition_differential"
    TIME_COURSE_DIFFERENTIAL = "time_course_differential"
    TARGETED_VALIDATION_REVIEW = "targeted_validation_review"
    EXPLORATORY_SUMMARY = "exploratory_summary"


class ExperimentDesignClassificationReport(JsonModel):
    """One governed design-type classification over an experiment design."""

    model_config = ConfigDict(extra="forbid")

    experiment_design: ExperimentDesign
    validity_report: ExperimentDesignValidityReport
    selected_conditions: tuple[str, ...] = Field(default_factory=tuple)
    primary_design_type: ExperimentDesignType
    detected_design_types: tuple[ExperimentDesignType, ...] = Field(
        default_factory=tuple
    )
    recommended_analysis_family: ExperimentDesignAnalysisFamily
    note: str = Field(..., min_length=1)


def build_experiment_design_classification_report(
    design: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str | None = None,
    pairing_field: str | None = None,
    require_complete_plex_channels: bool = False,
    timepoint_field: str | None = None,
    ordered_timepoints: tuple[str, ...] = (),
) -> ExperimentDesignClassificationReport:
    """Classify one experiment design into the method family it requires."""

    experiment_design = coerce_experiment_design(design)
    validity_report = build_experiment_design_validity_report(
        experiment_design,
        condition_a=condition_a,
        condition_b=condition_b,
        batch_field=batch_field,
        pairing_field=pairing_field,
        require_complete_plex_channels=require_complete_plex_channels,
        timepoint_field=timepoint_field,
        ordered_timepoints=ordered_timepoints,
    )
    selected_conditions = validity_report.selected_conditions or _analysis_conditions(
        experiment_design
    )
    comparison_condition_count = len(selected_conditions)
    has_longitudinal_structure = _has_longitudinal_structure(
        experiment_design,
        timepoint_field=timepoint_field,
    )
    has_targeted_intent = _has_declared_targeted_validation(experiment_design)
    has_exploratory_intent = _has_declared_exploratory_intent(experiment_design)
    has_pairing = _has_complete_pairing(
        experiment_design,
        selected_conditions=selected_conditions,
    )
    has_confounded_batches = (
        validity_report.summary.confounded_batch_condition_count > 0
    )
    detected_types = _detected_design_types(
        comparison_condition_count=comparison_condition_count,
        has_pairing=has_pairing,
        has_longitudinal_structure=has_longitudinal_structure,
        has_tmt_plexes=bool(experiment_design.plexes),
        has_confounded_batches=has_confounded_batches,
        has_targeted_intent=has_targeted_intent,
        has_exploratory_intent=has_exploratory_intent,
    )
    primary_design_type = _primary_design_type(
        detected_types,
        comparison_condition_count=comparison_condition_count,
    )
    recommended_analysis_family = _recommended_analysis_family(
        primary_design_type=primary_design_type,
        comparison_condition_count=comparison_condition_count,
        has_pairing=has_pairing,
        has_longitudinal_structure=has_longitudinal_structure,
    )
    return ExperimentDesignClassificationReport(
        experiment_design=experiment_design,
        validity_report=validity_report,
        selected_conditions=selected_conditions,
        primary_design_type=primary_design_type,
        detected_design_types=detected_types,
        recommended_analysis_family=recommended_analysis_family,
        note=(
            "design classification preserves modality and comparison structure so "
            "differential workflows choose the matching statistical or review family"
        ),
    )


def require_matching_experiment_design_analysis_family(
    design: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    chosen_analysis_family: ExperimentDesignAnalysisFamily,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str | None = None,
    pairing_field: str | None = None,
    require_complete_plex_channels: bool = False,
    timepoint_field: str | None = None,
    ordered_timepoints: tuple[str, ...] = (),
) -> ExperimentDesignClassificationReport:
    """Return one classification or raise when the chosen method mismatches it."""

    report = build_experiment_design_classification_report(
        design,
        condition_a=condition_a,
        condition_b=condition_b,
        batch_field=batch_field,
        pairing_field=pairing_field,
        require_complete_plex_channels=require_complete_plex_channels,
        timepoint_field=timepoint_field,
        ordered_timepoints=ordered_timepoints,
    )
    if report.recommended_analysis_family is chosen_analysis_family:
        return report
    raise ValueError(
        "experiment design type "
        f"{report.primary_design_type.value} requires "
        f"{report.recommended_analysis_family.value}, not "
        f"{chosen_analysis_family.value}"
    )


def render_experiment_design_classification_tsv(
    report: ExperimentDesignClassificationReport,
) -> str:
    """Render one stable design-type classification row as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "primary_design_type",
            "detected_design_types",
            "recommended_analysis_family",
            "selected_conditions",
        )
    )
    writer.writerow(
        (
            report.primary_design_type.value,
            ";".join(
                detected_type.value for detected_type in report.detected_design_types
            ),
            report.recommended_analysis_family.value,
            ";".join(report.selected_conditions),
        )
    )
    return buffer.getvalue()


def _detected_design_types(
    *,
    comparison_condition_count: int,
    has_pairing: bool,
    has_longitudinal_structure: bool,
    has_tmt_plexes: bool,
    has_confounded_batches: bool,
    has_targeted_intent: bool,
    has_exploratory_intent: bool,
) -> tuple[ExperimentDesignType, ...]:
    detected: list[ExperimentDesignType] = []
    if comparison_condition_count == 2:
        detected.append(ExperimentDesignType.TWO_GROUP)
    elif comparison_condition_count > 2:
        detected.append(ExperimentDesignType.MULTI_GROUP)
    if has_pairing:
        detected.append(ExperimentDesignType.PAIRED)
    if has_longitudinal_structure:
        detected.append(ExperimentDesignType.LONGITUDINAL)
    if has_tmt_plexes:
        detected.append(ExperimentDesignType.TMT_PLEXED)
    if has_confounded_batches:
        detected.append(ExperimentDesignType.BATCH_CONFOUNDED)
    if has_targeted_intent:
        detected.append(ExperimentDesignType.TARGETED_VALIDATION)
    if has_exploratory_intent or comparison_condition_count < 2:
        detected.append(ExperimentDesignType.EXPLORATORY)
    return tuple(dict.fromkeys(detected))


def _primary_design_type(
    detected_types: tuple[ExperimentDesignType, ...],
    *,
    comparison_condition_count: int,
) -> ExperimentDesignType:
    precedence = (
        ExperimentDesignType.TARGETED_VALIDATION,
        ExperimentDesignType.BATCH_CONFOUNDED,
        ExperimentDesignType.LONGITUDINAL,
        ExperimentDesignType.TMT_PLEXED,
        ExperimentDesignType.PAIRED,
        ExperimentDesignType.MULTI_GROUP,
        ExperimentDesignType.TWO_GROUP,
        ExperimentDesignType.EXPLORATORY,
    )
    for design_type in precedence:
        if design_type in detected_types:
            return design_type
    if comparison_condition_count >= 2:
        return ExperimentDesignType.TWO_GROUP
    return ExperimentDesignType.EXPLORATORY


def _recommended_analysis_family(
    *,
    primary_design_type: ExperimentDesignType,
    comparison_condition_count: int,
    has_pairing: bool,
    has_longitudinal_structure: bool,
) -> ExperimentDesignAnalysisFamily:
    if primary_design_type is ExperimentDesignType.TARGETED_VALIDATION:
        return ExperimentDesignAnalysisFamily.TARGETED_VALIDATION_REVIEW
    if primary_design_type is ExperimentDesignType.BATCH_CONFOUNDED:
        return ExperimentDesignAnalysisFamily.EXPLORATORY_SUMMARY
    if has_longitudinal_structure:
        return ExperimentDesignAnalysisFamily.TIME_COURSE_DIFFERENTIAL
    if has_pairing:
        return ExperimentDesignAnalysisFamily.PAIRED_DIFFERENTIAL
    if comparison_condition_count > 2:
        return ExperimentDesignAnalysisFamily.MULTI_CONDITION_DIFFERENTIAL
    if comparison_condition_count == 2:
        return ExperimentDesignAnalysisFamily.PAIRWISE_DIFFERENTIAL
    return ExperimentDesignAnalysisFamily.EXPLORATORY_SUMMARY


def _has_complete_pairing(
    experiment_design: ExperimentDesign,
    *,
    selected_conditions: tuple[str, ...],
) -> bool:
    if len(selected_conditions) != 2:
        return False
    relevant_entries = tuple(
        entry
        for entry in experiment_design.entries
        if entry.condition in selected_conditions
    )
    if not relevant_entries:
        return False
    pair_ids = {entry.pair_id for entry in relevant_entries}
    return not any(pair_id in (None, "") for pair_id in pair_ids)


def _has_longitudinal_structure(
    experiment_design: ExperimentDesign,
    *,
    timepoint_field: str | None,
) -> bool:
    if experiment_design.timepoints:
        return len(experiment_design.timepoints) >= 2
    if timepoint_field in (None, ""):
        return False
    return any(timepoint_field in entry.metadata for entry in experiment_design.entries)


def _has_declared_targeted_validation(experiment_design: ExperimentDesign) -> bool:
    declared_values = _declared_design_metadata_values(experiment_design)
    return any(
        value in {"targeted", "targeted_validation", "validation"}
        for value in declared_values
    )


def _has_declared_exploratory_intent(experiment_design: ExperimentDesign) -> bool:
    declared_values = _declared_design_metadata_values(experiment_design)
    return "exploratory" in declared_values


def _declared_design_metadata_values(
    experiment_design: ExperimentDesign,
) -> set[str]:
    values: set[str] = set()
    for entry in experiment_design.entries:
        for key in ("design_type", "analysis_intent", "workflow_family", "assay_type"):
            value = entry.metadata.get(key)
            if value in (None, ""):
                continue
            values.add(value.strip().lower())
    return values


def _analysis_conditions(experiment_design: ExperimentDesign) -> tuple[str, ...]:
    sample_conditions = tuple(
        sorted(
            {
                entry.condition
                for entry in experiment_design.entries
                if entry.sample_role is ExperimentalDesignSampleRole.SAMPLE
            }
        )
    )
    if sample_conditions:
        return sample_conditions
    return experiment_design.conditions


__all__ = [
    "ExperimentDesignAnalysisFamily",
    "ExperimentDesignClassificationReport",
    "ExperimentDesignType",
    "build_experiment_design_classification_report",
    "render_experiment_design_classification_tsv",
    "require_matching_experiment_design_analysis_family",
]
