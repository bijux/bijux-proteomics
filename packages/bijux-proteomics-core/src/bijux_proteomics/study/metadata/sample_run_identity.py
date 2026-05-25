# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned biological-sample to run identity model with explicit run-handling policy."""

from __future__ import annotations

from collections import defaultdict
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    ExperimentalDesignSampleRole,
)
from bijux_proteomics.study.design.experiment_design import (
    ExperimentDesign,
    coerce_experiment_design,
)
from bijux_proteomics_foundation import JsonModel


class SampleRunAnalysisPolicy(StrEnum):
    """Explicit policy for handling multiple LC-MS runs from one biological sample."""

    COMBINE_TECHNICAL_RUNS = "combine_technical_runs"
    SEPARATE_TECHNICAL_RUNS = "separate_technical_runs"


class SampleRunIdentitySample(JsonModel):
    """One biological sample and its governed run assignments."""

    model_config = ConfigDict(extra="forbid")

    biological_sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    cohort: str | None = None
    pair_id: str | None = None
    timepoint: str | None = None
    species: str | None = None
    tissue_or_cell_type: str | None = None
    perturbation: str | None = None
    sample_role: ExperimentalDesignSampleRole
    run_ids: tuple[str, ...] = Field(default_factory=tuple)
    technical_replicate_ids: tuple[str, ...] = Field(default_factory=tuple)


class SampleRunAssignment(JsonModel):
    """One explicit mapping from a biological sample to a run and analysis sample."""

    model_config = ConfigDict(extra="forbid")

    biological_sample_id: str = Field(..., min_length=1)
    analysis_sample_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    technical_replicate_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    sample_role: ExperimentalDesignSampleRole


class SampleRunIdentitySummary(JsonModel):
    """Deterministic summary over explicit sample and run identity assignments."""

    model_config = ConfigDict(extra="forbid")

    biological_sample_count: int = Field(..., ge=0)
    run_count: int = Field(..., ge=0)
    technical_replicate_count: int = Field(..., ge=0)
    analysis_sample_count: int = Field(..., ge=0)
    multi_run_sample_count: int = Field(..., ge=0)
    multi_technical_replicate_sample_count: int = Field(..., ge=0)


class SampleRunIdentityReport(JsonModel):
    """Owned run-identity report with resolved analysis entries under one policy."""

    model_config = ConfigDict(extra="forbid")

    experiment_design: ExperimentDesign
    policy: SampleRunAnalysisPolicy
    samples: tuple[SampleRunIdentitySample, ...] = Field(default_factory=tuple)
    run_assignments: tuple[SampleRunAssignment, ...] = Field(default_factory=tuple)
    analysis_entries: tuple[ExperimentalDesignEntry, ...] = Field(default_factory=tuple)
    summary: SampleRunIdentitySummary
    note: str = Field(..., min_length=1)


def build_sample_run_identity_report(
    design: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    policy: SampleRunAnalysisPolicy = SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS,
    required_consistency_fields: tuple[str, ...] = (),
) -> SampleRunIdentityReport:
    """Connect biological sample ids to run ids and technical replicate ids."""

    experiment_design = coerce_experiment_design(design)
    sample_entries = _entries_by_sample(experiment_design.entries)
    samples: list[SampleRunIdentitySample] = []
    run_assignments: list[SampleRunAssignment] = []
    analysis_entries: list[ExperimentalDesignEntry] = []

    for biological_sample_id in sorted(sample_entries):
        entries = sample_entries[biological_sample_id]
        primary = entries[0]
        technical_replicate_ids = tuple(
            sorted({_technical_replicate_id(entry) for entry in entries})
        )
        samples.append(
            SampleRunIdentitySample(
                biological_sample_id=biological_sample_id,
                condition=primary.condition,
                cohort=primary.cohort,
                pair_id=primary.pair_id,
                timepoint=_resolve_entry_field(primary, "timepoint"),
                species=_resolve_entry_field(primary, "species"),
                tissue_or_cell_type=_resolve_entry_field(
                    primary,
                    "tissue_or_cell_type",
                ),
                perturbation=_resolve_entry_field(primary, "perturbation"),
                sample_role=primary.sample_role,
                run_ids=tuple(sorted(entry.spectra_file for entry in entries)),
                technical_replicate_ids=technical_replicate_ids,
            )
        )
        if policy is SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS:
            analysis_entry = _combine_analysis_entry(
                biological_sample_id=biological_sample_id,
                entries=entries,
                required_consistency_fields=required_consistency_fields,
            )
            analysis_entries.append(analysis_entry)
            for entry in entries:
                run_assignments.append(
                    SampleRunAssignment(
                        biological_sample_id=biological_sample_id,
                        analysis_sample_id=analysis_entry.sample_id,
                        run_id=entry.spectra_file,
                        technical_replicate_id=_technical_replicate_id(entry),
                        condition=entry.condition,
                        sample_role=entry.sample_role,
                    )
                )
            continue
        for entry in entries:
            analysis_sample_id = _analysis_sample_id(
                biological_sample_id,
                _technical_replicate_id(entry),
            )
            analysis_entry = entry.model_copy(
                update={
                    "sample_id": analysis_sample_id,
                    "metadata": {
                        **entry.metadata,
                        "analysis_sample_id": analysis_sample_id,
                        "biological_sample_id": biological_sample_id,
                        "sample_run_policy": policy.value,
                    },
                }
            )
            analysis_entries.append(analysis_entry)
            run_assignments.append(
                SampleRunAssignment(
                    biological_sample_id=biological_sample_id,
                    analysis_sample_id=analysis_sample_id,
                    run_id=entry.spectra_file,
                    technical_replicate_id=_technical_replicate_id(entry),
                    condition=entry.condition,
                    sample_role=entry.sample_role,
                )
            )

    biological_samples = tuple(sorted(sample_entries))
    technical_replicates = {
        _technical_replicate_id(entry)
        for entry in experiment_design.entries
    }
    return SampleRunIdentityReport(
        experiment_design=experiment_design,
        policy=policy,
        samples=tuple(samples),
        run_assignments=tuple(
            sorted(
                run_assignments,
                key=lambda assignment: (
                    assignment.biological_sample_id,
                    assignment.analysis_sample_id,
                    assignment.run_id,
                ),
            )
        ),
        analysis_entries=tuple(
            sorted(
                analysis_entries,
                key=lambda entry: (entry.sample_id, entry.spectra_file),
            )
        ),
        summary=SampleRunIdentitySummary(
            biological_sample_count=len(biological_samples),
            run_count=len(experiment_design.runs),
            technical_replicate_count=len(technical_replicates),
            analysis_sample_count=len(analysis_entries),
            multi_run_sample_count=sum(
                1 for sample in samples if len(sample.run_ids) > 1
            ),
            multi_technical_replicate_sample_count=sum(
                1 for sample in samples if len(sample.technical_replicate_ids) > 1
            ),
        ),
        note=(
            "sample and run identity resolution connects biological sample ids to "
            "explicit LC-MS run ids and technical replicate ids, then resolves "
            "analysis-facing sample identities under one governed run-handling policy"
        ),
    )


