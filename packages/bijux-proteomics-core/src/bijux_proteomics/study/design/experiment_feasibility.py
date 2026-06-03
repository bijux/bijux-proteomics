# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned experiment-feasibility reporting before differential statistics start."""

from __future__ import annotations

import csv
from io import StringIO
from itertools import combinations

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    ExperimentalDesignReport,
)
from bijux_proteomics.study.design.design_classification import (
    ExperimentDesignAnalysisFamily,
    ExperimentDesignClassificationReport,
    ExperimentDesignType,
    build_experiment_design_classification_report,
)
from bijux_proteomics.study.design.design_validity import (
    ExperimentDesignValidityReport,
    build_experiment_design_validity_report,
)
from bijux_proteomics.study.design.experiment_design import (
    ExperimentDesign,
    coerce_experiment_design,
)
from bijux_proteomics.study.design.replicate_structure import (
    ReplicateStructureReport,
    build_replicate_structure_report,
    count_effective_statistical_units_by_condition,
)
from bijux_proteomics_foundation import JsonModel


class ExperimentFeasibilityContrastEntry(JsonModel):
    """One pairwise biological contrast and whether the design can support it."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    effective_statistical_units_a: int = Field(..., ge=0)
    effective_statistical_units_b: int = Field(..., ge=0)
    minimum_required_units: int = Field(..., ge=1)
    complete_pair_count: int = Field(..., ge=0)
    supported: bool
    supports_paired_model: bool
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    message: str = Field(..., min_length=1)


class ExperimentFeasibilityGroupSizeEntry(JsonModel):
    """Condition-level replicate support relevant to biological questions."""

    model_config = ConfigDict(extra="forbid")

    condition: str = Field(..., min_length=1)
    effective_statistical_unit_count: int = Field(..., ge=0)
    minimum_required_units: int = Field(..., ge=1)
    underpowered: bool


class ExperimentFeasibilityMetadataIssue(JsonModel):
    """Missing metadata or parse loss that limits experiment support."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    field: str | None = None
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    run_ids: tuple[str, ...] = Field(default_factory=tuple)
    condition_ids: tuple[str, ...] = Field(default_factory=tuple)


class ExperimentFeasibilityModelEntry(JsonModel):
    """Whether one analysis family is actually supportable by the design."""

    model_config = ConfigDict(extra="forbid")

    analysis_family: ExperimentDesignAnalysisFamily
    supported: bool
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    required_fields: tuple[str, ...] = Field(default_factory=tuple)
    message: str = Field(..., min_length=1)


class ExperimentFeasibilitySummary(JsonModel):
    """Compact experiment-feasibility summary over contrasts and models."""

    model_config = ConfigDict(extra="forbid")

    condition_count: int = Field(..., ge=0)
    valid_contrast_count: int = Field(..., ge=0)
    invalid_contrast_count: int = Field(..., ge=0)
    underpowered_condition_count: int = Field(..., ge=0)
    missing_metadata_count: int = Field(..., ge=0)
    impossible_model_count: int = Field(..., ge=0)
    parse_rejected_row_count: int = Field(..., ge=0)


class ExperimentFeasibilityReport(JsonModel):
    """Owned report of what the experiment can and cannot support."""

    model_config = ConfigDict(extra="forbid")

    experiment_design: ExperimentDesign
    replicate_structure_report: ReplicateStructureReport
    validity_report: ExperimentDesignValidityReport
    classification_report: ExperimentDesignClassificationReport
    minimum_statistical_units_per_condition: int = Field(..., ge=1)
    parse_rejected_row_count: int = Field(..., ge=0)
    valid_contrasts: tuple[ExperimentFeasibilityContrastEntry, ...] = Field(
        default_factory=tuple
    )
    invalid_contrasts: tuple[ExperimentFeasibilityContrastEntry, ...] = Field(
        default_factory=tuple
    )
    group_sizes: tuple[ExperimentFeasibilityGroupSizeEntry, ...] = Field(
        default_factory=tuple
    )
    missing_metadata: tuple[ExperimentFeasibilityMetadataIssue, ...] = Field(
        default_factory=tuple
    )
    model_support: tuple[ExperimentFeasibilityModelEntry, ...] = Field(
        default_factory=tuple
    )
    summary: ExperimentFeasibilitySummary
    note: str = Field(..., min_length=1)


