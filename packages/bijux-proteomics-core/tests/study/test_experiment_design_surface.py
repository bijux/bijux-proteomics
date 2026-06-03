# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    ExperimentalDesignSampleRole,
)
from bijux_proteomics.study import build_experiment_design, coerce_experiment_design


def test_build_experiment_design_aggregates_samples_runs_plexes_and_metadata() -> None:
    entries = (
        ExperimentalDesignEntry(
            sample_id="S1",
            cohort="cohort-a",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="run-001",
            technical_replicate_id="tech-001",
            identifications_file="id-001.tsv",
            batch="B1",
            instrument="Exploris-1",
            search_engine="diann",
            pair_id="pair-1",
            run_order=2,
            metadata={
                "timepoint": "T0",
                "species": "human",
                "tissue_or_cell_type": "hepatocyte",
                "perturbation": "vehicle",
            },
        ),
        ExperimentalDesignEntry(
            sample_id="S1",
            cohort="cohort-a",
            condition="control",
            replicate=1,
            fraction=2,
            spectra_file="run-002",
            technical_replicate_id="tech-002",
            identifications_file="id-002.tsv",
            batch="B1",
            instrument="Exploris-1",
            search_engine="diann",
            pair_id="pair-1",
            run_order=1,
            metadata={
                "timepoint": "T0",
                "species": "human",
                "cell_type": "hepatocyte",
                "perturbation": "vehicle",
            },
        ),
        ExperimentalDesignEntry(
            sample_id="S2",
            cohort="cohort-a",
            condition="treated",
            replicate=1,
            fraction=1,
            spectra_file="run-003",
            technical_replicate_id="tech-003",
            identifications_file="id-003.tsv",
            batch="B2",
            instrument="Orbitrap-2",
            search_engine="diann",
            pair_id="pair-1",
            run_order=3,
            multiplex_group="plex-01",
            multiplex_channel="126",
            sample_role=ExperimentalDesignSampleRole.SAMPLE,
            metadata={
                "timepoint": "T24",
                "species": "human",
                "tissue": "hepatocyte",
                "perturbation": "drug-x",
            },
        ),
        ExperimentalDesignEntry(
            sample_id="bridge",
            cohort="cohort-a",
            condition="bridge",
            replicate=1,
            fraction=1,
            spectra_file="run-004",
            technical_replicate_id="tech-bridge",
            identifications_file="id-004.tsv",
            batch="B2",
            instrument="Orbitrap-2",
            search_engine="diann",
            run_order=4,
            multiplex_group="plex-01",
            multiplex_channel="131",
            sample_role=ExperimentalDesignSampleRole.QC_BRIDGE,
            metadata={
                "timepoint": "T24",
                "species": "human",
                "tissue": "hepatocyte",
                "perturbation": "bridge-pool",
            },
        ),
    )

    design = build_experiment_design(entries)

    assert design.summary.sample_count == 3
    assert design.summary.run_count == 4
    assert design.summary.technical_replicate_count == 4
    assert design.summary.condition_count == 3
    assert design.summary.batch_count == 2
    assert design.summary.pair_count == 1
    assert design.summary.timepoint_count == 2
    assert design.summary.plex_count == 1
    assert design.summary.channel_count == 2
    assert design.summary.species_count == 1
    assert design.summary.tissue_or_cell_type_count == 1
    assert design.summary.perturbation_count == 3
    assert design.summary.instrument_count == 2
    assert design.conditions == ("bridge", "control", "treated")
    assert design.timepoints == ("T0", "T24")
    assert design.species == ("human",)
    assert design.tissue_or_cell_types == ("hepatocyte",)
    sample = next(sample for sample in design.samples if sample.sample_id == "S1")
    assert sample.run_ids == ("run-001", "run-002")
    assert sample.technical_replicate_ids == ("tech-001", "tech-002")
    assert sample.batch_ids == ("B1",)
    assert sample.instrument_ids == ("Exploris-1",)
    assert tuple(run.run_id for run in design.runs) == (
        "run-002",
        "run-001",
        "run-003",
        "run-004",
    )
    run = next(run for run in design.runs if run.run_id == "run-001")
    assert run.technical_replicate_id == "tech-001"
    assert run.run_order == 2
    plex = design.plexes[0]
    assert plex.plex_id == "plex-01"
    assert plex.run_ids == ("run-003", "run-004")
    assert plex.channels[0].channel_id == "126"
    assert plex.channels[1].sample_role is ExperimentalDesignSampleRole.QC_BRIDGE


def test_coerce_experiment_design_preserves_existing_object() -> None:
    entries = (
        ExperimentalDesignEntry(
            sample_id="S1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="run-001",
        ),
    )
    design = build_experiment_design(entries)

    assert coerce_experiment_design(design) is design
    assert coerce_experiment_design(entries).summary.run_count == 1
