# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain.records import (
    MissingValueState,
    QuantEntityKind,
    QuantMatrix,
    QuantMeasureKind,
)
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.lab import detect_sample_swaps, render_sample_swap_suspicion_tsv


def _swapped_matrix() -> QuantMatrix:
    return QuantMatrix(
        matrix_id="sample_identity_matrix",
        entity_kind=QuantEntityKind.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        entity_ids=("P001", "P002", "P003", "P004"),
        sample_ids=("control_1", "control_2", "case_1", "case_2"),
        values=(
            (100.0, 102.0, 420.0, 98.0),
            (120.0, 121.0, 395.0, 119.0),
            (140.0, 141.0, 370.0, 139.0),
            (160.0, 159.0, 345.0, 161.0),
        ),
        missing_value_states=(
            (
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
            ),
            (
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
            ),
            (
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
            ),
            (
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
            ),
        ),
        support_counts=((1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1)),
    )


def _metadata_with_swapped_label() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="control_1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="control_1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="control_2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="control_2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case_1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case_1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case_2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case_2.mzml",
        ),
    )


def test_detect_sample_swaps_flags_simulated_swapped_labels() -> None:
    rows = detect_sample_swaps(_swapped_matrix(), _metadata_with_swapped_label())
    lookup = {row.sample_id: row for row in rows}

    swapped = lookup["case_2"]
    assert swapped.expected_group == "case"
    assert swapped.nearest_neighbor_group == "control"
    assert swapped.swap_suspicion_score > 0.9

    supported = lookup["control_2"]
    assert supported.nearest_neighbor_group == "control"
    assert supported.swap_suspicion_score < 0.2


def test_detect_sample_swaps_reports_without_mutating_metadata() -> None:
    metadata = _metadata_with_swapped_label()
    before = tuple(entry.model_dump(mode="python") for entry in metadata)

    rows = detect_sample_swaps(_swapped_matrix(), metadata)
    rendered = render_sample_swap_suspicion_tsv(rows)

    after = tuple(entry.model_dump(mode="python") for entry in metadata)
    assert before == after
    assert rendered.startswith(
        "sample_id\texpected_group\tnearest_neighbor_sample\tnearest_neighbor_group\tswap_suspicion_score\n"
    )
    assert "case_2\tcase\t" in rendered
    assert "\tcontrol\t1.0000" in rendered
