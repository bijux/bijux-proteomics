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
    build_internal_standard_sample_qc,
    render_internal_standard_tracking_tsv,
    track_internal_standards,
)


def _standards_matrix() -> QuantMatrix:
    return QuantMatrix(
        matrix_id="internal_standard_matrix",
        entity_kind=QuantEntityKind.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        entity_ids=("STD_A", "STD_B", "P001"),
        sample_ids=("sample_a", "sample_b", "sample_c", "sample_d"),
        values=(
            (1000.0, 980.0, 620.0, None),
            (500.0, 510.0, 505.0, None),
            (2200.0, 2250.0, 2280.0, 2270.0),
        ),
        missing_value_states=(
            (
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.NOT_OBSERVED,
            ),
            (
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.NOT_OBSERVED,
            ),
            (
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
                MissingValueState.OBSERVED,
            ),
        ),
        support_counts=((1, 1, 1, 0), (1, 1, 1, 0), (1, 1, 1, 1)),
    )


def test_track_internal_standards_flags_drift_and_missing_rows() -> None:
    rows = track_internal_standards(_standards_matrix(), ("STD_A", "STD_B"))
    lookup = {(row.standard_id, row.sample_id): row for row in rows}

    drifted = lookup[("STD_A", "sample_c")]
    assert drifted.intensity == 620.0
    assert drifted.cv > 0.2
    assert drifted.missing is False
    assert drifted.drift_flag is True

    missing = lookup[("STD_B", "sample_d")]
    assert missing.intensity == 0.0
    assert missing.missing is True
    assert missing.drift_flag is True

    stable = lookup[("STD_B", "sample_b")]
    assert stable.cv < 0.02
    assert stable.drift_flag is False


def test_internal_standard_tracking_renders_tsv_and_builds_sample_qc() -> None:
    rows = track_internal_standards(_standards_matrix(), ("STD_A", "STD_B"))
    qc_rows = {
        row.sample_id: row for row in build_internal_standard_sample_qc(rows)
    }
    rendered = render_internal_standard_tracking_tsv(rows)

    assert qc_rows["sample_a"].qc_status.value == "pass"
    assert qc_rows["sample_c"].qc_status.value == "caution"
    assert "internal_standard_drift" in qc_rows["sample_c"].status_reason_codes
    assert qc_rows["sample_d"].qc_status.value == "fail"
    assert "internal_standard_missing" in qc_rows["sample_d"].status_reason_codes
    assert rendered.startswith("standard_id\tsample_id\tintensity\tcv\tmissing\tdrift_flag\n")
    assert "true" in rendered