def build_experiment_feasibility_report(
    design: ExperimentalDesignReport
    | ExperimentDesign
    | tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str | None = None,
    pairing_field: str | None = None,
    timepoint_field: str | None = None,
    ordered_timepoints: tuple[str, ...] = (),
    minimum_statistical_units_per_condition: int = 2,
) -> ExperimentFeasibilityReport:
    """Report supported contrasts, missing metadata, and impossible models."""

    accepted_entries, parse_rejected_row_count = _coerce_design_entries(design)
    experiment_design = coerce_experiment_design(accepted_entries)
    effective_batch_field = _resolve_batch_field(experiment_design, batch_field)
    effective_pairing_field = _resolve_pairing_field(experiment_design, pairing_field)
    effective_timepoint_field = _resolve_timepoint_field(
        experiment_design,
        timepoint_field,
    )
    replicate_structure_report = build_replicate_structure_report(
        experiment_design,
        minimum_statistical_units_per_condition=minimum_statistical_units_per_condition,
    )
    validity_report = build_experiment_design_validity_report(
        experiment_design,
        condition_a=condition_a,
        condition_b=condition_b,
        batch_field=effective_batch_field,
        pairing_field=effective_pairing_field,
        timepoint_field=effective_timepoint_field,
        ordered_timepoints=ordered_timepoints,
    )
    classification_report = build_experiment_design_classification_report(
        experiment_design,
        condition_a=condition_a,
        condition_b=condition_b,
        batch_field=effective_batch_field,
        pairing_field=effective_pairing_field,
        timepoint_field=effective_timepoint_field,
        ordered_timepoints=ordered_timepoints,
    )
    unit_counts = count_effective_statistical_units_by_condition(experiment_design)
    group_sizes = tuple(
        ExperimentFeasibilityGroupSizeEntry(
            condition=condition,
            effective_statistical_unit_count=unit_counts.get(condition, 0),
            minimum_required_units=minimum_statistical_units_per_condition,
            underpowered=(
                unit_counts.get(condition, 0) < minimum_statistical_units_per_condition
            ),
        )
        for condition in experiment_design.conditions
    )
    contrast_entries = _build_contrast_entries(
        experiment_design,
        unit_counts=unit_counts,
        minimum_statistical_units_per_condition=minimum_statistical_units_per_condition,
        batch_field=effective_batch_field,
        pairing_field=effective_pairing_field,
    )
    missing_metadata = _build_missing_metadata_issues(
        experiment_design,
        parse_rejected_row_count=parse_rejected_row_count,
        pairing_field=effective_pairing_field,
        timepoint_field=effective_timepoint_field,
        batch_field=effective_batch_field,
    )
    model_support = _build_model_support_entries(
        experiment_design,
        classification_report=classification_report,
        validity_report=validity_report,
        contrast_entries=contrast_entries,
        effective_pairing_field=effective_pairing_field,
        effective_timepoint_field=effective_timepoint_field,
        minimum_statistical_units_per_condition=minimum_statistical_units_per_condition,
    )
    valid_contrasts = tuple(entry for entry in contrast_entries if entry.supported)
    invalid_contrasts = tuple(
        entry for entry in contrast_entries if not entry.supported
    )
    return ExperimentFeasibilityReport(
        experiment_design=experiment_design,
        replicate_structure_report=replicate_structure_report,
        validity_report=validity_report,
        classification_report=classification_report,
        minimum_statistical_units_per_condition=minimum_statistical_units_per_condition,
        parse_rejected_row_count=parse_rejected_row_count,
        valid_contrasts=valid_contrasts,
        invalid_contrasts=invalid_contrasts,
        group_sizes=group_sizes,
        missing_metadata=missing_metadata,
        model_support=model_support,
        summary=ExperimentFeasibilitySummary(
            condition_count=len(experiment_design.conditions),
            valid_contrast_count=len(valid_contrasts),
            invalid_contrast_count=len(invalid_contrasts),
            underpowered_condition_count=sum(
                1 for entry in group_sizes if entry.underpowered
            ),
            missing_metadata_count=len(missing_metadata),
            impossible_model_count=sum(
                1 for entry in model_support if not entry.supported
            ),
            parse_rejected_row_count=parse_rejected_row_count,
        ),
        note=(
            "experiment feasibility reports supported contrasts, unsupported "
            "contrasts, effective group sizes, missing metadata, and impossible "
            "analysis families before any workflow starts statistics"
        ),
    )


