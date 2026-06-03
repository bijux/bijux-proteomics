# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Run-order carryover detection over targeted precursor observations."""

from __future__ import annotations

import csv
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.lab.carryover import (
    CarryoverIntensityEntry,
    CarryoverRunOrderEntry,
    detect_carryover,
)
from bijux_proteomics.study.experiment_design import (
    ExperimentDesign,
    ExperimentDesignRun,
    coerce_experiment_design,
)
from bijux_proteomics.targeted.result_import import TargetedResultImportReport
from bijux_proteomics_foundation import JsonModel


class TargetedCarryoverCandidateEntry(JsonModel):
    """One ordered-run carryover candidate for one targeted precursor."""

    model_config = ConfigDict(extra="forbid")

    source_run_id: str = Field(..., min_length=1)
    source_sample_id: str = Field(..., min_length=1)
    source_run_order: int = Field(..., ge=1)
    affected_run_id: str = Field(..., min_length=1)
    affected_sample_id: str = Field(..., min_length=1)
    affected_run_order: int = Field(..., ge=1)
    order_gap: int = Field(..., ge=1)
    precursor_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    protein_ref: str | None = None
    source_total_intensity: float = Field(..., ge=0.0)
    affected_total_intensity: float = Field(..., ge=0.0)
    repeated_signal_fraction: float = Field(..., ge=0.0)
    carryover_score: float = Field(..., ge=0.0, le=1.0)
    concern_codes: tuple[str, ...] = Field(default_factory=tuple)


class TargetedCarryoverSummary(JsonModel):
    """Compact summary over one targeted carryover review."""

    model_config = ConfigDict(extra="forbid")

    run_count: int = Field(..., ge=0)
    precursor_count: int = Field(..., ge=0)
    candidate_entry_count: int = Field(..., ge=0)
    affected_run_count: int = Field(..., ge=0)
    source_run_count: int = Field(..., ge=0)


class TargetedCarryoverReport(JsonModel):
    """Ordered-run carryover report over targeted precursor observations."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(..., min_length=1)
    candidates: tuple[TargetedCarryoverCandidateEntry, ...] = Field(
        default_factory=tuple
    )
    summary: TargetedCarryoverSummary
    note: str = Field(..., min_length=1)


def build_targeted_carryover_report(
    import_report: TargetedResultImportReport,
    design: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    high_source_relative_fraction_threshold: float = 0.75,
    low_level_repeated_signal_fraction_threshold: float = 0.1,
) -> TargetedCarryoverReport:
    """Detect carryover from ordered targeted runs and low-level repeated signal."""

    if high_source_relative_fraction_threshold <= 0.0:
        raise ValueError("high_source_relative_fraction_threshold must be positive")
    if (
        low_level_repeated_signal_fraction_threshold <= 0.0
        or low_level_repeated_signal_fraction_threshold >= 1.0
    ):
        raise ValueError(
            "low_level_repeated_signal_fraction_threshold must be between 0 and 1"
        )

    experiment_design = coerce_experiment_design(design)
    ordered_runs = _ordered_design_runs_by_sample_id(experiment_design)
    totals_by_precursor_sample = _precursor_totals_by_sample(import_report)
    carryover_rows = detect_carryover(
        tuple(
            CarryoverRunOrderEntry(
                run_id=run.run_id,
                run_order=_required_run_order(run),
            )
            for run in ordered_runs.values()
        ),
        _carryover_matrix(
            ordered_runs=ordered_runs,
            totals_by_precursor_sample=totals_by_precursor_sample,
        ),
        high_source_relative_fraction_threshold=high_source_relative_fraction_threshold,
        low_level_repeated_signal_fraction_threshold=low_level_repeated_signal_fraction_threshold,
    )
    candidates: list[TargetedCarryoverCandidateEntry] = []
    sample_id_by_run_id = {
        run.run_id: sample_id for sample_id, run in ordered_runs.items()
    }
    for row in carryover_rows:
        peptide_sequence, protein_ref = _precursor_identity(
            import_report, row.entity_id
        )
        candidates.append(
            TargetedCarryoverCandidateEntry(
                source_run_id=row.source_run,
                source_sample_id=sample_id_by_run_id[row.source_run],
                source_run_order=row.source_run_order,
                affected_run_id=row.affected_run,
                affected_sample_id=sample_id_by_run_id[row.affected_run],
                affected_run_order=row.affected_run_order,
                order_gap=row.order_gap,
                precursor_id=row.entity_id,
                peptide_sequence=peptide_sequence,
                protein_ref=protein_ref,
                source_total_intensity=row.source_intensity,
                affected_total_intensity=row.affected_intensity,
                repeated_signal_fraction=row.repeated_signal_fraction,
                carryover_score=row.carryover_score,
                concern_codes=row.concern_codes,
            )
        )

    sorted_candidates = tuple(
        sorted(
            candidates,
            key=lambda entry: (
                entry.affected_run_order,
                entry.precursor_id,
                entry.source_run_order,
            ),
        )
    )
    return TargetedCarryoverReport(
        source_name=import_report.source_name,
        candidates=sorted_candidates,
        summary=TargetedCarryoverSummary(
            run_count=len(ordered_runs),
            precursor_count=len(totals_by_precursor_sample),
            candidate_entry_count=len(sorted_candidates),
            affected_run_count=len(
                {entry.affected_run_id for entry in sorted_candidates}
            ),
            source_run_count=len({entry.source_run_id for entry in sorted_candidates}),
        ),
        note=(
            "targeted carryover review requires explicit run order, then flags low-level repeated precursor signal that follows a high-intensity earlier run so source and affected runs stay reviewable before follow-up trust"
        ),
    )


def render_targeted_carryover_summary_tsv(report: TargetedCarryoverReport) -> str:
    """Render the compact targeted carryover summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "source_name",
            "run_count",
            "precursor_count",
            "candidate_entry_count",
            "affected_run_count",
            "source_run_count",
            "note",
        ]
    )
    writer.writerow(
        [
            report.source_name,
            report.summary.run_count,
            report.summary.precursor_count,
            report.summary.candidate_entry_count,
            report.summary.affected_run_count,
            report.summary.source_run_count,
            report.note,
        ]
    )
    return buffer.getvalue()


