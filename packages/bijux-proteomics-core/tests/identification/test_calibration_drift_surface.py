# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import (
    CalibrationReleaseAlertSeverity,
    PsmRecord,
    TargetDecoyLabel,
    build_calibration_drift_report,
    build_calibration_release_gate_report,
)


def _previous_records() -> tuple[PsmRecord, ...]:
    return (
        PsmRecord(
            spectrum_id="scan-001",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=120.0,
            q_value=0.001,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan-002",
            peptide="PEPTIDER",
            canonical_peptide="PEPTIDER",
            charge=2,
            score=112.0,
            q_value=0.005,
            protein_refs=("P22222",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan-003",
            peptide="PEPTIDEX",
            canonical_peptide="PEPTIDEX",
            charge=3,
            score=85.0,
            q_value=0.02,
            protein_refs=("P33333",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan-004",
            peptide="DECOYPEP",
            canonical_peptide="DECOYPEP",
            charge=3,
            score=25.0,
            q_value=0.2,
            protein_refs=("DECOY_P44444",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
    )


def _current_records() -> tuple[PsmRecord, ...]:
    return (
        PsmRecord(
            spectrum_id="scan-101",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=120.0,
            q_value=0.001,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan-102",
            peptide="DECOYTOP",
            canonical_peptide="DECOYTOP",
            charge=2,
            score=118.0,
            q_value=0.005,
            protein_refs=("DECOY_P55555",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
        PsmRecord(
            spectrum_id="scan-103",
            peptide="PEPTIDEX",
            canonical_peptide="PEPTIDEX",
            charge=3,
            score=85.0,
            q_value=0.02,
            protein_refs=("P33333",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan-104",
            peptide="DECOYPEP",
            canonical_peptide="DECOYPEP",
            charge=3,
            score=25.0,
            q_value=0.2,
            protein_refs=("DECOY_P44444",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
    )


def test_calibration_drift_report_flags_stable_counts_with_worse_decoy_pressure() -> (
    None
):
    report = build_calibration_drift_report(
        _previous_records(),
        _current_records(),
        score_orientation="higher_better",
        bin_count=4,
        top_fraction=0.5,
        accepted_q_value_threshold=0.01,
    )

    assert report.acceptance.accepted_count_stable is True
    assert report.acceptance.previous_accepted_count == 2
    assert report.acceptance.current_accepted_count == 2
    assert report.acceptance.accepted_decoy_fraction_delta > 0.0
    assert report.top_fraction_decoy_delta > 0.0
    assert report.calibration_regression_detected is True
    assert any(
        "accepted record counts stayed stable" in reason
        for reason in report.regression_reasons
    )


def test_calibration_drift_report_stays_quiet_when_snapshots_match() -> None:
    report = build_calibration_drift_report(
        _previous_records(),
        _previous_records(),
        score_orientation="higher_better",
        bin_count=4,
        top_fraction=0.5,
        accepted_q_value_threshold=0.01,
    )

    assert report.distribution_shift_score == 0.0
    assert report.acceptance.accepted_decoy_fraction_delta == 0.0
    assert report.top_fraction_decoy_delta == 0.0
    assert report.calibration_regression_detected is False


def test_calibration_release_gate_blocks_flagship_regressions() -> None:
    drift = build_calibration_drift_report(
        _previous_records(),
        _current_records(),
        score_orientation="higher_better",
        bin_count=4,
        top_fraction=0.5,
        accepted_q_value_threshold=0.01,
    )

    gate = build_calibration_release_gate_report((("dda-flagship", drift),))

    assert gate.release_blocked is True
    assert len(gate.alerts) == 1
    assert gate.alerts[0].severity is CalibrationReleaseAlertSeverity.BLOCKING
