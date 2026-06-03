# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.dia_fragment_coelution import (
    extract_mzml_dia_fragment_trace_coelution,
    render_dia_fragment_coelution_fragments_tsv,
    render_dia_fragment_coelution_runs_tsv,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_extract_mzml_dia_fragment_trace_coelution_flags_shifted_and_missing_fragments() -> (
    None
):
    report = extract_mzml_dia_fragment_trace_coelution(
        (_format_fixture("dia_fragment_coelution.mzml"),),
        _format_fixture("dia_fragment_targets.tsv"),
        tolerance_ppm=10.0,
    )

    by_precursor = {entry.precursor_id: entry for entry in report.run_entries}
    strong_entry = by_precursor["prec_alpha"]
    shifted_entry = by_precursor["prec_beta"]

    assert report.run_ids == ("dia_fragment_coelution",)
    assert strong_entry.reference_fragment_id == "alpha_y7"
    assert strong_entry.passing_fragment_count == 3
    assert strong_entry.apex_spread_seconds == 0.0
    assert strong_entry.coelution_score == 1.0
    assert shifted_entry.reference_fragment_id == "beta_y7"
    assert shifted_entry.detected_fragment_count == 2
    assert shifted_entry.passing_fragment_count == 1
    assert shifted_entry.apex_spread_seconds == 10.0
    assert shifted_entry.failed_fragment_ids == ("beta_b4", "beta_y8")
    assert shifted_entry.coelution_score < 0.5
    assert "insufficient_passing_fragments" in shifted_entry.concern_codes
    assert "missing_peak" in shifted_entry.concern_codes
    assert "shifted_apex" in shifted_entry.concern_codes


def test_extract_mzml_dia_fragment_trace_coelution_preserves_fragment_ledgers() -> None:
    report = extract_mzml_dia_fragment_trace_coelution(
        (_format_fixture("dia_fragment_coelution.mzml"),),
        _format_fixture("dia_fragment_targets.tsv"),
        tolerance_ppm=10.0,
    )

    by_fragment = {
        (entry.precursor_id, entry.fragment_id): entry
        for entry in report.fragment_entries
    }
    shifted_fragment = by_fragment[("prec_beta", "beta_y8")]
    missing_fragment = by_fragment[("prec_beta", "beta_b4")]

    assert shifted_fragment.apex_shift_seconds == 10.0
    assert shifted_fragment.correlation_to_reference < 0.8
    assert shifted_fragment.failure_reason == "shifted_apex"
    assert shifted_fragment.passed is False
    assert missing_fragment.apex_time_seconds is None
    assert missing_fragment.correlation_to_reference is None
    assert missing_fragment.failure_reason == "missing_peak"
    assert missing_fragment.passed is False


def test_extract_mzml_dia_fragment_trace_coelution_renders_tsv_outputs() -> None:
    report = extract_mzml_dia_fragment_trace_coelution(
        (_format_fixture("dia_fragment_coelution.mzml"),),
        _format_fixture("dia_fragment_targets.tsv"),
        tolerance_ppm=10.0,
    )

    run_tsv = render_dia_fragment_coelution_runs_tsv(report)
    fragment_tsv = render_dia_fragment_coelution_fragments_tsv(report)

    assert run_tsv.splitlines()[0] == (
        "run_id\tprecursor_id\tpeptide_ref\treference_fragment_id\tfragment_count\t"
        "detected_fragment_count\tpassing_fragment_count\tapex_spread_seconds\t"
        "mean_correlation\tcoelution_score\tfailed_fragment_ids\tconcern_codes"
    )
    assert (
        "dia_fragment_coelution\tprec_beta\tPEPB\tbeta_y7\t3\t2\t1\t10.0000\t0.5578\t0.2971\tbeta_b4|beta_y8"
        in run_tsv
    )
    assert fragment_tsv.splitlines()[0] == (
        "run_id\tprecursor_id\tpeptide_ref\ttarget_id\tfragment_id\treference_fragment_id\t"
        "peak_id\tapex_time_seconds\tapex_intensity\tarea\tapex_shift_seconds\t"
        "correlation_to_reference\tpassed\tfailure_reason\tconcern_codes"
    )
    assert (
        "dia_fragment_coelution\tprec_beta\tPEPB\tbeta_y8\tbeta_y8\tbeta_y7\tbeta_y8_peak_001\t40.0000\t90.0000"
        in fragment_tsv
    )
