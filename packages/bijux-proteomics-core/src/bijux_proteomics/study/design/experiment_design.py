# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned experiment-design object shared across proteomics workflows."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry, ExperimentalDesignSampleRole
from bijux_proteomics_foundation import JsonModel


class ExperimentDesignChannel(JsonModel):
    """One multiplex channel assignment inside an experiment design."""

    model_config = ConfigDict(extra="forbid")

    plex_id: str = Field(..., min_length=1)
    channel_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    sample_role: ExperimentalDesignSampleRole


class ExperimentDesignPlex(JsonModel):
    """One multiplex group in an experiment design."""

    model_config = ConfigDict(extra="forbid")

    plex_id: str = Field(..., min_length=1)
    run_ids: tuple[str, ...] = Field(default_factory=tuple)
    channels: tuple[ExperimentDesignChannel, ...] = Field(default_factory=tuple)
    channel_count: int = Field(..., ge=0)


class ExperimentDesignRun(JsonModel):
    """One LC-MS run inside an owned experiment design."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    technical_replicate_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    cohort: str | None = None
    replicate: int = Field(..., ge=1)
    fraction: int = Field(..., ge=1)
    spectra_file: str = Field(..., min_length=1)
    identifications_file: str | None = None
    batch: str | None = None
    instrument: str | None = None
    search_engine: str | None = None
    pair_id: str | None = None
    run_order: int | None = Field(default=None, ge=1)
    timepoint: str | None = None
    species: str | None = None
    tissue_or_cell_type: str | None = None
    perturbation: str | None = None
    plex_id: str | None = None
    channel_id: str | None = None
    sample_role: ExperimentalDesignSampleRole
    metadata: dict[str, str] = Field(default_factory=dict)


class ExperimentDesignSample(JsonModel):
    """One biological sample aggregated across one or more runs."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    cohort: str | None = None
    pair_id: str | None = None
    timepoint: str | None = None
    species: str | None = None
    tissue_or_cell_type: str | None = None
    perturbation: str | None = None
    run_ids: tuple[str, ...] = Field(default_factory=tuple)
    technical_replicate_ids: tuple[str, ...] = Field(default_factory=tuple)
    batch_ids: tuple[str, ...] = Field(default_factory=tuple)
    instrument_ids: tuple[str, ...] = Field(default_factory=tuple)
    plex_ids: tuple[str, ...] = Field(default_factory=tuple)
    channel_ids: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, str] = Field(default_factory=dict)


class ExperimentDesignSummary(JsonModel):
    """Deterministic summary over one experiment-design object."""

    model_config = ConfigDict(extra="forbid")

    sample_count: int = Field(..., ge=0)
    run_count: int = Field(..., ge=0)
    technical_replicate_count: int = Field(..., ge=0)
    condition_count: int = Field(..., ge=0)
    batch_count: int = Field(..., ge=0)
    pair_count: int = Field(..., ge=0)
    timepoint_count: int = Field(..., ge=0)
    plex_count: int = Field(..., ge=0)
    channel_count: int = Field(..., ge=0)
    species_count: int = Field(..., ge=0)
    tissue_or_cell_type_count: int = Field(..., ge=0)
    perturbation_count: int = Field(..., ge=0)
    instrument_count: int = Field(..., ge=0)


