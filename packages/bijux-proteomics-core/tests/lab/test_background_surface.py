# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain.records import (
    MissingValueState,
    QuantEntityKind,
    QuantMatrix,
    QuantMeasureKind,
)
from bijux_proteomics.lab import (
    compare_samples_to_blanks,
    render_background_comparison_tsv,
)


def test_compare_samples_to_blanks_flags_blank_dominated_entities() -> None:
    matrix = QuantMatrix(
        matrix_id="background_matrix",
        entity_kind=QuantEntityKind.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        entity_ids=("P_blank_heavy", "P_biological"),
        sample_ids=("blank_a", "blank_b", "sample_1", "sample_2"),
        values=(
            (1000.0, 1200.0, 1500.0, 4800.0),
            (20.0, 15.0, 2200.0, 2600.0),
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
        ),
        support_counts=((1, 1, 1, 1), (1, 1, 1, 1)),
    )

    rows = compare_samples_to_blanks(matrix, blank_runs=("blank_a", "blank_b"))
    lookup = {(row.entity_id, row.sample_id): row for row in rows}

    downgraded = lookup[("P_blank_heavy", "sample_1")]
    assert downgraded.blank_intensity == 1200.0
    assert downgraded.sample_intensity == 1500.0
    assert downgraded.background_ratio == 0.8
    assert downgraded.background_flag is True

    supported = lookup[("P_blank_heavy", "sample_2")]
    assert supported.background_flag is False

    biological = lookup[("P_biological", "sample_1")]
    assert biological.blank_intensity == 20.0
    assert biological.background_ratio == 0.0091
    assert biological.background_flag is False


def test_compare_samples_to_blanks_renders_tsv_and_handles_missing_signal() -> None:
    matrix = QuantMatrix(
        matrix_id="background_missing_matrix",
        entity_kind=QuantEntityKind.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        entity_ids=("P_missing_sample",),
        sample_ids=("blank_a", "sample_1"),
        values=((700.0, None),),
        missing_value_states=(
            (
                MissingValueState.OBSERVED,
                MissingValueState.NOT_OBSERVED,
            ),
        ),
        support_counts=((1, 0),),
    )

    rows = compare_samples_to_blanks(matrix, blank_runs=("blank_a",))
    rendered = render_background_comparison_tsv(rows)

    assert rows[0].sample_intensity == 0.0
    assert rows[0].background_flag is True
    assert rendered.startswith(
        "entity_id\tsample_id\tblank_intensity\tsample_intensity\tbackground_ratio\tbackground_flag\n"
    )
    assert "true" in rendered
