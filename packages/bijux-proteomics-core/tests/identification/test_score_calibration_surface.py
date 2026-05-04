# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.confidence import (
    build_empirical_score_calibration_report,
)


def _records() -> tuple[PsmRecord, ...]:
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
            score=90.0,
            q_value=0.01,
            protein_refs=("P22222",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan-003",
            peptide="DECOYPEP",
            canonical_peptide="DECOYPEP",
            charge=3,
            score=40.0,
            q_value=0.2,
            protein_refs=("DECOY_P33333",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
    )


def test_empirical_score_calibration_report_tracks_bins_and_top_fraction_behavior() -> (
    None
):
    report = build_empirical_score_calibration_report(
        _records(),
        score_orientation="higher_better",
        bin_count=5,
        top_fraction=0.34,
    )

    assert report.total_records == 3
    assert report.bin_count == 5
    assert len(report.bins) == 5
    assert report.top_fraction_target_share == 1.0
    assert report.top_fraction_decoy_share == 0.0
    assert "target-dominant" in report.advisory


def test_empirical_score_calibration_report_surfaces_decoy_warning() -> None:
    report = build_empirical_score_calibration_report(
        _records(),
        score_orientation="lower_better",
        bin_count=4,
        top_fraction=0.67,
    )

    assert report.top_fraction_decoy_share > 0.0
    assert "includes decoys" in report.advisory