def require_feasible_experiment_design_for_analysis(
    design: ExperimentalDesignReport
    | ExperimentDesign
    | tuple[ExperimentalDesignEntry, ...],
    *,
    chosen_analysis_family: ExperimentDesignAnalysisFamily,
    condition_a: str | None = None,
    condition_b: str | None = None,
    batch_field: str | None = None,
    pairing_field: str | None = None,
    timepoint_field: str | None = None,
    ordered_timepoints: tuple[str, ...] = (),
    minimum_statistical_units_per_condition: int = 2,
) -> ExperimentFeasibilityReport:
    """Return one feasibility report or raise before statistics begin."""

    report = build_experiment_feasibility_report(
        design,
        condition_a=condition_a,
        condition_b=condition_b,
        batch_field=batch_field,
        pairing_field=pairing_field,
        timepoint_field=timepoint_field,
        ordered_timepoints=ordered_timepoints,
        minimum_statistical_units_per_condition=minimum_statistical_units_per_condition,
    )
    model_entry = next(
        entry
        for entry in report.model_support
        if entry.analysis_family is chosen_analysis_family
    )
    if not model_entry.supported:
        raise ValueError(
            "experiment design is not feasible for "
            f"{chosen_analysis_family.value}: {model_entry.message}"
        )
    if (
        chosen_analysis_family
        in (
            ExperimentDesignAnalysisFamily.PAIRWISE_DIFFERENTIAL,
            ExperimentDesignAnalysisFamily.PAIRED_DIFFERENTIAL,
        )
        and condition_a is not None
        and condition_b is not None
    ):
        contrast_entry = _find_contrast_entry(
            report,
            condition_a=condition_a,
            condition_b=condition_b,
        )
        if contrast_entry is None:
            raise ValueError(
                "experiment design is not feasible for "
                f"{chosen_analysis_family.value}: requested contrast "
                f"{condition_a} vs {condition_b} is not available"
            )
        if (
            chosen_analysis_family
            is ExperimentDesignAnalysisFamily.PAIRWISE_DIFFERENTIAL
        ):
            if not contrast_entry.supported:
                raise ValueError(
                    "experiment design is not feasible for "
                    f"{chosen_analysis_family.value}: {contrast_entry.message}"
                )
        elif not contrast_entry.supports_paired_model:
            raise ValueError(
                "experiment design is not feasible for "
                f"{chosen_analysis_family.value}: contrast {condition_a} vs "
                f"{condition_b} does not have the minimum complete pairs"
            )
    return report


def render_experiment_feasibility_valid_contrasts_tsv(
    report: ExperimentFeasibilityReport,
) -> str:
    """Render supported pairwise contrasts as TSV."""

    return _render_contrast_entries_tsv(report.valid_contrasts)


def render_experiment_feasibility_invalid_contrasts_tsv(
    report: ExperimentFeasibilityReport,
) -> str:
    """Render unsupported pairwise contrasts as TSV."""

    return _render_contrast_entries_tsv(report.invalid_contrasts)


def render_experiment_feasibility_group_sizes_tsv(
    report: ExperimentFeasibilityReport,
) -> str:
    """Render condition-level effective group sizes as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "condition",
            "effective_statistical_unit_count",
            "minimum_required_units",
            "underpowered",
        )
    )
    for entry in report.group_sizes:
        writer.writerow(
            (
                entry.condition,
                entry.effective_statistical_unit_count,
                entry.minimum_required_units,
                str(entry.underpowered).lower(),
            )
        )
    return buffer.getvalue()


def render_experiment_feasibility_missing_metadata_tsv(
    report: ExperimentFeasibilityReport,
) -> str:
    """Render missing metadata blockers and cautions as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        ("code", "message", "field", "sample_ids", "run_ids", "condition_ids")
    )
    for issue in report.missing_metadata:
        writer.writerow(
            (
                issue.code,
                issue.message,
                issue.field or "",
                ";".join(issue.sample_ids),
                ";".join(issue.run_ids),
                ";".join(issue.condition_ids),
            )
        )
    return buffer.getvalue()


