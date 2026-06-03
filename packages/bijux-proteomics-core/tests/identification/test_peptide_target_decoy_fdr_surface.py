# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.peptide_target_decoy_fdr import (
    build_peptide_target_decoy_fdr_report,
    collapse_peptide_fdr_evidence,
    render_peptide_target_decoy_fdr_summary_tsv,
    render_peptide_target_decoy_fdr_tsv,
)


def _higher_better_records() -> tuple[PsmRecord, ...]:
    return (
        PsmRecord(
            spectrum_id="scan=1001",
            peptide="PEPA",
            canonical_peptide="PEPA",
            charge=2,
            score=100.0,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=1002",
            peptide="PEPA",
            canonical_peptide="PEPA",
            charge=3,
            score=95.0,
            protein_refs=("P11111", "P22222"),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=1003",
            peptide="DECOYPEP",
            canonical_peptide="DECOYPEP",
            charge=2,
            score=90.0,
            protein_refs=("DECOY_P99999",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
        PsmRecord(
            spectrum_id="scan=1004",
            peptide="PEPB",
            canonical_peptide="PEPB",
            charge=2,
            score=80.0,
            protein_refs=("P33333",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )


def test_collapse_peptide_fdr_evidence_preserves_support_without_duplicate_entities() -> (
    None
):
    evidence_rows = collapse_peptide_fdr_evidence(_higher_better_records())

    assert len(evidence_rows) == 3
    by_peptide = {entry.canonical_peptide: entry for entry in evidence_rows}
    assert by_peptide["PEPA"].psm_count == 2
    assert by_peptide["PEPA"].spectrum_count == 2
    assert by_peptide["PEPA"].charge_states == (2, 3)
    assert by_peptide["PEPA"].protein_refs == ("P11111", "P22222")
    assert by_peptide["PEPA"].supporting_spectrum_ids == ("scan=1001", "scan=1002")


def test_peptide_target_decoy_fdr_report_keeps_monotonic_q_values_after_collapse() -> (
    None
):
    report = build_peptide_target_decoy_fdr_report(
        _higher_better_records(),
        threshold=0.5,
    )

    assert report.summary.total_peptide_count == 3
    assert report.summary.accepted_peptide_count == 3
    assert report.summary.q_values_monotonic is True
    assert [entry.evidence.canonical_peptide for entry in report.entries] == [
        "PEPA",
        "DECOYPEP",
        "PEPB",
    ]
    assert [entry.cumulative_targets for entry in report.entries] == [1, 1, 2]
    assert [entry.cumulative_decoys for entry in report.entries] == [0, 1, 1]
    assert [entry.raw_fdr for entry in report.entries] == [0.0, 1.0, 0.5]
    assert [entry.q_value for entry in report.entries] == [0.0, 0.5, 0.5]


def test_combined_evidence_policy_uses_support_to_break_score_ties() -> None:
    records = (
        PsmRecord(
            spectrum_id="scan=2001",
            peptide="TIEA",
            canonical_peptide="TIEA",
            charge=2,
            score=50.0,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=2002",
            peptide="TIEA",
            canonical_peptide="TIEA",
            charge=2,
            score=50.0,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=2003",
            peptide="TIEB",
            canonical_peptide="TIEB",
            charge=2,
            score=50.0,
            protein_refs=("P22222",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )

    report = build_peptide_target_decoy_fdr_report(
        records,
        evidence_policy="combined_evidence",
    )

    assert [entry.evidence.canonical_peptide for entry in report.entries] == [
        "TIEA",
        "TIEB",
    ]
    assert [entry.tie_group_size for entry in report.entries] == [1, 1]


def test_peptide_target_decoy_fdr_renderers_emit_stable_ledgers() -> None:
    report = build_peptide_target_decoy_fdr_report(
        _higher_better_records(),
        threshold=0.5,
    )

    summary_tsv = render_peptide_target_decoy_fdr_summary_tsv(report)
    entries_tsv = render_peptide_target_decoy_fdr_tsv(report)

    assert summary_tsv.startswith(
        "score_orientation\tevidence_policy\tthreshold\ttotal_peptide_count"
    )
    assert "reproducibility_hash" in summary_tsv
    assert entries_tsv.startswith(
        "rank\ttie_group_rank\ttie_group_size\tpeptide\tcanonical_peptide"
    )
    assert "PEPA\tPEPA\t100.0" in entries_tsv