class ExperimentDesign(JsonModel):
    """Owned experiment-design object over samples, runs, and assay structure."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ExperimentalDesignEntry, ...] = Field(default_factory=tuple)
    samples: tuple[ExperimentDesignSample, ...] = Field(default_factory=tuple)
    runs: tuple[ExperimentDesignRun, ...] = Field(default_factory=tuple)
    conditions: tuple[str, ...] = Field(default_factory=tuple)
    batches: tuple[str, ...] = Field(default_factory=tuple)
    pair_ids: tuple[str, ...] = Field(default_factory=tuple)
    timepoints: tuple[str, ...] = Field(default_factory=tuple)
    species: tuple[str, ...] = Field(default_factory=tuple)
    tissue_or_cell_types: tuple[str, ...] = Field(default_factory=tuple)
    perturbations: tuple[str, ...] = Field(default_factory=tuple)
    instruments: tuple[str, ...] = Field(default_factory=tuple)
    plexes: tuple[ExperimentDesignPlex, ...] = Field(default_factory=tuple)
    summary: ExperimentDesignSummary
    note: str = Field(..., min_length=1)


def build_experiment_design(
    entries: tuple[ExperimentalDesignEntry, ...],
) -> ExperimentDesign:
    """Build one owned experiment-design object from normalized row entries."""

    runs = tuple(
        sorted(
            (
                ExperimentDesignRun(
                    run_id=entry.spectra_file,
                    sample_id=entry.sample_id,
                    technical_replicate_id=_technical_replicate_id(entry),
                    condition=entry.condition,
                    cohort=entry.cohort,
                    replicate=entry.replicate,
                    fraction=entry.fraction,
                    spectra_file=entry.spectra_file,
                    identifications_file=entry.identifications_file,
                    batch=entry.batch,
                    instrument=entry.instrument,
                    search_engine=entry.search_engine,
                    pair_id=entry.pair_id,
                    run_order=entry.run_order,
                    timepoint=_metadata_value(entry, "timepoint"),
                    species=_metadata_value(entry, "species"),
                    tissue_or_cell_type=_tissue_or_cell_type(entry),
                    perturbation=_metadata_value(entry, "perturbation"),
                    plex_id=entry.multiplex_group,
                    channel_id=entry.multiplex_channel,
                    sample_role=entry.sample_role,
                    metadata=dict(sorted(entry.metadata.items())),
                )
                for entry in entries
            ),
            key=lambda run: (
                run.run_order is None,
                run.run_order or 0,
                run.run_id,
            ),
        )
    )
    sample_records: list[ExperimentDesignSample] = []
    for sample_id in sorted({entry.sample_id for entry in entries}):
        sample_entries = tuple(entry for entry in entries if entry.sample_id == sample_id)
        primary = sample_entries[0]
        sample_records.append(
            ExperimentDesignSample(
                sample_id=sample_id,
                condition=primary.condition,
                cohort=primary.cohort,
                pair_id=primary.pair_id,
                timepoint=_metadata_value(primary, "timepoint"),
                species=_metadata_value(primary, "species"),
                tissue_or_cell_type=_tissue_or_cell_type(primary),
                perturbation=_metadata_value(primary, "perturbation"),
                run_ids=tuple(sorted({entry.spectra_file for entry in sample_entries})),
                technical_replicate_ids=tuple(
                    sorted({_technical_replicate_id(entry) for entry in sample_entries})
                ),
                batch_ids=_sorted_nonempty(entry.batch for entry in sample_entries),
                instrument_ids=_sorted_nonempty(entry.instrument for entry in sample_entries),
                plex_ids=_sorted_nonempty(entry.multiplex_group for entry in sample_entries),
                channel_ids=_sorted_nonempty(entry.multiplex_channel for entry in sample_entries),
                metadata=dict(sorted(primary.metadata.items())),
            )
        )
    plex_records: list[ExperimentDesignPlex] = []
    for plex_id in sorted({entry.multiplex_group for entry in entries if entry.multiplex_group}):
        plex_entries = tuple(entry for entry in entries if entry.multiplex_group == plex_id)
        channels = tuple(
            sorted(
                (
                    ExperimentDesignChannel(
                        plex_id=plex_id,
                        channel_id=entry.multiplex_channel or "",
                        sample_id=entry.sample_id,
                        run_id=entry.spectra_file,
                        sample_role=entry.sample_role,
                    )
                    for entry in plex_entries
                    if entry.multiplex_channel is not None
                ),
                key=lambda channel: (channel.channel_id, channel.sample_id, channel.run_id),
            )
        )
        plex_records.append(
            ExperimentDesignPlex(
                plex_id=plex_id,
                run_ids=tuple(sorted({entry.spectra_file for entry in plex_entries})),
                channels=channels,
                channel_count=len(channels),
            )
        )
    conditions = tuple(sorted({entry.condition for entry in entries if entry.condition}))
    batches = _sorted_nonempty(entry.batch for entry in entries)
    pair_ids = _sorted_nonempty(entry.pair_id for entry in entries)
    timepoints = _sorted_nonempty(_metadata_value(entry, "timepoint") for entry in entries)
    species = _sorted_nonempty(_metadata_value(entry, "species") for entry in entries)
    tissue_or_cell_types = _sorted_nonempty(_tissue_or_cell_type(entry) for entry in entries)
    perturbations = _sorted_nonempty(_metadata_value(entry, "perturbation") for entry in entries)
    instruments = _sorted_nonempty(entry.instrument for entry in entries)
    return ExperimentDesign(
        entries=entries,
        samples=tuple(sample_records),
        runs=runs,
        conditions=conditions,
        batches=batches,
        pair_ids=pair_ids,
        timepoints=timepoints,
        species=species,
        tissue_or_cell_types=tissue_or_cell_types,
        perturbations=perturbations,
        instruments=instruments,
        plexes=tuple(plex_records),
        summary=ExperimentDesignSummary(
            sample_count=len(sample_records),
            run_count=len(runs),
            technical_replicate_count=len(
                {
                    _technical_replicate_id(entry)
                    for entry in entries
                }
            ),
            condition_count=len(conditions),
            batch_count=len(batches),
            pair_count=len(pair_ids),
            timepoint_count=len(timepoints),
            plex_count=len(plex_records),
            channel_count=sum(len(plex.channels) for plex in plex_records),
            species_count=len(species),
            tissue_or_cell_type_count=len(tissue_or_cell_types),
            perturbation_count=len(perturbations),
            instrument_count=len(instruments),
        ),
        note=(
            "experiment design aggregates normalized design-table rows into owned sample, run, "
            "plex, channel, condition, batch, pair, run order, timepoint, species, tissue-or-cell-type, "
            "perturbation, and instrument views so workflows do not rebuild study structure ad hoc"
        ),
    )


def coerce_experiment_design(
    design: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
) -> ExperimentDesign:
    """Return one owned experiment-design object from rows or an existing object."""

    if isinstance(design, ExperimentDesign):
        return design
    return build_experiment_design(design)


def _technical_replicate_id(entry: ExperimentalDesignEntry) -> str:
    value = entry.technical_replicate_id
    if value not in (None, ""):
        return value
    return entry.spectra_file


def _sorted_nonempty(values) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value}))


def _metadata_value(entry: ExperimentalDesignEntry, key: str) -> str | None:
    value = entry.metadata.get(key)
    if value is None:
        return None
    text = value.strip()
    return text or None


def _tissue_or_cell_type(entry: ExperimentalDesignEntry) -> str | None:
    return (
        _metadata_value(entry, "tissue_or_cell_type")
        or _metadata_value(entry, "tissue")
        or _metadata_value(entry, "cell_type")
    )


__all__ = [
    "ExperimentDesign",
    "ExperimentDesignChannel",
    "ExperimentDesignPlex",
    "ExperimentDesignRun",
    "ExperimentDesignSample",
    "ExperimentDesignSummary",
    "build_experiment_design",
    "coerce_experiment_design",
]
