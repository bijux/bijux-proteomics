# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import (
    FdrStressScenarioKind,
    FdrStressTrustState,
    PsmRecord,
    TargetDecoyLabel,
    build_empirical_score_calibration_report,
    build_entrapment_evaluation_report,
    build_fdr_stress_case_report,
)


def _entrapment_records() -> tuple[PsmRecord, ...]:
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
            peptide="ENTRAPPEP",
            canonical_peptide="ENTRAPPEP",
            charge=2,
            score=118.0,
            q_value=0.002,
            protein_refs=("ENTRAPMENT_P99999",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan-003",
            peptide="DECOYPEP",
            canonical_peptide="DECOYPEP",
            charge=3,
            score=20.0,
            q_value=0.2,
            protein_refs=("DECOY_P33333",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
    )


def test_empirical_score_calibration_report_adds_quantitative_uncertainty_bounds() -> (
    None
):
    report = build_empirical_score_calibration_report(
        _entrapment_records(),
        score_orientation="higher_better",
        bin_count=4,
        top_fraction=0.67,
    )

    assert report.top_fraction_decoy_interval_low >= 0.0
    assert report.top_fraction_decoy_interval_high <= 1.0
    assert report.top_fraction_decoy_interval_width >= 0.0
    assert all(
        entry.decoy_fraction_interval_low <= entry.decoy_fraction_interval_high
        for entry in report.bins
    )


def test_entrapment_evaluation_report_counts_accepted_entrapment_hits() -> None:
    report = build_entrapment_evaluation_report(
        _entrapment_records(),
        entrapment_protein_refs=("ENTRAPMENT_P99999",),
        accepted_q_value_threshold=0.01,
    )

    assert report.accepted_record_count == 2
    assert report.accepted_entrapment_count == 1
    assert report.accepted_entrapment_fraction > 0.0


def test_fdr_stress_case_report_refuses_no_decoy_and_flags_low_decoy_fragility() -> (
    None
):
    no_decoy = _entrapment_records()[:2]
    low_decoy = _entrapment_records()

    no_decoy_report = build_fdr_stress_case_report(
        no_decoy,
        scenario_kind=FdrStressScenarioKind.NO_DECOY,
        accepted_q_value_threshold=0.01,
    )
    low_decoy_report = build_fdr_stress_case_report(
        low_decoy,
        scenario_kind=FdrStressScenarioKind.LOW_DECOY,
        accepted_q_value_threshold=0.01,
        low_decoy_cutoff=2,
    )

    assert no_decoy_report.trust_state is FdrStressTrustState.REFUSED
    assert low_decoy_report.trust_state is FdrStressTrustState.FRAGILE
