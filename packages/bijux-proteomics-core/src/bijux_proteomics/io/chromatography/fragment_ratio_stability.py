# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Cross-run fragment-ratio stability over DIA and targeted fragment evidence."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from statistics import median
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.io.chromatography.dia_fragment_coelution import (
    DiaFragmentCoelutionReport,
)
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.targeted.result_import import TargetedResultImportReport


class FragmentRatioDataKind(StrEnum):
    """Owned raw-signal ratio-stability data kinds."""

    DIA = "dia"
    TARGETED = "targeted"


class FragmentRatioStabilityObservationEntry(JsonModel):
    """One run-resolved fragment-ratio observation against a cross-run expectation."""

    model_config = ConfigDict(extra="forbid")

    data_kind: FragmentRatioDataKind
    analyte_id: str = Field(..., min_length=1)
    peptide_ref: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    fragment_id: str = Field(..., min_length=1)
    expected_ratio: float = Field(..., ge=0.0, le=1.0)
    observed_ratio: float = Field(..., ge=0.0, le=1.0)
    absolute_ratio_delta: float = Field(..., ge=0.0, le=1.0)
    ratio_cv: float | None = Field(default=None, ge=0.0)
    drift_flag: bool = False
    unstable_fragment: bool = False
    concern_codes: tuple[str, ...] = Field(default_factory=tuple)


class FragmentRatioStabilityFragmentEntry(JsonModel):
    """One fragment-level stability summary over all observed runs for one analyte."""

    model_config = ConfigDict(extra="forbid")

    data_kind: FragmentRatioDataKind
    analyte_id: str = Field(..., min_length=1)
    peptide_ref: str = Field(..., min_length=1)
    fragment_id: str = Field(..., min_length=1)
    run_count: int = Field(..., ge=0)
    observed_run_count: int = Field(..., ge=0)
    expected_ratio: float = Field(..., ge=0.0, le=1.0)
    ratio_cv: float | None = Field(default=None, ge=0.0)
    drift_flagged_run_count: int = Field(..., ge=0)
    unstable_fragment: bool = False
    stability_score: float = Field(..., ge=0.0, le=1.0)
    concern_codes: tuple[str, ...] = Field(default_factory=tuple)


class FragmentRatioStabilitySummary(JsonModel):
    """Compact summary over one fragment-ratio stability report."""

    model_config = ConfigDict(extra="forbid")

    analyte_count: int = Field(..., ge=0)
    run_count: int = Field(..., ge=0)
    fragment_entry_count: int = Field(..., ge=0)
    observation_entry_count: int = Field(..., ge=0)
    unstable_fragment_count: int = Field(..., ge=0)
    drift_flagged_observation_count: int = Field(..., ge=0)


class FragmentRatioStabilityReport(JsonModel):
    """Cross-run fragment-ratio stability report over one raw-signal evidence kind."""

    model_config = ConfigDict(extra="forbid")

    data_kind: FragmentRatioDataKind
    fragment_entries: tuple[FragmentRatioStabilityFragmentEntry, ...] = Field(
        default_factory=tuple
    )
    observation_entries: tuple[FragmentRatioStabilityObservationEntry, ...] = Field(
        default_factory=tuple
    )
    summary: FragmentRatioStabilitySummary
    note: str = Field(..., min_length=1)


def build_targeted_fragment_ratio_stability_report(
    import_report: "TargetedResultImportReport",
    *,
    absolute_ratio_delta_threshold: float = 0.12,
    ratio_cv_threshold: float = 0.25,
) -> FragmentRatioStabilityReport:
    """Build cross-run transition-ratio stability from targeted observations."""

    observations: list[_RatioObservation] = []
    runs_by_analyte = _runs_by_targeted_analyte(import_report)
    for (analyte_id, run_id), analyte_observations in sorted(runs_by_analyte.items()):
        total_intensity = sum(item.intensity for item in analyte_observations)
        if total_intensity <= 0.0:
            continue
        peptide_ref = analyte_observations[0].peptide_sequence
        for observation in analyte_observations:
            observations.append(
                _RatioObservation(
                    analyte_id=analyte_id,
                    peptide_ref=peptide_ref,
                    run_id=run_id,
                    fragment_id=observation.transition_id,
                    observed_ratio=observation.intensity / total_intensity,
                )
            )

    return _build_fragment_ratio_stability_report(
        FragmentRatioDataKind.TARGETED,
        observations,
        absolute_ratio_delta_threshold=absolute_ratio_delta_threshold,
        ratio_cv_threshold=ratio_cv_threshold,
        note=(
            "fragment-ratio stability keeps targeted transition-share expectations, run-level drift, and cross-run instability visible before any transition is trusted for targeted support"
        ),
    )


