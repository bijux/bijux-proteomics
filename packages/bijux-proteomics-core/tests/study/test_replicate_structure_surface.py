# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.study import (
    build_replicate_structure_report,
    count_effective_statistical_units_by_condition,
    render_replicate_structure_tsv,
)


def test_replicate_structure_owner_distinguishes_injection_fraction_channel_and_repeated_measure_structure() -> (
    None
):
    report = build_replicate_structure_report(
        (
            ExperimentalDesignEntry(
                sample_id="subject-1_t0",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="subject-1_t0_run-1.mzml",
                technical_replicate_id="tech-1",
                pair_id="subject-1",
                metadata={"timepoint": "T0"},
            ),
            ExperimentalDesignEntry(
                sample_id="subject-1_t0",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="subject-1_t0_run-2.mzml",
                technical_replicate_id="tech-1",
                pair_id="subject-1",
                metadata={"timepoint": "T0"},
            ),
            ExperimentalDesignEntry(
                sample_id="subject-1_t1",
                condition="control",
                replicate=2,
                fraction=1,
                spectra_file="subject-1_t1_run-1.mzml",
                technical_replicate_id="tech-2",
                pair_id="subject-1",
                metadata={"timepoint": "T1"},
            ),
            ExperimentalDesignEntry(
                sample_id="treated-fractionated",
                condition="treatment",
                replicate=1,
                fraction=1,
                spectra_file="treated_frac1.mzml",
                technical_replicate_id="tech-3",
                multiplex_group="plex-a",
                multiplex_channel="126",
            ),
            ExperimentalDesignEntry(
                sample_id="treated-fractionated",
                condition="treatment",
                replicate=1,
                fraction=2,
                spectra_file="treated_frac2.mzml",
                technical_replicate_id="tech-4",
                multiplex_group="plex-a",
                multiplex_channel="126",
            ),
            ExperimentalDesignEntry(
                sample_id="treated-channel",
                condition="treatment",
                replicate=2,
                fraction=1,
                spectra_file="treated_channel.mzml",
                technical_replicate_id="tech-5",
                multiplex_group="plex-a",
                multiplex_channel="127N",
            ),
        ),
        minimum_statistical_units_per_condition=2,
    )

    control = next(
        entry for entry in report.condition_entries if entry.condition == "control"
    )
    treatment = next(
        entry for entry in report.condition_entries if entry.condition == "treatment"
    )
    repeated_measure = next(
        entry
        for entry in report.sample_entries
        if entry.biological_sample_id == "subject-1_t0"
    )

    assert control.biological_replicate_count == 2
    assert control.effective_statistical_unit_count == 1
    assert control.technical_replicate_count == 2
    assert control.injection_replicate_count == 1
    assert control.repeated_measure_subject_count == 1
    assert control.underpowered_for_statistics is True
    assert treatment.biological_replicate_count == 2
    assert treatment.effective_statistical_unit_count == 2
    assert treatment.fractionated_sample_count == 1
    assert treatment.multiplex_channel_count == 2
    assert repeated_measure.repeated_measure_subject_id == "subject-1"
    assert repeated_measure.effective_statistical_unit_id == "subject-1"
    assert repeated_measure.injection_replicate_count == 1
    assert "repeated_measure_subject_count" in render_replicate_structure_tsv(report)


def test_replicate_structure_owner_returns_condition_statistical_unit_counts() -> None:
    counts = count_effective_statistical_units_by_condition(
        (
            ExperimentalDesignEntry(
                sample_id="subject-1_t0",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="subject-1_t0_run-1.mzml",
                pair_id="subject-1",
                metadata={"timepoint": "T0"},
            ),
            ExperimentalDesignEntry(
                sample_id="subject-1_t1",
                condition="control",
                replicate=2,
                fraction=1,
                spectra_file="subject-1_t1_run-1.mzml",
                pair_id="subject-1",
                metadata={"timepoint": "T1"},
            ),
            ExperimentalDesignEntry(
                sample_id="subject-2_t0",
                condition="control",
                replicate=3,
                fraction=1,
                spectra_file="subject-2_t0_run-1.mzml",
                pair_id="subject-2",
                metadata={"timepoint": "T0"},
            ),
            ExperimentalDesignEntry(
                sample_id="subject-2_t1",
                condition="control",
                replicate=4,
                fraction=1,
                spectra_file="subject-2_t1_run-1.mzml",
                pair_id="subject-2",
                metadata={"timepoint": "T1"},
            ),
            ExperimentalDesignEntry(
                sample_id="treated-1",
                condition="treatment",
                replicate=1,
                fraction=1,
                spectra_file="treated-1_run-1.mzml",
            ),
            ExperimentalDesignEntry(
                sample_id="treated-2",
                condition="treatment",
                replicate=2,
                fraction=1,
                spectra_file="treated-2_run-1.mzml",
            ),
        )
    )

    assert counts == {"control": 2, "treatment": 2}
