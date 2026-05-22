# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification.contracts import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.psm_target_decoy_fdr import (
    build_psm_target_decoy_fdr_report,
    render_psm_target_decoy_fdr_summary_tsv,
    render_psm_target_decoy_fdr_tsv,
)


def _higher_better_records() -> tuple[PsmRecord, ...]:
    return (
        PsmRecord(
            spectrum_id="scan=4001",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=100.0,
            protein_refs=("P12345",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=4002",
            peptide="DECOYPEP",
            canonical_peptide="DECOYPEP",
            charge=2,
            score=95.0,
            protein_refs=("DECOY_P99999",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
        PsmRecord(
            spectrum_id="scan=4003",
            peptide="PEPTIDER",
            canonical_peptide="PEPTIDER",
            charge=2,
            score=90.0,
            protein_refs=("P12345",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )


def test_psm_target_decoy_fdr_report_exposes_ranked_raw_and_monotonic_state() -> None:
    report = build_psm_target_decoy_fdr_report(
        _higher_better_records(),
        threshold=0.5,
        score_orientation="higher_better",
    )

    assert report.summary.total_psm_count == 3
    assert report.summary.target_psm_count == 2
    assert report.summary.decoy_psm_count == 1
    assert report.summary.accepted_psm_count == 3
    assert report.summary.q_values_monotonic is True
    assert report.entries[0].cumulative_targets == 1
    assert report.entries[0].cumulative_decoys == 0
    assert report.entries[0].raw_fdr == 0.0
    assert report.entries[1].raw_fdr == 1.0
    assert report.entries[1].q_value == 0.5
    assert report.entries[2].q_value == 0.5


def test_psm_target_decoy_fdr_report_honors_lower_better_and_tie_policy() -> None:
    tied_records = (
        PsmRecord(
            spectrum_id="scan-a",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=0.01,
            protein_refs=("P1",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan-b",
            peptide="DECOYPEP",
            canonical_peptide="DECOYPEP",
            charge=2,
            score=0.01,
            protein_refs=("DECOY_P2",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
        PsmRecord(
            spectrum_id="scan-c",
            peptide="PEPK",
            canonical_peptide="PEPK",
            charge=2,
            score=0.02,
            protein_refs=("P3",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )

    grouped = build_psm_target_decoy_fdr_report(
        tied_records,
        score_orientation="lower_better",
        tie_handling="score_group",
    )
    ordered = build_psm_target_decoy_fdr_report(
        tied_records,
        score_orientation="lower_better",
        tie_handling="stable_record_order",
    )

    assert grouped.entries[0].tie_group_size == 2
    assert grouped.entries[0].raw_fdr == grouped.entries[1].raw_fdr
    assert grouped.entries[0].q_value == grouped.entries[1].q_value
    assert ordered.entries[0].tie_group_size == 1
    assert ordered.entries[0].raw_fdr != ordered.entries[1].raw_fdr


def test_psm_target_decoy_fdr_renderers_surface_raw_fdr_and_policy() -> None:
    report = build_psm_target_decoy_fdr_report(
        _higher_better_records(),
        threshold=0.5,
    )

    entries_tsv = render_psm_target_decoy_fdr_tsv(report)
    summary_tsv = render_psm_target_decoy_fdr_summary_tsv(report)

    assert entries_tsv.startswith(
        "rank\ttie_group_rank\ttie_group_size\tspectrum_id\tcanonical_peptide"
    )
    assert "raw_fdr\tq_value\taccepted" in entries_tsv
    assert summary_tsv.startswith(
        "score_orientation\ttie_handling\tthreshold\ttotal_psm_count"
    )
    assert "higher_better\tscore_group\t0.5\t3\t2\t1\t3\t2\t1\ttrue\t" in summary_tsv