def score_dia_fragment_ratio_stability(
    coelution_report: DiaFragmentCoelutionReport,
    *,
    absolute_ratio_delta_threshold: float = 0.12,
    ratio_cv_threshold: float = 0.25,
) -> FragmentRatioStabilityReport:
    """Build cross-run fragment-ratio stability from DIA fragment-trace coelution."""

    observations: list[_RatioObservation] = []
    fragments_by_run = _dia_fragments_by_run(coelution_report)
    for (analyte_id, run_id), fragment_entries in sorted(fragments_by_run.items()):
        total_area = sum(entry.area for entry in fragment_entries if entry.area > 0.0)
        if total_area <= 0.0:
            continue
        peptide_ref = fragment_entries[0].peptide_ref
        for entry in fragment_entries:
            if entry.area <= 0.0:
                continue
            observations.append(
                _RatioObservation(
                    analyte_id=analyte_id,
                    peptide_ref=peptide_ref,
                    run_id=run_id,
                    fragment_id=entry.fragment_id,
                    observed_ratio=entry.area / total_area,
                )
            )

    return _build_fragment_ratio_stability_report(
        FragmentRatioDataKind.DIA,
        observations,
        absolute_ratio_delta_threshold=absolute_ratio_delta_threshold,
        ratio_cv_threshold=ratio_cv_threshold,
        note=(
            "fragment-ratio stability keeps DIA fragment-share expectations, run-level drift, and cross-run instability visible before any fragment is trusted for precursor support"
        ),
    )


def render_fragment_ratio_stability_fragments_tsv(
    report: FragmentRatioStabilityReport,
) -> str:
    """Render fragment-level ratio-stability summaries as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "data_kind",
            "analyte_id",
            "peptide_ref",
            "fragment_id",
            "run_count",
            "observed_run_count",
            "expected_ratio",
            "ratio_cv",
            "drift_flagged_run_count",
            "unstable_fragment",
            "stability_score",
            "concern_codes",
        )
    )
    for entry in report.fragment_entries:
        writer.writerow(
            (
                entry.data_kind.value,
                entry.analyte_id,
                entry.peptide_ref,
                entry.fragment_id,
                entry.run_count,
                entry.observed_run_count,
                f"{entry.expected_ratio:.6f}",
                "" if entry.ratio_cv is None else f"{entry.ratio_cv:.6f}",
                entry.drift_flagged_run_count,
                str(entry.unstable_fragment).lower(),
                f"{entry.stability_score:.6f}",
                "|".join(entry.concern_codes),
            )
        )
    return buffer.getvalue()


def render_fragment_ratio_stability_observations_tsv(
    report: FragmentRatioStabilityReport,
) -> str:
    """Render run-level ratio observations and drift flags as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "data_kind",
            "analyte_id",
            "peptide_ref",
            "run_id",
            "fragment_id",
            "expected_ratio",
            "observed_ratio",
            "absolute_ratio_delta",
            "ratio_cv",
            "drift_flag",
            "unstable_fragment",
            "concern_codes",
        )
    )
    for entry in report.observation_entries:
        writer.writerow(
            (
                entry.data_kind.value,
                entry.analyte_id,
                entry.peptide_ref,
                entry.run_id,
                entry.fragment_id,
                f"{entry.expected_ratio:.6f}",
                f"{entry.observed_ratio:.6f}",
                f"{entry.absolute_ratio_delta:.6f}",
                "" if entry.ratio_cv is None else f"{entry.ratio_cv:.6f}",
                str(entry.drift_flag).lower(),
                str(entry.unstable_fragment).lower(),
                "|".join(entry.concern_codes),
            )
        )
    return buffer.getvalue()


class _RatioObservation(JsonModel):
    """Internal run-level fragment ratio input."""

    model_config = ConfigDict(extra="forbid")

    analyte_id: str = Field(..., min_length=1)
    peptide_ref: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    fragment_id: str = Field(..., min_length=1)
    observed_ratio: float = Field(..., ge=0.0, le=1.0)