def resolve_sample_run_analysis_entries(
    design: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    policy: SampleRunAnalysisPolicy = SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS,
    required_consistency_fields: tuple[str, ...] = (),
) -> tuple[ExperimentalDesignEntry, ...]:
    """Return policy-resolved analysis entries with explicit sample identities."""

    report = build_sample_run_identity_report(
        design,
        policy=policy,
        required_consistency_fields=required_consistency_fields,
    )
    return report.analysis_entries


def _combine_analysis_entry(
    *,
    biological_sample_id: str,
    entries: tuple[ExperimentalDesignEntry, ...],
    required_consistency_fields: tuple[str, ...],
) -> ExperimentalDesignEntry:
    primary = entries[0]
    consistency_fields = _DEFAULT_CONSISTENCY_FIELDS + tuple(
        field
        for field in required_consistency_fields
        if field not in _DEFAULT_CONSISTENCY_FIELDS
    )
    for field in consistency_fields:
        values = {
            value
            for value in (
                _resolve_entry_field(entry, field)
                for entry in entries
            )
            if value not in (None, "")
        }
        if len(values) <= 1:
            continue
        raise ValueError(
            "sample/run policy "
            f"{SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS.value!r} requires "
            f"one consistent {field!r} value across runs for biological sample "
            f"{biological_sample_id!r}"
        )
    return primary.model_copy(
        update={
            "metadata": {
                **primary.metadata,
                "analysis_sample_id": biological_sample_id,
                "biological_sample_id": biological_sample_id,
                "run_ids": ";".join(sorted(entry.spectra_file for entry in entries)),
                "technical_replicate_ids": ";".join(
                    sorted(_technical_replicate_id(entry) for entry in entries)
                ),
                "sample_run_policy": (
                    SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS.value
                ),
            }
        }
    )


def _analysis_sample_id(
    biological_sample_id: str,
    technical_replicate_id: str,
) -> str:
    return (
        f"{biological_sample_id}__technical_replicate_{technical_replicate_id}"
    )


def _entries_by_sample(
    entries: tuple[ExperimentalDesignEntry, ...],
) -> dict[str, tuple[ExperimentalDesignEntry, ...]]:
    grouped: dict[str, list[ExperimentalDesignEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.sample_id].append(entry)
    return {
        sample_id: tuple(
            sorted(
                sample_entries,
                key=lambda entry: (
                    _technical_replicate_id(entry),
                    entry.spectra_file,
                    entry.fraction,
                ),
            )
        )
        for sample_id, sample_entries in grouped.items()
    }


def _resolve_entry_field(
    entry: ExperimentalDesignEntry,
    field: str,
) -> str | None:
    direct_fields = {
        "sample_id": entry.sample_id,
        "cohort": entry.cohort,
        "condition": entry.condition,
        "batch": entry.batch,
        "instrument": entry.instrument,
        "search_engine": entry.search_engine,
        "pair_id": entry.pair_id,
        "technical_replicate_id": entry.technical_replicate_id,
        "multiplex_group": entry.multiplex_group,
        "multiplex_channel": entry.multiplex_channel,
        "sample_role": entry.sample_role.value,
    }
    if field == "tissue_or_cell_type":
        return (
            entry.metadata.get("tissue_or_cell_type")
            or entry.metadata.get("tissue")
            or entry.metadata.get("cell_type")
        )
    if field in direct_fields:
        return direct_fields[field]
    return entry.metadata.get(field)


def _technical_replicate_id(entry: ExperimentalDesignEntry) -> str:
    if entry.technical_replicate_id not in (None, ""):
        assert entry.technical_replicate_id is not None
        return entry.technical_replicate_id
    return entry.spectra_file


_DEFAULT_CONSISTENCY_FIELDS = (
    "condition",
    "cohort",
    "pair_id",
    "sample_role",
    "timepoint",
    "species",
    "tissue_or_cell_type",
    "perturbation",
)
