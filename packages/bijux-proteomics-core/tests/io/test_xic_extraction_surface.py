# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.xic_extraction import (
    XicToleranceUnit,
    extract_mzml_xic_traces,
    parse_xic_target_table,
    render_xic_traces_tsv,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_parse_xic_target_table_accepts_precursor_targets_with_rt_windows() -> None:
    report = parse_xic_target_table(_format_fixture("xic_targets.tsv"))

    assert report.rejected_rows == ()
    assert len(report.accepted_entries) == 3
    assert report.accepted_entries[0].target_id == "target_alpha"
    assert report.accepted_entries[0].precursor_mz == 500.0
    assert report.accepted_entries[0].rt_start_seconds == 5.0
    assert report.accepted_entries[0].rt_end_seconds == 25.0
    assert report.accepted_entries[0].expected_charge == 2
    assert report.accepted_entries[1].metadata["panel_group"] == "beta"


def test_parse_xic_target_table_rejects_duplicate_ids_and_invalid_rt_windows(
    tmp_path: Path,
) -> None:
    table_path = tmp_path / "xic_targets.invalid.tsv"
    table_path.write_text(
        "\n".join(
            (
                "target_id\tprecursor_mz\trt_start_seconds\trt_end_seconds",
                "target_a\t500.0\t20\t10",
                "target_b\t700.0\t\t",
                "target_b\t710.0\t\t",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_xic_target_table(table_path)

    assert len(report.accepted_entries) == 1
    assert report.accepted_entries[0].target_id == "target_b"
    assert len(report.rejected_rows) == 2
    assert report.rejected_rows[0].reason == "rt_start_seconds cannot exceed rt_end_seconds"
    assert report.rejected_rows[1].reason == "duplicate target_id 'target_b'"


def test_extract_mzml_xic_traces_uses_ms1_spectra_and_rt_windows() -> None:
    report = extract_mzml_xic_traces(
        _format_fixture("xic_review.mzml"),
        _format_fixture("xic_targets.tsv"),
        tolerance_ppm=10.0,
    )

    assert report.tolerance_unit is XicToleranceUnit.PPM
    assert report.tolerance_value == 10.0
    assert report.total_spectra == 4
    assert report.eligible_spectra == 3
    assert len(report.trace_points) == 8

    alpha_rows = [point for point in report.trace_points if point.target_id == "target_alpha"]
    beta_rows = [point for point in report.trace_points if point.target_id == "target_beta"]
    gamma_rows = [point for point in report.trace_points if point.target_id == "target_gamma"]

    assert [point.time_seconds for point in alpha_rows] == [10.0, 20.0]
    assert [point.intensity for point in alpha_rows] == [1000.0, 1500.0]
    assert [point.time_seconds for point in beta_rows] == [10.0, 20.0, 30.0]
    assert [point.intensity for point in beta_rows] == [2000.0, 2500.0, 3000.0]
    assert all(point.intensity == 0.0 for point in gamma_rows)
    assert all(point.matched_peak_count == 0 for point in gamma_rows)


def test_extract_mzml_xic_traces_supports_dalton_windows() -> None:
    report = extract_mzml_xic_traces(
        _format_fixture("xic_review.mzml"),
        _format_fixture("xic_targets.tsv"),
        tolerance_da=0.002,
    )

    beta_rows = [point for point in report.trace_points if point.target_id == "target_beta"]

    assert report.tolerance_unit is XicToleranceUnit.DALTON
    assert beta_rows[0].intensity == 2000.0
    assert beta_rows[1].intensity == 0.0
    assert beta_rows[2].intensity == 3000.0


def test_render_xic_traces_tsv_emits_trace_rows_with_mz_windows() -> None:
    report = extract_mzml_xic_traces(
        _format_fixture("xic_review.mzml"),
        _format_fixture("xic_targets.tsv"),
        tolerance_ppm=10.0,
    )

    rendered = render_xic_traces_tsv(report)
    rows = rendered.strip().splitlines()

    assert rows[0] == (
        "target_id\tspectrum_id\ttime_seconds\tprecursor_mz\tmz_window_lower\t"
        "mz_window_upper\tintensity\tmatched_peak_count"
    )
    assert (
        "target_alpha\tscan=7000\t10\t500.000000\t499.995000\t500.005000\t1000\t1"
        in rows
    )
    assert (
        "target_gamma\tscan=7002\t30\t650.000000\t649.993500\t650.006500\t0\t0"
        in rows
    )
