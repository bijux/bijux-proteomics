# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.study.lc_drift import (
    LcDriftDimension,
    LcDriftDirection,
    LcDriftRunQcEntry,
    detect_lc_drift,
    render_lc_drift_tsv,
)


def test_detect_lc_drift_flags_gradual_rt_and_intensity_drift_without_promoting_other_dimensions() -> (
    None
):
    rows = detect_lc_drift(
        (
            LcDriftRunQcEntry(
                run_id="run-01",
                run_order=1,
                median_rt=900.0,
                tic=1_000_000.0,
                ms2_count=5000,
                id_count=1200,
                median_peak_width=12.0,
            ),
            LcDriftRunQcEntry(
                run_id="run-02",
                run_order=2,
                median_rt=920.0,
                tic=950_000.0,
                ms2_count=4975,
                id_count=1180,
                median_peak_width=12.0,
            ),
            LcDriftRunQcEntry(
                run_id="run-03",
                run_order=3,
                median_rt=940.0,
                tic=900_000.0,
                ms2_count=4950,
                id_count=1160,
                median_peak_width=12.0,
            ),
            LcDriftRunQcEntry(
                run_id="run-04",
                run_order=4,
                median_rt=960.0,
                tic=850_000.0,
                ms2_count=4925,
                id_count=900,
                median_peak_width=12.0,
            ),
            LcDriftRunQcEntry(
                run_id="run-05",
                run_order=5,
                median_rt=980.0,
                tic=800_000.0,
                ms2_count=4900,
                id_count=1140,
                median_peak_width=12.0,
            ),
            LcDriftRunQcEntry(
                run_id="run-06",
                run_order=6,
                median_rt=1000.0,
                tic=750_000.0,
                ms2_count=4875,
                id_count=1120,
                median_peak_width=12.0,
            ),
        )
    )
    rendered = render_lc_drift_tsv(rows)

    assert rows
    assert {row.affected_qc_dimension for row in rows} == {
        LcDriftDimension.MEDIAN_RT,
        LcDriftDimension.TIC,
    }
    rt_rows = [
        row for row in rows if row.affected_qc_dimension is LcDriftDimension.MEDIAN_RT
    ]
    tic_rows = [row for row in rows if row.affected_qc_dimension is LcDriftDimension.TIC]

    assert rt_rows[0].run_id == "run-03"
    assert rt_rows[-1].run_id == "run-06"
    assert all(row.drift_direction is LcDriftDirection.INCREASING for row in rt_rows)
    assert tic_rows[0].run_id == "run-03"
    assert tic_rows[-1].run_id == "run-06"
    assert all(row.drift_direction is LcDriftDirection.DECREASING for row in tic_rows)
    assert rt_rows[-1].drift_metric > rt_rows[0].drift_metric
    assert tic_rows[-1].drift_metric > tic_rows[0].drift_metric
    assert "run_id\tdrift_metric\tdrift_direction\tdrift_severity\taffected_qc_dimension" in rendered
    assert "run-06" in rendered
    assert "median_rt" in rendered
    assert "tic" in rendered


def test_detect_lc_drift_rejects_single_run_failure_patterns() -> None:
    rows = detect_lc_drift(
        (
            LcDriftRunQcEntry(
                run_id="run-01",
                run_order=1,
                median_rt=900.0,
                tic=1_000_000.0,
                ms2_count=5000,
                id_count=1200,
                median_peak_width=12.0,
            ),
            LcDriftRunQcEntry(
                run_id="run-02",
                run_order=2,
                median_rt=901.0,
                tic=995_000.0,
                ms2_count=4980,
                id_count=1190,
                median_peak_width=12.1,
            ),
            LcDriftRunQcEntry(
                run_id="run-03",
                run_order=3,
                median_rt=900.0,
                tic=1_005_000.0,
                ms2_count=5010,
                id_count=1210,
                median_peak_width=12.0,
            ),
            LcDriftRunQcEntry(
                run_id="run-04",
                run_order=4,
                median_rt=1200.0,
                tic=200_000.0,
                ms2_count=1800,
                id_count=250,
                median_peak_width=22.0,
            ),
            LcDriftRunQcEntry(
                run_id="run-05",
                run_order=5,
                median_rt=902.0,
                tic=998_000.0,
                ms2_count=4995,
                id_count=1195,
                median_peak_width=12.1,
            ),
            LcDriftRunQcEntry(
                run_id="run-06",
                run_order=6,
                median_rt=901.0,
                tic=1_002_000.0,
                ms2_count=5005,
                id_count=1205,
                median_peak_width=12.0,
            ),
        )
    )

    assert rows == ()