def render_targeted_carryover_candidates_tsv(report: TargetedCarryoverReport) -> str:
    """Render targeted carryover candidates as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "source_run_id",
            "source_sample_id",
            "source_run_order",
            "affected_run_id",
            "affected_sample_id",
            "affected_run_order",
            "order_gap",
            "precursor_id",
            "peptide_sequence",
            "protein_ref",
            "source_total_intensity",
            "affected_total_intensity",
            "repeated_signal_fraction",
            "carryover_score",
            "concern_codes",
        ]
    )
    for entry in report.candidates:
        writer.writerow(
            [
                entry.source_run_id,
                entry.source_sample_id,
                entry.source_run_order,
                entry.affected_run_id,
                entry.affected_sample_id,
                entry.affected_run_order,
                entry.order_gap,
                entry.precursor_id,
                entry.peptide_sequence,
                "" if entry.protein_ref is None else entry.protein_ref,
                f"{entry.source_total_intensity:g}",
                f"{entry.affected_total_intensity:g}",
                f"{entry.repeated_signal_fraction:.6f}",
                f"{entry.carryover_score:.4f}",
                "|".join(entry.concern_codes),
            ]
        )
    return buffer.getvalue()


def _ordered_design_runs_by_sample_id(
    design: ExperimentDesign,
) -> dict[str, ExperimentDesignRun]:
    runs_by_sample_id: dict[str, ExperimentDesignRun] = {}
    missing_run_order = [run.sample_id for run in design.runs if run.run_order is None]
    if missing_run_order:
        raise ValueError(
            "run_order is required for carryover analysis and is missing for: "
            + ", ".join(sorted(set(missing_run_order)))
        )
    duplicate_sample_ids = {
        run.sample_id
        for run in design.runs
        if sum(candidate.sample_id == run.sample_id for candidate in design.runs) > 1
    }
    if duplicate_sample_ids:
        raise ValueError(
            "carryover analysis requires one ordered design run per targeted sample_id and is ambiguous for: "
            + ", ".join(sorted(duplicate_sample_ids))
        )
    duplicate_run_order: set[int] = {
        run.run_order
        for run in design.runs
        if run.run_order is not None
        and sum(candidate.run_order == run.run_order for candidate in design.runs) > 1
    }
    if duplicate_run_order:
        duplicated = ", ".join(str(value) for value in sorted(duplicate_run_order))
        raise ValueError(
            "carryover analysis requires unique run_order values and found duplicates for: "
            + duplicated
        )
    for run in design.runs:
        runs_by_sample_id[run.sample_id] = run
    return runs_by_sample_id


def _precursor_totals_by_sample(
    import_report: TargetedResultImportReport,
) -> dict[str, dict[str, float]]:
    totals: dict[str, dict[str, float]] = {}
    for observation in import_report.observations:
        totals.setdefault(observation.precursor_id, {}).setdefault(
            observation.sample_id,
            0.0,
        )
        totals[observation.precursor_id][observation.sample_id] += observation.intensity
    return totals


def _precursor_identity(
    import_report: TargetedResultImportReport,
    precursor_id: str,
) -> tuple[str, str | None]:
    matching = [
        observation
        for observation in import_report.observations
        if observation.precursor_id == precursor_id
    ]
    if not matching:
        raise ValueError(f"precursor identity is missing for {precursor_id!r}")
    protein_ref = next(
        (
            observation.protein_ref
            for observation in matching
            if observation.protein_ref
        ),
        None,
    )
    return matching[0].peptide_sequence, protein_ref


def _required_run_order(run: ExperimentDesignRun) -> int:
    if run.run_order is None:
        raise ValueError(
            "carryover analysis requires validated run_order values for all design runs"
        )
    return run.run_order


def _carryover_matrix(
    *,
    ordered_runs: dict[str, ExperimentDesignRun],
    totals_by_precursor_sample: dict[str, dict[str, float]],
) -> tuple[CarryoverIntensityEntry, ...]:
    rows: list[CarryoverIntensityEntry] = []
    for precursor_id, sample_totals in sorted(totals_by_precursor_sample.items()):
        for sample_id, intensity in sorted(sample_totals.items()):
            run = ordered_runs.get(sample_id)
            if run is None:
                continue
            rows.append(
                CarryoverIntensityEntry(
                    run_id=run.run_id,
                    entity_id=precursor_id,
                    intensity=intensity,
                )
            )
    return tuple(rows)


__all__ = [
    "TargetedCarryoverCandidateEntry",
    "TargetedCarryoverReport",
    "TargetedCarryoverSummary",
    "build_targeted_carryover_report",
    "render_targeted_carryover_candidates_tsv",
    "render_targeted_carryover_summary_tsv",
]
