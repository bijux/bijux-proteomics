# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.dia_fragment_coelution import (
    DiaFragmentCoelutionFragmentEntry,
    DiaFragmentCoelutionReport,
    DiaFragmentCoelutionRunEntry,
)
from bijux_proteomics.io.fragment_ratio_stability import (
    build_targeted_fragment_ratio_stability_report,
    score_dia_fragment_ratio_stability,
)
from bijux_proteomics.targeted.result_import import build_skyline_result_import_report


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_build_targeted_fragment_ratio_stability_report_flags_unstable_transition_ratios() -> (
    None
):
    report = build_targeted_fragment_ratio_stability_report(
        build_skyline_result_import_report(
            _format_fixture("skyline_targeted_qc_results.tsv")
        )
    )

    assert report.summary.analyte_count == 2
    assert report.summary.run_count == 4
    assert report.summary.fragment_entry_count == 4
    assert report.summary.observation_entry_count == 14
    assert report.summary.unstable_fragment_count == 1
    assert report.summary.drift_flagged_observation_count == 2

    by_fragment = {
        (entry.analyte_id, entry.fragment_id): entry
        for entry in report.fragment_entries
    }
    unstable_entry = by_fragment[("PEPTIDEK/2", "y8")]
    stable_entry = by_fragment[("PEPTIDEK/2", "y7")]

    assert round(unstable_entry.expected_ratio, 6) == 0.236842
    assert round(unstable_entry.ratio_cv or 0.0, 6) == 0.396731
    assert unstable_entry.drift_flagged_run_count == 1
    assert unstable_entry.unstable_fragment is True
    assert unstable_entry.concern_codes == ("ratio_drift", "high_ratio_cv")
    assert stable_entry.unstable_fragment is False

    by_observation = {
        (entry.analyte_id, entry.run_id, entry.fragment_id): entry
        for entry in report.observation_entries
    }
    drifted_observation = by_observation[("PEPTIDEK/2", "treat_r1", "y8")]
    reference_observation = by_observation[("PEPTIDEK/2", "control_r2", "y8")]

    assert round(drifted_observation.observed_ratio, 6) == 0.105263
    assert round(drifted_observation.absolute_ratio_delta, 6) == 0.131579
    assert drifted_observation.drift_flag is True
    assert drifted_observation.unstable_fragment is True
    assert drifted_observation.concern_codes == ("ratio_drift", "high_ratio_cv")
    assert reference_observation.drift_flag is False


def test_score_dia_fragment_ratio_stability_compares_fragment_ratios_across_runs() -> (
    None
):
    report = score_dia_fragment_ratio_stability(
        DiaFragmentCoelutionReport(
            run_ids=("run_alpha", "run_beta"),
            run_entries=(
                DiaFragmentCoelutionRunEntry(
                    run_id="run_alpha",
                    precursor_id="prec_alpha",
                    peptide_ref="PEPA",
                    reference_fragment_id="alpha_y7",
                    fragment_count=2,
                    detected_fragment_count=2,
                    passing_fragment_count=2,
                    apex_spread_seconds=0.0,
                    mean_correlation=1.0,
                    coelution_score=1.0,
                    failed_fragment_ids=(),
                    concern_codes=(),
                ),
                DiaFragmentCoelutionRunEntry(
                    run_id="run_beta",
                    precursor_id="prec_alpha",
                    peptide_ref="PEPA",
                    reference_fragment_id="alpha_y7",
                    fragment_count=2,
                    detected_fragment_count=2,
                    passing_fragment_count=2,
                    apex_spread_seconds=0.0,
                    mean_correlation=1.0,
                    coelution_score=1.0,
                    failed_fragment_ids=(),
                    concern_codes=(),
                ),
            ),
            fragment_entries=(
                DiaFragmentCoelutionFragmentEntry(
                    run_id="run_alpha",
                    precursor_id="prec_alpha",
                    peptide_ref="PEPA",
                    target_id="alpha_y7",
                    fragment_id="alpha_y7",
                    reference_fragment_id="alpha_y7",
                    peak_id="alpha_y7_peak_001",
                    apex_time_seconds=30.0,
                    apex_intensity=100.0,
                    area=2000.0,
                    apex_shift_seconds=0.0,
                    correlation_to_reference=1.0,
                    passed=True,
                    failure_reason=None,
                    concern_codes=(),
                ),
                DiaFragmentCoelutionFragmentEntry(
                    run_id="run_alpha",
                    precursor_id="prec_alpha",
                    peptide_ref="PEPA",
                    target_id="alpha_y8",
                    fragment_id="alpha_y8",
                    reference_fragment_id="alpha_y7",
                    peak_id="alpha_y8_peak_001",
                    apex_time_seconds=30.0,
                    apex_intensity=90.0,
                    area=1000.0,
                    apex_shift_seconds=0.0,
                    correlation_to_reference=0.95,
                    passed=True,
                    failure_reason=None,
                    concern_codes=(),
                ),
                DiaFragmentCoelutionFragmentEntry(
                    run_id="run_beta",
                    precursor_id="prec_alpha",
                    peptide_ref="PEPA",
                    target_id="alpha_y7",
                    fragment_id="alpha_y7",
                    reference_fragment_id="alpha_y7",
                    peak_id="alpha_y7_peak_001",
                    apex_time_seconds=30.0,
                    apex_intensity=120.0,
                    area=2600.0,
                    apex_shift_seconds=0.0,
                    correlation_to_reference=1.0,
                    passed=True,
                    failure_reason=None,
                    concern_codes=(),
                ),
                DiaFragmentCoelutionFragmentEntry(
                    run_id="run_beta",
                    precursor_id="prec_alpha",
                    peptide_ref="PEPA",
                    target_id="alpha_y8",
                    fragment_id="alpha_y8",
                    reference_fragment_id="alpha_y7",
                    peak_id="alpha_y8_peak_001",
                    apex_time_seconds=30.0,
                    apex_intensity=40.0,
                    area=400.0,
                    apex_shift_seconds=0.0,
                    correlation_to_reference=0.96,
                    passed=True,
                    failure_reason=None,
                    concern_codes=(),
                ),
            ),
        ),
        absolute_ratio_delta_threshold=0.08,
        ratio_cv_threshold=0.25,
    )

    assert report.summary.analyte_count == 1
    assert report.summary.run_count == 2
    assert report.summary.fragment_entry_count == 2
    assert report.summary.observation_entry_count == 4
    assert report.summary.unstable_fragment_count == 1
    assert report.summary.drift_flagged_observation_count == 4

    by_fragment = {
        (entry.analyte_id, entry.fragment_id): entry
        for entry in report.fragment_entries
    }
    stable_entry = by_fragment[("prec_alpha", "alpha_y7")]
    shifted_entry = by_fragment[("prec_alpha", "alpha_y8")]
    assert stable_entry.unstable_fragment is False
    assert round(shifted_entry.expected_ratio, 6) == 0.233333
    assert round(shifted_entry.ratio_cv or 0.0, 6) == 0.606092
    assert shifted_entry.drift_flagged_run_count == 2
    assert shifted_entry.unstable_fragment is True
    assert shifted_entry.stability_score < 0.1

    by_observation = {
        (entry.run_id, entry.fragment_id): entry for entry in report.observation_entries
    }
    drifted_entry = by_observation[("run_beta", "alpha_y8")]
    assert round(drifted_entry.observed_ratio, 6) == 0.133333
    assert round(drifted_entry.absolute_ratio_delta, 6) == 0.1
    assert drifted_entry.drift_flag is True
    assert drifted_entry.unstable_fragment is True