def _build_fragment_ratio_stability_report(
    data_kind: FragmentRatioDataKind,
    observations: list[_RatioObservation],
    *,
    absolute_ratio_delta_threshold: float,
    ratio_cv_threshold: float,
    note: str,
) -> FragmentRatioStabilityReport:
    if absolute_ratio_delta_threshold <= 0.0:
        raise ValueError("absolute_ratio_delta_threshold must be greater than zero")
    if ratio_cv_threshold <= 0.0:
        raise ValueError("ratio_cv_threshold must be greater than zero")

    grouped_by_fragment: dict[tuple[str, str], list[_RatioObservation]] = {}
    run_ids: set[str] = set()
    analyte_ids: set[str] = set()
    runs_by_analyte: dict[str, set[str]] = {}
    for observation in observations:
        grouped_by_fragment.setdefault(
            (observation.analyte_id, observation.fragment_id),
            [],
        ).append(observation)
        run_ids.add(observation.run_id)
        analyte_ids.add(observation.analyte_id)
        runs_by_analyte.setdefault(observation.analyte_id, set()).add(observation.run_id)

    fragment_entries: list[FragmentRatioStabilityFragmentEntry] = []
    observation_entries: list[FragmentRatioStabilityObservationEntry] = []
    for (analyte_id, fragment_id), fragment_observations in sorted(grouped_by_fragment.items()):
        observed_ratios = [entry.observed_ratio for entry in fragment_observations]
        peptide_ref = fragment_observations[0].peptide_ref
        expected_ratio = median(observed_ratios)
        ratio_cv = _coefficient_of_variation(observed_ratios)
        unstable_fragment = ratio_cv is not None and ratio_cv > ratio_cv_threshold

        drift_flagged_run_count = 0
        for observation in sorted(fragment_observations, key=lambda item: item.run_id):
            absolute_ratio_delta = abs(observation.observed_ratio - expected_ratio)
            drift_flag = absolute_ratio_delta > absolute_ratio_delta_threshold
            if drift_flag:
                drift_flagged_run_count += 1
            concern_codes: list[str] = []
            if drift_flag:
                concern_codes.append("ratio_drift")
            if unstable_fragment:
                concern_codes.append("high_ratio_cv")
            observation_entries.append(
                FragmentRatioStabilityObservationEntry(
                    data_kind=data_kind,
                    analyte_id=analyte_id,
                    peptide_ref=observation.peptide_ref,
                    run_id=observation.run_id,
                    fragment_id=fragment_id,
                    expected_ratio=expected_ratio,
                    observed_ratio=observation.observed_ratio,
                    absolute_ratio_delta=absolute_ratio_delta,
                    ratio_cv=ratio_cv,
                    drift_flag=drift_flag,
                    unstable_fragment=unstable_fragment,
                    concern_codes=tuple(concern_codes),
                )
            )

        fragment_concerns: list[str] = []
        if len(fragment_observations) < 2:
            fragment_concerns.append("insufficient_runs")
        if drift_flagged_run_count > 0:
            fragment_concerns.append("ratio_drift")
        if unstable_fragment:
            fragment_concerns.append("high_ratio_cv")
        fragment_entries.append(
            FragmentRatioStabilityFragmentEntry(
                data_kind=data_kind,
                analyte_id=analyte_id,
                peptide_ref=peptide_ref,
                fragment_id=fragment_id,
                run_count=len(runs_by_analyte.get(analyte_id, set())),
                observed_run_count=len(fragment_observations),
                expected_ratio=expected_ratio,
                ratio_cv=ratio_cv,
                drift_flagged_run_count=drift_flagged_run_count,
                unstable_fragment=unstable_fragment,
                stability_score=_stability_score(
                    ratio_cv=ratio_cv,
                    ratio_cv_threshold=ratio_cv_threshold,
                    drift_flagged_run_count=drift_flagged_run_count,
                    observed_run_count=len(fragment_observations),
                ),
                concern_codes=tuple(fragment_concerns),
            )
        )

    sorted_fragment_entries = tuple(
        sorted(
            fragment_entries,
            key=lambda entry: (
                entry.analyte_id,
                entry.fragment_id,
            ),
        )
    )
    sorted_observation_entries = tuple(
        sorted(
            observation_entries,
            key=lambda entry: (
                entry.analyte_id,
                entry.run_id,
                entry.fragment_id,
            ),
        )
    )
    return FragmentRatioStabilityReport(
        data_kind=data_kind,
        fragment_entries=sorted_fragment_entries,
        observation_entries=sorted_observation_entries,
        summary=FragmentRatioStabilitySummary(
            analyte_count=len(analyte_ids),
            run_count=len(run_ids),
            fragment_entry_count=len(sorted_fragment_entries),
            observation_entry_count=len(sorted_observation_entries),
            unstable_fragment_count=sum(
                entry.unstable_fragment for entry in sorted_fragment_entries
            ),
            drift_flagged_observation_count=sum(
                entry.drift_flag for entry in sorted_observation_entries
            ),
        ),
        note=note,
    )


def _runs_by_targeted_analyte(
    import_report: "TargetedResultImportReport",
) -> dict[tuple[str, str], list[object]]:
    grouped: dict[tuple[str, str], list[object]] = {}
    for observation in import_report.observations:
        grouped.setdefault((observation.precursor_id, observation.sample_id), []).append(
            observation
        )
    return grouped


def _dia_fragments_by_run(
    report: DiaFragmentCoelutionReport,
) -> dict[tuple[str, str], list[object]]:
    grouped: dict[tuple[str, str], list[object]] = {}
    for entry in report.fragment_entries:
        grouped.setdefault((entry.precursor_id, entry.run_id), []).append(entry)
    return grouped


def _coefficient_of_variation(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean_value = sum(values) / len(values)
    if mean_value <= 0.0:
        return None
    squared_distance_sum = sum((value - mean_value) ** 2 for value in values)
    variance = squared_distance_sum / (len(values) - 1)
    return variance**0.5 / mean_value


def _stability_score(
    *,
    ratio_cv: float | None,
    ratio_cv_threshold: float,
    drift_flagged_run_count: int,
    observed_run_count: int,
) -> float:
    cv_penalty = (
        0.0
        if ratio_cv is None
        else 0.5 * min(ratio_cv / ratio_cv_threshold, 1.0)
    )
    drift_penalty = (
        0.0
        if observed_run_count <= 0
        else 0.5 * min(drift_flagged_run_count / observed_run_count, 1.0)
    )
    return max(0.0, round(1.0 - cv_penalty - drift_penalty, 4))