def render_experiment_feasibility_model_support_tsv(
    report: ExperimentFeasibilityReport,
) -> str:
    """Render supported and impossible analysis families as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "analysis_family",
            "supported",
            "reason_codes",
            "required_fields",
            "message",
        )
    )
    for entry in report.model_support:
        writer.writerow(
            (
                entry.analysis_family.value,
                str(entry.supported).lower(),
                ";".join(entry.reason_codes),
                ";".join(entry.required_fields),
                entry.message,
            )
        )
    return buffer.getvalue()


def _coerce_design_entries(
    design: ExperimentalDesignReport
    | ExperimentDesign
    | tuple[ExperimentalDesignEntry, ...],
) -> tuple[tuple[ExperimentalDesignEntry, ...], int]:
    if isinstance(design, ExperimentalDesignReport):
        return design.accepted_entries, len(design.rejected_rows)
    experiment_design = coerce_experiment_design(design)
    return experiment_design.entries, 0


def _resolve_batch_field(
    experiment_design: ExperimentDesign,
    batch_field: str | None,
) -> str | None:
    if batch_field is not None:
        return batch_field or None
    if experiment_design.batches:
        return "batch"
    return None


def _resolve_pairing_field(
    experiment_design: ExperimentDesign,
    pairing_field: str | None,
) -> str | None:
    if pairing_field is not None:
        return pairing_field or None
    if experiment_design.pair_ids:
        return "pair_id"
    return None


def _resolve_timepoint_field(
    experiment_design: ExperimentDesign,
    timepoint_field: str | None,
) -> str | None:
    if timepoint_field is not None:
        return timepoint_field or None
    if experiment_design.timepoints:
        return "timepoint"
    return None


def _build_contrast_entries(
    experiment_design: ExperimentDesign,
    *,
    unit_counts: dict[str, int],
    minimum_statistical_units_per_condition: int,
    batch_field: str | None,
    pairing_field: str | None,
) -> tuple[ExperimentFeasibilityContrastEntry, ...]:
    entries: list[ExperimentFeasibilityContrastEntry] = []
    for condition_a, condition_b in combinations(experiment_design.conditions, 2):
        reason_codes: list[str] = []
        units_a = unit_counts.get(condition_a, 0)
        units_b = unit_counts.get(condition_b, 0)
        if units_a < minimum_statistical_units_per_condition:
            reason_codes.append("insufficient_group_size")
        if units_b < minimum_statistical_units_per_condition:
            reason_codes.append("insufficient_group_size")
        if batch_field is not None:
            validity_report = build_experiment_design_validity_report(
                experiment_design,
                condition_a=condition_a,
                condition_b=condition_b,
                batch_field=batch_field,
            )
            if validity_report.summary.confounded_batch_condition_count:
                reason_codes.append("batch_condition_confounding")
        complete_pair_count = _complete_pair_count(
            experiment_design,
            condition_a=condition_a,
            condition_b=condition_b,
            pairing_field=pairing_field,
        )
        supports_paired_model = pairing_field is not None and complete_pair_count >= 2
        supported = not reason_codes
        message = (
            f"contrast {condition_a} vs {condition_b} is supportable"
            if supported
            else (
                f"contrast {condition_a} vs {condition_b} is not supportable because "
                + ", ".join(sorted(set(reason_codes)))
            )
        )
        entries.append(
            ExperimentFeasibilityContrastEntry(
                condition_a=condition_a,
                condition_b=condition_b,
                effective_statistical_units_a=units_a,
                effective_statistical_units_b=units_b,
                minimum_required_units=minimum_statistical_units_per_condition,
                complete_pair_count=complete_pair_count,
                supported=supported,
                supports_paired_model=supports_paired_model,
                reason_codes=tuple(sorted(set(reason_codes))),
                message=message,
            )
        )
    return tuple(entries)


def _build_missing_metadata_issues(
    experiment_design: ExperimentDesign,
    *,
    parse_rejected_row_count: int,
    pairing_field: str | None,
    timepoint_field: str | None,
    batch_field: str | None,
) -> tuple[ExperimentFeasibilityMetadataIssue, ...]:
    issues: list[ExperimentFeasibilityMetadataIssue] = []
    if parse_rejected_row_count:
        issues.append(
            ExperimentFeasibilityMetadataIssue(
                code="rejected_design_rows",
                message=(
                    f"{parse_rejected_row_count} design row(s) were rejected during "
                    "parsing and are unavailable for feasibility assessment"
                ),
            )
        )
    if pairing_field is not None:
        missing_pair_entries = tuple(
            entry for entry in experiment_design.entries if entry.pair_id in (None, "")
        )
        if missing_pair_entries:
            issues.append(
                ExperimentFeasibilityMetadataIssue(
                    code="missing_pairing_metadata",
                    message=(
                        "paired analysis is incomplete because some design rows are "
                        "missing pair identifiers"
                    ),
                    field=pairing_field,
                    sample_ids=tuple(
                        sorted({entry.sample_id for entry in missing_pair_entries})
                    ),
                    run_ids=tuple(
                        sorted({entry.spectra_file for entry in missing_pair_entries})
                    ),
                    condition_ids=tuple(
                        sorted({entry.condition for entry in missing_pair_entries})
                    ),
                )
            )
    if timepoint_field is not None:
        missing_timepoint_entries = tuple(
            entry
            for entry in experiment_design.entries
            if entry.metadata.get(timepoint_field, "").strip() == ""
        )
        if missing_timepoint_entries:
            issues.append(
                ExperimentFeasibilityMetadataIssue(
                    code="missing_timepoint_metadata",
                    message=(
                        "time-course analysis is incomplete because some design rows "
                        "are missing timepoint metadata"
                    ),
                    field=timepoint_field,
                    sample_ids=tuple(
                        sorted({entry.sample_id for entry in missing_timepoint_entries})
                    ),
                    run_ids=tuple(
                        sorted(
                            {entry.spectra_file for entry in missing_timepoint_entries}
                        )
                    ),
                    condition_ids=tuple(
                        sorted({entry.condition for entry in missing_timepoint_entries})
                    ),
                )
            )
    if batch_field is not None:
        missing_batch_entries = tuple(
            entry for entry in experiment_design.entries if entry.batch in (None, "")
        )
        if missing_batch_entries and experiment_design.batches:
            issues.append(
                ExperimentFeasibilityMetadataIssue(
                    code="missing_batch_metadata",
                    message=(
                        "batch-adjusted analysis is incomplete because some design rows "
                        "are missing batch metadata"
                    ),
                    field=batch_field,
                    sample_ids=tuple(
                        sorted({entry.sample_id for entry in missing_batch_entries})
                    ),
                    run_ids=tuple(
                        sorted({entry.spectra_file for entry in missing_batch_entries})
                    ),
                    condition_ids=tuple(
                        sorted({entry.condition for entry in missing_batch_entries})
                    ),
                )
            )
    return tuple(issues)


def _build_model_support_entries(
    experiment_design: ExperimentDesign,
    *,
    classification_report: ExperimentDesignClassificationReport,
    validity_report: ExperimentDesignValidityReport,
    contrast_entries: tuple[ExperimentFeasibilityContrastEntry, ...],
    effective_pairing_field: str | None,
    effective_timepoint_field: str | None,
    minimum_statistical_units_per_condition: int,
) -> tuple[ExperimentFeasibilityModelEntry, ...]:
    valid_pairwise_contrast_count = sum(
        1 for entry in contrast_entries if entry.supported
    )
    invalid_pairwise_reason_codes = {
        reason_code
        for entry in contrast_entries
        if not entry.supported
        for reason_code in entry.reason_codes
    }
    underpowered_condition_count = len(
        {
            condition
            for entry in contrast_entries
            if "insufficient_group_size" in entry.reason_codes
            for condition in (entry.condition_a, entry.condition_b)
        }
    )
    paired_contrast_count = sum(
        1
        for entry in contrast_entries
        if entry.supported and entry.supports_paired_model
    )
    condition_count = len(experiment_design.conditions)
    invalid_reason_codes = {issue.code for issue in validity_report.issues}
    primary_design_type = classification_report.primary_design_type
    model_entries = [
        _pairwise_model_entry(
            primary_design_type=primary_design_type,
            valid_pairwise_contrast_count=valid_pairwise_contrast_count,
            invalid_pairwise_reason_codes=invalid_pairwise_reason_codes,
        ),
        _paired_model_entry(
            effective_pairing_field=effective_pairing_field,
            paired_contrast_count=paired_contrast_count,
            primary_design_type=primary_design_type,
        ),
        _multi_condition_model_entry(
            condition_count=condition_count,
            valid_pairwise_contrast_count=valid_pairwise_contrast_count,
            primary_design_type=primary_design_type,
            underpowered_condition_count=underpowered_condition_count,
        ),
        _time_course_model_entry(
            effective_timepoint_field=effective_timepoint_field,
            primary_design_type=primary_design_type,
            invalid_reason_codes=invalid_reason_codes,
            timepoint_count=len(experiment_design.timepoints),
        ),
    ]
    return tuple(model_entries)


def _pairwise_model_entry(
    *,
    primary_design_type: ExperimentDesignType,
    valid_pairwise_contrast_count: int,
    invalid_pairwise_reason_codes: set[str],
) -> ExperimentFeasibilityModelEntry:
    reason_codes: list[str] = []
    if valid_pairwise_contrast_count == 0:
        if invalid_pairwise_reason_codes:
            reason_codes.extend(sorted(invalid_pairwise_reason_codes))
        else:
            reason_codes.append("no_supported_contrast")
    if primary_design_type in (
        ExperimentDesignType.PAIRED,
        ExperimentDesignType.LONGITUDINAL,
        ExperimentDesignType.BATCH_CONFOUNDED,
        ExperimentDesignType.TARGETED_VALIDATION,
        ExperimentDesignType.EXPLORATORY,
    ):
        reason_codes.append("different_analysis_family_required")
    supported = not reason_codes
    return ExperimentFeasibilityModelEntry(
        analysis_family=ExperimentDesignAnalysisFamily.PAIRWISE_DIFFERENTIAL,
        supported=supported,
        reason_codes=tuple(sorted(set(reason_codes))),
        required_fields=(),
        message=(
            "pairwise differential analysis is supportable"
            if supported
            else "pairwise differential analysis is not supportable because "
            + ", ".join(sorted(set(reason_codes)))
        ),
    )


def _paired_model_entry(
    *,
    effective_pairing_field: str | None,
    paired_contrast_count: int,
    primary_design_type: ExperimentDesignType,
) -> ExperimentFeasibilityModelEntry:
    reason_codes: list[str] = []
    if effective_pairing_field is None:
        reason_codes.append("missing_pairing_metadata")
    if paired_contrast_count == 0:
        reason_codes.append("insufficient_complete_pairs")
    if primary_design_type in (
        ExperimentDesignType.LONGITUDINAL,
        ExperimentDesignType.BATCH_CONFOUNDED,
        ExperimentDesignType.TARGETED_VALIDATION,
        ExperimentDesignType.EXPLORATORY,
    ):
        reason_codes.append("different_analysis_family_required")
    supported = not reason_codes
    return ExperimentFeasibilityModelEntry(
        analysis_family=ExperimentDesignAnalysisFamily.PAIRED_DIFFERENTIAL,
        supported=supported,
        reason_codes=tuple(sorted(set(reason_codes))),
        required_fields=("pair_id",),
        message=(
            "paired differential analysis is supportable"
            if supported
            else "paired differential analysis is not supportable because "
            + ", ".join(sorted(set(reason_codes)))
        ),
    )


def _multi_condition_model_entry(
    *,
    condition_count: int,
    valid_pairwise_contrast_count: int,
    primary_design_type: ExperimentDesignType,
    underpowered_condition_count: int,
) -> ExperimentFeasibilityModelEntry:
    reason_codes: list[str] = []
    if condition_count < 2:
        reason_codes.append("insufficient_condition_count")
    if valid_pairwise_contrast_count == 0 or underpowered_condition_count > 0:
        reason_codes.append("insufficient_group_size")
    if primary_design_type in (
        ExperimentDesignType.PAIRED,
        ExperimentDesignType.LONGITUDINAL,
        ExperimentDesignType.BATCH_CONFOUNDED,
        ExperimentDesignType.TARGETED_VALIDATION,
        ExperimentDesignType.EXPLORATORY,
    ):
        reason_codes.append("different_analysis_family_required")
    supported = not reason_codes
    return ExperimentFeasibilityModelEntry(
        analysis_family=ExperimentDesignAnalysisFamily.MULTI_CONDITION_DIFFERENTIAL,
        supported=supported,
        reason_codes=tuple(sorted(set(reason_codes))),
        required_fields=(),
        message=(
            "multi-condition differential analysis is supportable"
            if supported
            else "multi-condition differential analysis is not supportable because "
            + ", ".join(sorted(set(reason_codes)))
        ),
    )


def _time_course_model_entry(
    *,
    effective_timepoint_field: str | None,
    primary_design_type: ExperimentDesignType,
    invalid_reason_codes: set[str],
    timepoint_count: int,
) -> ExperimentFeasibilityModelEntry:
    reason_codes: list[str] = []
    if effective_timepoint_field is None:
        reason_codes.append("missing_timepoint_metadata")
    if timepoint_count < 2:
        reason_codes.append("insufficient_timepoint_count")
    if "missing_timepoint_order" in invalid_reason_codes:
        reason_codes.append("missing_timepoint_order")
    if primary_design_type is not ExperimentDesignType.LONGITUDINAL:
        reason_codes.append("different_analysis_family_required")
    supported = not reason_codes
    return ExperimentFeasibilityModelEntry(
        analysis_family=ExperimentDesignAnalysisFamily.TIME_COURSE_DIFFERENTIAL,
        supported=supported,
        reason_codes=tuple(sorted(set(reason_codes))),
        required_fields=("timepoint",),
        message=(
            "time-course differential analysis is supportable"
            if supported
            else "time-course differential analysis is not supportable because "
            + ", ".join(sorted(set(reason_codes)))
        ),
    )


def _complete_pair_count(
    experiment_design: ExperimentDesign,
    *,
    condition_a: str,
    condition_b: str,
    pairing_field: str | None,
) -> int:
    if pairing_field is None:
        return 0
    pair_map: dict[str, dict[str, set[str]]] = {}
    for entry in experiment_design.entries:
        pair_id = entry.pair_id
        if pair_id in (None, "") or entry.condition not in {condition_a, condition_b}:
            continue
        pair_map.setdefault(pair_id, {}).setdefault(entry.condition, set()).add(
            entry.sample_id
        )
    return sum(
        1
        for by_condition in pair_map.values()
        if len(by_condition.get(condition_a, set())) == 1
        and len(by_condition.get(condition_b, set())) == 1
    )


def _find_contrast_entry(
    report: ExperimentFeasibilityReport,
    *,
    condition_a: str,
    condition_b: str,
) -> ExperimentFeasibilityContrastEntry | None:
    requested = frozenset((condition_a, condition_b))
    for entry in (*report.valid_contrasts, *report.invalid_contrasts):
        if frozenset((entry.condition_a, entry.condition_b)) == requested:
            return entry
    return None


def _render_contrast_entries_tsv(
    entries: tuple[ExperimentFeasibilityContrastEntry, ...],
) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "condition_a",
            "condition_b",
            "effective_statistical_units_a",
            "effective_statistical_units_b",
            "minimum_required_units",
            "complete_pair_count",
            "supported",
            "supports_paired_model",
            "reason_codes",
            "message",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.condition_a,
                entry.condition_b,
                entry.effective_statistical_units_a,
                entry.effective_statistical_units_b,
                entry.minimum_required_units,
                entry.complete_pair_count,
                str(entry.supported).lower(),
                str(entry.supports_paired_model).lower(),
                ";".join(entry.reason_codes),
                entry.message,
            )
        )
    return buffer.getvalue()


__all__ = [
    "ExperimentFeasibilityContrastEntry",
    "ExperimentFeasibilityGroupSizeEntry",
    "ExperimentFeasibilityMetadataIssue",
    "ExperimentFeasibilityModelEntry",
    "ExperimentFeasibilityReport",
    "ExperimentFeasibilitySummary",
    "build_experiment_feasibility_report",
    "render_experiment_feasibility_group_sizes_tsv",
    "render_experiment_feasibility_invalid_contrasts_tsv",
    "render_experiment_feasibility_missing_metadata_tsv",
    "render_experiment_feasibility_model_support_tsv",
    "render_experiment_feasibility_valid_contrasts_tsv",
    "require_feasible_experiment_design_for_analysis",
]
